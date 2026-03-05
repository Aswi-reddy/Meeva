from __future__ import annotations

from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.conf import settings
from django.db import connection
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from core_admin.models import Admin
from users.models import User, Wishlist, PasswordResetOTP
from vendor.models import Vendor, Product, Order

from .permissions import IsUser, IsVendor, IsAdmin
from .pagination import OptionalPageNumberPagination
from .serializers import (
    ProductSerializer,
    VendorProductUpsertSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    WishlistItemSerializer,
    AdminVendorSerializer,
    UserRegisterSerializer,
    ForgotPasswordSerializer,
    VerifyOTPSerializer,
    ResetPasswordSerializer,
)

import hashlib


def _auth_username(role: str, email: str) -> str:
    role = (role or '').strip().lower()
    email = (email or '').strip().lower()
    digest = hashlib.sha256(f"{role}:{email}".encode('utf-8')).hexdigest()[:32]
    return f"meeva:{role}:{digest}"


def _issue_tokens(role: str, entity_id: int, email: str) -> dict:
    """Issue refresh/access tokens carrying Meeva-specific claims."""
    username = _auth_username(role, email)
    auth_user, _ = DjangoUser.objects.get_or_create(
        username=username,
        defaults={'email': email, 'is_active': True},
    )

    refresh = RefreshToken.for_user(auth_user)
    refresh['role'] = role
    refresh['entity_id'] = int(entity_id)
    refresh['email'] = email

    access = refresh.access_token
    return {
        'refresh': str(refresh),
        'access': str(access),
    }


class AuthLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_login'

    def post(self, request):
        role = (request.data.get('role') or '').strip().lower()
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''

        if role not in {'user', 'vendor', 'admin'}:
            return Response({'detail': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)
        if not email or not password:
            return Response({'detail': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate against existing custom tables (keeps current flow untouched).
        if role == 'user':
            principal_obj = User.objects.filter(email=email, is_active=True).first()
            if not principal_obj or not check_password(password, principal_obj.password):
                return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        elif role == 'vendor':
            principal_obj = Vendor.objects.filter(email=email, is_active=True).first()
            if not principal_obj or not check_password(password, principal_obj.password):
                return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

            if principal_obj.status in {'rejected', 'suspended'}:
                return Response({'detail': f'Vendor status is "{principal_obj.status}".'}, status=status.HTTP_403_FORBIDDEN)

        else:  # admin
            principal_obj = Admin.objects.filter(email=email, is_active=True).first()
            if not principal_obj or not check_password(password, principal_obj.password):
                return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        tokens = _issue_tokens(role=role, entity_id=principal_obj.id, email=email)

        return Response(
            {
                'role': role,
                'id': principal_obj.id,
                'email': email,
                'tokens': tokens,
            },
            status=status.HTTP_200_OK,
        )


class AuthLogoutView(APIView):
    """Blacklist a refresh token (JWT logout)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get('refresh')
        if not refresh:
            return Response({'detail': 'refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except TokenError:
            return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            # If blacklist app isn't migrated/available, surface a clean error.
            return Response({'detail': 'Logout not available on this deployment.'}, status=status.HTTP_501_NOT_IMPLEMENTED)

        return Response(status=status.HTTP_204_NO_CONTENT)


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Minimal DB check (fast): SELECT 1
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
        except Exception:
            return Response({'status': 'down'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({'status': 'ok'}, status=status.HTTP_200_OK)


class AuthRegisterView(APIView):
    """Register a new customer (users.User).

    This intentionally does not create a Django auth user or issue JWTs.
    Clients should call /auth/login/ after registration.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Best-effort welcome email (do not block registration)
        try:
            send_mail(
                subject='🎉 Welcome to Meeva!',
                message=(
                    f"Hello {user.first_name},\n\n"
                    f"Welcome to Meeva! Your account has been created successfully.\n\n"
                    f"Account Details:\n"
                    f"• Name: {user.first_name} {user.last_name}\n"
                    f"• Email: {user.email}\n\n"
                    f"You can now log in and start shopping from our marketplace.\n\n"
                    f"Login here: http://localhost:8000/user/login/\n\n"
                    f"Team Meeva"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass

        return Response(
            {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            status=status.HTTP_201_CREATED,
        )


class AuthForgotPasswordView(APIView):
    """Start OTP-based password reset for user/vendor."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_otp'

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data['role']
        email = serializer.validated_data['email']

        # Don't leak whether the email exists: return generic 200.
        if role == 'user':
            principal = User.objects.filter(email=email, is_active=True).first()
            greeting_name = principal.first_name if principal else 'there'
            subject = '🔐 Password Reset OTP - Meeva'
        else:
            principal = Vendor.objects.filter(email=email, is_active=True).first()
            greeting_name = principal.full_name if principal else 'there'
            subject = '🔐 Password Reset OTP - Meeva Vendor'

        if principal:
            otp_code = PasswordResetOTP.generate_otp()
            PasswordResetOTP.objects.filter(email=email, role=role).delete()
            PasswordResetOTP.objects.create(
                email=email,
                otp=otp_code,
                role=role,
                expires_at=timezone.now() + timezone.timedelta(minutes=10),
            )
            try:
                send_mail(
                    subject=subject,
                    message=(
                        f"Hello {greeting_name},\n\n"
                        f"Your OTP for password reset is: {otp_code}\n\n"
                        f"This OTP is valid for 10 minutes.\n\n"
                        f"If you did not request this, please ignore this email.\n\n"
                        f"Team Meeva"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception:
                # Only error if we were actually trying to send.
                return Response({'detail': 'Failed to send OTP email.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'detail': 'If an account exists, an OTP has been sent.'}, status=status.HTTP_200_OK)


class AuthVerifyOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_otp'

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data['role']
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        otp_record = PasswordResetOTP.objects.filter(
            email=email,
            role=role,
            otp=otp,
            is_verified=False,
        ).first()
        if not otp_record:
            return Response({'detail': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        if otp_record.is_expired:
            return Response({'detail': 'OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        otp_record.is_verified = True
        otp_record.save(update_fields=['is_verified'])
        return Response({'detail': 'OTP verified.'}, status=status.HTTP_200_OK)


class AuthResetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_otp'

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data['role']
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        otp_record = PasswordResetOTP.objects.filter(
            email=email,
            role=role,
            otp=otp,
            is_verified=True,
        ).first()
        if not otp_record:
            return Response({'detail': 'OTP not verified.'}, status=status.HTTP_400_BAD_REQUEST)
        if otp_record.is_expired:
            return Response({'detail': 'OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        if role == 'user':
            principal = User.objects.filter(email=email, is_active=True).first()
        else:
            principal = Vendor.objects.filter(email=email, is_active=True).first()
        if not principal:
            return Response({'detail': 'Account not found.'}, status=status.HTTP_404_NOT_FOUND)

        principal.password = make_password(new_password)
        principal.save(update_fields=['password'])
        PasswordResetOTP.objects.filter(email=email, role=role).delete()

        return Response({'detail': 'Password updated successfully.'}, status=status.HTTP_200_OK)


class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    pagination_class = OptionalPageNumberPagination

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related('vendor').prefetch_related('size_stocks')

        q = (self.request.query_params.get('q') or '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))

        category = (self.request.query_params.get('category') or '').strip()
        if category:
            qs = qs.filter(category=category)

        sort = (self.request.query_params.get('sort') or 'newest').strip()
        if sort == 'price_low':
            qs = qs.order_by('price')
        elif sort == 'price_high':
            qs = qs.order_by('-price')
        else:
            qs = qs.order_by('-created_at')

        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class ProductDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('vendor').prefetch_related('size_stocks')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class OrderCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsUser]
    serializer_class = OrderCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order, context={'request': request}).data, status=status.HTTP_201_CREATED)


class UserOrderListCreateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsUser]
    pagination_class = OptionalPageNumberPagination

    def get(self, request):
        qs = Order.objects.filter(buyer_email=request.user.email).select_related('product', 'vendor').order_by('-created_at')
        page = self.paginate_queryset(qs)
        if page is not None:
            data = OrderSerializer(page, many=True, context={'request': request}).data
            return self.get_paginated_response(data)
        data = OrderSerializer(qs, many=True, context={'request': request}).data
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order, context={'request': request}).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        role = getattr(request.user, 'role', None)
        entity_id = getattr(request.user, 'entity_id', None)
        email = getattr(request.user, 'email', None)

        qs = Order.objects.select_related('product', 'vendor').prefetch_related('product__size_stocks')
        if role == 'user':
            order = get_object_or_404(qs, id=pk, buyer_email=email)
        elif role == 'vendor':
            order = get_object_or_404(qs, id=pk, vendor_id=entity_id)
        elif role == 'admin':
            order = get_object_or_404(qs, id=pk)
        else:
            return Response({'detail': 'Invalid role.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(OrderSerializer(order, context={'request': request}).data, status=status.HTTP_200_OK)


class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated, IsUser]

    def post(self, request, order_id: int):
        order = get_object_or_404(
            Order.objects.select_related('product', 'vendor'),
            id=order_id,
            buyer_email=request.user.email,
        )

        if order.status != 'pending':
            return Response({'detail': 'Only pending orders can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = 'cancelled'
        order.save(update_fields=['status'])
        return Response(OrderSerializer(order, context={'request': request}).data, status=status.HTTP_200_OK)


class VendorProductListCreateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsVendor]
    pagination_class = OptionalPageNumberPagination

    def get(self, request):
        qs = (
            Product.objects.filter(vendor_id=request.user.entity_id)
            .select_related('vendor')
            .prefetch_related('size_stocks')
            .order_by('-created_at')
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            data = ProductSerializer(page, many=True, context={'request': request}).data
            return self.get_paginated_response(data)
        data = ProductSerializer(qs, many=True, context={'request': request}).data
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        vendor = Vendor.objects.get(id=request.user.entity_id)
        serializer = VendorProductUpsertSerializer(
            data=request.data,
            context={'request': request, 'vendor': vendor},
        )
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(ProductSerializer(product, context={'request': request}).data, status=status.HTTP_201_CREATED)


class VendorProductDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get_object(self, request, pk: int) -> Product:
        return Product.objects.select_related('vendor').prefetch_related('size_stocks').get(
            id=pk,
            vendor_id=request.user.entity_id,
        )

    def get(self, request, pk: int):
        product = self.get_object(request, pk)
        return Response(ProductSerializer(product, context={'request': request}).data, status=status.HTTP_200_OK)

    def put(self, request, pk: int):
        vendor = Vendor.objects.get(id=request.user.entity_id)
        product = self.get_object(request, pk)
        serializer = VendorProductUpsertSerializer(
            product,
            data=request.data,
            context={'request': request, 'vendor': vendor},
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(ProductSerializer(updated, context={'request': request}).data, status=status.HTTP_200_OK)

    def patch(self, request, pk: int):
        vendor = Vendor.objects.get(id=request.user.entity_id)
        product = self.get_object(request, pk)
        serializer = VendorProductUpsertSerializer(
            product,
            data=request.data,
            partial=True,
            context={'request': request, 'vendor': vendor},
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(ProductSerializer(updated, context={'request': request}).data, status=status.HTTP_200_OK)

    def delete(self, request, pk: int):
        product = self.get_object(request, pk)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VendorOrderListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsVendor]
    pagination_class = OptionalPageNumberPagination

    def get(self, request):
        qs = (
            Order.objects.filter(vendor_id=request.user.entity_id)
            .select_related('product', 'vendor')
            .order_by('-created_at')
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            data = OrderSerializer(page, many=True, context={'request': request}).data
            return self.get_paginated_response(data)
        return Response(OrderSerializer(qs, many=True, context={'request': request}).data, status=status.HTTP_200_OK)


class VendorOrderStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def post(self, request, order_id: int):
        new_status = (request.data.get('status') or '').strip()
        valid_statuses = [s[0] for s in Order.STATUS_CHOICES]

        if new_status not in valid_statuses:
            return Response({'detail': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            order = (
                Order.objects.select_for_update()
                .select_related('product', 'vendor')
                .get(id=order_id, vendor_id=request.user.entity_id)
            )

            previous_status = order.status
            if previous_status == new_status:
                return Response(OrderSerializer(order, context={'request': request}).data, status=status.HTTP_200_OK)

            accepted_statuses = {'confirmed', 'shipped', 'delivered'}
            if previous_status == 'pending' and new_status in accepted_statuses:
                from vendor.views import _deduct_stock_on_accept

                ok, err = _deduct_stock_on_accept(order)
                if not ok:
                    return Response({'detail': f'Cannot accept order: {err}'}, status=status.HTTP_400_BAD_REQUEST)

                from vendor.emails import send_user_order_accepted_email

                if not order.user_accepted_email_sent and send_user_order_accepted_email(order):
                    order.user_accepted_email_sent = True

            if new_status == 'delivered':
                from vendor.emails import send_user_order_delivered_email

                if not order.user_delivered_email_sent and send_user_order_delivered_email(order):
                    order.user_delivered_email_sent = True

            order.status = new_status
            order.save()

        return Response(OrderSerializer(order, context={'request': request}).data, status=status.HTTP_200_OK)


class WishlistListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsUser]
    pagination_class = OptionalPageNumberPagination

    def get(self, request):
        qs = (
            Wishlist.objects.filter(user_id=request.user.entity_id)
            .select_related('product', 'product__vendor')
            .prefetch_related('product__size_stocks')
            .order_by('-added_at')
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            data = WishlistItemSerializer(page, many=True, context={'request': request}).data
            return self.get_paginated_response(data)
        return Response(WishlistItemSerializer(qs, many=True, context={'request': request}).data, status=status.HTTP_200_OK)


class WishlistToggleView(APIView):
    permission_classes = [IsAuthenticated, IsUser]

    def post(self, request):
        product_id = request.data.get('product_id')
        try:
            product_id = int(product_id)
        except Exception:
            return Response({'detail': 'product_id must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        product = (
            Product.objects.filter(id=product_id, is_active=True)
            .select_related('vendor')
            .prefetch_related('size_stocks')
            .first()
        )
        if not product:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        item = Wishlist.objects.filter(user_id=request.user.entity_id, product_id=product_id).first()
        if item:
            item.delete()
            return Response({'in_wishlist': False}, status=status.HTTP_200_OK)

        Wishlist.objects.create(user_id=request.user.entity_id, product_id=product_id)
        return Response({'in_wishlist': True}, status=status.HTTP_200_OK)


class VendorSalesReportView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get(self, request):
        vendor_id = request.user.entity_id
        all_orders = (
            Order.objects.filter(vendor_id=vendor_id)
            .select_related('product', 'vendor')
            .order_by('-created_at')
        )
        active_orders = all_orders.exclude(status='cancelled')
        total_revenue = active_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_orders = active_orders.count()
        return Response(
            {
                'vendor_id': vendor_id,
                'total_revenue': str(total_revenue),
                'total_orders': total_orders,
                'orders': OrderSerializer(all_orders, many=True, context={'request': request}).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminVendorListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = OptionalPageNumberPagination

    def get(self, request):
        status_filter = (request.query_params.get('status') or 'all').strip()
        qs = Vendor.objects.all().order_by('-created_at')
        if status_filter != 'all':
            qs = qs.filter(status=status_filter)
        page = self.paginate_queryset(qs)
        if page is not None:
            data = AdminVendorSerializer(page, many=True, context={'request': request}).data
            return self.get_paginated_response(data)
        return Response(AdminVendorSerializer(qs, many=True, context={'request': request}).data, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.user.role
        entity_id = request.user.entity_id

        if role == 'user':
            u = get_object_or_404(User, id=entity_id, is_active=True)
            return Response(
                {
                    'role': 'user',
                    'id': u.id,
                    'email': u.email,
                    'first_name': u.first_name,
                    'last_name': u.last_name,
                    'phone': u.phone,
                    'address': u.address,
                },
                status=status.HTTP_200_OK,
            )

        if role == 'vendor':
            v = get_object_or_404(Vendor, id=entity_id, is_active=True)
            return Response(
                {
                    'role': 'vendor',
                    'id': v.id,
                    'email': v.email,
                    'vendor_id': v.vendor_id,
                    'business_name': v.business_name,
                    'status': v.status,
                },
                status=status.HTTP_200_OK,
            )

        a = get_object_or_404(Admin, id=entity_id, is_active=True)
        return Response(
            {
                'role': 'admin',
                'id': a.id,
                'email': a.email,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        # Minimal profile updates (safe fields only)
        role = request.user.role
        entity_id = request.user.entity_id

        if role != 'user':
            return Response({'detail': 'Profile update supported only for user role.'}, status=status.HTTP_403_FORBIDDEN)

        u = get_object_or_404(User, id=entity_id, is_active=True)
        for field in ['first_name', 'last_name', 'phone', 'address']:
            if field in request.data:
                setattr(u, field, (request.data.get(field) or '').strip())
        u.save()
        return self.get(request)


class VendorDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get(self, request):
        vendor = get_object_or_404(Vendor, id=request.user.entity_id, is_active=True)
        total_products = vendor.products.count()
        active_orders = vendor.orders.exclude(status='cancelled')
        total_orders = active_orders.count()
        total_revenue = active_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        recent_orders = vendor.orders.select_related('product').order_by('-created_at')[:5]

        return Response(
            {
                'vendor': {
                    'id': vendor.id,
                    'vendor_id': vendor.vendor_id,
                    'business_name': vendor.business_name,
                    'status': vendor.status,
                },
                'total_products': total_products,
                'total_orders': total_orders,
                'total_revenue': str(total_revenue),
                'recent_orders': OrderSerializer(recent_orders, many=True, context={'request': request}).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminVendorDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminVendorSerializer
    queryset = Vendor.objects.all().order_by('-created_at')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class AdminVendorApproveView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, vendor_id: int):
        vendor = get_object_or_404(Vendor, id=vendor_id)
        vendor.status = 'approved'
        vendor.approved_by = request.user.email
        vendor.approved_at = timezone.now()
        vendor.rejection_reason = None
        vendor.is_active = True
        vendor.save()

        from vendor.emails import send_vendor_approval_email

        send_vendor_approval_email(vendor, request.user.email)
        return Response(AdminVendorSerializer(vendor, context={'request': request}).data, status=status.HTTP_200_OK)


class AdminVendorRejectView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, vendor_id: int):
        reason = (request.data.get('rejection_reason') or '').strip() or 'No reason provided'
        vendor = get_object_or_404(Vendor, id=vendor_id)
        vendor.status = 'rejected'
        vendor.rejection_reason = reason
        vendor.save()

        from vendor.emails import send_vendor_rejection_email

        send_vendor_rejection_email(vendor, reason)
        return Response(AdminVendorSerializer(vendor, context={'request': request}).data, status=status.HTTP_200_OK)


class AdminVendorSuspendView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, vendor_id: int):
        vendor = get_object_or_404(Vendor, id=vendor_id)
        vendor.status = 'suspended'
        vendor.is_active = False
        vendor.save()

        from vendor.emails import send_vendor_suspension_email

        send_vendor_suspension_email(vendor)
        return Response(AdminVendorSerializer(vendor, context={'request': request}).data, status=status.HTTP_200_OK)


class AdminVendorActivateView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, vendor_id: int):
        vendor = get_object_or_404(Vendor, id=vendor_id)
        vendor.status = 'approved'
        vendor.is_active = True
        vendor.save()

        from vendor.emails import send_vendor_reactivation_email

        send_vendor_reactivation_email(vendor)
        return Response(AdminVendorSerializer(vendor, context={'request': request}).data, status=status.HTTP_200_OK)
