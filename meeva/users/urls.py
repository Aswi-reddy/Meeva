from django.urls import path
from . import views

urlpatterns = [
    # User Authentication
    path('login/', views.user_login, name='user_login'),
    path('register/', views.user_register, name='user_register'),
    path('logout/', views.user_logout, name='user_logout'),

    # Forgot Password
    path('forgot-password/', views.user_forgot_password, name='user_forgot_password'),
    path('verify-otp/', views.user_verify_otp, name='user_verify_otp'),
    path('reset-password/', views.user_reset_password, name='user_reset_password'),

    # Browse & Shop
    path('products/', views.browse_products, name='browse_products'),
    path('checkout/<int:product_id>/', views.checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),

    # Cart
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/success/', views.cart_order_success, name='cart_order_success'),

    # My Orders
    path('my-orders/', views.my_orders, name='my_orders'),

    # Wishlist
    path('wishlist/', views.view_wishlist, name='view_wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
]
