from django.contrib import admin

from .models import Vendor, Product, Order, ProductSizeStock


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
	list_display = ['id', 'vendor_id', 'business_name', 'email', 'status', 'is_active', 'created_at']
	search_fields = ['vendor_id', 'business_name', 'email', 'phone']
	list_filter = ['status', 'is_active', 'created_at']
	readonly_fields = ['vendor_id', 'created_at', 'updated_at', 'approved_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ['id', 'name', 'vendor', 'category', 'price', 'quantity', 'is_active', 'created_at']
	search_fields = ['name', 'description', 'vendor__business_name', 'vendor__email']
	list_filter = ['category', 'is_active', 'created_at']
	raw_id_fields = ['vendor']
	readonly_fields = ['created_at', 'updated_at']


@admin.register(ProductSizeStock)
class ProductSizeStockAdmin(admin.ModelAdmin):
	list_display = ['id', 'product', 'size', 'quantity', 'updated_at']
	search_fields = ['product__name', 'size']
	list_filter = ['size', 'updated_at']
	raw_id_fields = ['product']
	readonly_fields = ['updated_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ['id', 'vendor', 'product', 'buyer_email', 'quantity', 'status', 'total_price', 'created_at']
	search_fields = ['buyer_email', 'buyer_name', 'vendor__business_name', 'product__name']
	list_filter = ['status', 'created_at']
	raw_id_fields = ['vendor', 'product']
	readonly_fields = ['created_at', 'updated_at']
