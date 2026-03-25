from django.urls import path

from . import admin_views

urlpatterns = [
    path('dashboard/', admin_views.AdminDashboardView.as_view(), name='api_admin_dashboard'),

    path('vendors/', admin_views.AdminVendorsView.as_view(), name='api_admin_vendors'),
    path('vendors/pending/', admin_views.AdminPendingVendorsView.as_view(), name='api_admin_pending_vendors'),
    path('vendors/<int:vendor_id>/', admin_views.AdminVendorDetailView.as_view(), name='api_admin_vendor_detail'),

    path('vendors/<int:vendor_id>/approve/', admin_views.AdminVendorApproveView.as_view(), name='api_admin_vendor_approve'),
    path('vendors/<int:vendor_id>/reject/', admin_views.AdminVendorRejectView.as_view(), name='api_admin_vendor_reject'),
    path('vendors/<int:vendor_id>/suspend/', admin_views.AdminVendorSuspendView.as_view(), name='api_admin_vendor_suspend'),
    path('vendors/<int:vendor_id>/activate/', admin_views.AdminVendorActivateView.as_view(), name='api_admin_vendor_activate'),
]
