from django.contrib import admin

from .models import User, Wishlist, PasswordResetOTP


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ['id', 'email', 'first_name', 'last_name', 'is_active', 'created_at']
	search_fields = ['email', 'first_name', 'last_name', 'phone']
	list_filter = ['is_active', 'created_at']
	readonly_fields = ['created_at', 'updated_at']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
	list_display = ['id', 'user', 'product', 'added_at']
	search_fields = ['user__email', 'product__name']
	list_filter = ['added_at']
	raw_id_fields = ['user', 'product']
	readonly_fields = ['added_at']


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
	list_display = ['id', 'email', 'role', 'is_verified', 'created_at', 'expires_at']
	search_fields = ['email', 'otp']
	list_filter = ['role', 'is_verified', 'created_at', 'expires_at']
	readonly_fields = ['created_at', 'expires_at']
