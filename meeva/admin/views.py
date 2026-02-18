from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get admin credentials from .env
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@meeva.com')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Admin@123456')


@csrf_protect
@require_http_methods(["GET", "POST"])
def admin_login(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        # Validate credentials against .env
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            # Set session to mark admin as logged in
            request.session['admin_logged_in'] = True
            request.session['admin_email'] = email
            messages.success(request, 'Welcome to Meeva Admin Dashboard!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid email or password. Please try again.')
    
    return render(request, 'admin/login.html')


def admin_dashboard(request):
    """
    Admin dashboard - shows admin panel
    Requires admin to be logged in via session
    """
    # Check if admin is logged in
    if not request.session.get('admin_logged_in'):
        messages.warning(request, 'Please login first.')
        return redirect('admin_login')
    
    context = {
        'admin_email': request.session.get('admin_email', 'Admin'),
    }
    
    return render(request, 'admin/dashboard.html', context)


def admin_logout(request):
    """
    Logout admin - clear session
    """
    request.session.flush()
    messages.success(request, 'Successfully logged out.')
    return redirect('admin_login')
