from django.db import models
from django.conf import settings


class Admin(models.Model):
    email = models.EmailField(unique=True, max_length=255)
    django_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='meeva_core_admin',
    )
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Admin'
        verbose_name_plural = 'Admins'
        ordering = ['-created_at']

    def __str__(self):
        return self.email
