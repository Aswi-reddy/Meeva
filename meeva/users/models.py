from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import random


class User(models.Model):
    """Customer/User model"""
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, max_length=255)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number')],
        blank=True
    )
    address = models.TextField(blank=True)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Wishlist(models.Model):
    """Wishlist model for users to save favourite products"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey('vendor.Product', on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        ordering = ['-added_at']
        unique_together = ('user', 'product')
        indexes = [
            models.Index(fields=['user', 'added_at'], name='wishlist_user_added_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name}"


class PasswordResetOTP(models.Model):
    """OTP model for password reset (shared by user and vendor)"""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('vendor', 'Vendor'),
    ]
    
    email = models.EmailField(max_length=255)
    otp = models.CharField(max_length=6)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = 'Password Reset OTP'
        verbose_name_plural = 'Password Reset OTPs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'role', 'is_verified'], name='otp_email_role_verified_idx'),
            models.Index(fields=['expires_at'], name='otp_expires_at_idx'),
        ]
    
    def __str__(self):
        return f"OTP for {self.email} ({self.role})"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)
