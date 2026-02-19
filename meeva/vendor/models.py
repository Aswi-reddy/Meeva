from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from decimal import Decimal


class Vendor(models.Model):
    """Vendor model for multi-vendor marketplace"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    # Basic Information
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, max_length=255)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number')]
    )
    password = models.CharField(max_length=255)
    
    # Business Information
    business_name = models.CharField(max_length=255)
    business_address = models.TextField()
    business_description = models.TextField(blank=True, null=True)
    
    # KYC Documents
    aadhar_number = models.CharField(
        max_length=12,
        validators=[RegexValidator(r'^\d{12}$', 'Aadhar must be 12 digits')]
    )
    pan_number = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', 'Enter valid PAN format')]
    )
    license_number = models.CharField(max_length=50)
    
    # Document Uploads
    aadhar_image = models.ImageField(upload_to='vendor_documents/aadhar/', null=True, blank=True)
    pan_image = models.ImageField(upload_to='vendor_documents/pan/', null=True, blank=True)
    license_image = models.ImageField(upload_to='vendor_documents/license/', null=True, blank=True)
    
    # Bank Details
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(
        max_length=11,
        validators=[RegexValidator(r'^[A-Z]{4}0[A-Z0-9]{6}$', 'Enter valid IFSC code')]
    )
    account_holder_name = models.CharField(max_length=255)
    
    # Platform Settings
    platform_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Status and Verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True)
    
    # Admin Actions
    rejection_reason = models.TextField(blank=True, null=True)
    approved_by = models.CharField(max_length=255, blank=True, null=True)  # Admin email
    approved_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.business_name} ({self.email})"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
