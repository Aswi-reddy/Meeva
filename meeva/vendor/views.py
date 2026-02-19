from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.hashers import make_password, check_password
from .models import Vendor
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
    """Vendor login"""
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        try:
            vendor = Vendor.objects.get(email=email, is_active=True)
            
            if vendor.status == 'pending':
                messages.warning(request, 'Your account is pending admin approval.')
            elif vendor.status == 'rejected':
                messages.error(request, f'Your account was rejected. Reason: {vendor.rejection_reason}')
            elif vendor.status == 'suspended':
                messages.error(request, 'Your account has been suspended. Contact admin.')
            elif check_password(password, vendor.password):
                if vendor.status == 'approved':
                    request.session['vendor_logged_in'] = True
                    request.session['vendor_email'] = email
                    request.session['vendor_id'] = vendor.id
                    messages.success(request, f'Welcome back, {vendor.business_name}!')
                    return redirect('vendor_dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        except Vendor.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'vendor/login.html')


def vendor_dashboard(request):
    """Vendor dashboard - only for approved vendors"""
    if not request.session.get('vendor_logged_in'):
        messages.warning(request, 'Please login first.')
        return redirect('vendor_login')
    
    vendor = Vendor.objects.get(id=request.session.get('vendor_id'))
    
    context = {
        'vendor': vendor,
    }
    
    return render(request, 'vendor/dashboard.html', context)


def vendor_logout(request):
    """Logout vendor"""
    request.session.flush()
    messages.success(request, 'Successfully logged out.')
    return redirect('vendor_login')
