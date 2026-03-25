from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate, get_user_model, login as django_login, logout as django_logout
from django.db import IntegrityError
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from .models import User, PasswordResetOTP, Wishlist
from vendor.models import Product, Order


def _safe_username_from_email(email: str, suffix: str | None = None) -> str:
    email = (email or '').strip()
    if suffix:
        base = f"{email}_{suffix}"
    else:
        base = email

    UserModel = get_user_model()
    max_len = UserModel._meta.get_field('username').max_length
    return (base or 'user')[:max_len]


def _get_or_create_auth_user_for_customer(customer: User):
    """Return (auth_user, created). Ensures customer.django_user is set."""
    if getattr(customer, 'django_user_id', None):
        return customer.django_user, False

    UserModel = get_user_model()
    email = (customer.email or '').strip()
    username = _safe_username_from_email(email)

    # Try exact username match first.
    auth_user = UserModel.objects.filter(username=username).first()
    if not auth_user:
        # Fallback: reuse an auth user with same email if present.
        auth_user = UserModel.objects.filter(email=email).first()

    if auth_user:
        customer.django_user = auth_user
        customer.save(update_fields=['django_user'])
        return auth_user, False

    # Create new auth user. Keep password hash identical to legacy customer.password.
    auth_user = UserModel(
        username=username,
        email=email,
        first_name=customer.first_name or '',
        last_name=customer.last_name or '',
        is_active=bool(customer.is_active),
    )
    auth_user.password = customer.password or ''

    try:
        auth_user.save()
    except IntegrityError:
        # Extremely unlikely: username collision (e.g., truncated email). Disambiguate by customer id.
        auth_user.username = _safe_username_from_email(email, str(customer.id))
        auth_user.save()

    customer.django_user = auth_user
    customer.save(update_fields=['django_user'])
    return auth_user, True


def _get_customer_from_request(request):
    """Return the meeva customer (users.User) linked to the current Django auth user, or None."""
    if not request.user.is_authenticated:
        return None
    try:
        return request.user.meeva_customer
    except User.DoesNotExist:
        return None


@csrf_protect
@require_http_methods(["GET", "POST"])
def user_login(request):
    """User login"""
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            if check_password(password, user.password):
                # Ensure a corresponding Django auth user exists and is in sync.
                auth_user, _ = _get_or_create_auth_user_for_customer(user)
                if auth_user and user.password and auth_user.password != user.password:
                    auth_user.password = user.password
                    auth_user.is_active = bool(user.is_active)
                    auth_user.save(update_fields=['password', 'is_active'])

                # Log in via Django auth (keeps request.user consistent) while preserving legacy sessions.
                authenticated = None
                if auth_user:
                    authenticated = authenticate(request, username=auth_user.username, password=password)
                if authenticated:
                    django_login(request, authenticated)
                elif auth_user:
                    # Fallback: we already validated password against legacy hash.
                    auth_user.backend = 'django.contrib.auth.backends.ModelBackend'
                    django_login(request, auth_user)

                request.session['user_logged_in'] = True
                request.session['user_email'] = email
                request.session['user_id'] = user.id
                messages.success(request, f'Welcome back, {user.first_name}!')
                
                # Redirect based on pending action
                product_id = request.session.pop('next_checkout_product_id', None)
                if product_id:
                    return redirect('checkout', product_id=product_id)

                redirect_to = request.session.pop('redirect_after_login', None)
                if redirect_to == 'cart':
                    return redirect('view_cart')

                return redirect('browse_products')
            else:
                messages.error(request, 'Invalid email or password.')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'users/login.html')


@csrf_protect
@require_http_methods(["GET", "POST"])
def user_register(request):
    """User registration"""
    if request.method == "POST":
        try:
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()
            
            if not first_name or not last_name or not email or not password:
                messages.error(request, 'All fields are required!')
                return render(request, 'users/register.html')
            
            if password != confirm_password:
                messages.error(request, 'Passwords do not match!')
                return render(request, 'users/register.html')
            
            if len(password) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
                return render(request, 'users/register.html')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered. Please login.')
                return redirect('user_login')

            password_hash = make_password(password)
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password_hash,
            )

            # Create corresponding Django auth user (username=email) and link it.
            UserModel = get_user_model()
            username = _safe_username_from_email(email)
            auth_user = UserModel(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )
            auth_user.password = password_hash
            try:
                auth_user.save()
            except IntegrityError:
                auth_user.username = _safe_username_from_email(email, str(user.id))
                auth_user.save()

            user.django_user = auth_user
            user.save(update_fields=['django_user'])

            # Send welcome email to the new user
            try:
                send_mail(
                    subject='🎉 Welcome to Meeva!',
                    message=(
                        f'Hello {first_name},\n\n'
                        f'Welcome to Meeva! Your account has been created successfully.\n\n'
                        f'Account Details:\n'
                        f'• Name: {first_name} {last_name}\n'
                        f'• Email: {email}\n\n'
                        f'You can now log in and start shopping from our marketplace.\n\n'
                        f'Login here: http://localhost:8000/user/login/\n\n'
                        f'Happy Shopping!\n'
                        f'Team Meeva'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
            except Exception:
                pass  # Don't block registration if email fails
            
            messages.success(request, 'Registration successful! Please login.')
            return redirect('user_login')
        
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'users/register.html')


def browse_products(request):
    """Browse all products (public view - no login required)"""
    all_products = Product.objects.filter(is_active=True).select_related('vendor').prefetch_related('size_stocks')
    
    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        all_products = all_products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    
    # Category filter
    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        all_products = all_products.filter(category=category_filter)
    
    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        all_products = all_products.order_by('price')
    elif sort_by == 'price_high':
        all_products = all_products.order_by('-price')
    else:
        all_products = all_products.order_by('-created_at')
    
    cart = request.session.get('cart', {})
    
    # Get wishlist product IDs for the logged-in user
    wishlist_product_ids = []
    customer = _get_customer_from_request(request)
    if customer:
        wishlist_product_ids = list(
            Wishlist.objects.filter(user_id=customer.id).values_list('product_id', flat=True)
        )
    
    context = {
        'products': all_products,
        'is_user_logged_in': request.user.is_authenticated,
        'cart_count': sum(item['quantity'] for item in cart.values()),
        'wishlist_count': len(wishlist_product_ids),
        'wishlist_product_ids': wishlist_product_ids,
        'categories': Product.CATEGORY_CHOICES,
        'current_category': category_filter,
        'current_sort': sort_by,
        'search_query': search_query,
    }
    return render(request, 'users/browse_products.html', context)


def user_logout(request):
    """Logout user"""
    try:
        django_logout(request)
    except Exception:
        pass
    request.session.flush()
    messages.success(request, 'Successfully logged out.')
    return redirect('browse_products')


@require_http_methods(["GET", "POST"])
def checkout(request, product_id):
    """Checkout page to collect buyer details and place order"""
    # If user is not logged in, redirect to login with next parameter
    if not request.user.is_authenticated:
        request.session['next_checkout_product_id'] = product_id
        messages.info(request, 'Please login to proceed with your purchase.')
        return redirect('user_login')
    
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    if request.method == "POST":
        # Collect buyer details
        buyer_name = request.POST.get('buyer_name', '').strip()
        buyer_email = request.POST.get('buyer_email', '').strip()
        buyer_phone = request.POST.get('buyer_phone', '').strip()
        buyer_address = request.POST.get('buyer_address', '').strip()
        quantity = request.POST.get('quantity', '1').strip()
        selected_size = request.POST.get('size', '').strip()
        
        # Validation
        if not all([buyer_name, buyer_email, buyer_phone, buyer_address, quantity]):
            messages.error(request, 'All fields are required!')
            return render(request, 'users/checkout.html', {'product': product})
        
        # Validate size if product has sizes
        if product.sizes and not selected_size:
            messages.error(request, 'Please select a size.')
            return render(request, 'users/checkout.html', {'product': product})
        
        try:
            quantity = int(quantity)
            if quantity < 1:
                messages.error(request, 'Quantity must be at least 1.')
                return render(request, 'users/checkout.html', {'product': product})
            
            if quantity > product.quantity:
                # Validate against size-wise stock when available
                available = product.available_quantity_for_size(selected_size) if selected_size else product.total_available_quantity
                messages.error(request, f'Only {available} units available.')
                return render(request, 'users/checkout.html', {'product': product})

            # Validate size-wise stock (if configured)
            available = product.available_quantity_for_size(selected_size) if selected_size else product.total_available_quantity
            if available < quantity:
                messages.error(request, f'Only {available} units available.')
                return render(request, 'users/checkout.html', {'product': product})
            
            # Calculate total price
            total_price = product.price * quantity
            
            # Create order
            order = Order.objects.create(
                product=product,
                vendor=product.vendor,
                buyer_name=buyer_name,
                buyer_email=buyer_email,
                buyer_phone=buyer_phone,
                buyer_address=buyer_address,
                quantity=quantity,
                size=selected_size,
                price_per_unit=product.price,
                total_price=total_price,
                status='pending'
            )

            # Stock is deducted only when vendor accepts the order.
            
            # Send email to vendor
            send_order_notification_email(order)
            
            # Store order ID in session for confirmation page
            request.session['order_id'] = order.id
            
            messages.success(request, 'Order placed successfully!')
            return redirect('order_confirmation', order_id=order.id)
        
        except ValueError:
            messages.error(request, 'Invalid quantity.')
        except Exception as e:
            messages.error(request, f'Error placing order: {str(e)}')
    
    # Pre-fill user info if logged in
    user_email = ''
    user_name = ''
    user_phone = ''
    user_address = ''
    
    customer = _get_customer_from_request(request)
    if customer:
        user_email = customer.email
        user_name = f"{customer.first_name} {customer.last_name}"
        user_phone = customer.phone
        user_address = customer.address
    
    context = {
        'product': product,
        'user_email': user_email,
        'user_name': user_name,
        'user_phone': user_phone,
        'user_address': user_address,
        'is_user_logged_in': request.user.is_authenticated,
    }
    
    return render(request, 'users/checkout.html', context)


def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id)
    
    context = {
        'order': order,
        'is_user_logged_in': request.user.is_authenticated,
    }
    
    return render(request, 'users/order_confirmation.html', context)


def send_order_notification_email(order):
    """Send order notification email to vendor"""
    try:
        subject = f"New Order #{order.id} - {order.product.name}"
        size_line = f"\n- Size: {order.size}" if order.size else ""
        message = f"""
Dear {order.vendor.business_name},

A new order has been placed for your product!

Order Details:
- Order ID: {order.id}
- Product: {order.product.name}
- Quantity: {order.quantity}{size_line}
- Price per Unit: ₹{order.price_per_unit}
- Total Amount: ₹{order.total_price}

Buyer Details:
- Name: {order.buyer_name}
- Email: {order.buyer_email}
- Phone: {order.buyer_phone}
- Address: {order.buyer_address}

Please log in to your vendor dashboard to manage this order.

Best regards,
Meeva Team
        """
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [order.vendor.email],
            fail_silently=True
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False


# ==================== CART VIEWS ====================

def cart_count(request):
    """Helper: return number of distinct items in session cart"""
    cart = request.session.get('cart', {})
    return sum(item['quantity'] for item in cart.values())


def add_to_cart(request, product_id):
    """Add a product to the session cart (must be logged in)"""
    if not request.user.is_authenticated:
        request.session['redirect_after_login'] = 'cart'
        messages.info(request, 'Please login to add items to your cart.')
        return redirect('user_login')

    product = (
        Product.objects.filter(id=product_id, is_active=True)
        .select_related('vendor')
        .prefetch_related('size_stocks')
        .first()
    )
    if not product:
        messages.error(request, 'Product not found.')
        return redirect('browse_products')
    
    # Get selected size
    selected_size = request.GET.get('size', '').strip()
    
    # If product has sizes but none selected, redirect back with error
    if product.get_sizes_list() and not selected_size:
        messages.warning(request, f'Please select a size for "{product.name}".')
        next_page = request.META.get('HTTP_REFERER', 'browse_products')
        return redirect(next_page)

    # Validate stock for selected size (or global fallback)
    available = product.available_quantity_for_size(selected_size) if selected_size else product.total_available_quantity
    if available < 1:
        messages.warning(request, f'"{product.name}" is out of stock.')
        next_page = request.META.get('HTTP_REFERER', 'browse_products')
        return redirect(next_page)
    
    cart = request.session.get('cart', {})
    # Use composite key: product_id-size so same product with different sizes = different entries
    key = f"{product_id}-{selected_size}" if selected_size else str(product_id)

    if key in cart:
        if cart[key]['quantity'] < available:
            cart[key]['quantity'] += 1
            messages.success(request, f'"{product.name}" quantity updated in cart.')
        else:
            messages.warning(request, f'Only {available} units available.')
    else:
        cart[key] = {
            'product_id': product_id,
            'name': product.name,
            'price': str(product.price),
            'quantity': 1,
            'image': product.image.url if product.image else None,
            'vendor_id': product.vendor.id,
            'vendor_name': product.vendor.business_name,
            'max_qty': available,
            'size': selected_size,
        }
        size_msg = f' (Size: {selected_size})' if selected_size else ''
        messages.success(request, f'"{product.name}"{size_msg} added to cart!')

    request.session['cart'] = cart
    next_page = request.META.get('HTTP_REFERER', 'browse_products')
    return redirect(next_page)


def remove_from_cart(request, product_id):
    """Remove a product from the session cart"""
    cart = request.session.get('cart', {})
    key = request.GET.get('key', str(product_id))
    if key in cart:
        del cart[key]
        request.session['cart'] = cart
        messages.success(request, 'Item removed from cart.')
    return redirect('view_cart')


def view_cart(request):
    """Display cart and process order placement"""
    if not request.user.is_authenticated:
        request.session['redirect_after_login'] = 'cart'
        messages.info(request, 'Please login to view your cart.')
        return redirect('user_login')

    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    for key, item in cart.items():
        subtotal = float(item['price']) * item['quantity']
        total += subtotal
        cart_items.append({
            **item,
            'subtotal': subtotal,
            'cart_key': key,
        })

    if request.method == 'POST':
        buyer_name = request.POST.get('buyer_name', '').strip()
        buyer_email = request.POST.get('buyer_email', '').strip()
        buyer_phone = request.POST.get('buyer_phone', '').strip()
        buyer_address = request.POST.get('buyer_address', '').strip()

        if not all([buyer_name, buyer_email, buyer_phone, buyer_address]):
            messages.error(request, 'All delivery details are required!')
        elif not cart_items:
            messages.error(request, 'Your cart is empty!')
        else:
            created_orders = []
            errors = []
            for key, item in list(cart.items()):
                try:
                    product = (
                        Product.objects.filter(id=item['product_id'], is_active=True)
                        .select_related('vendor')
                        .prefetch_related('size_stocks')
                        .first()
                    )
                    if not product:
                        errors.append(f"{item['name']} is no longer available.")
                        continue
                    qty = item['quantity']

                    selected_size = (item.get('size') or '').strip()
                    available = product.available_quantity_for_size(selected_size) if selected_size else product.total_available_quantity
                    if qty > available:
                        qty = available
                    if qty < 1:
                        errors.append(f"{item['name']} is out of stock.")
                        continue
                    order = Order.objects.create(
                        product=product,
                        vendor=product.vendor,
                        buyer_name=buyer_name,
                        buyer_email=buyer_email,
                        buyer_phone=buyer_phone,
                        buyer_address=buyer_address,
                        quantity=qty,
                        size=item.get('size', ''),
                        price_per_unit=product.price,
                        total_price=product.price * qty,
                        status='pending'
                    )
                    send_order_notification_email(order)
                    created_orders.append(order)
                except Exception as e:
                    errors.append(str(e))

            if errors:
                for err in errors:
                    messages.error(request, err)

            if created_orders:
                request.session['cart'] = {}
                request.session['last_orders'] = [o.id for o in created_orders]
                messages.success(request, f'{len(created_orders)} order(s) placed successfully!')
                return redirect('cart_order_success')

    # Pre-fill user details
    user_name = user_email_val = user_phone = user_address = ''
    customer = _get_customer_from_request(request)
    if customer:
        user_name = f"{customer.first_name} {customer.last_name}"
        user_email_val = customer.email
        user_phone = customer.phone
        user_address = customer.address

    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': sum(i['quantity'] for i in cart.values()),
        'is_user_logged_in': True,
        'user_name': user_name,
        'user_email': user_email_val,
        'user_phone': user_phone,
        'user_address': user_address,
    }
    return render(request, 'users/cart.html', context)


def cart_order_success(request):
    """Success page after cart order placement"""
    order_ids = request.session.get('last_orders', [])
    orders = Order.objects.filter(id__in=order_ids) if order_ids else []
    context = {
        'orders': orders,
        'is_user_logged_in': request.user.is_authenticated,
        'cart_count': 0,
    }
    return render(request, 'users/cart_order_success.html', context)


def my_orders(request):
    """Display user's orders (must be logged in)"""
    if not request.user.is_authenticated:
        messages.info(request, 'Please login to view your orders.')
        return redirect('user_login')

    customer = _get_customer_from_request(request)
    if not customer:
        messages.info(request, 'Please login to view your orders.')
        return redirect('user_login')
    user_email = customer.email

    # Get all orders placed by this user's email
    orders = Order.objects.filter(buyer_email=user_email).order_by('-created_at')
    cart = request.session.get('cart', {})

    context = {
        'orders': orders,
        'is_user_logged_in': True,
        'cart_count': sum(item['quantity'] for item in cart.values()),
    }
    return render(request, 'users/my_orders.html', context)


# ==================== FORGOT PASSWORD VIEWS ====================

@csrf_protect
@require_http_methods(["GET", "POST"])
def user_forgot_password(request):
    """Step 1: Take email and send OTP"""
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'users/forgot_password.html')
        
        # Check if email exists in User table
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return render(request, 'users/forgot_password.html')
        
        # Generate OTP
        otp_code = PasswordResetOTP.generate_otp()
        
        # Delete any previous OTPs for this email & role
        PasswordResetOTP.objects.filter(email=email, role='user').delete()
        
        # Create new OTP
        PasswordResetOTP.objects.create(
            email=email,
            otp=otp_code,
            role='user',
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        
        # Send OTP via email
        try:
            send_mail(
                subject='🔐 Password Reset OTP - Meeva',
                message=f'Hello {user.first_name},\n\nYour OTP for password reset is: {otp_code}\n\nThis OTP is valid for 10 minutes.\n\nIf you did not request this, please ignore this email.\n\nTeam Meeva',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            request.session['reset_email'] = email
            request.session['reset_role'] = 'user'
            messages.success(request, 'OTP sent to your email. Please check your inbox.')
            return redirect('user_verify_otp')
        except Exception as e:
            messages.error(request, f'Failed to send OTP email. Please try again later.')
            return render(request, 'users/forgot_password.html')
    
    return render(request, 'users/forgot_password.html')


@csrf_protect
@require_http_methods(["GET", "POST"])
def user_verify_otp(request):
    """Step 2: Verify OTP"""
    email = request.session.get('reset_email')
    role = request.session.get('reset_role')
    
    if not email or role != 'user':
        messages.error(request, 'Session expired. Please start again.')
        return redirect('user_forgot_password')
    
    if request.method == "POST":
        entered_otp = request.POST.get('otp', '').strip()
        
        if not entered_otp:
            messages.error(request, 'Please enter the OTP.')
            return render(request, 'users/verify_otp.html', {'email': email})
        
        try:
            otp_record = PasswordResetOTP.objects.get(
                email=email, role='user', otp=entered_otp, is_verified=False
            )
            
            if otp_record.is_expired:
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('user_forgot_password')
            
            # Mark OTP as verified
            otp_record.is_verified = True
            otp_record.save()
            
            request.session['otp_verified'] = True
            messages.success(request, 'OTP verified! Please set your new password.')
            return redirect('user_reset_password')
            
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please try again.')
    
    return render(request, 'users/verify_otp.html', {'email': email})


@csrf_protect
@require_http_methods(["GET", "POST"])
def user_reset_password(request):
    """Step 3: Reset password"""
    email = request.session.get('reset_email')
    role = request.session.get('reset_role')
    otp_verified = request.session.get('otp_verified')
    
    if not email or role != 'user' or not otp_verified:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('user_forgot_password')
    
    if request.method == "POST":
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if not new_password or not confirm_password:
            messages.error(request, 'Both password fields are required.')
            return render(request, 'users/reset_password.html')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'users/reset_password.html')
        
        if len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'users/reset_password.html')
        
        try:
            user = User.objects.get(email=email, is_active=True)
            password_hash = make_password(new_password)
            user.password = password_hash
            user.save(update_fields=['password', 'updated_at'])

            # Keep Django auth user in sync.
            auth_user, _ = _get_or_create_auth_user_for_customer(user)
            if auth_user:
                auth_user.password = password_hash
                auth_user.is_active = bool(user.is_active)
                auth_user.save(update_fields=['password', 'is_active'])
            
            # Cleanup OTPs and session
            PasswordResetOTP.objects.filter(email=email, role='user').delete()
            request.session.pop('reset_email', None)
            request.session.pop('reset_role', None)
            request.session.pop('otp_verified', None)
            
            messages.success(request, 'Password updated successfully! Please login with your new password.')
            return redirect('user_login')
            
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('user_forgot_password')
    
    return render(request, 'users/reset_password.html')


# ==================== WISHLIST VIEWS ====================

def toggle_wishlist(request, product_id):
    """Add or remove a product from the user's wishlist"""
    if not request.user.is_authenticated:
        messages.info(request, 'Please login to add items to your wishlist.')
        return redirect('user_login')
    
    customer = _get_customer_from_request(request)
    if not customer:
        messages.info(request, 'Please login to add items to your wishlist.')
        return redirect('user_login')
    user = customer
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    wishlist_item = Wishlist.objects.filter(user=user, product=product).first()
    
    if wishlist_item:
        wishlist_item.delete()
        messages.success(request, f'"{product.name}" removed from your wishlist.')
    else:
        Wishlist.objects.create(user=user, product=product)
        messages.success(request, f'"{product.name}" added to your wishlist!')
    
    # Redirect back to the same page
    next_url = request.GET.get('next', request.META.get('HTTP_REFERER', 'browse_products'))
    return redirect(next_url)


def view_wishlist(request):
    """View all wishlist items"""
    if not request.user.is_authenticated:
        messages.info(request, 'Please login to view your wishlist.')
        return redirect('user_login')
    
    customer = _get_customer_from_request(request)
    if not customer:
        messages.info(request, 'Please login to view your wishlist.')
        return redirect('user_login')
    wishlist_items = (
        Wishlist.objects.filter(user_id=customer.id)
        .select_related('product', 'product__vendor')
        .prefetch_related('product__size_stocks')
    )
    cart = request.session.get('cart', {})
    
    context = {
        'wishlist_items': wishlist_items,
        'is_user_logged_in': True,
        'cart_count': sum(item['quantity'] for item in cart.values()),
        'wishlist_count': wishlist_items.count(),
    }
    return render(request, 'users/wishlist.html', context)
