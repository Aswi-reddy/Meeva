from rest_framework.permissions import BasePermission


class IsVendorUser(BasePermission):
    """Allows access only to authenticated users linked to a Vendor via OneToOne."""

    message = 'Vendor authentication required.'

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False

        vendor = getattr(user, 'meeva_vendor', None)
        if vendor is None:
            return False

        return bool(getattr(vendor, 'is_active', True))


class IsCustomerUser(BasePermission):
    """Allows access only to authenticated users linked to a Customer (users.User) via OneToOne."""

    message = 'Customer authentication required.'

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False

        customer = getattr(user, 'meeva_customer', None)
        if customer is None:
            return False

        return bool(getattr(customer, 'is_active', True))


class IsCoreAdminUser(BasePermission):
    """Allows access only to authenticated users linked to a Core Admin via OneToOne."""

    message = 'Admin authentication required.'

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False

        admin = getattr(user, 'meeva_core_admin', None)
        if admin is None:
            return False

        return bool(getattr(admin, 'is_active', True))
