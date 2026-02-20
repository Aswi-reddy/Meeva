from django.urls import path
from . import views

urlpatterns = [
    # Vendor Authentication
    path('register/', views.vendor_register, name='vendor_register'),
    path('login/', views.vendor_login, name='vendor_login'),
    path('logout/', views.vendor_logout, name='vendor_logout'),

    # Vendor Dashboard
    path('dashboard/', views.vendor_dashboard, name='vendor_dashboard'),

    # Products
    path('products/', views.vendor_products, name='vendor_products'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),

    # Orders & Sales
    path('orders/', views.vendor_orders, name='vendor_orders'),
    path('orders/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('sales-report/', views.vendor_sales_report, name='vendor_sales_report'),
]
