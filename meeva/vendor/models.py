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
        indexes = [
            models.Index(fields=['status', 'created_at'], name='vendor_status_created_idx'),
            models.Index(fields=['is_active', 'created_at'], name='vendor_active_created_idx'),
        ]
    
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
        indexes = [
            models.Index(fields=['is_active', 'created_at'], name='product_active_created_idx'),
            models.Index(fields=['category', 'created_at'], name='product_category_created_idx'),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.vendor.business_name}"
    
    def get_sizes_list(self):
        """Return list of available sizes"""
        if self.sizes:
            return [s.strip() for s in self.sizes.split(',') if s.strip()]
        return []

    def get_sizes_with_stock(self):
        """Return list of (size, stock_qty_or_None) for templates.

        If size-wise stock rows exist, returns per-size quantity.
        Otherwise returns None for each size (legacy behavior).
        """
        sizes = self.get_sizes_list()
        stocks = {}
        try:
            # Avoid crashing templates if migrations not applied yet
            stocks = {s.size: s.quantity for s in self.size_stocks.all()}
        except Exception:
            stocks = {}

        has_specific = bool(stocks)
        if not sizes:
            return []

        if not has_specific:
            return [(s, None) for s in sizes]
        return [(s, int(stocks.get(s, 0))) for s in sizes]

    @property
    def total_available_quantity(self):
        """Total available units.

        For size-wise products, sums per-size quantities when available.
        Otherwise falls back to Product.quantity.
        """
        try:
            if hasattr(self, 'size_stocks'):
                rows = list(self.size_stocks.all())
                if rows:
                    return int(sum(s.quantity for s in rows))
        except Exception:
            pass
        return int(self.quantity)

    def available_quantity_for_size(self, size):
        """Available quantity for a given size (or global quantity fallback)."""
        size = (size or '').strip()
        if not size:
            return self.total_available_quantity

        try:
            if hasattr(self, 'size_stocks'):
                # If size-wise stock is configured, enforce it.
                # If not configured (no rows), fall back to legacy Product.quantity.
                rows = list(self.size_stocks.all())
                if not rows:
                    return int(self.quantity)

                for row in rows:
                    if row.size == size:
                        return int(row.quantity)
                return 0
        except Exception:
            pass

        return int(self.quantity)

    @property
    def is_in_stock(self):
        return self.total_available_quantity > 0


class ProductSizeStock(models.Model):
    """Size-wise stock for a product (used when Product.sizes is set)."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='size_stocks')
    size = models.CharField(max_length=50)
    quantity = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product Size Stock'
        verbose_name_plural = 'Product Size Stocks'
        unique_together = ('product', 'size')
        ordering = ['size']
        indexes = [
            models.Index(fields=['product', 'size'], name='sizestock_product_size_idx'),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.size}: {self.quantity}"


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

    # User notifications (send only once per milestone)
    user_accepted_email_sent = models.BooleanField(default=False)
    user_delivered_email_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer_email', 'created_at'], name='order_buyer_created_idx'),
            models.Index(fields=['vendor', 'status', 'created_at'], name='ord_vend_stat_cr_idx'),
            models.Index(fields=['status', 'created_at'], name='order_status_created_idx'),
        ]
    
    def __str__(self):
        return f"Order #{self.id} - {self.buyer_name}"
