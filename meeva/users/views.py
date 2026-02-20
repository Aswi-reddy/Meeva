from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from .models import User
from vendor.models import Product, Order


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
            
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=make_password(password),
            )
            
            messages.success(request, 'Registration successful! Please login.')
            return redirect('user_login')
        
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'users/register.html')


def browse_products(request):
    """Browse all products (public view - no login required)"""
    all_products = Product.objects.filter(is_active=True)
    
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
    context = {
        'products': all_products,
        'is_user_logged_in': request.session.get('user_logged_in', False),
        'cart_count': sum(item['quantity'] for item in cart.values()),
        'categories': Product.CATEGORY_CHOICES,
        'current_category': category_filter,
        'current_sort': sort_by,
        'search_query': search_query,
    }
    return render(request, 'users/browse_products.html', context)


def user_logout(request):
    """Logout user"""
    request.session.flush()
    messages.success(request, 'Successfully logged out.')
    return redirect('browse_products')


@require_http_methods(["GET", "POST"])
def checkout(request, product_id):
    """Checkout page to collect buyer details and place order"""
    # If user is not logged in, redirect to login with next parameter
    if not request.session.get('user_logged_in'):
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
                messages.error(request, f'Only {product.quantity} units available.')
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
            
            # Update product quantity
            product.quantity -= quantity
            product.save()
            
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
    
    if request.session.get('user_logged_in'):
        user_id = request.session.get('user_id')
        user = User.objects.get(id=user_id)
        user_email = user.email
        user_name = f"{user.first_name} {user.last_name}"
        user_phone = user.phone
        user_address = user.address
    
    context = {
        'product': product,
        'user_email': user_email,
        'user_name': user_name,
        'user_phone': user_phone,
        'user_address': user_address,
        'is_user_logged_in': request.session.get('user_logged_in', False),
    }
    
    return render(request, 'users/checkout.html', context)


def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id)
    
    context = {
        'order': order,
        'is_user_logged_in': request.session.get('user_logged_in', False),
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
    if not request.session.get('user_logged_in'):
        request.session['redirect_after_login'] = 'cart'
        messages.info(request, 'Please login to add items to your cart.')
        return redirect('user_login')

    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Get selected size
    selected_size = request.GET.get('size', '').strip()
    
    # If product has sizes but none selected, redirect back with error
    if product.sizes and not selected_size:
        messages.warning(request, f'Please select a size for "{product.name}".')
        next_page = request.META.get('HTTP_REFERER', 'browse_products')
        return redirect(next_page)
    
    cart = request.session.get('cart', {})
    # Use composite key: product_id-size so same product with different sizes = different entries
    key = f"{product_id}-{selected_size}" if selected_size else str(product_id)

    if key in cart:
        if cart[key]['quantity'] < product.quantity:
            cart[key]['quantity'] += 1
            messages.success(request, f'"{product.name}" quantity updated in cart.')
        else:
            messages.warning(request, f'Only {product.quantity} units available.')
    else:
        cart[key] = {
            'product_id': product_id,
            'name': product.name,
            'price': str(product.price),
            'quantity': 1,
            'image': product.image.url if product.image else None,
            'vendor_id': product.vendor.id,
            'vendor_name': product.vendor.business_name,
            'max_qty': product.quantity,
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
    if not request.session.get('user_logged_in'):
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
                    product = Product.objects.get(id=item['product_id'], is_active=True)
                    qty = item['quantity']
                    if qty > product.quantity:
                        qty = product.quantity
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
                    product.quantity -= qty
                    product.save()
                    send_order_notification_email(order)
                    created_orders.append(order)
                except Product.DoesNotExist:
                    errors.append(f"{item['name']} is no longer available.")
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
    user_id = request.session.get('user_id')
    if user_id:
        from .models import User as UserModel
        try:
            u = UserModel.objects.get(id=user_id)
            user_name = f"{u.first_name} {u.last_name}"
            user_email_val = u.email
            user_phone = u.phone
            user_address = u.address
        except Exception:
            pass

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
        'is_user_logged_in': request.session.get('user_logged_in', False),
        'cart_count': 0,
    }
    return render(request, 'users/cart_order_success.html', context)


def my_orders(request):
    """Display user's orders (must be logged in)"""
    if not request.session.get('user_logged_in'):
        messages.info(request, 'Please login to view your orders.')
        return redirect('user_login')

    user_id = request.session.get('user_id')
    user = get_object_or_404(User, id=user_id)
    user_email = user.email

    # Get all orders placed by this user's email
    orders = Order.objects.filter(buyer_email=user_email).order_by('-created_at')
    cart = request.session.get('cart', {})

    context = {
        'orders': orders,
        'is_user_logged_in': True,
        'cart_count': sum(item['quantity'] for item in cart.values()),
    }
    return render(request, 'users/my_orders.html', context)

