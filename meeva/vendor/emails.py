"""
Email utilities for vendor notifications
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_vendor_registration_email(vendor):
    """Send email to vendor after successful registration"""
    subject = '🎉 Registration Successful - Meeva Platform'
    
    message = f"""
Hello {vendor.full_name},

Thank you for registering with Meeva as a vendor!

Your application has been successfully submitted and is now pending review by our admin team.

Business Details:
- Business Name: {vendor.business_name}
- Email: {vendor.email}
- Registration Date: {vendor.created_at.strftime('%B %d, %Y')}

What happens next?
Our admin team will review your application and documents within 24-48 hours. You will receive an email notification once your application is reviewed.

If approved, you'll be able to:
- Login to your vendor dashboard
- Add and manage products
- Process customer orders
- Track your sales and revenue

Important Note:
Please ensure all the documents uploaded are clear and valid. If there are any issues, your application may be rejected.

Thank you for choosing Meeva!

Best regards,
Team Meeva
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [vendor.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending registration email: {str(e)}")
        return False


def send_vendor_approval_email(vendor, admin_email):
    """Send email to vendor when application is approved"""
    subject = '✅ Application Approved - Welcome to Meeva!'
    
    message = f"""
Congratulations {vendor.full_name}!

Your vendor application for "{vendor.business_name}" has been APPROVED! 🎉

You can now login to your vendor dashboard and start selling on the Meeva platform.

Login Details:
- Website: http://localhost:8000/vendor/login/
- Email: {vendor.email}
- Use the password you created during registration

What you can do now:
✓ Login to your vendor dashboard
✓ Add products to your catalog
✓ Manage inventory and pricing
✓ Process customer orders
✓ Track sales and revenue

Platform Fee: {vendor.platform_fee_percentage}%
(This fee will be automatically deducted from each sale)

Approved by: {admin_email}
Approval Date: {vendor.approved_at.strftime('%B %d, %Y at %I:%M %p')}

We're excited to have you as part of the Meeva family!

If you have any questions, please contact our support team.

Best regards,
Team Meeva
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [vendor.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending approval email: {str(e)}")
        return False


def send_vendor_rejection_email(vendor, rejection_reason):
    """Send email to vendor when application is rejected"""
    subject = '❌ Application Update - Meeva Platform'
    
    message = f"""
Hello {vendor.full_name},

Thank you for your interest in becoming a vendor on the Meeva platform.

Unfortunately, we are unable to approve your application for "{vendor.business_name}" at this time.

Reason for Rejection:
{rejection_reason}

What you can do:
If you believe this was a mistake or if you've resolved the issues mentioned, you can:
1. Contact our support team for clarification
2. Submit a new application with corrected information

We appreciate your understanding and hope to work with you in the future.

If you have any questions, please don't hesitate to reach out to our support team.

Best regards,
Team Meeva
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [vendor.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending rejection email: {str(e)}")
        return False


def send_vendor_suspension_email(vendor):
    """Send email to vendor when account is suspended"""
    subject = '⚠️ Account Suspended - Meeva Platform'
    
    message = f"""
Hello {vendor.full_name},

This is to inform you that your vendor account for "{vendor.business_name}" has been temporarily suspended.

Business Name: {vendor.business_name}
Suspension Date: {vendor.updated_at.strftime('%B %d, %Y at %I:%M %p')}

During the suspension period:
- You will not be able to login to your dashboard
- Your products will not be visible to customers
- No new orders can be placed for your products

To resolve this matter:
Please contact our admin team immediately to understand the reason for suspension and the steps needed to reactivate your account.

Support Email: {settings.DEFAULT_FROM_EMAIL}

We hope to resolve this matter quickly and have you back on the platform soon.

Best regards,
Team Meeva
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [vendor.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending suspension email: {str(e)}")
        return False


def send_vendor_reactivation_email(vendor):
    """Send email to vendor when account is reactivated"""
    subject = '✅ Account Reactivated - Meeva Platform'
    
    message = f"""
Great news, {vendor.full_name}!

Your vendor account for "{vendor.business_name}" has been REACTIVATED! 🎉

Business Name: {vendor.business_name}
Reactivation Date: {vendor.updated_at.strftime('%B %d, %Y at %I:%M %p')}

You can now:
✓ Login to your vendor dashboard
✓ Your products are visible to customers again
✓ Accept and process new orders
✓ Continue selling on Meeva platform

Login here: http://localhost:8000/vendor/login/
Email: {vendor.email}

Thank you for your patience and cooperation. We're glad to have you back!

If you have any questions, please contact our support team.

Best regards,
Team Meeva
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [vendor.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending reactivation email: {str(e)}")
        return False
