from django.shortcuts import render
from django.db.models import Q
from vendor.models import Product

def landing_page(request):
    """Landing page with products - always public, logs out any user"""
    # Clear user login session so landing page is always public
    request.session.pop('user_logged_in', None)
    request.session.pop('user_email', None)
    request.session.pop('user_id', None)
    request.session.pop('cart', None)

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
    return render(request, 'pages/landing.html', context)


def role_login(request):
    """Choose USER or VENDOR login"""
    return render(request, 'pages/role_login.html')
