from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate, get_user_model, login as django_login, logout as django_logout
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Vendor, Product, Order, ProductSizeStock
from .emails import (
    send_vendor_registration_email,
    send_user_order_accepted_email,
    send_user_order_delivered_email,
)
from users.models import PasswordResetOTP


def _safe_username_from_email(email: str, suffix: str | None = None) -> str:
    email = (email or '').strip()
    base = f"{email}_{suffix}" if suffix else email
    UserModel = get_user_model()
    max_len = UserModel._meta.get_field('username').max_length
    return (base or 'user')[:max_len]


def _split_name(full_name: str):
    full_name = (full_name or '').strip()
    if not full_name:
        return '', ''
    parts = [p for p in full_name.split(' ') if p]
    if len(parts) == 1:
        return parts[0], ''
    return parts[0], ' '.join(parts[1:])


def _get_or_create_auth_user_for_vendor(vendor: Vendor):
    """Return (auth_user, created). Ensures vendor.django_user is set."""
    if getattr(vendor, 'django_user_id', None):
        return vendor.django_user, False

    UserModel = get_user_model()
    email = (vendor.email or '').strip()
    username = _safe_username_from_email(email)

    auth_user = UserModel.objects.filter(username=username).first()
    if not auth_user:
        auth_user = UserModel.objects.filter(email=email).first()

    if auth_user:
        vendor.django_user = auth_user
        vendor.save(update_fields=['django_user'])
        return auth_user, False

    first_name, last_name = _split_name(getattr(vendor, 'full_name', ''))
    auth_user = UserModel(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_active=bool(getattr(vendor, 'is_active', True)),
    )
    auth_user.password = vendor.password or ''

    try:
        auth_user.save()
    except IntegrityError:
        auth_user.username = _safe_username_from_email(email, str(vendor.id))
        auth_user.save()

    vendor.django_user = auth_user
    vendor.save(update_fields=['django_user'])
    return auth_user, True


def _parse_size_stock_input(raw_text):
    """Parse size stock input like: 'S:10, M:0, L:5' or 'S=10,M=0'."""
    raw_text = (raw_text or '').strip()
    if not raw_text:
        return {}

    pairs = [p.strip() for p in raw_text.split(',') if p.strip()]
    result = {}
    for pair in pairs:
        if ':' in pair:
            size_part, qty_part = pair.split(':', 1)
        elif '=' in pair:
            size_part, qty_part = pair.split('=', 1)
        else:
            raise ValueError('Invalid format. Use S:10, M:0, L:5')

        size = size_part.strip()
        qty_str = qty_part.strip()
        if not size:
            raise ValueError('Size cannot be empty.')
        try:
            qty = int(qty_str)
        except ValueError:
            raise ValueError(f'Invalid quantity for size "{size}".')
        if qty < 0:
            raise ValueError('Quantity cannot be negative.')
        result[size] = qty
    return result


def _apply_size_stock(product, raw_text):
    """Upsert ProductSizeStock rows from vendor input and sync Product.quantity.

    No-op when raw_text is blank (keeps legacy/global quantity flow).
    """
    raw_text = (raw_text or '').strip()
    if not raw_text:
        # Keep existing size stock rows as-is when vendor doesn't provide input.
        return

    stock_map = _parse_size_stock_input(raw_text)
    sizes = product.get_sizes_list()

    if sizes:
        unknown = [k for k in stock_map.keys() if k not in sizes]
        if unknown:
            raise ValueError(f"Unknown size(s) not in sizes list: {', '.join(unknown)}")

    with transaction.atomic():
        if sizes:
            ProductSizeStock.objects.filter(product=product).exclude(size__in=sizes).delete()

        for size, qty in stock_map.items():
            ProductSizeStock.objects.update_or_create(
                product=product,
                size=size,
                defaults={'quantity': qty},
            )

        # Sync total quantity from per-size stock when present
        if ProductSizeStock.objects.filter(product=product).exists():
            total = ProductSizeStock.objects.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
            product.quantity = int(total)
            product.save(update_fields=['quantity'])


def _deduct_stock_on_accept(order):
    """Deduct stock for the order. Returns (ok, error_message)."""
    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=order.product_id)
        qty = int(order.quantity)

        # If product uses size-wise stock and order has size, decrement that size row.
        if getattr(order, 'size', '') and ProductSizeStock.objects.filter(product=product).exists():
            row = ProductSizeStock.objects.select_for_update().filter(product=product, size=order.size).first()
            if not row:
                return False, f'Size "{order.size}" not configured for this product.'
            if row.quantity < qty:
                return False, f'Insufficient stock for size "{order.size}" (available: {row.quantity}).'
            row.quantity -= qty
            row.save(update_fields=['quantity', 'updated_at'])

            total = ProductSizeStock.objects.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
            product.quantity = int(total)
            product.save(update_fields=['quantity'])
            return True, ''

        # Fallback: global quantity
        if product.quantity < qty:
            return False, f'Insufficient stock (available: {product.quantity}).'
        product.quantity -= qty
        product.save(update_fields=['quantity'])
        return True, ''


@csrf_protect
@require_http_methods(["GET", "POST"])
def vendor_register(request):
    """Vendor registration with document upload"""
    if request.method == "POST":
        try:
            # Basic validation
            required_fields = ['full_name', 'email', 'phone', 'password', 'confirm_password', 'business_name', 
                             'business_address', 'aadhar_number', 'pan_number', 'license_number',
                             'bank_name', 'account_number', 'ifsc_code', 'account_holder_name']
            
            for field in required_fields:
                if not request.POST.get(field):
                    messages.error(request, f'{field.replace("_", " ").title()} is required')
                    return render(request, 'vendor/register.html')
            
            # Validate password match
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            if password != confirm_password:
                messages.error(request, 'Passwords do not match! Please make sure both passwords are identical.')
                return render(request, 'vendor/register.html')
            
            if len(password) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
                return render(request, 'vendor/register.html')
            
            # Check if email already exists
            if Vendor.objects.filter(email=request.POST.get('email')).exists():
                messages.error(request, 'Email already registered. Please login.')
                return redirect('vendor_login')
            
            # Create vendor
            password_hash = make_password(password)
            vendor = Vendor.objects.create(
                full_name=request.POST.get('full_name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                password=password_hash,
                business_name=request.POST.get('business_name'),
                business_address=request.POST.get('business_address'),
                business_description=request.POST.get('business_description', ''),
                aadhar_number=request.POST.get('aadhar_number'),
                pan_number=request.POST.get('pan_number'),
                license_number=request.POST.get('license_number'),
                bank_name=request.POST.get('bank_name'),
                account_number=request.POST.get('account_number'),
                ifsc_code=request.POST.get('ifsc_code'),
                account_holder_name=request.POST.get('account_holder_name'),
                aadhar_image=request.FILES.get('aadhar_image'),
                pan_image=request.FILES.get('pan_image'),
                license_image=request.FILES.get('license_image'),
                status='pending'
            )

            # Create corresponding Django auth user and link it.
            UserModel = get_user_model()
            username = _safe_username_from_email(vendor.email)
            first_name, last_name = _split_name(vendor.full_name)
            auth_user = UserModel(
                username=username,
                email=vendor.email,
                first_name=first_name,
                last_name=last_name,
                is_active=bool(vendor.is_active),
            )
            auth_user.password = password_hash
            try:
                auth_user.save()
            except IntegrityError:
                auth_user.username = _safe_username_from_email(vendor.email, str(vendor.id))
                auth_user.save()
            vendor.django_user = auth_user
            vendor.save(update_fields=['django_user'])
            
            # Send registration confirmation email
            email_sent = send_vendor_registration_email(vendor)
            
            if email_sent:
                messages.success(request, 'Registration successful! A confirmation email has been sent to your email address. Your application is pending admin approval.')
            else:
                messages.success(request, 'Registration successful! Your application is pending admin approval.')
            
            return redirect('vendor_login')
            
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'vendor/register.html')


@csrf_protect
@require_http_methods(["GET", "POST"])
def vendor_login(request):
    """Vendor login with email or vendor ID"""
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        vendor_id = request.POST.get('vendor_id', '').strip()
        password = request.POST.get('password', '').strip()
        
        try:
            # Try to find vendor by email or vendor_id
            vendor = None
            if email:
                vendor = Vendor.objects.get(email=email, is_active=True)
            elif vendor_id:
                vendor = Vendor.objects.get(vendor_id=vendor_id, is_active=True)
            
            if not vendor:
                messages.error(request, 'Invalid email/vendor ID or password.')
                return render(request, 'vendor/login.html')
            
            if vendor.status == 'rejected':
                messages.error(request, f'Your account was rejected. Reason: {vendor.rejection_reason}')
            elif vendor.status == 'suspended':
                messages.error(request, 'Your account has been suspended. Contact admin.')
            elif check_password(password, vendor.password):
                # Allow login for pending and approved vendors
                if vendor.status in ['pending', 'approved']:
                    # Ensure corresponding Django auth user exists and is in sync.
                    auth_user, _ = _get_or_create_auth_user_for_vendor(vendor)
                    if auth_user and vendor.password and auth_user.password != vendor.password:
                        auth_user.password = vendor.password
                        auth_user.is_active = bool(vendor.is_active)
                        auth_user.save(update_fields=['password', 'is_active'])

                    # Log in via Django auth (keeps request.user consistent) while preserving legacy sessions.
                    authenticated = None
                    if auth_user:
                        authenticated = authenticate(request, username=auth_user.username, password=password)
                    if authenticated:
                        django_login(request, authenticated)
                    elif auth_user:
                        auth_user.backend = 'django.contrib.auth.backends.ModelBackend'
                        django_login(request, auth_user)

                    request.session['vendor_logged_in'] = True
                    request.session['vendor_email'] = vendor.email
                    request.session['vendor_id'] = vendor.id
                    messages.success(request, f'Welcome back, {vendor.business_name}!')
                    return redirect('vendor_dashboard')
            else:
                messages.error(request, 'Invalid email/vendor ID or password.')
        except Vendor.DoesNotExist:
            messages.error(request, 'Invalid email/vendor ID or password.')
    
    return render(request, 'vendor/login.html')


def vendor_dashboard(request):
    """Vendor dashboard - overview with statistics"""
    vendor = check_vendor_login(request)
    if not vendor:
        return redirect('vendor_login')
    
    # Get statistics (excluding cancelled orders)
    total_products = vendor.products.count()
    active_orders = vendor.orders.exclude(status='cancelled')
    total_orders = active_orders.count()
    total_revenue = active_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # Get recent 5 orders (all statuses for visibility)
    recent_orders = vendor.orders.all()[:5]
    
    context = {
        'vendor': vendor,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'vendor/dashboard.html', context)


def vendor_logout(request):
    """Logout vendor"""
    try:
        django_logout(request)
    except Exception:
        pass
    request.session.flush()
    messages.success(request, 'Successfully logged out.')
    return redirect('vendor_login')


def check_vendor_login(request):
    """Helper function to check if vendor is logged in"""
    # Primary: Django auth session + OneToOne link
    if getattr(request, 'user', None) and request.user.is_authenticated:
        vendor = getattr(request.user, 'meeva_vendor', None)
        if vendor and getattr(vendor, 'is_active', True):
            # Preserve legacy session keys for existing templates/flows
            request.session['vendor_logged_in'] = True
            request.session['vendor_email'] = vendor.email
            request.session['vendor_id'] = vendor.id
            return vendor

    # Fallback: legacy session (best-effort bridge into Django auth)
    vendor_id = request.session.get('vendor_id')
    if request.session.get('vendor_logged_in') and vendor_id:
        vendor = Vendor.objects.filter(id=vendor_id, is_active=True).first()
        if vendor:
            auth_user, _ = _get_or_create_auth_user_for_vendor(vendor)
            if auth_user:
                auth_user.backend = 'django.contrib.auth.backends.ModelBackend'
                django_login(request, auth_user)

            request.session['vendor_logged_in'] = True
            request.session['vendor_email'] = vendor.email
            request.session['vendor_id'] = vendor.id
            return vendor

    messages.warning(request, 'Please login first.')
    return None


# ==================== PRODUCT VIEWS ====================

def vendor_products(request):
    """View all vendor products"""
    vendor = check_vendor_login(request)
    if not vendor:
        return redirect('vendor_login')
    
    products = vendor.products.all().prefetch_related('size_stocks')
    context = {
        'vendor': vendor,
        'products': products,
    }
    return render(request, 'vendor/products.html', context)


@csrf_protect
@require_http_methods(["GET", "POST"])
def add_product(request):
    """Add new product"""
    vendor = check_vendor_login(request)
    if not vendor:
        return redirect('vendor_login')
    
    if request.method == "POST":
        try:
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            category = request.POST.get('category', 'other').strip()
            sizes = request.POST.get('sizes', '').strip()
            size_stock = request.POST.get('size_stock', '').strip()
            price = request.POST.get('price', '')
            quantity = request.POST.get('quantity', '')
            image = request.FILES.get('image')
            
            if not name or not description or not price or not quantity:
                messages.error(request, 'All fields are required!')
                return render(request, 'vendor/add_product.html', {'vendor': vendor, 'categories': Product.CATEGORY_CHOICES})
            
            product = Product.objects.create(
                vendor=vendor,
                name=name,
                description=description,
                category=category,
                sizes=sizes,
                price=float(price),
                quantity=int(quantity),
                image=image,
            )

            # Optional: size-wise stock input
            if sizes and size_stock:
                try:
                    _apply_size_stock(product, size_stock)
                except Exception as e:
                    messages.warning(request, f'Size-wise stock not applied: {str(e)}')
            
            messages.success(request, 'Product added successfully!')
            return redirect('vendor_products')
        
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
    
    context = {'vendor': vendor, 'categories': Product.CATEGORY_CHOICES}
    return render(request, 'vendor/add_product.html', context)


@csrf_protect
@require_http_methods(["GET", "POST"])
def edit_product(request, product_id):
    """Edit product"""
    vendor = check_vendor_login(request)
    if not vendor:
        return redirect('vendor_login')
    
    try:
        product = Product.objects.get(id=product_id, vendor=vendor)
    except Product.DoesNotExist:
        messages.error(request, 'Product not found!')
        return redirect('vendor_products')
    
    if request.method == "POST":
        try:
            product.name = request.POST.get('name', product.name)
            product.description = request.POST.get('description', product.description)
            product.category = request.POST.get('category', product.category)
            product.sizes = request.POST.get('sizes', product.sizes)
            size_stock = request.POST.get('size_stock', '').strip()
            product.price = float(request.POST.get('price', product.price))
            product.quantity = int(request.POST.get('quantity', product.quantity))
            
            if 'image' in request.FILES:
                product.image = request.FILES.get('image')
            
            product.save()

            # If size-wise stock exists, drop rows for removed sizes.
            sizes_list = product.get_sizes_list()
            if sizes_list and ProductSizeStock.objects.filter(product=product).exists():
                ProductSizeStock.objects.filter(product=product).exclude(size__in=sizes_list).delete()
                total = ProductSizeStock.objects.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
                product.quantity = int(total)
                product.save(update_fields=['quantity'])

            # Optional: update size-wise stock
            if product.sizes and size_stock:
                try:
                    _apply_size_stock(product, size_stock)
                except Exception as e:
                    messages.warning(request, f'Size-wise stock not applied: {str(e)}')
            messages.success(request, 'Product updated successfully!')
            return redirect('vendor_products')
        
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
    
    context = {'vendor': vendor, 'product': product, 'categories': Product.CATEGORY_CHOICES}
    return render(request, 'vendor/edit_product.html', context)


def delete_product(request, product_id):
    """Delete product"""
    vendor = check_vendor_login(request)
    if not vendor:
        return redirect('vendor_login')
    
    try:
        product = Product.objects.get(id=product_id, vendor=vendor)
        product.delete()
        messages.success(request, 'Product deleted successfully!')
    except Product.DoesNotExist:
        messages.error(request, 'Product not found!')
    
    return redirect('vendor_products')


# ==================== ORDER VIEWS ====================

def vendor_orders(request):
    """View all vendor orders"""
    vendor = check_vendor_login(request)
    if not vendor:
        return redirect('vendor_login')

    orders = vendor.orders.all()
    context = {
        'vendor': vendor,
        'orders': orders,
    }
    return render(request, 'vendor/orders.html', context)


def update_order_status(request, order_id):
    """Vendor accepts / rejects / updates order status"""
    vendor = check_vendor_login(request)
    if not vendor:
        return redirect('vendor_login')

    order = get_object_or_404(Order, id=order_id, vendor=vendor)
    new_status = request.POST.get('status', '').strip()
    valid = [s[0] for s in Order.STATUS_CHOICES]

    if new_status not in valid:
        messages.error(request, 'Invalid status.')
        return redirect('vendor_orders')

    previous_status = order.status
    if previous_status == new_status:
        return redirect('vendor_orders')

    # When vendor accepts (moves off pending into a fulfillment status), deduct stock.
    accepted_statuses = {'confirmed', 'shipped', 'delivered'}
    if previous_status == 'pending' and new_status in accepted_statuses:
        ok, err = _deduct_stock_on_accept(order)
        if not ok:
            messages.error(request, f'Cannot accept order: {err}')
            return redirect('vendor_orders')

        # Email user once on acceptance
        if not order.user_accepted_email_sent:
            if send_user_order_accepted_email(order):
                order.user_accepted_email_sent = True

    # Email user once on delivered
    if new_status == 'delivered' and not order.user_delivered_email_sent:
        if send_user_order_delivered_email(order):
            order.user_delivered_email_sent = True

    order.status = new_status
    order.save()
    messages.success(request, f'Order #{order.id} marked as "{order.get_status_display()}".')

    return redirect('vendor_orders')


def vendor_sales_report(request):
    """View sales report with detailed statistics"""
    vendor = check_vendor_login(request)
    if not vendor:
        return redirect('vendor_login')
    
    # Exclude cancelled orders from revenue calculations
    all_orders = vendor.orders.all()
    active_orders = vendor.orders.exclude(status='cancelled')
    total_revenue = active_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_orders_count = active_orders.count()
    
    context = {
        'vendor': vendor,
        'orders': all_orders,  # Show all orders in list for transparency
        'total_revenue': total_revenue,
        'total_orders': total_orders_count,
    }
    return render(request, 'vendor/sales_report.html', context)


# ==================== FORGOT PASSWORD VIEWS ====================

@csrf_protect
@require_http_methods(["GET", "POST"])
def vendor_forgot_password(request):
    """Step 1: Take email and send OTP"""
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'vendor/forgot_password.html')
        
        # Check if email exists in Vendor table
        try:
            vendor = Vendor.objects.get(email=email, is_active=True)
        except Vendor.DoesNotExist:
            messages.error(request, 'No vendor account found with this email address.')
            return render(request, 'vendor/forgot_password.html')
        
        # Generate OTP
        otp_code = PasswordResetOTP.generate_otp()
        
        # Delete any previous OTPs for this email & role
        PasswordResetOTP.objects.filter(email=email, role='vendor').delete()
        
        # Create new OTP
        PasswordResetOTP.objects.create(
            email=email,
            otp=otp_code,
            role='vendor',
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        
        # Send OTP via email
        try:
            send_mail(
                subject='🔐 Password Reset OTP - Meeva Vendor',
                message=f'Hello {vendor.full_name},\n\nYour OTP for password reset is: {otp_code}\n\nThis OTP is valid for 10 minutes.\n\nIf you did not request this, please ignore this email.\n\nTeam Meeva',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            request.session['reset_email'] = email
            request.session['reset_role'] = 'vendor'
            messages.success(request, 'OTP sent to your email. Please check your inbox.')
            return redirect('vendor_verify_otp')
        except Exception as e:
            messages.error(request, f'Failed to send OTP email. Please try again later.')
            return render(request, 'vendor/forgot_password.html')
    
    return render(request, 'vendor/forgot_password.html')


@csrf_protect
@require_http_methods(["GET", "POST"])
def vendor_verify_otp(request):
    """Step 2: Verify OTP"""
    email = request.session.get('reset_email')
    role = request.session.get('reset_role')
    
    if not email or role != 'vendor':
        messages.error(request, 'Session expired. Please start again.')
        return redirect('vendor_forgot_password')
    
    if request.method == "POST":
        entered_otp = request.POST.get('otp', '').strip()
        
        if not entered_otp:
            messages.error(request, 'Please enter the OTP.')
            return render(request, 'vendor/verify_otp.html', {'email': email})
        
        try:
            otp_record = PasswordResetOTP.objects.get(
                email=email, role='vendor', otp=entered_otp, is_verified=False
            )
            
            if otp_record.is_expired:
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('vendor_forgot_password')
            
            # Mark OTP as verified
            otp_record.is_verified = True
            otp_record.save()
            
            request.session['otp_verified'] = True
            messages.success(request, 'OTP verified! Please set your new password.')
            return redirect('vendor_reset_password')
            
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please try again.')
    
    return render(request, 'vendor/verify_otp.html', {'email': email})


@csrf_protect
@require_http_methods(["GET", "POST"])
def vendor_reset_password(request):
    """Step 3: Reset password"""
    email = request.session.get('reset_email')
    role = request.session.get('reset_role')
    otp_verified = request.session.get('otp_verified')
    
    if not email or role != 'vendor' or not otp_verified:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('vendor_forgot_password')
    
    if request.method == "POST":
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if not new_password or not confirm_password:
            messages.error(request, 'Both password fields are required.')
            return render(request, 'vendor/reset_password.html')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'vendor/reset_password.html')
        
        if len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'vendor/reset_password.html')
        
        try:
            vendor = Vendor.objects.get(email=email, is_active=True)
            password_hash = make_password(new_password)
            vendor.password = password_hash
            vendor.save(update_fields=['password', 'updated_at'])

            # Keep Django auth user in sync.
            auth_user, _ = _get_or_create_auth_user_for_vendor(vendor)
            if auth_user:
                auth_user.password = password_hash
                auth_user.is_active = bool(vendor.is_active)
                auth_user.save(update_fields=['password', 'is_active'])
            
            # Cleanup OTPs and session
            PasswordResetOTP.objects.filter(email=email, role='vendor').delete()
            request.session.pop('reset_email', None)
            request.session.pop('reset_role', None)
            request.session.pop('otp_verified', None)
            
            messages.success(request, 'Password updated successfully! Please login with your new password.')
            return redirect('vendor_login')
            
        except Vendor.DoesNotExist:
            messages.error(request, 'Vendor not found.')
            return redirect('vendor_forgot_password')
    
    return render(request, 'vendor/reset_password.html')
