from django.contrib.auth.models import AnonymousUser
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from vendor.models import Product

from .serializers import ProductSerializer, ProductDetailSerializer


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def me(request):
    """Return info about the current Django-authenticated user and linked role records.

    Uses session auth (cookie) and does not change any UI flow.
    """
    user = getattr(request, 'user', None)
    is_authenticated = bool(user and not isinstance(user, AnonymousUser) and user.is_authenticated)

    payload = {
        'is_authenticated': is_authenticated,
        'user': None,
        'roles': {
            'customer': None,
            'vendor': None,
            'core_admin': None,
        },
    }

    if not is_authenticated:
        return Response(payload)

    payload['user'] = {
        'id': user.id,
        'username': getattr(user, 'username', ''),
        'email': getattr(user, 'email', ''),
        'first_name': getattr(user, 'first_name', ''),
        'last_name': getattr(user, 'last_name', ''),
    }

    customer = getattr(user, 'meeva_customer', None)
    if customer is not None:
        payload['roles']['customer'] = {
            'id': customer.id,
            'email': getattr(customer, 'email', ''),
        }

    vendor = getattr(user, 'meeva_vendor', None)
    if vendor is not None:
        payload['roles']['vendor'] = {
            'id': vendor.id,
            'vendor_id': getattr(vendor, 'vendor_id', ''),
            'email': getattr(vendor, 'email', ''),
            'business_name': getattr(vendor, 'business_name', ''),
            'status': getattr(vendor, 'status', ''),
        }

    core_admin = getattr(user, 'meeva_core_admin', None)
    if core_admin is not None:
        payload['roles']['core_admin'] = {
            'id': core_admin.id,
            'email': getattr(core_admin, 'email', ''),
        }

    return Response(payload)


class ProductListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        qs = (
            Product.objects
            .filter(is_active=True)
            .select_related('vendor')
            .order_by('-created_at')
        )
        serializer = ProductSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class ProductDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, product_id: int):
        product = (
            Product.objects
            .select_related('vendor')
            .prefetch_related('size_stocks')
            .filter(is_active=True, id=product_id)
            .first()
        )
        if not product:
            return Response({'detail': 'Not found.'}, status=404)
        serializer = ProductDetailSerializer(product, context={'request': request})
        return Response(serializer.data)
