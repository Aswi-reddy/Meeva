from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views

urlpatterns = [
    # Docs
    path('schema/', SpectacularAPIView.as_view(), name='api_schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api_schema'), name='api_docs'),

    # Auth
    path('auth/login/', views.AuthLoginView.as_view(), name='api_auth_login'),
    path('auth/register/', views.AuthRegisterView.as_view(), name='api_auth_register'),
    path('auth/forgot-password/', views.AuthForgotPasswordView.as_view(), name='api_auth_forgot_password'),
    path('auth/verify-otp/', views.AuthVerifyOTPView.as_view(), name='api_auth_verify_otp'),
    path('auth/reset-password/', views.AuthResetPasswordView.as_view(), name='api_auth_reset_password'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='api_auth_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='api_auth_verify'),
    path('auth/logout/', views.AuthLogoutView.as_view(), name='api_auth_logout'),

    # Me
    path('me/', views.MeView.as_view(), name='api_me'),

    # Health
    path('health/', views.HealthView.as_view(), name='api_health'),

    # Products
    path('products/', views.ProductListView.as_view(), name='api_products_list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='api_products_detail'),

    # Orders
    path('orders/', views.UserOrderListCreateView.as_view(), name='api_orders_list_create'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='api_orders_detail'),
    path('orders/<int:order_id>/cancel/', views.OrderCancelView.as_view(), name='api_orders_cancel'),

    # Wishlist (User)
    path('wishlist/', views.WishlistListView.as_view(), name='api_wishlist_list'),
    path('wishlist/toggle/', views.WishlistToggleView.as_view(), name='api_wishlist_toggle'),

    # Vendor
    path('vendor/products/', views.VendorProductListCreateView.as_view(), name='api_vendor_products_list_create'),
    path('vendor/products/<int:pk>/', views.VendorProductDetailView.as_view(), name='api_vendor_products_detail'),
    path('vendor/orders/', views.VendorOrderListView.as_view(), name='api_vendor_orders_list'),
    path('vendor/orders/<int:order_id>/status/', views.VendorOrderStatusUpdateView.as_view(), name='api_vendor_order_status'),
    path('vendor/dashboard/', views.VendorDashboardView.as_view(), name='api_vendor_dashboard'),
    path('vendor/sales-report/', views.VendorSalesReportView.as_view(), name='api_vendor_sales_report'),

    # Admin
    path('admin/vendors/', views.AdminVendorListView.as_view(), name='api_admin_vendors_list'),
    path('admin/vendors/<int:pk>/', views.AdminVendorDetailView.as_view(), name='api_admin_vendors_detail'),
    path('admin/vendors/<int:vendor_id>/approve/', views.AdminVendorApproveView.as_view(), name='api_admin_vendors_approve'),
    path('admin/vendors/<int:vendor_id>/reject/', views.AdminVendorRejectView.as_view(), name='api_admin_vendors_reject'),
    path('admin/vendors/<int:vendor_id>/suspend/', views.AdminVendorSuspendView.as_view(), name='api_admin_vendors_suspend'),
    path('admin/vendors/<int:vendor_id>/activate/', views.AdminVendorActivateView.as_view(), name='api_admin_vendors_activate'),
]
