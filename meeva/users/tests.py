from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command

import io

from .models import PasswordResetOTP


class OtpCleanupCommandTests(TestCase):
	def test_cleanup_otps_deletes_expired_only(self):
		now = timezone.now()
		expired = PasswordResetOTP.objects.create(
			email='x@example.com',
			otp='111111',
			role='user',
			is_verified=False,
			expires_at=now - timezone.timedelta(minutes=1),
		)
		active = PasswordResetOTP.objects.create(
			email='y@example.com',
			otp='222222',
			role='vendor',
			is_verified=True,
			expires_at=now + timezone.timedelta(minutes=10),
		)

		out = io.StringIO()
		call_command('cleanup_otps', stdout=out)

		self.assertFalse(PasswordResetOTP.objects.filter(id=expired.id).exists())
		self.assertTrue(PasswordResetOTP.objects.filter(id=active.id).exists())
