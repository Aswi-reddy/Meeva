# MEEVA — Multi-Vendor E-Commerce Marketplace Platform

## Presentation Content (14 Slides)

---

## SLIDE 1 — Title Slide

**Title:** MEEVA — Multi-Vendor E-Commerce Marketplace Platform

**Subtitle:** A Full-Stack Web Application Built with Django 5.2

**Tagline:** A marketplace ecosystem where vendors sell, customers shop, and admins govern — all under one platform.

**Tech Badges:** Django 5.2 | Python 3.x | Tailwind CSS | SQLite | Pillow | SMTP Email | Gunicorn

**Metrics at a Glance:**

- 4 Django Apps — `pages`, `users`, `vendor`, `core_admin`
- 7 Database Models — Admin, User, Vendor, Product, ProductSizeStock, Order, Wishlist, PasswordResetOTP
- 23 HTML Templates across 4 template directories
- 30+ URL Endpoints
- 6 Automated Email Notification Types
- 5-Stage Order Lifecycle: Pending → Confirmed → Shipped → Delivered / Cancelled

---

## SLIDE 2 — Problem Statement & Project Overview

**Problem Statement:**
Traditional e-commerce platforms are single-seller systems. Small businesses lack a unified platform to sell alongside other vendors, while customers must visit multiple websites. There is no centralized system with vendor KYC verification, admin oversight, and a unified shopping experience.

**Solution — Meeva:**
Meeva is a multi-vendor marketplace that solves this by providing three dedicated portals:

1. **Customer Portal** — Browse a unified catalog from all approved vendors, add to cart/wishlist, checkout, and track orders.
2. **Vendor Portal** — Register with KYC documents, manage products with size-wise stock, fulfill orders, and view sales analytics.
3. **Admin Portal** — Oversee vendor onboarding with approve/reject/suspend/reactivate workflows, review KYC documents, and monitor platform statistics.

**Key Innovation:** Complete vendor lifecycle management with KYC verification — no vendor can sell without admin-verified identity (Aadhar, PAN, Business License).

---

## SLIDE 3 — Why Django? Technical Justification

**Django is a full-stack framework, not just backend.**

| Capability                         | How Meeva Uses It                                                                      | Alternative Would Require                                            |
| ---------------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **ORM (Object-Relational Mapper)** | 7 models with ForeignKey relationships, validators, auto-migrations                    | SQLAlchemy + Alembic (Flask) or Sequelize + manual migrations (Node) |
| **Template Engine**                | 23 server-rendered HTML pages with `{% csrf_token %}`, `{% for %}`, `{% if %}`         | Separate React/Vue frontend + API layer                              |
| **Built-in Security**              | CSRF protection, password hashing (PBKDF2), XSS auto-escaping, clickjacking middleware | bcrypt + csurf + helmet + manual sanitization                        |
| **Session Framework**              | Session-based cart (zero Redis/JWT), session-based auth for 3 portals                  | express-session + Redis setup                                        |
| **Email Backend**                  | `send_mail()` — 6 email types with 2 lines of config                                   | Nodemailer + template engine                                         |
| **File Uploads**                   | `ImageField(upload_to='...')` for KYC documents & product images                       | Multer + manual path management                                      |
| **Admin Interface**                | Built-in Django admin for emergency database access                                    | Build from scratch or use AdminBro                                   |
| **Migration System**               | 6 auto-generated migration files tracking every schema change                          | Manual SQL or Knex/TypeORM migrations                                |
| **Management Commands**            | Custom `bootstrap_admin` command for initial admin setup                               | Custom CLI scripts                                                   |
| **Aggregation Queries**            | `Sum`, `Count`, `Q` objects for dashboards & sales reports                             | Raw SQL queries                                                      |

**Bottom Line:** Django gave us a production-ready multi-portal marketplace in a single codebase with zero external frontend framework.

---

## SLIDE 4 — System Architecture & App Structure

**Architecture:** Django MTV (Model-Template-View) — Monolithic Full-Stack

```
Client Browser
    │
    ▼
[Django URL Router] ──── meeva/urls.py
    │
    ├── /             →  pages app      (Landing, Role Selector)
    ├── /user/        →  users app      (Customer Portal)
    ├── /vendor/      →  vendor app     (Vendor Portal)
    └── /meevaadmin/  →  core_admin app (Admin Portal)
    │
    ▼
[Views.py] ── Business Logic ── [Models.py] ── Django ORM ── [SQLite DB]
    │
    ▼
[Templates/] ── Tailwind CSS + Font Awesome ── HTML Response to Browser
```

**App Responsibility Matrix:**

| App          | Models Owned                             | Templates               | URL Endpoints | Role                |
| ------------ | ---------------------------------------- | ----------------------- | ------------- | ------------------- |
| `pages`      | None                                     | 2 (landing, role_login) | 2             | Public entry point  |
| `users`      | User, Wishlist, PasswordResetOTP         | 11                      | 14            | Customer experience |
| `vendor`     | Vendor, Product, ProductSizeStock, Order | 11                      | 14            | Seller operations   |
| `core_admin` | Admin                                    | 5                       | 10            | Platform governance |

**Django Capability Used:** App-based modularity — each app is self-contained with its own `models.py`, `views.py`, `urls.py`, `migrations/`. Django enforces separation of concerns by design.

---

## SLIDE 5 — Database Schema & Model Relationships

**7 Models across 3 apps:**

**Relationship Diagram:**

```
Admin (core_admin)                    User (users)
  │                                     │
  │ approved_by (stores email)          │ ForeignKey (One-to-Many)
  │                                     ▼
  ▼                                  Wishlist ──── FK ──── Product
Vendor ──────────────────────────────────────────────────────┐
  │                                                          │
  │ ForeignKey (One-to-Many)          ForeignKey (One-to-Many)│
  ▼                                                          │
Product ◄────────────────────────────────────────────────────┘
  │
  │ ForeignKey (One-to-Many)          ForeignKey (One-to-Many)
  ├─────────────────┐
  ▼                 ▼
Order         ProductSizeStock

PasswordResetOTP (Standalone — shared by User & Vendor via role field)
```

**Relationship Types:**

| Relationship               | Type            | Django Implementation                                                  | Explanation                                                                                                                                           |
| -------------------------- | --------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Vendor → Product           | **One-to-Many** | `ForeignKey(Vendor, on_delete=CASCADE, related_name='products')`       | One vendor owns many products. Deleting vendor deletes all their products.                                                                            |
| Vendor → Order             | **One-to-Many** | `ForeignKey(Vendor, on_delete=CASCADE, related_name='orders')`         | One vendor receives many orders.                                                                                                                      |
| Product → Order            | **One-to-Many** | `ForeignKey(Product, on_delete=CASCADE, related_name='orders')`        | One product can appear in many orders.                                                                                                                |
| Product → ProductSizeStock | **One-to-Many** | `ForeignKey(Product, on_delete=CASCADE, related_name='size_stocks')`   | One product has many size-stock entries (S:10, M:5, L:3).                                                                                             |
| User → Wishlist            | **One-to-Many** | `ForeignKey(User, on_delete=CASCADE, related_name='wishlist_items')`   | One user has many wishlist items.                                                                                                                     |
| Wishlist → Product         | **Many-to-One** | `ForeignKey(Product, on_delete=CASCADE, related_name='wishlisted_by')` | Many users can wishlist the same product. `unique_together = ('user', 'product')` prevents duplicates — effectively a **Many-to-Many through table**. |

**Django Capabilities Used:** `ForeignKey` with `on_delete=CASCADE`, `related_name` for reverse queries, `unique_together` constraint, `RegexValidator` for Aadhar/PAN/IFSC, `MinValueValidator`/`MaxValueValidator`, `auto_now_add`/`auto_now` for timestamps.

---

## SLIDE 6 — MODULE 1: Customer Portal (users app)

**Role:** End customers who browse, shop, and track orders.

**Backend (views.py — 748 lines, 14 URL endpoints):**

| Feature         | View Function                                                                         | Django Capability Used                                                                                                                                       |
| --------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Registration    | `user_register()`                                                                     | `make_password()` — PBKDF2 hashing, `send_mail()` for welcome email                                                                                          |
| Login           | `user_login()`                                                                        | `check_password()`, Session management (`request.session`), smart redirect after login                                                                       |
| Browse Products | `browse_products()`                                                                   | `Q` objects for search (`name__icontains OR description__icontains`), `select_related('vendor')`, `prefetch_related('size_stocks')` for N+1 query prevention |
| Session Cart    | `add_to_cart()`, `view_cart()`, `remove_from_cart()`                                  | Django sessions — cart stored as `request.session['cart']` dictionary, zero database writes                                                                  |
| Checkout        | `checkout()`                                                                          | `get_object_or_404()`, Order creation with `Order.objects.create()`, email notification to vendor                                                            |
| Order History   | `my_orders()`                                                                         | Filter orders by `buyer_email`, ordered by `-created_at`                                                                                                     |
| Wishlist        | `toggle_wishlist()`, `view_wishlist()`                                                | Wishlist model with `unique_together` preventing duplicate entries                                                                                           |
| Forgot Password | 3-step flow: `user_forgot_password()` → `user_verify_otp()` → `user_reset_password()` | OTP generation, expiry check via `@property is_expired`, session-based flow control                                                                          |

**Frontend (11 templates):**

- `login.html`, `register.html` — Forms with CSRF tokens, password validation feedback
- `browse_products.html` — Product grid with search bar, category dropdown, sort (price/newest), wishlist toggle heart icons
- `cart.html` — Multi-item cart with quantity display, subtotal calculation, checkout form with pre-filled user details
- `checkout.html` — Single-product checkout with size selector, address form
- `my_orders.html` — Order history table with status badges (Pending=yellow, Confirmed=blue, Shipped=purple, Delivered=green, Cancelled=red)
- `wishlist.html` — Wishlist grid with remove/add-to-cart actions

**Frontend Tech:** Tailwind CSS via CDN, Font Awesome 6.4 icons, Clash Display typography (Fontshare), CSS animations (fadeUp, scaleIn, slideLeft)

---

## SLIDE 7 — MODULE 2: Vendor Portal (vendor app)

**Role:** Sellers who register with KYC, manage inventory, and fulfill orders.

**Backend (views.py — 628 lines, 14 URL endpoints):**

| Feature          | View Function                                         | Django Capability Used                                                                                                                                                     |
| ---------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| KYC Registration | `vendor_register()`                                   | `request.FILES.get()` for document upload (Aadhar, PAN, License images), `ImageField(upload_to='vendor_documents/...')`, auto-generated Vendor ID (`MEV` + 8 random chars) |
| Dual Login       | `vendor_login()`                                      | Login via **email OR Vendor ID** — `Vendor.objects.get(email=...)` or `Vendor.objects.get(vendor_id=...)`                                                                  |
| Dashboard        | `vendor_dashboard()`                                  | `aggregate(Sum('total_price'))` for revenue, `.count()` for product/order stats                                                                                            |
| Product CRUD     | `add_product()`, `edit_product()`, `delete_product()` | Full Create-Read-Update-Delete with `ImageField` for product images, 10 category choices                                                                                   |
| Size-Wise Stock  | `_apply_size_stock()`, `_parse_size_stock_input()`    | `ProductSizeStock` model with `update_or_create()`, `transaction.atomic()` for consistency, total quantity auto-synced                                                     |
| Order Management | `vendor_orders()`, `update_order_status()`            | Status transition logic: stock deducted only on acceptance via `_deduct_stock_on_accept()` using `select_for_update()` (row-level DB lock)                                 |
| Sales Report     | `vendor_sales_report()`                               | Revenue aggregation excluding cancelled orders                                                                                                                             |
| Forgot Password  | 3-step OTP flow (shared with users)                   | `PasswordResetOTP` model with role='vendor'                                                                                                                                |

**Key Business Logic — Stock Deduction with Database Locking:**

```python
def _deduct_stock_on_accept(order):
    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=order.product_id)
        # Deduct size-wise or global stock
```

`select_for_update()` prevents race conditions when multiple orders are accepted simultaneously — this is a Django ORM capability that maps to SQL `SELECT ... FOR UPDATE`.

**Frontend (11 templates):**

- `register.html` — Multi-section form: Personal Info → Business Info → KYC Documents (file upload) → Bank Details
- `dashboard.html` — Stats cards (Products, Orders, Revenue), recent orders table
- `products.html` — Product listing with Edit/Delete actions
- `add_product.html` / `edit_product.html` — Product form with category dropdown, sizes input, image upload
- `orders.html` — Order management table with status update dropdown (Confirm/Ship/Deliver/Cancel)
- `sales_report.html` — Revenue analytics with order breakdown

---

## SLIDE 8 — MODULE 3: Admin Portal (core_admin app)

**Role:** Platform administrator who governs vendor onboarding and platform integrity.

**Backend (views.py — 10 URL endpoints):**

| Feature                    | View Function       | Django Capability Used                                                                                       |
| -------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------ |
| Secure Login               | `admin_login()`     | `check_password()` against `Admin` model, session-based auth                                                 |
| Dashboard                  | `admin_dashboard()` | `.count()` queries for pending/approved/rejected/suspended vendor counts                                     |
| Pending Queue              | `pending_vendors()` | `Vendor.objects.filter(status='pending').order_by('-created_at')`                                            |
| Vendor Directory           | `all_vendors()`     | Dynamic filtering: `request.GET.get('status')` with conditional `.filter()`                                  |
| Vendor Detail + KYC Review | `vendor_detail()`   | `get_object_or_404()` — displays all vendor info including uploaded KYC document images                      |
| Approve                    | `approve_vendor()`  | Sets status='approved', records `approved_by` (admin email), `approved_at` (timestamp), sends approval email |
| Reject                     | `reject_vendor()`   | Sets status='rejected', stores `rejection_reason`, sends rejection email with reason                         |
| Suspend                    | `suspend_vendor()`  | Sets status='suspended', `is_active=False`, sends suspension email                                           |
| Reactivate                 | `activate_vendor()` | Sets status='approved', `is_active=True`, sends reactivation email                                           |

**Vendor Lifecycle State Machine (managed by Admin):**

```
Registered → Pending → Approved → (can be Suspended → Reactivated)
                    → Rejected
```

**Admin Bootstrap (Custom Management Command):**

```
python manage.py bootstrap_admin --email admin@meeva.com --password securepass
```

Uses Django's `BaseCommand` — reads from environment variables or CLI args. Idempotent (safe to run multiple times).

**Frontend (5 templates):**

- `login.html` — Clean admin login form
- `dashboard.html` — Platform stats cards (Total, Pending, Approved, Rejected, Suspended vendors)
- `pending_vendors.html` — Queue of applications awaiting review
- `all_vendors.html` — Full vendor directory with status filter tabs (All/Pending/Approved/Rejected/Suspended)
- `vendor_detail.html` — Complete vendor profile with KYC document viewer (Aadhar/PAN/License images), action buttons (Approve/Reject/Suspend/Activate)

---

## SLIDE 9 — Automated Email Notification System

**Backend:** `vendor/emails.py` (196 lines) + inline `send_mail()` calls in views

**Django Capability:** `django.core.mail.send_mail()` — configured with Gmail SMTP in `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

**8 Email Notification Types:**

| #   | Trigger                    | Recipient | Function                                                                |
| --- | -------------------------- | --------- | ----------------------------------------------------------------------- |
| 1   | Customer Registration      | Customer  | Inline `send_mail()` in `user_register()`                               |
| 2   | Vendor Registration        | Vendor    | `send_vendor_registration_email()` — includes Vendor ID                 |
| 3   | Vendor Approved            | Vendor    | `send_vendor_approval_email()` — includes login instructions            |
| 4   | Vendor Rejected            | Vendor    | `send_vendor_rejection_email()` — includes rejection reason             |
| 5   | Vendor Suspended           | Vendor    | `send_vendor_suspension_email()`                                        |
| 6   | Vendor Reactivated         | Vendor    | `send_vendor_reactivation_email()`                                      |
| 7   | New Order Placed           | Vendor    | `send_order_notification_email()` — full order details                  |
| 8   | Order Accepted / Delivered | Customer  | `send_user_order_accepted_email()`, `send_user_order_delivered_email()` |

**Design Decision:** All emails use `fail_silently=True` or try/except so that email failures never block the primary user action (registration, order placement, etc.). Flags `user_accepted_email_sent` and `user_delivered_email_sent` on the Order model ensure emails are sent **only once per milestone**.

---

## SLIDE 10 — Security Architecture

**Django provides 6 layers of security used in Meeva:**

| Layer                       | Django Feature                           | Implementation in Meeva                                                                                             |
| --------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Password Security**       | `make_password()` / `check_password()`   | PBKDF2-SHA256 hashing with random salt — never stored in plain text                                                 |
| **Custom Password Policy**  | `AUTH_PASSWORD_VALIDATORS`               | Custom `CustomPasswordValidator`: must contain uppercase, lowercase, digit, and special character                   |
| **CSRF Protection**         | `@csrf_protect` + `{% csrf_token %}`     | Every POST form protected — 14 forms across all portals                                                             |
| **Input Validation**        | `RegexValidator` on model fields         | Aadhar (`^\d{12}$`), PAN (`^[A-Z]{5}[0-9]{4}[A-Z]{1}$`), IFSC (`^[A-Z]{4}0[A-Z0-9]{6}$`), Phone (`^\+?1?\d{9,15}$`) |
| **XSS Prevention**          | Django template auto-escaping            | All `{{ variable }}` outputs are HTML-escaped by default                                                            |
| **Session Security**        | Production settings                      | `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `SECURE_SSL_REDIRECT=True` in production                   |
| **Clickjacking Protection** | `XFrameOptionsMiddleware`                | Enabled in middleware — prevents page from being embedded in iframes                                                |
| **HTTP Method Enforcement** | `@require_http_methods(["GET", "POST"])` | All sensitive views restricted to allowed methods only                                                              |
| **Environment Secrets**     | `python-dotenv`                          | SECRET_KEY, DB credentials, email passwords loaded from `.env` — never hardcoded                                    |

---

## SLIDE 11 — Frontend Technology & User Experience

**Tech Stack:** Tailwind CSS (CDN) + Font Awesome 6.4 + Clash Display Font + Django Template Language

**Why Tailwind CSS with Django Templates (not React/Vue)?**

- No build pipeline needed — CDN-based Tailwind + Django template rendering = zero JavaScript framework overhead
- Server-Side Rendering (SSR) — every page is fully rendered before reaching the browser, resulting in fast first-paint and SEO-friendly pages
- Django template tags (`{% for product in products %}`, `{% if is_user_logged_in %}`, `{% csrf_token %}`) handle dynamic content without any API layer

**Frontend Features Across Modules:**

| Feature             | Implementation                                                                                                  |
| ------------------- | --------------------------------------------------------------------------------------------------------------- |
| Responsive Design   | Tailwind's `sm:`, `md:`, `lg:` breakpoints across all 23 templates                                              |
| CSS Animations      | Custom `@keyframes fadeUp`, `scaleIn`, `slideLeft` on landing page                                              |
| Icon System         | Font Awesome 6.4 — shopping cart, heart (wishlist), search, status indicators                                   |
| Typography          | Clash Display from Fontshare — modern, professional appearance                                                  |
| Flash Messages      | Django's `messages` framework — success (green), error (red), warning (yellow), info (blue) toast notifications |
| Form Handling       | CSRF tokens, pre-filled fields from session data, client-side + server-side validation                          |
| Status Badges       | Color-coded order/vendor status badges using Tailwind utility classes                                           |
| Theme Configuration | Centralized `theme_config.html` template for consistent theming                                                 |

---

## SLIDE 12 — Advantages & Future Enhancements

**Advantages of Meeva:**

| Advantage                               | Detail                                                                                                |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Single Codebase**                     | Full-stack in one Django project — no separate frontend/backend repos, no API versioning overhead     |
| **KYC-First Marketplace**               | No vendor can sell without admin-verified Aadhar, PAN, and Business License — builds platform trust   |
| **Zero External Dependencies for Cart** | Session-based cart requires no Redis, no database writes — lightweight and fast                       |
| **Atomic Stock Management**             | `select_for_update()` + `transaction.atomic()` prevents overselling in race conditions                |
| **Deployment-Ready**                    | Gunicorn + WhiteNoise + dj-database-url — deploys to Render/Railway/Heroku with near-zero config      |
| **Database Portable**                   | SQLite in development, PostgreSQL/MySQL in production via `dj-database-url` — single config line swap |
| **Idempotent Admin Setup**              | `bootstrap_admin` management command can be run safely in CI/CD pipelines                             |

**Future Enhancements:**

| Enhancement                     | Technical Approach                                                                  |
| ------------------------------- | ----------------------------------------------------------------------------------- |
| **Payment Gateway Integration** | Razorpay/Stripe SDK — add `payment_status` field to Order model                     |
| **Real-Time Order Tracking**    | Django Channels (WebSocket) for live status updates                                 |
| **Product Reviews & Ratings**   | New `Review` model with ForeignKey to User + Product (Many-to-One)                  |
| **Vendor Analytics Dashboard**  | Chart.js / ApexCharts integration with Django REST Framework API endpoints          |
| **Image CDN & Optimization**    | Cloudinary/S3 storage backend replacing local `FileSystemStorage`                   |
| **Multi-Language Support**      | Django's `i18n` framework — already configured (`USE_I18N = True`)                  |
| **SMS OTP via Twilio**          | Extend `PasswordResetOTP` model to support SMS delivery channel                     |
| **Pagination**                  | Django's `Paginator` class for product listings and order history                   |
| **Elasticsearch Integration**   | Replace `Q(name__icontains=...)` with full-text search for better product discovery |

---

## SLIDE 13 — Project Justification & Conclusion

**Why This Project Matters:**

1. **Real-World Industry Problem** — Multi-vendor marketplaces (Amazon, Flipkart, Etsy) are the dominant e-commerce model. Meeva demonstrates the core architecture of such platforms.

2. **End-to-End Coverage** — This is not a CRUD demo. It covers:
   - 3 distinct user roles with separate authentication
   - KYC document verification workflow
   - 5-stage order lifecycle with stock management
   - 8 automated email notifications
   - Session-based cart with multi-product checkout
   - OTP-based password recovery
   - Sales analytics and revenue reporting

3. **Django's Full Capability Demonstrated:**
   - ORM with complex relationships (One-to-Many, Many-to-Many via through table)
   - Custom management commands (`bootstrap_admin`)
   - Custom validators (`CustomPasswordValidator`, `RegexValidator`)
   - Template engine with conditional rendering
   - Session framework for cart and authentication
   - Email backend for SMTP notifications
   - File upload handling with `ImageField`
   - Database transactions with `select_for_update()`
   - Aggregation queries (`Sum`, `Count`, `Q`)
   - Middleware stack (Security, Session, CSRF, Clickjacking)

4. **Production-Grade Practices:**
   - Environment variables for all secrets
   - WhiteNoise for static file serving
   - Gunicorn as WSGI server
   - SSL/HTTPS configuration for production
   - Database-agnostic via `dj-database-url`

**Final Statement:**
Meeva proves that Django is not just a backend framework — it is a complete full-stack platform capable of building a production-ready, multi-role, security-sensitive marketplace application. The monolithic architecture was the right choice for this scale, delivering faster development, simpler deployment, and unified security — without the overhead of a separate frontend framework or microservices architecture.

---

## SLIDE 14 — Thank You & Demo

**Title:** Thank You

**Live Demo URLs:**

- Landing Page: `/`
- Customer Login: `/user/login/`
- Vendor Registration: `/vendor/register/`
- Admin Dashboard: `/meevaadmin/login/`

**Tech Stack Recap:**
Django 5.2 | Python 3.x | Tailwind CSS | SQLite / PostgreSQL | Pillow | Gmail SMTP | Gunicorn | WhiteNoise

**Team / Contact Information**
[Your names and details here]
