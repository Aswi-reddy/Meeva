from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from decimal import Decimal
import random
import string


class Vendor(models.Model):
    """Vendor model for multi-vendor marketplace"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    # Unique Vendor ID
    vendor_id = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    
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
    
    def save(self, *args, **kwargs):
        """Generate unique vendor ID before saving"""
        if not self.vendor_id:
            self.vendor_id = self.generate_vendor_id()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_vendor_id():
        """Generate unique vendor ID: MEV + 8 random chars (letters + numbers)"""
        while True:
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            vendor_id = f"MEV{random_part}"
            if not Vendor.objects.filter(vendor_id=vendor_id).exists():
                return vendor_id


class Product(models.Model):
    """Product model for vendor products"""
    
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('fashion', 'Fashion'),
        ('home', 'Home'),
        ('sports', 'Sports'),
        ('books', 'Books'),
        ('beauty', 'Beauty'),
        ('toys', 'Toys'),
        ('grocery', 'Grocery'),
        ('automotive', 'Automotive'),
        ('other', 'Other'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    sizes = models.CharField(max_length=255, blank=True, default='', help_text='Comma-separated sizes e.g. S,M,L,XL or 6,7,8,9,10')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.vendor.business_name}"
    
    def get_sizes_list(self):
        """Return list of available sizes"""
        if self.sizes:
            return [s.strip() for s in self.sizes.split(',') if s.strip()]
        return []


class Order(models.Model):
    """Order model for customer purchases"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='orders')
    
    # Buyer Details
    buyer_name = models.CharField(max_length=255)
    buyer_email = models.EmailField()
    buyer_phone = models.CharField(max_length=15)
    buyer_address = models.TextField()
    
    # Order Details
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    size = models.CharField(max_length=50, blank=True, default='')
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.buyer_name}"
