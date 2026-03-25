from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate, get_user_model, login as django_login, logout as django_logout
from django.db import IntegrityError
from django.utils import timezone
from .models import Admin
from vendor.models import Vendor
from vendor.emails import (
    send_vendor_approval_email,
    send_vendor_rejection_email,
    send_vendor_suspension_email,
    send_vendor_reactivation_email
)


def _safe_username_from_email(email: str, suffix: str | None = None) -> str:
    email = (email or '').strip()
    base = f"{email}_{suffix}" if suffix else email
    UserModel = get_user_model()
    max_len = UserModel._meta.get_field('username').max_length
    return (base or 'user')[:max_len]


def _get_or_create_auth_user_for_admin(admin: Admin):
    """Return (auth_user, created). Ensures admin.django_user is set."""
    if getattr(admin, 'django_user_id', None):
        return admin.django_user, False

    UserModel = get_user_model()
    email = (admin.email or '').strip()
    username = _safe_username_from_email(email)

    auth_user = UserModel.objects.filter(username=username).first()
    if not auth_user:
        auth_user = UserModel.objects.filter(email=email).first()

    if auth_user:
        admin.django_user = auth_user
        admin.save(update_fields=['django_user'])
        return auth_user, False

    auth_user = UserModel(
        username=username,
        email=email,
        is_active=bool(getattr(admin, 'is_active', True)),
        is_staff=True,
        is_superuser=False,
    )
    auth_user.password = admin.password or ''
    try:
        auth_user.save()
    except IntegrityError:
        auth_user.username = _safe_username_from_email(email, str(admin.id))
        auth_user.save()

    admin.django_user = auth_user
    admin.save(update_fields=['django_user'])
    return auth_user, True


def check_admin_login(request):
    """Helper: ensure admin is authenticated via Django auth (with legacy-session fallback)."""
    # Primary: Django auth session + OneToOne link
    if getattr(request, 'user', None) and request.user.is_authenticated:
        admin = getattr(request.user, 'meeva_core_admin', None)
        if admin and getattr(admin, 'is_active', True):
            request.session['admin_logged_in'] = True
            request.session['admin_email'] = admin.email
            request.session['admin_id'] = admin.id
            return admin

    # Fallback: legacy session (best-effort bridge into Django auth)
    admin_id = request.session.get('admin_id')
    if request.session.get('admin_logged_in') and admin_id:
        admin = Admin.objects.filter(id=admin_id, is_active=True).first()
        if admin:
            auth_user, _ = _get_or_create_auth_user_for_admin(admin)
            if auth_user:
                auth_user.backend = 'django.contrib.auth.backends.ModelBackend'
                django_login(request, auth_user)

            request.session['admin_logged_in'] = True
            request.session['admin_email'] = admin.email
            request.session['admin_id'] = admin.id
            return admin

    messages.warning(request, 'Please login first.')
    return None


@csrf_protect
@require_http_methods(["GET", "POST"])
def admin_login(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        # Validate credentials against database
        try:
            admin = Admin.objects.get(email=email, is_active=True)
            if check_password(password, admin.password):
                auth_user, _ = _get_or_create_auth_user_for_admin(admin)
                if auth_user and admin.password and auth_user.password != admin.password:
                    auth_user.password = admin.password
                    auth_user.is_active = bool(admin.is_active)
                    auth_user.is_staff = True
                    auth_user.save(update_fields=['password', 'is_active', 'is_staff'])

                authenticated = None
                if auth_user:
                    authenticated = authenticate(request, username=auth_user.username, password=password)
                if authenticated:
                    django_login(request, authenticated)
                elif auth_user:
                    auth_user.backend = 'django.contrib.auth.backends.ModelBackend'
                    django_login(request, auth_user)

                # Set session to mark admin as logged in
                request.session['admin_logged_in'] = True
                request.session['admin_email'] = email
                request.session['admin_id'] = admin.id
                messages.success(request, 'Welcome to Meeva Admin Dashboard!')
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid email or password. Please try again.')
        except Admin.DoesNotExist:
            messages.error(request, 'Invalid email or password. Please try again.')
    
    return render(request, 'admin/login.html')


def admin_dashboard(request):
    admin = check_admin_login(request)
    if not admin:
        return redirect('admin_login')
    
    # Get vendor statistics
    pending_count = Vendor.objects.filter(status='pending').count()
    approved_count = Vendor.objects.filter(status='approved').count()
    rejected_count = Vendor.objects.filter(status='rejected').count()
    suspended_count = Vendor.objects.filter(status='suspended').count()
    total_vendors = Vendor.objects.count()
    
    context = {
        'admin_email': admin.email,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'suspended_count': suspended_count,
        'total_vendors': total_vendors,
    }
    
    return render(request, 'admin/dashboard.html', context)


def admin_logout(request):
    """
    Logout admin - clear session
    """
    try:
        django_logout(request)
    except Exception:
        pass
    request.session.flush()
    messages.success(request, 'Successfully logged out.')
    return redirect('admin_login')


# ============ VENDOR MANAGEMENT VIEWS ============

def pending_vendors(request):
    """List all pending vendor applications"""
    admin = check_admin_login(request)
    if not admin:
        return redirect('admin_login')
    
    vendors = Vendor.objects.filter(status='pending').order_by('-created_at')
    
    context = {
        'admin_email': admin.email,
        'vendors': vendors,
        'page_title': 'Pending Vendor Applications',
    }
    
    return render(request, 'admin/pending_vendors.html', context)


def all_vendors(request):
    """List all vendors with filtering"""
    admin = check_admin_login(request)
    if not admin:
        return redirect('admin_login')
    
    # Get filter parameter
    status_filter = request.GET.get('status', 'all')
    
    if status_filter == 'all':
        vendors = Vendor.objects.all().order_by('-created_at')
    else:
        vendors = Vendor.objects.filter(status=status_filter).order_by('-created_at')
    
    context = {
        'admin_email': admin.email,
        'vendors': vendors,
        'status_filter': status_filter,
        'page_title': 'All Vendors',
    }
    
    return render(request, 'admin/all_vendors.html', context)


def vendor_detail(request, vendor_id):
    """View detailed information about a vendor including documents"""
    admin = check_admin_login(request)
    if not admin:
        return redirect('admin_login')
    
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    context = {
        'admin_email': admin.email,
        'vendor': vendor,
    }
    
    return render(request, 'admin/vendor_detail.html', context)


@require_http_methods(["POST"])
def approve_vendor(request, vendor_id):
    """Approve a vendor application"""
    admin = check_admin_login(request)
    if not admin:
        return redirect('admin_login')
    
    vendor = get_object_or_404(Vendor, id=vendor_id)
    admin_email = admin.email
    
    vendor.status = 'approved'
    vendor.approved_by = admin_email
    vendor.approved_at = timezone.now()
    vendor.rejection_reason = None
    vendor.save()
    
    # Send approval email to vendor
    email_sent = send_vendor_approval_email(vendor, admin_email)
    
    if email_sent:
        messages.success(request, f'Vendor "{vendor.business_name}" has been approved successfully! Confirmation email sent to vendor.')
    else:
        messages.success(request, f'Vendor "{vendor.business_name}" has been approved successfully! (Email notification failed)')
    
    return redirect('vendor_detail', vendor_id=vendor_id)


@require_http_methods(["POST"])
def reject_vendor(request, vendor_id):
    """Reject a vendor application"""
    admin = check_admin_login(request)
    if not admin:
        return redirect('admin_login')
    
    vendor = get_object_or_404(Vendor, id=vendor_id)
    rejection_reason = request.POST.get('rejection_reason', 'No reason provided')
    
    vendor.status = 'rejected'
    vendor.rejection_reason = rejection_reason
    vendor.save()
    
    # Send rejection email to vendor
    email_sent = send_vendor_rejection_email(vendor, rejection_reason)
    
    if email_sent:
        messages.success(request, f'Vendor "{vendor.business_name}" has been rejected. Notification email sent to vendor.')
    else:
        messages.success(request, f'Vendor "{vendor.business_name}" has been rejected. (Email notification failed)')
    
    return redirect('vendor_detail', vendor_id=vendor_id)


@require_http_methods(["POST"])
def suspend_vendor(request, vendor_id):
    """Suspend an approved vendor"""
    admin = check_admin_login(request)
    if not admin:
        return redirect('admin_login')
    
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    vendor.status = 'suspended'
    vendor.is_active = False
    vendor.save()
    
    # Send suspension email to vendor
    email_sent = send_vendor_suspension_email(vendor)
    
    if email_sent:
        messages.success(request, f'Vendor "{vendor.business_name}" has been suspended. Notification email sent to vendor.')
    else:
        messages.success(request, f'Vendor "{vendor.business_name}" has been suspended. (Email notification failed)')
    
    return redirect('vendor_detail', vendor_id=vendor_id)


@require_http_methods(["POST"])
def activate_vendor(request, vendor_id):
    """Activate a suspended vendor"""
    admin = check_admin_login(request)
    if not admin:
        return redirect('admin_login')
    
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    vendor.status = 'approved'
    vendor.is_active = True
    vendor.save()
    
    # Send reactivation email to vendor
    email_sent = send_vendor_reactivation_email(vendor)
    
    if email_sent:
        messages.success(request, f'Vendor "{vendor.business_name}" has been activated. Confirmation email sent to vendor.')
    else:
        messages.success(request, f'Vendor "{vendor.business_name}" has been activated. (Email notification failed)')
    
    return redirect('vendor_detail', vendor_id=vendor_id)
