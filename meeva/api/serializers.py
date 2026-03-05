from __future__ import annotations

from django.db.models import Sum
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from vendor.models import Product, Vendor, Order
from vendor.models import ProductSizeStock
from users.models import Wishlist, User, PasswordResetOTP


class VendorMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'vendor_id', 'business_name']


class ProductSerializer(serializers.ModelSerializer):
    vendor = VendorMiniSerializer(read_only=True)
    sizes_list = serializers.SerializerMethodField()
    sizes_with_stock = serializers.SerializerMethodField()
    total_available_quantity = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'vendor',
            'name',
            'description',
            'category',
            'sizes',
            'sizes_list',
            'sizes_with_stock',
            'price',
            'quantity',
            'total_available_quantity',
            'is_in_stock',
            'image_url',
            'is_active',
            'created_at',
            'updated_at',
        ]

    def get_sizes_list(self, obj: Product):
        return obj.get_sizes_list()

    def get_sizes_with_stock(self, obj: Product):
        return obj.get_sizes_with_stock()

    def get_image_url(self, obj: Product):
        request = self.context.get('request')
        if not obj.image:
            return None
        url = obj.image.url
        if request is None:
            return url
        return request.build_absolute_uri(url)


class VendorProductUpsertSerializer(serializers.ModelSerializer):
    size_stock = serializers.CharField(required=False, allow_blank=True, write_only=True)
    vendor = VendorMiniSerializer(read_only=True)
    sizes_list = serializers.SerializerMethodField(read_only=True)
    sizes_with_stock = serializers.SerializerMethodField(read_only=True)
    total_available_quantity = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'vendor',
            'name',
            'description',
            'category',
            'sizes',
            'size_stock',
            'sizes_list',
            'sizes_with_stock',
            'price',
            'quantity',
            'total_available_quantity',
            'is_in_stock',
            'image',
            'image_url',
            'is_active',
            'created_at',
            'updated_at',
        ]

    def get_sizes_list(self, obj: Product):
        return obj.get_sizes_list()

    def get_sizes_with_stock(self, obj: Product):
        return obj.get_sizes_with_stock()

    def get_image_url(self, obj: Product):
        request = self.context.get('request')
        if not obj.image:
            return None
        url = obj.image.url
        if request is None:
            return url
        return request.build_absolute_uri(url)

    def validate_sizes(self, value: str):
        return (value or '').strip()

    def create(self, validated_data):
        size_stock = (validated_data.pop('size_stock', '') or '').strip()
        vendor = self.context['vendor']
        product = Product.objects.create(vendor=vendor, **validated_data)

        if product.sizes and size_stock:
            from vendor.views import _apply_size_stock

            _apply_size_stock(product, size_stock)
        return product

    def update(self, instance: Product, validated_data):
        size_stock = (validated_data.pop('size_stock', '') or '').strip()
        for key, val in validated_data.items():
            setattr(instance, key, val)
        instance.save()

        # Keep size stocks consistent when sizes change even if size_stock isn't provided.
        sizes_list = instance.get_sizes_list()
        if sizes_list and ProductSizeStock.objects.filter(product=instance).exists():
            ProductSizeStock.objects.filter(product=instance).exclude(size__in=sizes_list).delete()
            total = ProductSizeStock.objects.filter(product=instance).aggregate(Sum('quantity'))['quantity__sum'] or 0
            instance.quantity = int(total)
            instance.save(update_fields=['quantity'])

        if instance.sizes and size_stock:
            from vendor.views import _apply_size_stock

            _apply_size_stock(instance, size_stock)

        return instance


class OrderCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    size = serializers.CharField(required=False, allow_blank=True, max_length=50)

    buyer_name = serializers.CharField(max_length=255)
    buyer_email = serializers.EmailField()
    buyer_phone = serializers.CharField(max_length=15)
    buyer_address = serializers.CharField()

    def validate(self, attrs):
        request = self.context.get('request')
        product_id = attrs['product_id']
        size = (attrs.get('size') or '').strip()
        qty = int(attrs['quantity'])

        # Enforce that a user can only place orders with their own email.
        if request is not None and getattr(getattr(request, 'user', None), 'is_authenticated', False):
            principal_email = (getattr(request.user, 'email', '') or '').strip().lower()
            buyer_email = (attrs.get('buyer_email') or '').strip().lower()
            if principal_email and buyer_email and principal_email != buyer_email:
                raise serializers.ValidationError({'buyer_email': 'Must match the authenticated user email.'})

        product = (
            Product.objects.filter(id=product_id, is_active=True)
            .select_related('vendor')
            .prefetch_related('size_stocks')
            .first()
        )
        if not product:
            raise serializers.ValidationError({'product_id': 'Product not found.'})

        # Enforce size selection if product has sizes configured
        if product.sizes and not size:
            raise serializers.ValidationError({'size': 'Size is required for this product.'})

        # Validate stock availability (size-wise when configured)
        available = product.available_quantity_for_size(size) if size else product.total_available_quantity
        if available < qty:
            raise serializers.ValidationError({'quantity': f'Only {available} units available.'})

        # Validate size exists in sizes list if provided
        sizes_list = product.get_sizes_list()
        if size and sizes_list and size not in sizes_list:
            raise serializers.ValidationError({'size': 'Invalid size for this product.'})

        attrs['product'] = product
        attrs['vendor'] = product.vendor
        attrs['size'] = size
        return attrs

    def create(self, validated_data):
        product = validated_data['product']
        vendor = validated_data['vendor']
        qty = int(validated_data['quantity'])
        size = validated_data.get('size', '')

        total_price = product.price * qty

        order = Order.objects.create(
            product=product,
            vendor=vendor,
            buyer_name=validated_data['buyer_name'],
            buyer_email=validated_data['buyer_email'],
            buyer_phone=validated_data['buyer_phone'],
            buyer_address=validated_data['buyer_address'],
            quantity=qty,
            size=size,
            price_per_unit=product.price,
            total_price=total_price,
            status='pending',
        )

        # Notify vendor (reuse existing behavior)
        try:
            from users.views import send_order_notification_email

            send_order_notification_email(order)
        except Exception:
            # Keep API order creation successful even if email fails
            pass

        return order


class OrderSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'product',
            'vendor_id',
            'buyer_name',
            'buyer_email',
            'buyer_phone',
            'buyer_address',
            'quantity',
            'size',
            'price_per_unit',
            'total_price',
            'status',
            'created_at',
            'updated_at',
        ]


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'added_at']


class UserRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)
    phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value: str):
        value = (value or '').strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already registered.')
        return value

    def validate(self, attrs):
        password = attrs.get('password') or ''
        confirm = attrs.get('confirm_password') or ''
        if password != confirm:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        if len(password) < 6:
            raise serializers.ValidationError({'password': 'Password must be at least 6 characters long.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        raw_password = validated_data.pop('password')
        return User.objects.create(
            **validated_data,
            password=make_password(raw_password),
        )


class ForgotPasswordSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['user', 'vendor'])
    email = serializers.EmailField(max_length=255)

    def validate_email(self, value: str):
        return (value or '').strip().lower()


class VerifyOTPSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['user', 'vendor'])
    email = serializers.EmailField(max_length=255)
    otp = serializers.CharField(max_length=6)

    def validate_email(self, value: str):
        return (value or '').strip().lower()

    def validate_otp(self, value: str):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('OTP is required.')
        return value


class ResetPasswordSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['user', 'vendor'])
    email = serializers.EmailField(max_length=255)
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    def validate_email(self, value: str):
        return (value or '').strip().lower()

    def validate(self, attrs):
        new_password = (attrs.get('new_password') or '').strip()
        confirm = (attrs.get('confirm_password') or '').strip()
        if new_password != confirm:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        if len(new_password) < 6:
            raise serializers.ValidationError({'new_password': 'Password must be at least 6 characters long.'})
        return attrs


class AdminVendorSerializer(serializers.ModelSerializer):
    aadhar_image_url = serializers.SerializerMethodField()
    pan_image_url = serializers.SerializerMethodField()
    license_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = [
            'id',
            'vendor_id',
            'full_name',
            'email',
            'phone',
            'business_name',
            'business_address',
            'business_description',
            'aadhar_number',
            'pan_number',
            'license_number',
            'aadhar_image_url',
            'pan_image_url',
            'license_image_url',
            'platform_fee_percentage',
            'status',
            'is_active',
            'rejection_reason',
            'approved_by',
            'approved_at',
            'created_at',
            'updated_at',
        ]

    def _abs(self, request, url: str | None):
        if not url:
            return None
        if request is None:
            return url
        return request.build_absolute_uri(url)

    def get_aadhar_image_url(self, obj: Vendor):
        request = self.context.get('request')
        return self._abs(request, obj.aadhar_image.url if obj.aadhar_image else None)

    def get_pan_image_url(self, obj: Vendor):
        request = self.context.get('request')
        return self._abs(request, obj.pan_image.url if obj.pan_image else None)

    def get_license_image_url(self, obj: Vendor):
        request = self.context.get('request')
        return self._abs(request, obj.license_image.url if obj.license_image else None)
