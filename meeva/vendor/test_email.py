"""
Test email functionality
Run this to test if email is working: python manage.py shell
Then: from vendor.test_email import test_email; test_email()
"""
from django.core.mail import send_mail
from django.conf import settings


def test_email():
    """Test email configuration"""
    try:
        send_mail(
            'Test Email - Meeva Platform',
            'This is a test email from Meeva. If you receive this, email configuration is working correctly!',
            settings.DEFAULT_FROM_EMAIL,
            ['sumanaswireddy@gmail.com'],  # Send to same email for testing
            fail_silently=False,
        )
        print("✅ Test email sent successfully!")
        print(f"Email sent from: {settings.DEFAULT_FROM_EMAIL}")
        print(f"Email sent to: sumanaswireddy@gmail.com")
        return True
    except Exception as e:
        print(f"❌ Error sending test email: {str(e)}")
        print("\nCommon issues:")
        print("1. Gmail 2FA: You need to use App Password instead of regular password")
        print("   - Go to: https://myaccount.google.com/apppasswords")
        print("   - Create an app password for 'Mail'")
        print("   - Use that password in .env file")
        print("\n2. Less Secure Apps: Gmail has disabled this feature")
        print("\n3. Check your email and password in .env file")
        return False


if __name__ == '__main__':
    test_email()
