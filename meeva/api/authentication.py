from __future__ import annotations

from typing import Optional, Tuple

from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication

from .principals import MeevaPrincipal


class MeevaJWTAuthentication(JWTAuthentication):
    """JWT authentication that returns a role-aware principal.

    We intentionally avoid depending on Django's auth user model for business auth,
    because this codebase currently uses custom User/Vendor/Admin tables.

    Tokens are issued by the API login endpoint with custom claims:
    - role: 'user' | 'vendor' | 'admin'
    - entity_id: the corresponding model PK
    - email: login email
    """

    def authenticate(self, request: Request) -> Optional[Tuple[MeevaPrincipal, object]]:
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except Exception as exc:
            raise exceptions.AuthenticationFailed('Invalid token.') from exc

        role = validated_token.get('role')
        entity_id = validated_token.get('entity_id')
        email = validated_token.get('email')

        if not role or not entity_id or not email:
            raise exceptions.AuthenticationFailed('Token missing required claims.')

        principal = MeevaPrincipal(role=str(role), entity_id=int(entity_id), email=str(email))
        return principal, validated_token
