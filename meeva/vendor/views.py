from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Sum, Count, Q
from .models import Vendor, Product, Order
from .emails import send_vendor_registration_email


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
            vendor = Vendor.objects.create(
                full_name=request.POST.get('full_name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                password=make_password(password),
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
    if not request.session.get('vendor_logged_in'):
        messages.warning(request, 'Please login first.')
        return redirect('vendor_login')
    
    vendor = Vendor.objects.get(id=request.session.get('vendor_id'))
    
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
    request.session.flush()
    messages.success(request, 'Successfully logged out.')
    return redirect('vendor_login')


def check_vendor_login(request):
    """Helper function to check if vendor is logged in"""
    if not request.session.get('vendor_logged_in'):
        messages.warning(request, 'Please login first.')
        return None
    return Vendor.objects.get(id=request.session.get('vendor_id'))


# ==================== PRODUCT VIEWS ====================

def vendor_products(request):
    """View all vendor products"""
    vendor = check_vendor_login(request)
    if not vendor:
        return redirect('vendor_login')
    
    products = vendor.products.all()
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
            product.price = float(request.POST.get('price', product.price))
            product.quantity = int(request.POST.get('quantity', product.quantity))
            
            if 'image' in request.FILES:
                product.image = request.FILES.get('image')
            
            product.save()
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

    if new_status in valid:
        order.status = new_status
        order.save()
        messages.success(request, f'Order #{order.id} marked as "{order.get_status_display()}".')
    else:
        messages.error(request, 'Invalid status.')

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
