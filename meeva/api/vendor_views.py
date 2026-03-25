from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import TruncDate
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from vendor.emails import send_user_order_accepted_email, send_user_order_delivered_email
from vendor.models import Product, Order, ProductSizeStock

from .permissions import IsVendorUser
from .serializers import ProductDetailSerializer, OrderSerializer


def _deduct_stock_on_accept(order: Order):
    """Deduct stock for the order. Returns (ok, error_message)."""
    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=order.product_id)
        qty = int(order.quantity)

        if getattr(order, 'size', '') and ProductSizeStock.objects.filter(product=product).exists():
            row = ProductSizeStock.objects.select_for_update().filter(product=product, size=order.size).first()
            if not row:
                return False, f'Size "{order.size}" not configured for this product.'
            if row.quantity < qty:
                return False, f'Insufficient stock for size "{order.size}" (available: {row.quantity}).'

            row.quantity -= qty
            row.save(update_fields=['quantity', 'updated_at'])

            total = ProductSizeStock.objects.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
            product.quantity = int(total)
            product.save(update_fields=['quantity'])
            return True, ''

        if product.quantity < qty:
            return False, f'Insufficient stock (available: {product.quantity}).'

        product.quantity -= qty
        product.save(update_fields=['quantity'])
        return True, ''


class VendorProductsView(APIView):
    permission_classes = [IsVendorUser]

    def get(self, request):
        vendor = request.user.meeva_vendor
        qs = (
            Product.objects
            .filter(vendor=vendor)
            .select_related('vendor')
            .prefetch_related('size_stocks')
            .order_by('-created_at')
        )
        serializer = ProductDetailSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class VendorOrdersView(APIView):
    permission_classes = [IsVendorUser]

    def get(self, request):
        vendor = request.user.meeva_vendor
        qs = (
            Order.objects
            .filter(vendor=vendor)
            .select_related('product', 'vendor')
            .order_by('-created_at')
        )
        serializer = OrderSerializer(qs, many=True)
        return Response(serializer.data)


class VendorOrderStatusUpdateView(APIView):
    permission_classes = [IsVendorUser]

    def post(self, request, order_id: int):
        vendor = request.user.meeva_vendor
        order = (
            Order.objects
            .select_related('product', 'vendor')
            .filter(id=order_id, vendor=vendor)
            .first()
        )
        if not order:
            return Response({'detail': 'Not found.'}, status=404)

        new_status = (request.data.get('status') or '').strip()
        valid = [s[0] for s in Order.STATUS_CHOICES]
        if new_status not in valid:
            return Response({'detail': 'Invalid status.'}, status=400)

        previous_status = order.status
        if previous_status == new_status:
            return Response(OrderSerializer(order).data)

        accepted_statuses = {'confirmed', 'shipped', 'delivered'}
        if previous_status == 'pending' and new_status in accepted_statuses:
            ok, err = _deduct_stock_on_accept(order)
            if not ok:
                return Response({'detail': f'Cannot accept order: {err}'}, status=400)

            if not order.user_accepted_email_sent:
                if send_user_order_accepted_email(order):
                    order.user_accepted_email_sent = True

        if new_status == 'delivered' and not order.user_delivered_email_sent:
            if send_user_order_delivered_email(order):
                order.user_delivered_email_sent = True

        order.status = new_status
        order.save()

        return Response(OrderSerializer(order).data)


class VendorSalesReportView(APIView):
    permission_classes = [IsVendorUser]

    def get(self, request):
        vendor = request.user.meeva_vendor

        # Mirror existing vendor_sales_report logic:
        # - show all orders
        # - revenue + order count exclude cancelled
        all_orders = (
            Order.objects
            .filter(vendor=vendor)
            .select_related('product', 'vendor')
            .order_by('-created_at')
        )
        active_orders = all_orders.exclude(status='cancelled')

        total_revenue = active_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_orders = active_orders.count()

        cancelled_orders_count = all_orders.filter(status='cancelled').count()
        pending_count = all_orders.filter(status='pending').count()
        delivered_count = all_orders.filter(status='delivered').count()

        revenue_by_day_qs = (
            active_orders
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(revenue=Sum('total_price'))
            .order_by('day')
        )
        revenue_by_day = [
            {
                'date': (row['day'].isoformat() if row.get('day') else None),
                'revenue': str(row.get('revenue') or 0),
            }
            for row in revenue_by_day_qs
        ]

        return Response({
            'total_revenue': str(total_revenue),
            'total_orders': total_orders,
            'cancelled_orders_count': cancelled_orders_count,
            'pending_count': pending_count,
            'delivered_count': delivered_count,
            'revenue_by_day': revenue_by_day,
            'orders': OrderSerializer(all_orders, many=True).data,
        })
