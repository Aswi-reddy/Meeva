from decimal import Decimal

from django.core.mail import send_mail
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Wishlist
from vendor.models import Product, Order

from .permissions import IsCustomerUser
from .serializers import (
    CartAddItemSerializer,
    CartRemoveItemSerializer,
    CartUpdateItemSerializer,
    CheckoutFromCartSerializer,
    CheckoutSingleProductSerializer,
    CustomerOrderSerializer,
    WishlistItemSerializer,
)


def _get_customer(request):
    return request.user.meeva_customer


def _cart_key(product_id: int, size: str) -> str:
    size = (size or '').strip()
    return f"{product_id}-{size}" if size else str(product_id)


def _cart_totals(cart: dict) -> dict:
    cart_items = []
    total = Decimal('0')
    cart_count = 0

    for key, item in cart.items():
        try:
            price = Decimal(str(item.get('price') or '0'))
        except Exception:
            price = Decimal('0')
        qty = int(item.get('quantity') or 0)
        cart_count += max(qty, 0)

        subtotal = price * qty
        total += subtotal

        cart_items.append({
            **item,
            'cart_key': key,
            'subtotal': str(subtotal),
        })

    return {
        'items': cart_items,
        'total': str(total),
        'cart_count': cart_count,
    }


def _send_order_notification_email(order: Order) -> bool:
    try:
        subject = f"New Order #{order.id} - {order.product.name}"
        size_line = f"\n- Size: {order.size}" if order.size else ""
        message = f"""
Dear {order.vendor.business_name},

A new order has been placed for your product!

Order Details:
- Order ID: {order.id}
- Product: {order.product.name}
- Quantity: {order.quantity}{size_line}
- Price per Unit: ₹{order.price_per_unit}
- Total Amount: ₹{order.total_price}

Buyer Details:
- Name: {order.buyer_name}
- Email: {order.buyer_email}
- Phone: {order.buyer_phone}
- Address: {order.buyer_address}

Please log in to your vendor dashboard to manage this order.

Best regards,
Meeva Team
        """
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [order.vendor.email],
            fail_silently=True,
        )
        return True
    except Exception:
        return False


class UserCartView(APIView):
    permission_classes = [IsCustomerUser]

    def get(self, request):
        cart = request.session.get('cart', {})
        return Response(_cart_totals(cart))

    def post(self, request):
        serializer = CartAddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        selected_size = (serializer.validated_data.get('size') or '').strip()

        product = (
            Product.objects
            .filter(id=product_id, is_active=True)
            .select_related('vendor')
            .prefetch_related('size_stocks')
            .first()
        )
        if not product:
            return Response({'detail': 'Product not found.'}, status=404)

        if product.get_sizes_list() and not selected_size:
            return Response({'detail': 'Please select a size.'}, status=400)

        available = product.available_quantity_for_size(selected_size) if selected_size else product.total_available_quantity
        if available < 1:
            return Response({'detail': 'Out of stock.'}, status=400)

        cart = request.session.get('cart', {})
        key = _cart_key(product_id, selected_size)

        if key in cart:
            if int(cart[key].get('quantity') or 0) < int(available):
                cart[key]['quantity'] = int(cart[key].get('quantity') or 0) + 1
            else:
                return Response({'detail': f'Only {available} units available.'}, status=400)
        else:
            cart[key] = {
                'product_id': product_id,
                'name': product.name,
                'price': str(product.price),
                'quantity': 1,
                'image': (product.image.url if product.image else None),
                'vendor_id': product.vendor.id,
                'vendor_name': product.vendor.business_name,
                'max_qty': int(available),
                'size': selected_size,
            }

        # Keep max_qty current
        cart[key]['max_qty'] = int(available)

        request.session['cart'] = cart
        return Response(_cart_totals(cart))

    def patch(self, request):
        serializer = CartUpdateItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart_key = serializer.validated_data['cart_key']
        quantity = int(serializer.validated_data['quantity'])

        cart = request.session.get('cart', {})
        if cart_key not in cart:
            return Response({'detail': 'Cart item not found.'}, status=404)

        if quantity <= 0:
            del cart[cart_key]
            request.session['cart'] = cart
            return Response(_cart_totals(cart))

        item = cart[cart_key]
        product_id = int(item.get('product_id') or 0)
        selected_size = (item.get('size') or '').strip()

        product = (
            Product.objects
            .filter(id=product_id, is_active=True)
            .prefetch_related('size_stocks')
            .first()
        )
        if not product:
            return Response({'detail': 'Product no longer available.'}, status=400)

        available = product.available_quantity_for_size(selected_size) if selected_size else product.total_available_quantity
        if quantity > int(available):
            return Response({'detail': f'Only {available} units available.'}, status=400)

        item['quantity'] = quantity
        item['max_qty'] = int(available)
        cart[cart_key] = item
        request.session['cart'] = cart

        return Response(_cart_totals(cart))

    def delete(self, request):
        serializer = CartRemoveItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart_key = serializer.validated_data['cart_key']
        cart = request.session.get('cart', {})
        if cart_key in cart:
            del cart[cart_key]
            request.session['cart'] = cart
        return Response(_cart_totals(cart))


class UserWishlistView(APIView):
    permission_classes = [IsCustomerUser]

    def get(self, request):
        customer = _get_customer(request)
        qs = (
            Wishlist.objects
            .filter(user_id=customer.id)
            .select_related('product', 'product__vendor')
            .prefetch_related('product__size_stocks')
            .order_by('-added_at')
        )
        return Response(WishlistItemSerializer(qs, many=True, context={'request': request}).data)

    def post(self, request):
        product_id = int(request.data.get('product_id') or 0)
        if product_id < 1:
            return Response({'detail': 'product_id is required.'}, status=400)

        customer = _get_customer(request)
        product = Product.objects.filter(id=product_id, is_active=True).first()
        if not product:
            return Response({'detail': 'Product not found.'}, status=404)

        existing = Wishlist.objects.filter(user_id=customer.id, product_id=product_id).first()
        if existing:
            existing.delete()
            return Response({'product_id': product_id, 'in_wishlist': False})

        Wishlist.objects.create(user_id=customer.id, product_id=product_id)
        return Response({'product_id': product_id, 'in_wishlist': True}, status=201)


class UserOrdersView(APIView):
    permission_classes = [IsCustomerUser]

    def get(self, request):
        customer = _get_customer(request)
        qs = (
            Order.objects
            .filter(buyer_email=customer.email)
            .select_related('product', 'vendor')
            .order_by('-created_at')
        )
        return Response(CustomerOrderSerializer(qs, many=True, context={'request': request}).data)


class UserOrderDetailView(APIView):
    permission_classes = [IsCustomerUser]

    def get(self, request, order_id: int):
        customer = _get_customer(request)
        order = (
            Order.objects
            .filter(id=order_id, buyer_email=customer.email)
            .select_related('product', 'vendor')
            .first()
        )
        if not order:
            return Response({'detail': 'Not found.'}, status=404)
        return Response(CustomerOrderSerializer(order, context={'request': request}).data)


class UserCheckoutView(APIView):
    permission_classes = [IsCustomerUser]

    def post(self, request):
        # Mode A: checkout from cart
        if bool(request.data.get('from_cart')):
            serializer = CheckoutFromCartSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            cart = request.session.get('cart', {})
            if not cart:
                return Response({'detail': 'Your cart is empty.'}, status=400)

            buyer_name = serializer.validated_data['buyer_name'].strip()
            buyer_email = serializer.validated_data['buyer_email'].strip()
            buyer_phone = serializer.validated_data['buyer_phone'].strip()
            buyer_address = serializer.validated_data['buyer_address'].strip()

            created_orders = []
            errors = []

            for key, item in list(cart.items()):
                try:
                    product = (
                        Product.objects
                        .filter(id=item.get('product_id'), is_active=True)
                        .select_related('vendor')
                        .prefetch_related('size_stocks')
                        .first()
                    )
                    if not product:
                        errors.append(f"{item.get('name') or 'Item'} is no longer available.")
                        continue

                    qty = int(item.get('quantity') or 0)
                    selected_size = (item.get('size') or '').strip()

                    available = product.available_quantity_for_size(selected_size) if selected_size else product.total_available_quantity
                    if qty > int(available):
                        qty = int(available)
                    if qty < 1:
                        errors.append(f"{product.name} is out of stock.")
                        continue

                    order = Order.objects.create(
                        product=product,
                        vendor=product.vendor,
                        buyer_name=buyer_name,
                        buyer_email=buyer_email,
                        buyer_phone=buyer_phone,
                        buyer_address=buyer_address,
                        quantity=qty,
                        size=selected_size,
                        price_per_unit=product.price,
                        total_price=product.price * qty,
                        status='pending',
                    )
                    _send_order_notification_email(order)
                    created_orders.append(order)
                except Exception as e:
                    errors.append(str(e))

            if created_orders:
                request.session['cart'] = {}
                request.session['last_orders'] = [o.id for o in created_orders]

            payload = {
                'created_order_ids': [o.id for o in created_orders],
                'errors': errors,
                'cart': _cart_totals(request.session.get('cart', {})),
            }
            return Response(payload, status=201 if created_orders else 400)

        # Mode B: checkout a single product
        serializer = CheckoutSingleProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        quantity = int(serializer.validated_data['quantity'])
        selected_size = (serializer.validated_data.get('size') or '').strip()

        product = (
            Product.objects
            .filter(id=product_id, is_active=True)
            .select_related('vendor')
            .prefetch_related('size_stocks')
            .first()
        )
        if not product:
            return Response({'detail': 'Product not found.'}, status=404)

        if product.sizes and not selected_size:
            return Response({'detail': 'Please select a size.'}, status=400)

        available = product.available_quantity_for_size(selected_size) if selected_size else product.total_available_quantity
        if int(available) < quantity:
            return Response({'detail': f'Only {available} units available.'}, status=400)

        order = Order.objects.create(
            product=product,
            vendor=product.vendor,
            buyer_name=serializer.validated_data['buyer_name'].strip(),
            buyer_email=serializer.validated_data['buyer_email'].strip(),
            buyer_phone=serializer.validated_data['buyer_phone'].strip(),
            buyer_address=serializer.validated_data['buyer_address'].strip(),
            quantity=quantity,
            size=selected_size,
            price_per_unit=product.price,
            total_price=product.price * quantity,
            status='pending',
        )
        _send_order_notification_email(order)
        request.session['order_id'] = order.id

        return Response(CustomerOrderSerializer(order, context={'request': request}).data, status=201)
