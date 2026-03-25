from django.urls import path, include

from . import views

urlpatterns = [
    path('auth/me/', views.me, name='api_me'),
    path('products/', views.ProductListView.as_view(), name='api_products_list'),
    path('products/<int:product_id>/', views.ProductDetailView.as_view(), name='api_products_detail'),
    path('admin/', include('api.admin_urls')),
    path('user/', include('api.user_urls')),
    path('vendor/', include('api.vendor_urls')),
]
