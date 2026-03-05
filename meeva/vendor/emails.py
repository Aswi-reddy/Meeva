"""
Simple email utilities for vendor notifications
"""
from django.core.mail import send_mail
from django.conf import settings


def send_user_order_accepted_email(order):
    """Email user once when vendor accepts the order."""
    subject = f"✅ Order Confirmed - Meeva (Order #{order.id})"
    size_line = f"\nSize: {order.size}" if getattr(order, 'size', '') else ""
    message = f"""
Hello {order.buyer_name},

Good news — your order has been accepted by the vendor.

Order Details:
Order ID: {order.id}
Product: {order.product.name}{size_line}
Quantity: {order.quantity}
Total: ₹{order.total_price}

You can track the status in My Orders.

Thanks,
Meeva Team
"""

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.buyer_email], fail_silently=False)
        return True
    except Exception as e:
        print(f"❌ User accepted email error: {e}")
        return False


def send_user_order_delivered_email(order):
    """Email user once when order is marked delivered."""
    subject = f"📦 Delivered - Meeva (Order #{order.id})"
    size_line = f"\nSize: {order.size}" if getattr(order, 'size', '') else ""
    message = f"""
Hello {order.buyer_name},

Your order has been delivered.

Order Details:
Order ID: {order.id}
Product: {order.product.name}{size_line}
Quantity: {order.quantity}

Thanks for shopping with Meeva.

Meeva Team
"""

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.buyer_email], fail_silently=False)
        return True
    except Exception as e:
        print(f"❌ User delivered email error: {e}")
        return False


def send_vendor_registration_email(vendor):
    """Send simple email to vendor after registration"""
    subject = '🎉 Registration Successful - Meeva'
    
    message = f"""
Hello {vendor.full_name}! 👋

Thanks for registering with Meeva!

📋 Your Details:
• Vendor ID: {vendor.vendor_id}
• Business: {vendor.business_name}
• Email: {vendor.email}

✅ What's Next?
Your application is under review. We'll email you within 24-48 hours.

Once approved, you can login and start selling!

🔑 Save your Vendor ID: {vendor.vendor_id}
(You may need this for reference)

Thanks,
Team Meeva 🏪
    """
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [vendor.email], fail_silently=False)
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def send_vendor_approval_email(vendor, admin_email):
    """Send email when vendor is approved"""
    subject = '✅ You are Approved - Meeva'
    
    message = f"""
Congratulations {vendor.full_name}! 🎉

Your business "{vendor.business_name}" is APPROVED!

� Your Vendor ID: {vendor.vendor_id}

�🔑 Login Now:
• Website: http://localhost:8000/vendor/login/
• Email: {vendor.email}
• Password: (use your registration password)

💰 Platform Fee: {vendor.platform_fee_percentage}%

Start selling now! 🚀

Team Meeva
    """
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [vendor.email], fail_silently=False)
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def send_vendor_rejection_email(vendor, rejection_reason):
    """Send email when vendor is rejected"""
    subject = '❌ Application Update - Meeva'
    
    message = f"""
Hello {vendor.full_name},

We cannot approve "{vendor.business_name}" right now.

📝 Reason:
{rejection_reason}

You can contact support or submit a new application.

Team Meeva
    """
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [vendor.email], fail_silently=False)
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def send_vendor_suspension_email(vendor):
    """Send email when vendor is suspended"""
    subject = '⚠️ Account Suspended - Meeva'
    
    message = f"""
Hello {vendor.full_name},

Your account "{vendor.business_name}" is suspended.

Contact support to resolve this.

Team Meeva
    """
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [vendor.email], fail_silently=False)
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def send_vendor_reactivation_email(vendor):
    """Send email when vendor is reactivated"""
    subject = '✅ Account Active - Meeva'
    
    message = f"""
Great news {vendor.full_name}! 🎉

Your account "{vendor.business_name}" is active again!

Login: http://localhost:8000/vendor/login/

Team Meeva
    """
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [vendor.email], fail_silently=False)
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False
