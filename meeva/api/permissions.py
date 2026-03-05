from __future__ import annotations

from rest_framework.permissions import BasePermission


class IsRole(BasePermission):
    """Allow access only to principals with a given role."""

    required_role: str = ''

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        return getattr(user, 'role', None) == self.required_role


class IsUser(IsRole):
    required_role = 'user'


class IsVendor(IsRole):
    required_role = 'vendor'


class IsAdmin(IsRole):
    required_role = 'admin'
