from django.urls import path

from . import vendor_views

urlpatterns = [
    path('products/', vendor_views.VendorProductsView.as_view(), name='api_vendor_products'),
    path('orders/', vendor_views.VendorOrdersView.as_view(), name='api_vendor_orders'),
    path('orders/<int:order_id>/status/', vendor_views.VendorOrderStatusUpdateView.as_view(), name='api_vendor_order_status'),
    path('sales-report/', vendor_views.VendorSalesReportView.as_view(), name='api_vendor_sales_report'),
]
