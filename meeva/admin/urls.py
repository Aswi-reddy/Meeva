from django.urls import path
from . import views

urlpatterns = [
    # Admin authentication
    path('login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.admin_logout, name='admin_logout'),
    
    # Vendor Management
    path('pending-vendors/', views.pending_vendors, name='pending_vendors'),
    path('vendors/', views.all_vendors, name='all_vendors'),
    path('vendor/<int:vendor_id>/', views.vendor_detail, name='vendor_detail'),
    path('vendor/<int:vendor_id>/approve/', views.approve_vendor, name='approve_vendor'),
    path('vendor/<int:vendor_id>/reject/', views.reject_vendor, name='reject_vendor'),
    path('vendor/<int:vendor_id>/suspend/', views.suspend_vendor, name='suspend_vendor'),
    path('vendor/<int:vendor_id>/activate/', views.activate_vendor, name='activate_vendor'),
]
