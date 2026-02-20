"""
Simple email test - Run: python manage.py shell
Then: from vendor.test_email import test_email; test_email()
"""
from django.core.mail import send_mail
from django.conf import settings


def test_email():
    """Test if email works"""
    try:
        send_mail(
            '✅ Test Email - Meeva',
            'This is a test! If you got this, email is working! 🎉',
            settings.DEFAULT_FROM_EMAIL,
            ['sumanaswireddy@gmail.com'],
            fail_silently=False,
        )
        print("✅ Email sent successfully!")
        print(f"From: {settings.DEFAULT_FROM_EMAIL}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Fix:")
        print("1. Check your Google App Password")
        print("2. Get it from: https://myaccount.google.com/apppasswords")
        return False


if __name__ == '__main__':
    test_email()
