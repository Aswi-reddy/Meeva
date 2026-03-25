from rest_framework import serializers

from vendor.models import Product, ProductSizeStock, Order
from vendor.models import Vendor

from users.models import Wishlist


class ProductSizeStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSizeStock
        fields = [
            'size',
            'quantity',
            'updated_at',
        ]


class ProductSerializer(serializers.ModelSerializer):
    vendor_business_name = serializers.CharField(source='vendor.business_name', read_only=True)
    vendor_id = serializers.CharField(source='vendor.vendor_id', read_only=True)
    image_url = serializers.SerializerMethodField()
    sizes_list = serializers.SerializerMethodField()
    total_available_quantity = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'category',
            'sizes',
            'sizes_list',
            'price',
            'quantity',
            'total_available_quantity',
            'is_in_stock',
            'image_url',
            'is_active',
            'vendor_id',
            'vendor_business_name',
            'created_at',
            'updated_at',
        ]

    def get_image_url(self, obj: Product):
        request = self.context.get('request')
        if not getattr(obj, 'image', None):
            return None
        if not obj.image:
            return None
        try:
            url = obj.image.url
        except Exception:
            return None
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_sizes_list(self, obj: Product):
        try:
            return obj.get_sizes_list()
        except Exception:
            return []


class ProductDetailSerializer(ProductSerializer):
    size_stocks = ProductSizeStockSerializer(many=True, read_only=True)

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['size_stocks']


class OrderSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_id = serializers.IntegerField(source='product.id', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'product_id',
            'product_name',
            'buyer_name',
            'buyer_email',
            'buyer_phone',
            'buyer_address',
            'quantity',
            'size',
            'price_per_unit',
            'total_price',
            'status',
            'status_display',
            'user_accepted_email_sent',
            'user_delivered_email_sent',
            'created_at',
            'updated_at',
        ]


class CustomerOrderSerializer(OrderSerializer):
    vendor_business_name = serializers.CharField(source='vendor.business_name', read_only=True)
    vendor_id = serializers.CharField(source='vendor.vendor_id', read_only=True)
    product_image_url = serializers.SerializerMethodField()

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + [
            'vendor_id',
            'vendor_business_name',
            'product_image_url',
        ]

    def get_product_image_url(self, obj: Order):
        request = self.context.get('request')
        product = getattr(obj, 'product', None)
        if not product or not getattr(product, 'image', None):
            return None
        if not product.image:
            return None
        try:
            url = product.image.url
        except Exception:
            return None
        if request:
            return request.build_absolute_uri(url)
        return url


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductDetailSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = [
            'id',
            'product',
            'added_at',
        ]


class CartAddItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    size = serializers.CharField(required=False, allow_blank=True, default='')


class CartUpdateItemSerializer(serializers.Serializer):
    cart_key = serializers.CharField()
    quantity = serializers.IntegerField(min_value=0)


class CartRemoveItemSerializer(serializers.Serializer):
    cart_key = serializers.CharField()


class CheckoutFromCartSerializer(serializers.Serializer):
    from_cart = serializers.BooleanField(default=True)
    buyer_name = serializers.CharField()
    buyer_email = serializers.EmailField()
    buyer_phone = serializers.CharField()
    buyer_address = serializers.CharField()


class CheckoutSingleProductSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    buyer_name = serializers.CharField()
    buyer_email = serializers.EmailField()
    buyer_phone = serializers.CharField()
    buyer_address = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)
    size = serializers.CharField(required=False, allow_blank=True, default='')


class AdminVendorListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Vendor
        fields = [
            'id',
            'vendor_id',
            'business_name',
            'full_name',
            'email',
            'phone',
            'status',
            'status_display',
            'is_active',
            'created_at',
            'updated_at',
        ]


class AdminVendorDetailSerializer(AdminVendorListSerializer):
    aadhar_image_url = serializers.SerializerMethodField()
    pan_image_url = serializers.SerializerMethodField()
    license_image_url = serializers.SerializerMethodField()

    class Meta(AdminVendorListSerializer.Meta):
        fields = AdminVendorListSerializer.Meta.fields + [
            'business_address',
            'business_description',
            'aadhar_number',
            'pan_number',
            'license_number',
            'bank_name',
            'account_holder_name',
            'account_number',
            'ifsc_code',
            'platform_fee_percentage',
            'rejection_reason',
            'approved_by',
            'approved_at',
            'aadhar_image_url',
            'pan_image_url',
            'license_image_url',
        ]

    def _build_file_url(self, request, field):
        if not field:
            return None
        try:
            url = field.url
        except Exception:
            return None
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_aadhar_image_url(self, obj: Vendor):
        return self._build_file_url(self.context.get('request'), getattr(obj, 'aadhar_image', None))

    def get_pan_image_url(self, obj: Vendor):
        return self._build_file_url(self.context.get('request'), getattr(obj, 'pan_image', None))

    def get_license_image_url(self, obj: Vendor):
        return self._build_file_url(self.context.get('request'), getattr(obj, 'license_image', None))


class AdminVendorRejectSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=False, allow_blank=True, default='No reason provided')
