from django.contrib import admin

from .models import Admin


@admin.register(Admin)
class CoreAdminAdmin(admin.ModelAdmin):
	list_display = ['id', 'email', 'is_active', 'created_at', 'updated_at']
	search_fields = ['email']
	list_filter = ['is_active', 'created_at']
	readonly_fields = ['created_at', 'updated_at']
