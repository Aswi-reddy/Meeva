from django.test import TestCase, override_settings
from django.contrib.auth.hashers import make_password
from django.core import mail

from rest_framework.test import APIClient

from users.models import User, PasswordResetOTP
from vendor.models import Vendor, Product
from vendor.models import Order
from core_admin.models import Admin


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ApiSmokeTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.vendor = Vendor.objects.create(
            full_name='Vendor Name',
            email='vendor@example.com',
            phone='+911234567890',
            password=make_password('VendorPass1!'),
            business_name='Vendor Biz',
            business_address='Address',
            business_description='',
            aadhar_number='123456789012',
            pan_number='ABCDE1234F',
            license_number='LIC123',
            bank_name='Bank',
            account_number='1234567890',
            ifsc_code='ABCD0123456',
            account_holder_name='Vendor Name',
            status='approved',
            is_active=True,
        )

        self.product = Product.objects.create(
            vendor=self.vendor,
            name='Test Product',
            description='Desc',
            category='other',
            sizes='',
            price='100.00',
            quantity=10,
            is_active=True,
        )

        self.user = User.objects.create(
            first_name='U',
            last_name='Ser',
            email='user@example.com',
            phone='+911111111111',
            address='Addr',
            password=make_password('UserPass1!'),
            is_active=True,
        )

        self.admin = Admin.objects.create(
            email='admin@example.com',
            password=make_password('AdminPass1!'),
            is_active=True,
        )

    def _login(self, role: str, email: str, password: str) -> str:
        resp = self.client.post(
            '/api/v1/auth/login/',
            data={'role': role, 'email': email, 'password': password},
            format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        return resp.json()['tokens']['access']

    def test_products_list_public(self):
        resp = self.client.get('/api/v1/products/')
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

        # Optional pagination (only if requested)
        paged = self.client.get('/api/v1/products/?page=1&page_size=1')
        self.assertEqual(paged.status_code, 200)
        self.assertIn('results', paged.json())

    def test_user_orders_flow(self):
        access = self._login('user', 'user@example.com', 'UserPass1!')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        me = self.client.get('/api/v1/me/')
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()['email'], 'user@example.com')

        create = self.client.post(
            '/api/v1/orders/',
            data={
                'product_id': self.product.id,
                'quantity': 1,
                'buyer_name': 'U Ser',
                'buyer_email': 'user@example.com',
                'buyer_phone': '+911111111111',
                'buyer_address': 'Addr',
            },
            format='json',
        )
        self.assertEqual(create.status_code, 201, create.content)

        listing = self.client.get('/api/v1/orders/')
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(len(listing.json()), 1)

        listing_paged = self.client.get('/api/v1/orders/?page=1&page_size=1')
        self.assertEqual(listing_paged.status_code, 200)
        self.assertIn('results', listing_paged.json())

    def test_vendor_products_list(self):
        access = self._login('vendor', 'vendor@example.com', 'VendorPass1!')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.get('/api/v1/vendor/products/')
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

        dash = self.client.get('/api/v1/vendor/dashboard/')
        self.assertEqual(dash.status_code, 200)
        self.assertIn('total_products', dash.json())

    def test_vendor_orders_and_status_update(self):
        # Create an order for this vendor
        order = Order.objects.create(
            product=self.product,
            vendor=self.vendor,
            buyer_name='U Ser',
            buyer_email='user@example.com',
            buyer_phone='+911111111111',
            buyer_address='Addr',
            quantity=1,
            size='',
            price_per_unit=self.product.price,
            total_price=self.product.price,
            status='pending',
        )

        access = self._login('vendor', 'vendor@example.com', 'VendorPass1!')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        listing = self.client.get('/api/v1/vendor/orders/')
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(len(listing.json()), 1)

        update = self.client.post(
            f'/api/v1/vendor/orders/{order.id}/status/',
            data={'status': 'confirmed'},
            format='json',
        )
        self.assertEqual(update.status_code, 200, update.content)
        self.assertEqual(update.json()['status'], 'confirmed')

    def test_user_wishlist_toggle_and_list(self):
        access = self._login('user', 'user@example.com', 'UserPass1!')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        toggle_on = self.client.post('/api/v1/wishlist/toggle/', data={'product_id': self.product.id}, format='json')
        self.assertEqual(toggle_on.status_code, 200)
        self.assertEqual(toggle_on.json()['in_wishlist'], True)

        listing = self.client.get('/api/v1/wishlist/')
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(len(listing.json()), 1)

        toggle_off = self.client.post('/api/v1/wishlist/toggle/', data={'product_id': self.product.id}, format='json')
        self.assertEqual(toggle_off.status_code, 200)
        self.assertEqual(toggle_off.json()['in_wishlist'], False)

    def test_vendor_sales_report(self):
        access = self._login('vendor', 'vendor@example.com', 'VendorPass1!')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.get('/api/v1/vendor/sales-report/')
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn('total_revenue', payload)
        self.assertIn('orders', payload)

    def test_admin_vendor_lifecycle(self):
        access = self._login('admin', 'admin@example.com', 'AdminPass1!')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        listing = self.client.get('/api/v1/admin/vendors/?status=all')
        self.assertEqual(listing.status_code, 200)

        approve = self.client.post(f'/api/v1/admin/vendors/{self.vendor.id}/approve/', data={}, format='json')
        self.assertEqual(approve.status_code, 200, approve.content)
        self.assertEqual(approve.json()['status'], 'approved')

        suspend = self.client.post(f'/api/v1/admin/vendors/{self.vendor.id}/suspend/', data={}, format='json')
        self.assertEqual(suspend.status_code, 200)
        self.assertEqual(suspend.json()['status'], 'suspended')

        activate = self.client.post(f'/api/v1/admin/vendors/{self.vendor.id}/activate/', data={}, format='json')
        self.assertEqual(activate.status_code, 200)
        self.assertEqual(activate.json()['status'], 'approved')

        reject = self.client.post(
            f'/api/v1/admin/vendors/{self.vendor.id}/reject/',
            data={'rejection_reason': 'Incomplete docs'},
            format='json',
        )
        self.assertEqual(reject.status_code, 200)
        self.assertEqual(reject.json()['status'], 'rejected')

    def test_logout_blacklists_refresh(self):
        resp = self.client.post(
            '/api/v1/auth/login/',
            data={'role': 'user', 'email': 'user@example.com', 'password': 'UserPass1!'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        refresh = resp.json()['tokens']['refresh']
        access = resp.json()['tokens']['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        out = self.client.post('/api/v1/auth/logout/', data={'refresh': refresh}, format='json')
        # Depending on migration state, this could be 204 or 501; in tests it should be 204.
        self.assertEqual(out.status_code, 204)

    def test_user_register_then_login(self):
        resp = self.client.post(
            '/api/v1/auth/register/',
            data={
                'first_name': 'New',
                'last_name': 'User',
                'email': 'new.user@example.com',
                'password': 'NewUser1!',
                'confirm_password': 'NewUser1!',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.content)

        login = self.client.post(
            '/api/v1/auth/login/',
            data={'role': 'user', 'email': 'new.user@example.com', 'password': 'NewUser1!'},
            format='json',
        )
        self.assertEqual(login.status_code, 200, login.content)
        self.assertIn('tokens', login.json())

    def test_user_password_reset_otp_flow(self):
        mail.outbox.clear()

        forgot = self.client.post(
            '/api/v1/auth/forgot-password/',
            data={'role': 'user', 'email': 'user@example.com'},
            format='json',
        )
        self.assertEqual(forgot.status_code, 200, forgot.content)
        self.assertGreaterEqual(len(mail.outbox), 1)

        otp = PasswordResetOTP.objects.filter(email='user@example.com', role='user').first()
        self.assertIsNotNone(otp)

        verify = self.client.post(
            '/api/v1/auth/verify-otp/',
            data={'role': 'user', 'email': 'user@example.com', 'otp': otp.otp},
            format='json',
        )
        self.assertEqual(verify.status_code, 200, verify.content)

        reset = self.client.post(
            '/api/v1/auth/reset-password/',
            data={
                'role': 'user',
                'email': 'user@example.com',
                'otp': otp.otp,
                'new_password': 'UserPass2!',
                'confirm_password': 'UserPass2!',
            },
            format='json',
        )
        self.assertEqual(reset.status_code, 200, reset.content)

        # Login should work with new password
        login = self.client.post(
            '/api/v1/auth/login/',
            data={'role': 'user', 'email': 'user@example.com', 'password': 'UserPass2!'},
            format='json',
        )
        self.assertEqual(login.status_code, 200, login.content)

    def test_user_order_detail_and_cancel(self):
        access = self._login('user', 'user@example.com', 'UserPass1!')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        create = self.client.post(
            '/api/v1/orders/',
            data={
                'product_id': self.product.id,
                'quantity': 1,
                'buyer_name': 'U Ser',
                'buyer_email': 'user@example.com',
                'buyer_phone': '+911111111111',
                'buyer_address': 'Addr',
            },
            format='json',
        )
        self.assertEqual(create.status_code, 201, create.content)
        order_id = create.json()['id']

        detail = self.client.get(f'/api/v1/orders/{order_id}/')
        self.assertEqual(detail.status_code, 200, detail.content)
        self.assertEqual(detail.json()['id'], order_id)

        cancel = self.client.post(f'/api/v1/orders/{order_id}/cancel/', data={}, format='json')
        self.assertEqual(cancel.status_code, 200, cancel.content)
        self.assertEqual(cancel.json()['status'], 'cancelled')
