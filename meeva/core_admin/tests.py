from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class DiagnoseDbCommandTests(TestCase):
	def test_diagnose_db_outputs_expected_fields(self):
		out = StringIO()
		call_command('diagnose_db', stdout=out)
		output = out.getvalue()

		self.assertIn('Active database connection', output)
		self.assertIn('Vendor:', output)
		self.assertIn('ENGINE:', output)
		self.assertIn('PASSWORD: [REDACTED]', output)
