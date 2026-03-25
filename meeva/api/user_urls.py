from django.urls import path

from . import user_views

urlpatterns = [
    path('cart/', user_views.UserCartView.as_view(), name='api_user_cart'),
    path('wishlist/', user_views.UserWishlistView.as_view(), name='api_user_wishlist'),
    path('orders/', user_views.UserOrdersView.as_view(), name='api_user_orders'),
    path('orders/<int:order_id>/', user_views.UserOrderDetailView.as_view(), name='api_user_order_detail'),
    path('checkout/', user_views.UserCheckoutView.as_view(), name='api_user_checkout'),
]
