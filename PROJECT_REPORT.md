# MEEVA — Multi-Vendor E-Commerce Marketplace

## Comprehensive Project Report

---

**Project Title:** Meeva — Multi-Vendor E-Commerce Marketplace Platform  
**Version:** 1.0  
**Date:** July 2025  
**Technology Stack:** Django 5.2.11 · Python · SQLite · Tailwind CSS  
**Repository Structure:** Django Monolithic Application with 4 Custom Apps  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Overview](#2-project-overview)
   - 2.1 Business Problem
   - 2.2 Objectives
   - 2.3 Scope
   - 2.4 Deliverables
   - 2.5 Success Criteria
3. [Solution Architecture & Design](#3-solution-architecture--design)
   - 3.1 System Architecture
   - 3.2 Technology Stack
   - 3.3 Database Design
   - 3.4 Application Module Design
   - 3.5 Integration Points
   - 3.6 Security Considerations
   - 3.7 Scalability Considerations
4. [Implementation Plan](#4-implementation-plan)
   - 4.1 Development Phases
   - 4.2 Module Implementation Details
   - 4.3 URL Routing & API Design
   - 4.4 Frontend Design System
   - 4.5 Risk Assessment
   - 4.6 Testing Strategy
5. [Conclusion & Next Steps](#5-conclusion--next-steps)
6. [Appendices](#6-appendices)

---

## 1. Executive Summary

**Meeva** is a full-stack multi-vendor e-commerce marketplace platform built on the Django 5.2.11 framework. The platform connects three distinct user roles — **Customers**, **Vendors**, and **Administrators** — through a unified web application featuring dedicated dashboards, workflows, and access controls for each stakeholder.

The platform addresses the growing demand for marketplace-style e-commerce by enabling multiple vendors to register, undergo KYC verification, list products, and manage orders within a single ecosystem. Customers can browse products from all approved vendors, add items to a session-based cart, place orders, and track their purchase history. Platform administrators oversee the entire ecosystem through a management dashboard that handles vendor approval/rejection workflows, account suspension, and operational monitoring.

### Key Highlights

| Metric | Value |
|---|---|
| **Total Django Apps** | 4 (pages, users, vendor, admin) |
| **Database Models** | 5 (Vendor, Product, Order, User, Admin) |
| **HTML Templates** | 23 pages across 4 template directories |
| **URL Endpoints** | 30+ distinct routes |
| **Email Notifications** | 6 automated email types |
| **Authentication** | Session-based with hashed passwords |
| **KYC Verification** | Aadhar, PAN, License document upload and validation |
| **Cart System** | Session-based multi-product cart |
| **Order Lifecycle** | 5-stage pipeline (Pending → Confirmed → Shipped → Delivered / Cancelled) |

The application employs a dark professional UI theme inspired by modern design systems, with a vibrant hero landing page (#4318FF blue accent) and consistent Tailwind CSS styling across all 23 pages. The frontend uses the Clash Display font family from Fontshare and Font Awesome 6.4.0 for iconography.

---

## 2. Project Overview

### 2.1 Business Problem

Traditional e-commerce platforms typically operate under a single-seller model, limiting market diversity and placing the burden of inventory management, product curation, and customer acquisition on a single entity. This model presents several challenges:

- **Limited Product Variety:** A single-seller model restricts the catalog to what one entity can source and stock.
- **High Barrier to Entry:** Small and medium businesses lack the technical infrastructure to launch standalone e-commerce stores.
- **Fragmented Vendor Onboarding:** Without a structured KYC and approval workflow, ensuring vendor legitimacy remains a manual, error-prone process.
- **Lack of Centralized Order Management:** Vendors operating independently lose visibility into platform-wide sales analytics and order lifecycle management.
- **Trust Deficit:** Customers lack confidence when buying from unverified sellers without a centralized platform overseeing quality and compliance.

### 2.2 Objectives

The Meeva platform was developed with the following core objectives:

1. **Build a Multi-Vendor Marketplace:** Create a centralized platform where multiple vendors can register, get verified, and sell their products to a shared customer base.
2. **Implement Robust KYC Verification:** Establish an admin-controlled verification workflow that validates vendor identity through Aadhar, PAN, and Business License documents before granting selling privileges.
3. **Deliver an Intuitive Shopping Experience:** Provide customers with a seamless product browsing, cart management, and checkout experience with real-time order tracking.
4. **Enable Vendor Self-Service:** Equip vendors with dashboards to manage products, track orders, update order statuses, and view sales reports independently.
5. **Provide Administrative Oversight:** Give platform administrators full visibility and control over vendor lifecycle management (approval, rejection, suspension, reactivation) with automated email notifications.
6. **Ensure Security & Data Integrity:** Implement password hashing, CSRF protection, session-based authentication, and input validation throughout all user-facing forms.

### 2.3 Scope

#### In Scope

| Area | Details |
|---|---|
| **User Management** | Customer registration, login/logout, profile auto-fill during checkout |
| **Vendor Management** | Registration with KYC documents, login via Email or Vendor ID, dashboard with statistics |
| **Product Management** | CRUD operations for vendor products with image uploads |
| **Order Management** | Single-product checkout, multi-product cart checkout, 5-stage order lifecycle |
| **Admin Panel** | Vendor approval/rejection/suspension/reactivation with email notifications |
| **Email System** | SMTP-based automated emails for 6 event types via Gmail |
| **Frontend** | Responsive dark-themed UI with Tailwind CSS and modern typography |
| **Landing Page** | Vibrant hero section with product catalog display |

#### Out of Scope (v1.0)

- Payment gateway integration (Razorpay, Stripe, etc.)
- Real-time notifications (WebSockets)
- Product reviews and ratings
- Search and advanced filtering
- Inventory alerts and low-stock notifications
- Multi-language / internationalization support
- Mobile application (iOS/Android)
- Analytics dashboard with charts/graphs

### 2.4 Deliverables

| # | Deliverable | Status |
|---|---|---|
| D1 | Django project with 4 fully functional apps | ✅ Delivered |
| D2 | 5 database models with migrations | ✅ Delivered |
| D3 | 23 responsive HTML templates with dark theme | ✅ Delivered |
| D4 | Session-based authentication for 3 user roles | ✅ Delivered |
| D5 | KYC document upload and admin verification workflow | ✅ Delivered |
| D6 | Session-based shopping cart with multi-product support | ✅ Delivered |
| D7 | Automated email notification system (6 types) | ✅ Delivered |
| D8 | Vendor sales report page | ✅ Delivered |
| D9 | Sokoo-inspired landing page with hero section | ✅ Delivered |
| D10 | Project documentation | ✅ Delivered |

### 2.5 Success Criteria

| Criteria | Target | Status |
|---|---|---|
| All user roles can register, login, and access their respective dashboards | Functional for Admin, Vendor, User | ✅ Met |
| Vendors can list products with images and manage inventory | Full CRUD with image uploads | ✅ Met |
| Customers can browse, add to cart, and checkout | Single and multi-product checkout | ✅ Met |
| Admin can approve/reject/suspend/activate vendors | 4 lifecycle actions with email | ✅ Met |
| Email notifications sent on key events | 6 automated email types | ✅ Met |
| Consistent UI theme across all 23 pages | Dark professional theme | ✅ Met |
| Django system check passes with 0 issues | `python manage.py check` | ✅ Met |
| Passwords stored securely | Django `make_password` / `check_password` | ✅ Met |

---

## 3. Solution Architecture & Design

### 3.1 System Architecture

Meeva follows a **monolithic Django MVT (Model-View-Template)** architecture with 4 decoupled Django applications, each responsible for a specific domain.

#### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Web Browser)                        │
│                                                                     │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│   │ Customer  │  │  Vendor  │  │  Admin   │  │  Public Visitor  │   │
│   │   UI      │  │   UI     │  │   UI     │  │      UI          │   │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬──────────┘   │
│        │              │              │                │              │
└────────┼──────────────┼──────────────┼────────────────┼──────────────┘
         │              │              │                │
    HTTPS/HTTP     HTTPS/HTTP     HTTPS/HTTP       HTTPS/HTTP
         │              │              │                │
┌────────┼──────────────┼──────────────┼────────────────┼──────────────┐
│        ▼              ▼              ▼                ▼              │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    Django URL Router                        │   │
│   │    /user/*  │  /vendor/*  │  /meevaadmin/*  │  /*           │   │
│   └──────┬──────────┬────────────────┬──────────────┬───────────┘   │
│          │          │                │              │                │
│   ┌──────▼───┐ ┌────▼─────┐  ┌──────▼──────┐ ┌────▼─────┐         │
│   │  Users   │ │  Vendor  │  │   Admin     │ │  Pages   │         │
│   │  App     │ │  App     │  │   App       │ │  App     │         │
│   │          │ │          │  │             │ │          │         │
│   │ • Login  │ │ • Login  │  │ • Login     │ │ • Landing│         │
│   │ • Regis. │ │ • Regis. │  │ • Dashboard │ │ • Role   │         │
│   │ • Browse │ │ • Dashbd │  │ • Vendor    │ │   Login  │         │
│   │ • Cart   │ │ • Produc.│  │   Mgmt      │ │          │         │
│   │ • Orders │ │ • Orders │  │ • Approve/  │ │          │         │
│   │ • Chkout │ │ • Sales  │  │   Reject    │ │          │         │
│   └──────┬───┘ └────┬─────┘  └──────┬──────┘ └────┬─────┘         │
│          │          │                │              │                │
│   ┌──────▼──────────▼────────────────▼──────────────▼───────────┐   │
│   │                    Django ORM Layer                          │   │
│   └──────────────────────────┬──────────────────────────────────┘   │
│                              │                                      │
│   ┌──────────────────────────▼──────────────────────────────────┐   │
│   │                   SQLite3 Database                          │   │
│   │   ┌────────┐ ┌─────────┐ ┌───────┐ ┌──────┐ ┌───────┐     │   │
│   │   │ Vendor │ │ Product │ │ Order │ │ User │ │ Admin │     │   │
│   │   └────────┘ └─────────┘ └───────┘ └──────┘ └───────┘     │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│   ┌──────────────────────────▼──────────────────────────────────┐   │
│   │              File System (Media Storage)                    │   │
│   │   /media/products/          - Product images                │   │
│   │   /media/vendor_documents/  - KYC documents (Aadhar/PAN/    │   │
│   │                               License)                      │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│   ┌──────────────────────────▼──────────────────────────────────┐   │
│   │              SMTP Email Service (Gmail)                     │   │
│   │   • Vendor Registration Confirmation                        │   │
│   │   • Vendor Approval / Rejection / Suspension Notices        │   │
│   │   • Order Notification to Vendor                            │   │
│   │   • Vendor Reactivation Notice                              │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│                      DJANGO SERVER (meeva)                          │
└─────────────────────────────────────────────────────────────────────┘
```

#### Application Flow Diagram

```
┌──────────────────── USER JOURNEY ────────────────────┐
│                                                       │
│   Landing Page (/)                                    │
│        │                                              │
│        ├── Browse Products (public, no login)         │
│        │        │                                     │
│        │        ├── Add to Cart → Login Required      │
│        │        │        │                            │
│        │        │        ▼                            │
│        │        │   View Cart → Enter Details         │
│        │        │        │                            │
│        │        │        ▼                            │
│        │        │   Place Order(s) → Email to Vendor  │
│        │        │        │                            │
│        │        │        ▼                            │
│        │        │   Order Success Page                │
│        │        │                                     │
│        │        └── Direct Checkout → Login Required  │
│        │                 │                            │
│        │                 ▼                            │
│        │            Checkout Form → Place Order       │
│        │                 │                            │
│        │                 ▼                            │
│        │            Order Confirmation                │
│        │                                              │
│        └── My Orders (login required)                 │
│                                                       │
└───────────────────────────────────────────────────────┘

┌──────────────────── VENDOR JOURNEY ──────────────────┐
│                                                       │
│   Register → Upload KYC Docs → Email Confirmation     │
│        │                                              │
│        ▼                                              │
│   Wait for Admin Approval                             │
│        │                                              │
│        ▼                                              │
│   Login (Email or Vendor ID)                          │
│        │                                              │
│        ├── Dashboard (Stats: Products, Orders, Rev.)  │
│        │                                              │
│        ├── Products Management                        │
│        │     ├── Add Product (with image)              │
│        │     ├── Edit Product                         │
│        │     └── Delete Product                       │
│        │                                              │
│        ├── Orders Management                          │
│        │     └── Update Status (Confirm/Ship/Deliver) │
│        │                                              │
│        └── Sales Report (Revenue Analytics)           │
│                                                       │
└───────────────────────────────────────────────────────┘

┌──────────────────── ADMIN JOURNEY ───────────────────┐
│                                                       │
│   Login (/meevaadmin/login/)                          │
│        │                                              │
│        ▼                                              │
│   Dashboard (Vendor Statistics Overview)              │
│        │                                              │
│        ├── Pending Vendors List                       │
│        │     └── Review → Approve / Reject            │
│        │                    │                         │
│        │                    ▼                         │
│        │              Email Notification to Vendor    │
│        │                                              │
│        ├── All Vendors (Filter by Status)             │
│        │     └── View Detail → Suspend / Activate     │
│        │                         │                    │
│        │                         ▼                    │
│        │                   Email Notification         │
│        │                                              │
│        └── Vendor Detail View                         │
│              (Full KYC Docs, Bank Info, Status)        │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### 3.2 Technology Stack

#### Backend

| Component | Technology | Version | Purpose |
|---|---|---|---|
| Framework | Django | 5.2.11 | Web application framework (MVT pattern) |
| Language | Python | 3.x | Server-side programming |
| Database | SQLite3 | Built-in | Relational data storage |
| ORM | Django ORM | 5.2.11 | Database abstraction layer |
| Password Hashing | Django Auth | Built-in | `make_password` / `check_password` (PBKDF2) |
| Email | Django Mail | Built-in | SMTP email via Gmail |
| Image Processing | Pillow | 11.1.0 | Image upload handling and validation |
| Environment Config | python-dotenv | 1.2.1 | `.env` file for secrets management |
| CORS | django-cors-headers | 4.9.0 | Cross-origin resource sharing |
| SQL Parsing | sqlparse | 0.5.5 | SQL formatting (Django dependency) |

#### Frontend

| Component | Technology | Version | Purpose |
|---|---|---|---|
| CSS Framework | Tailwind CSS | CDN (latest) | Utility-first responsive styling |
| Typography | Clash Display | Fontshare CDN | Primary display font family |
| Icons | Font Awesome | 6.4.0 | UI iconography |
| Templating | Django Templates | Built-in | Server-side HTML rendering with template tags |
| Animations | CSS Keyframes + IntersectionObserver | Native | Scroll-triggered animations on landing page |

#### Infrastructure

| Component | Technology | Purpose |
|---|---|---|
| Web Server | Django Development Server | Local development (`runserver`) |
| Static Files | Django `STATICFILES_DIRS` | CSS, JS, image assets |
| Media Files | Django `MEDIA_ROOT` | User-uploaded product images and KYC documents |
| Session Storage | Django Sessions (DB-backed) | Authentication state and cart data |
| Email Provider | Gmail SMTP | Transactional email delivery |

### 3.3 Database Design

#### Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     DATABASE SCHEMA                         │
│                      (db.sqlite3)                           │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────────┐
│       ADMIN          │         │         USER             │
├──────────────────────┤         ├──────────────────────────┤
│ id (PK, BigAuto)     │         │ id (PK, BigAuto)         │
│ email (unique)       │         │ first_name (char 255)    │
│ password (char 255)  │         │ last_name (char 255)     │
│ is_active (bool)     │         │ email (unique, char 255) │
│ created_at (datetime)│         │ phone (char 15)          │
│ updated_at (datetime)│         │ address (text)           │
└──────────────────────┘         │ password (char 255)      │
                                 │ is_active (bool)         │
                                 │ created_at (datetime)    │
                                 │ updated_at (datetime)    │
                                 └──────────────────────────┘

┌────────────────────────────────────┐
│             VENDOR                 │
├────────────────────────────────────┤
│ id (PK, BigAuto)                   │
│ vendor_id (unique, auto-gen MEV+8) │
│ full_name (char 255)               │
│ email (unique, email)              │
│ phone (char 15, regex validated)   │
│ password (char 255, hashed)        │
│ business_name (char 255)           │
│ business_address (text)            │
│ business_description (text, null)  │
│ aadhar_number (char 12, regex)     │
│ pan_number (char 10, regex)        │
│ license_number (char 50)           │
│ aadhar_image (image, nullable)     │
│ pan_image (image, nullable)        │
│ license_image (image, nullable)    │
│ bank_name (char 255)               │
│ account_number (char 50)           │
│ ifsc_code (char 11, regex)         │
│ account_holder_name (char 255)     │
│ platform_fee_percentage (dec 5,2)  │
│ status (enum: pending/approved/    │
│         rejected/suspended)        │
│ is_active (bool, default True)     │
│ rejection_reason (text, nullable)  │
│ approved_by (char 255, nullable)   │
│ approved_at (datetime, nullable)   │
│ created_at (datetime)              │
│ updated_at (datetime)              │
├────────────────────────────────────┤
│ Methods:                           │
│   generate_vendor_id() → MEV+8     │
│   is_pending (property)            │
│   is_approved (property)           │
└──────────┬───────────────┬─────────┘
           │               │
      1:N  │          1:N  │
           │               │
┌──────────▼───────┐  ┌────▼──────────────────────┐
│    PRODUCT       │  │         ORDER              │
├──────────────────┤  ├───────────────────────────┤
│ id (PK, BigAuto) │  │ id (PK, BigAuto)          │
│ vendor (FK→      │  │ product (FK→Product)       │
│   Vendor)        │  │ vendor (FK→Vendor)         │
│ name (char 255)  │  │ buyer_name (char 255)      │
│ description (txt)│  │ buyer_email (email)        │
│ price (dec 10,2) │  │ buyer_phone (char 15)      │
│ quantity (int)   │  │ buyer_address (text)       │
│ image (image,    │  │ quantity (int, min 1)       │
│   nullable)      │  │ price_per_unit (dec 10,2)  │
│ is_active (bool) │  │ total_price (dec 10,2)     │
│ created_at       │  │ status (enum: pending/     │
│ updated_at       │  │   confirmed/shipped/       │
└──────────┬───────┘  │   delivered/cancelled)     │
           │          │ created_at (datetime)      │
      1:N  │          │ updated_at (datetime)      │
           │          └───────────────────────────┘
           │                     ▲
           │          1:N        │
           └─────────────────────┘
```

#### Relationship Summary

| Relationship | Type | Description |
|---|---|---|
| Vendor → Product | One-to-Many | A vendor can have multiple products; each product belongs to exactly one vendor |
| Vendor → Order | One-to-Many | A vendor receives multiple orders; each order is associated with one vendor |
| Product → Order | One-to-Many | A product can appear in multiple orders; each order references one product |
| Admin ↔ Vendor | Logical (not FK) | Admin approves/rejects vendors; tracked via `approved_by` (admin email string) |
| User ↔ Order | Logical (not FK) | Orders are linked to users via `buyer_email` matching `User.email` |

#### Data Validation Rules

| Field | Model | Validation |
|---|---|---|
| `phone` | Vendor | Regex: `^\+?1?\d{9,15}$` |
| `aadhar_number` | Vendor | Regex: `^\d{12}$` (exactly 12 digits) |
| `pan_number` | Vendor | Regex: `^[A-Z]{5}[0-9]{4}[A-Z]{1}$` (Indian PAN format) |
| `ifsc_code` | Vendor | Regex: `^[A-Z]{4}0[A-Z0-9]{6}$` (Indian IFSC format) |
| `platform_fee_percentage` | Vendor | Min: 0, Max: 100 (default: 15.00%) |
| `price` | Product | Min: 0 (non-negative) |
| `quantity` | Product | Min: 0 (non-negative) |
| `quantity` | Order | Min: 1 (at least 1 unit) |
| `password` | All auth forms | Min 6 characters (view-level validation) |
| `email` | Vendor, User | Unique constraint at database level |

### 3.4 Application Module Design

#### Module 1: Pages App (`pages/`)

**Purpose:** Public-facing pages accessible without authentication.

| Component | File | Description |
|---|---|---|
| Views | `pages/views.py` | 2 view functions: `landing_page`, `role_login` |
| URLs | `pages/urls.py` | 2 routes: `/` (landing), `/role-login/` |
| Models | `pages/models.py` | None (uses Vendor app's Product model for landing display) |
| Templates | `templates/pages/` | `landing.html`, `role_login.html` |

**Landing Page Features:**
- Vibrant #4318FF blue hero section with "COMMERCE REIMAGINED" headline
- Floating decorative CSS shapes and gradient animations
- "START SELLING" and "EXPLORE SHOP" call-to-action buttons
- Product catalog grid below the hero with IntersectionObserver scroll animations
- Responsive navbar that transitions from blue to dark on scroll
- Cart count badge for logged-in users

#### Module 2: Users App (`users/`)

**Purpose:** Customer-facing features including authentication, shopping, cart, and order management.

| Component | File | Description |
|---|---|---|
| Views | `users/views.py` | 11 view functions covering auth, browse, cart, checkout, orders |
| URLs | `users/urls.py` | 11 routes under `/user/` prefix |
| Models | `users/models.py` | 1 model: `User` |
| Templates | `templates/users/` | 8 templates |

**View Functions:**

| View | Method | Auth | Description |
|---|---|---|---|
| `user_login` | GET/POST | Public | Login with email + password; redirects to pending checkout if applicable |
| `user_register` | GET/POST | Public | Register with name, email, password; validates password match and length |
| `user_logout` | GET | Logged in | Flushes session and redirects to browse |
| `browse_products` | GET | Public | Lists all active products from all approved vendors |
| `checkout` | GET/POST | Required | Single-product checkout with buyer detail form; auto-fills logged-in user info |
| `order_confirmation` | GET | Public | Displays order details after successful purchase |
| `add_to_cart` | GET | Required | Adds product to session cart with quantity management |
| `remove_from_cart` | GET | Any | Removes item from session cart |
| `view_cart` | GET/POST | Required | Displays cart, handles bulk order placement with delivery details |
| `cart_order_success` | GET | Any | Success page showing all orders placed from cart |
| `my_orders` | GET | Required | Lists all orders placed by the logged-in user's email |

**Cart Architecture (Session-Based):**

```
Session['cart'] = {
    "<product_id>": {
        "product_id": int,
        "name": str,
        "price": str (Decimal as string),
        "quantity": int,
        "image": str (URL) or None,
        "vendor_id": int,
        "vendor_name": str,
        "max_qty": int
    },
    ...
}
```

#### Module 3: Vendor App (`vendor/`)

**Purpose:** Vendor-facing features including registration with KYC, product management, order fulfillment, and sales analytics.

| Component | File | Description |
|---|---|---|
| Views | `vendor/views.py` | 10 view functions |
| URLs | `vendor/urls.py` | 11 routes under `/vendor/` prefix |
| Models | `vendor/models.py` | 3 models: `Vendor`, `Product`, `Order` |
| Emails | `vendor/emails.py` | 5 email utility functions |
| Templates | `templates/vendor/` | 8 templates |

**View Functions:**

| View | Method | Auth | Description |
|---|---|---|---|
| `vendor_register` | GET/POST | Public | Multi-step registration with 14 required fields + 3 document uploads |
| `vendor_login` | GET/POST | Public | Login via email or Vendor ID; blocks rejected/suspended vendors |
| `vendor_logout` | GET | Logged in | Flushes session |
| `vendor_dashboard` | GET | Required | Overview with total products, orders, revenue; recent 5 orders |
| `vendor_products` | GET | Required | Lists all vendor's products |
| `add_product` | GET/POST | Required | Create product with name, description, price, quantity, image |
| `edit_product` | GET/POST | Required | Update product fields; optional image replacement |
| `delete_product` | POST | Required | Delete product by ID (ownership validated) |
| `vendor_orders` | GET | Required | Lists all orders received by the vendor |
| `update_order_status` | POST | Required | Change order status (pending → confirmed → shipped → delivered / cancelled) |
| `vendor_sales_report` | GET | Required | Revenue analytics excluding cancelled orders |

**Vendor ID Generation:**
```
Format: MEV + 8 random uppercase alphanumeric characters
Example: MEVA3B7K2P9X
Uniqueness: Guaranteed via database lookup loop
```

**Email Notification Functions:**

| Function | Trigger | Recipient |
|---|---|---|
| `send_vendor_registration_email()` | Vendor registers | Vendor |
| `send_vendor_approval_email()` | Admin approves vendor | Vendor |
| `send_vendor_rejection_email()` | Admin rejects vendor | Vendor |
| `send_vendor_suspension_email()` | Admin suspends vendor | Vendor |
| `send_vendor_reactivation_email()` | Admin reactivates vendor | Vendor |
| `send_order_notification_email()` | Customer places order | Vendor |

#### Module 4: Admin App (`admin/`)

**Purpose:** Platform administration for vendor lifecycle management and operational oversight.

| Component | File | Description |
|---|---|---|
| Views | `admin/views.py` | 7 view functions |
| URLs | `admin/urls.py` | 8 routes under `/meevaadmin/` prefix |
| Models | `admin/models.py` | 1 model: `Admin` |
| Templates | `templates/admin/` | 5 templates |

**View Functions:**

| View | Method | Auth | Description |
|---|---|---|---|
| `admin_login` | GET/POST | Public | Admin authentication |
| `admin_dashboard` | GET | Required | Statistics: pending, approved, rejected, suspended, total vendors |
| `admin_logout` | GET | Logged in | Clears admin session |
| `pending_vendors` | GET | Required | List of vendors awaiting approval |
| `all_vendors` | GET | Required | All vendors with status filter (`?status=approved`, etc.) |
| `vendor_detail` | GET | Required | Full vendor profile: KYC docs, bank info, status history |
| `approve_vendor` | POST | Required | Approve vendor + send approval email |
| `reject_vendor` | POST | Required | Reject with reason + send rejection email |
| `suspend_vendor` | POST | Required | Suspend + deactivate + send suspension email |
| `activate_vendor` | POST | Required | Reactivate + send reactivation email |

### 3.5 Integration Points

#### Internal Integrations

```
┌──────────┐    imports Product, Order     ┌──────────┐
│  Pages   │ ◄─────────────────────────────│  Vendor  │
│  App     │   (landing page product list) │  App     │
└──────────┘                               └──────┬───┘
                                                   │
┌──────────┐    imports Product, Order     ┌───────┘
│  Users   │ ◄────────────────────────────┘
│  App     │   (browse, cart, checkout)
└──────────┘

┌──────────┐    imports Vendor model       ┌──────────┐
│  Admin   │ ◄─────────────────────────────│  Vendor  │
│  App     │    imports email functions     │  App     │
└──────────┘                               └──────────┘
```

| Source App | Target App | Dependency | Purpose |
|---|---|---|---|
| Pages | Vendor | `Product` model | Display active products on landing page |
| Users | Vendor | `Product`, `Order` models | Browse products, create orders |
| Admin | Vendor | `Vendor` model, email functions | Manage vendor lifecycle, send notifications |

#### External Integrations

| Service | Protocol | Configuration |
|---|---|---|
| Gmail SMTP | SMTP/TLS (port 587) | `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` via environment variables |

### 3.6 Security Considerations

#### Implemented Security Measures

| Measure | Implementation | Coverage |
|---|---|---|
| **Password Hashing** | Django's `make_password()` (PBKDF2 with SHA256) | All user/vendor/admin passwords |
| **CSRF Protection** | `@csrf_protect` decorator + `{% csrf_token %}` template tag | All POST forms |
| **Session Authentication** | Django session framework (DB-backed) | All authenticated views |
| **Input Validation** | Django model validators (regex) + view-level checks | Phone, Aadhar, PAN, IFSC, email, password |
| **HTTP Method Restriction** | `@require_http_methods` decorator | State-changing operations (POST only) |
| **Object Ownership** | Vendor-scoped queries (`Product.objects.get(vendor=vendor)`) | Product CRUD, order management |
| **XSS Prevention** | Django template auto-escaping | All template variables |
| **Clickjacking Protection** | `XFrameOptionsMiddleware` | All responses |
| **Environment Variables** | `python-dotenv` for secrets | `SECRET_KEY`, `EMAIL_HOST_PASSWORD` |

#### Security Recommendations for Production

| Area | Current State | Recommended Action |
|---|---|---|
| `DEBUG` | `True` (via env) | Set to `False` in production |
| `ALLOWED_HOSTS` | `['*']` | Restrict to specific domain(s) |
| `SECRET_KEY` | Fallback to hardcoded value | Use strong unique key via env only |
| HTTPS | Not enforced | Enable `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` |
| Rate Limiting | Not implemented | Add `django-ratelimit` for login/registration endpoints |
| Password Policy | Min 6 chars (view-level) | Use Django's full password validation pipeline |
| Session Security | Default settings | Set `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY` |
| Admin Default | Migration creates default admin | Change default credentials immediately |

### 3.7 Scalability Considerations

#### Current Architecture Limitations

| Component | Limitation | Impact |
|---|---|---|
| SQLite3 | Single-writer, file-based | Not suitable for concurrent writes in production |
| Session cart | Stored in DB-backed sessions | Cart data lost on session expiry |
| Media storage | Local filesystem | Not suitable for distributed deployments |
| Email delivery | Synchronous in request cycle | Delays response time during email send |

#### Recommended Scaling Strategies

| Strategy | Technology | Benefit |
|---|---|---|
| **Database Migration** | PostgreSQL / MySQL | Concurrent access, better performance at scale |
| **Cache Layer** | Redis | Session storage, frequently accessed data caching |
| **Async Email** | Celery + Redis/RabbitMQ | Non-blocking email delivery |
| **Object Storage** | AWS S3 / MinIO | Scalable media file storage |
| **Web Server** | Gunicorn + Nginx | Production-grade request handling |
| **Containerization** | Docker + Docker Compose | Reproducible deployments |
| **CDN** | Cloudflare / AWS CloudFront | Static asset delivery optimization |

---

## 4. Implementation Plan

### 4.1 Development Phases

```
┌─────────────────────────────────────────────────────────────────┐
│                   DEVELOPMENT TIMELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: Foundation & Core Models                              │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ • Django project setup (meeva/)                      │        │
│  │ • Settings configuration (DB, media, static, email)  │        │
│  │ • Vendor model with KYC fields                       │        │
│  │ • Product and Order models                           │        │
│  │ • User and Admin models                              │        │
│  │ • Database migrations                                │        │
│  │ • Default admin account creation (migration)         │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                 │
│  Phase 2: Vendor Module                                         │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ • Vendor registration with KYC document upload       │        │
│  │ • Vendor login (email + Vendor ID dual auth)         │        │
│  │ • Vendor dashboard with statistics                   │        │
│  │ • Product CRUD (add, edit, delete, list)             │        │
│  │ • Order management with status updates               │        │
│  │ • Sales report page                                  │        │
│  │ • Email notification system                          │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                 │
│  Phase 3: Admin Module                                          │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ • Admin login authentication                         │        │
│  │ • Admin dashboard with vendor statistics             │        │
│  │ • Pending vendor review workflow                     │        │
│  │ • Vendor approval / rejection with email             │        │
│  │ • Vendor suspension / reactivation                   │        │
│  │ • All vendors listing with status filtering          │        │
│  │ • Vendor detail view with document preview           │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                 │
│  Phase 4: Customer Module                                       │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ • Customer registration and login                    │        │
│  │ • Product browsing (public access)                   │        │
│  │ • Single-product direct checkout                     │        │
│  │ • Session-based shopping cart                        │        │
│  │ • Cart checkout with bulk order creation             │        │
│  │ • Order confirmation and success pages               │        │
│  │ • My Orders page (order history)                     │        │
│  │ • Order email notification to vendors                │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                 │
│  Phase 5: Frontend & UI/UX                                      │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ • Unified dark professional theme (23 pages)         │        │
│  │ • Tailwind CSS with Clash Display typography         │        │
│  │ • Sokoo-inspired landing page with blue hero         │        │
│  │ • Responsive design for all screen sizes             │        │
│  │ • Toast notifications via Django messages             │        │
│  │ • Scroll animations with IntersectionObserver        │        │
│  │ • Consistent navigation and footer across pages      │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Module Implementation Details

#### 4.2.1 Authentication System

All three user roles (Customer, Vendor, Admin) use independent, session-based authentication without Django's built-in `auth` module:

```
Authentication Flow:
─────────────────

  POST /login
       │
       ▼
  Find user by email
       │
       ├── Not Found → Error message
       │
       ▼
  check_password(input, stored_hash)
       │
       ├── Mismatch → Error message
       │
       ▼
  Check account status
       │
       ├── Rejected/Suspended → Error with reason
       │
       ▼
  Set session variables:
    • session['<role>_logged_in'] = True
    • session['<role>_email'] = email
    • session['<role>_id'] = user.id
       │
       ▼
  Redirect to dashboard / intended page
```

**Session Variables by Role:**

| Role | Session Keys |
|---|---|
| Customer | `user_logged_in`, `user_email`, `user_id`, `cart`, `last_orders` |
| Vendor | `vendor_logged_in`, `vendor_email`, `vendor_id` |
| Admin | `admin_logged_in`, `admin_email`, `admin_id` |

#### 4.2.2 Vendor Onboarding Workflow

```
Step 1: Registration Form (14 fields + 3 file uploads)
    │
    ├── Validate required fields
    ├── Validate password (min 6 chars, confirmation match)
    ├── Check email uniqueness
    ├── Hash password with make_password()
    ├── Auto-generate Vendor ID (MEV + 8 chars)
    ├── Save with status='pending'
    │
    ▼
Step 2: Confirmation Email sent to vendor
    │
    ▼
Step 3: Admin reviews application
    │
    ├── View KYC documents (Aadhar, PAN, License)
    ├── Review business details and bank information
    │
    ├── APPROVE → status='approved', approved_at=now()
    │      └── Approval email sent to vendor
    │
    └── REJECT → status='rejected', rejection_reason=<reason>
           └── Rejection email sent to vendor
```

#### 4.2.3 Order Lifecycle

```
Order Created (status: 'pending')
    │
    ├── Customer places order via checkout or cart
    ├── Product quantity decremented
    ├── Email sent to vendor
    │
    ▼
Vendor Confirms (status: 'confirmed')
    │
    ▼
Vendor Ships (status: 'shipped')
    │
    ▼
Vendor Marks Delivered (status: 'delivered')

    ──── OR at any stage ────

Vendor Cancels (status: 'cancelled')
    └── Excluded from revenue calculations
```

#### 4.2.4 Cart System

The cart uses Django sessions for server-side storage, requiring no additional database models:

```
Add to Cart:
    1. Check user login → redirect to login if not
    2. Validate product exists and is active
    3. If product in cart: increment quantity (up to available stock)
    4. If new product: add entry with product details
    5. Save cart dict to session

Cart Checkout:
    1. Collect delivery details (name, email, phone, address)
    2. Loop through cart items:
        a. Verify product still active and in stock
        b. Create Order for each item
        c. Decrement product stock
        d. Send email to respective vendor
    3. Clear cart from session
    4. Store order IDs in session for success page
    5. Redirect to success page
```

### 4.3 URL Routing & API Design

#### Complete URL Map

| Prefix | Path | Name | View | Method |
|---|---|---|---|---|
| `/` | `/` | `landing_page` | `pages.views.landing_page` | GET |
| `/` | `/role-login/` | `role_login` | `pages.views.role_login` | GET |
| `/user/` | `login/` | `user_login` | `users.views.user_login` | GET, POST |
| `/user/` | `register/` | `user_register` | `users.views.user_register` | GET, POST |
| `/user/` | `logout/` | `user_logout` | `users.views.user_logout` | GET |
| `/user/` | `products/` | `browse_products` | `users.views.browse_products` | GET |
| `/user/` | `checkout/<int:product_id>/` | `checkout` | `users.views.checkout` | GET, POST |
| `/user/` | `order-confirmation/<int:order_id>/` | `order_confirmation` | `users.views.order_confirmation` | GET |
| `/user/` | `cart/` | `view_cart` | `users.views.view_cart` | GET, POST |
| `/user/` | `cart/add/<int:product_id>/` | `add_to_cart` | `users.views.add_to_cart` | GET |
| `/user/` | `cart/remove/<int:product_id>/` | `remove_from_cart` | `users.views.remove_from_cart` | GET |
| `/user/` | `cart/success/` | `cart_order_success` | `users.views.cart_order_success` | GET |
| `/user/` | `my-orders/` | `my_orders` | `users.views.my_orders` | GET |
| `/vendor/` | `register/` | `vendor_register` | `vendor.views.vendor_register` | GET, POST |
| `/vendor/` | `login/` | `vendor_login` | `vendor.views.vendor_login` | GET, POST |
| `/vendor/` | `logout/` | `vendor_logout` | `vendor.views.vendor_logout` | GET |
| `/vendor/` | `dashboard/` | `vendor_dashboard` | `vendor.views.vendor_dashboard` | GET |
| `/vendor/` | `products/` | `vendor_products` | `vendor.views.vendor_products` | GET |
| `/vendor/` | `products/add/` | `add_product` | `vendor.views.add_product` | GET, POST |
| `/vendor/` | `products/edit/<int:product_id>/` | `edit_product` | `vendor.views.edit_product` | GET, POST |
| `/vendor/` | `products/delete/<int:product_id>/` | `delete_product` | `vendor.views.delete_product` | POST |
| `/vendor/` | `orders/` | `vendor_orders` | `vendor.views.vendor_orders` | GET |
| `/vendor/` | `orders/<int:order_id>/status/` | `update_order_status` | `vendor.views.update_order_status` | POST |
| `/vendor/` | `sales-report/` | `vendor_sales_report` | `vendor.views.vendor_sales_report` | GET |
| `/meevaadmin/` | `login/` | `admin_login` | `admin.views.admin_login` | GET, POST |
| `/meevaadmin/` | `dashboard/` | `admin_dashboard` | `admin.views.admin_dashboard` | GET |
| `/meevaadmin/` | `logout/` | `admin_logout` | `admin.views.admin_logout` | GET |
| `/meevaadmin/` | `pending-vendors/` | `pending_vendors` | `admin.views.pending_vendors` | GET |
| `/meevaadmin/` | `vendors/` | `all_vendors` | `admin.views.all_vendors` | GET |
| `/meevaadmin/` | `vendor/<int:vendor_id>/` | `vendor_detail` | `admin.views.vendor_detail` | GET |
| `/meevaadmin/` | `vendor/<int:vendor_id>/approve/` | `approve_vendor` | `admin.views.approve_vendor` | POST |
| `/meevaadmin/` | `vendor/<int:vendor_id>/reject/` | `reject_vendor` | `admin.views.reject_vendor` | POST |
| `/meevaadmin/` | `vendor/<int:vendor_id>/suspend/` | `suspend_vendor` | `admin.views.suspend_vendor` | POST |
| `/meevaadmin/` | `vendor/<int:vendor_id>/activate/` | `activate_vendor` | `admin.views.activate_vendor` | POST |

### 4.4 Frontend Design System

#### Theme Specification

| Property | Value | Usage |
|---|---|---|
| Background (primary) | `#0a0a0a` | Page body background |
| Background (cards) | `#141414` | Card and container backgrounds |
| Background (inputs) | `#1a1a1a` | Form input fields |
| Border color | `#222222` | Card borders, dividers |
| Text (primary) | `#ffffff` | Headings, buttons, primary content |
| Text (secondary) | `#888888` | Labels, descriptions, metadata |
| Text (muted) | `#555555` | Placeholders, disabled content |
| Accent (hero) | `#4318FF` | Landing page hero section |
| Font family | `Clash Display` | All headings and body text |
| Icon library | Font Awesome 6.4.0 | Navigation, buttons, status indicators |

#### Template Inventory

| Directory | Template | Purpose |
|---|---|---|
| `templates/pages/` | `landing.html` | Public landing page with hero + product grid |
| `templates/pages/` | `role_login.html` | User/Vendor login role selector |
| `templates/users/` | `login.html` | Customer login form |
| `templates/users/` | `register.html` | Customer registration form |
| `templates/users/` | `browse_products.html` | Product catalog with cart controls |
| `templates/users/` | `cart.html` | Shopping cart with delivery details form |
| `templates/users/` | `checkout.html` | Single-product checkout form |
| `templates/users/` | `order_confirmation.html` | Post-purchase order details |
| `templates/users/` | `cart_order_success.html` | Multi-order success summary |
| `templates/users/` | `my_orders.html` | Customer order history |
| `templates/vendor/` | `login.html` | Vendor login (email or Vendor ID) |
| `templates/vendor/` | `register.html` | Vendor registration with KYC uploads |
| `templates/vendor/` | `dashboard.html` | Vendor overview with stats |
| `templates/vendor/` | `products.html` | Vendor product listing |
| `templates/vendor/` | `add_product.html` | New product form |
| `templates/vendor/` | `edit_product.html` | Product edit form |
| `templates/vendor/` | `orders.html` | Vendor order management |
| `templates/vendor/` | `sales_report.html` | Revenue analytics |
| `templates/admin/` | `login.html` | Admin authentication |
| `templates/admin/` | `dashboard.html` | Admin overview with vendor stats |
| `templates/admin/` | `pending_vendors.html` | Pending vendor applications list |
| `templates/admin/` | `all_vendors.html` | All vendors with status filtering |
| `templates/admin/` | `vendor_detail.html` | Detailed vendor profile with KYC docs |

### 4.5 Risk Assessment

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | SQLite concurrency bottleneck under load | High | High | Migrate to PostgreSQL for production |
| R2 | Email delivery failures (Gmail rate limits) | Medium | Medium | Implement retry logic; switch to transactional email service (SendGrid, Mailgun) |
| R3 | Session data loss on server restart | Medium | Low | Configure persistent session storage (Redis/DB) |
| R4 | Unauthorized access to vendor data | Low | High | Already mitigated via session checks + ownership validation |
| R5 | Large file uploads exhausting disk space | Medium | Medium | Add file size validation; implement cloud storage |
| R6 | Cart abandonment data loss | Medium | Low | Session expiry clears cart; consider persistent cart model |
| R7 | Missing payment integration | N/A | High | Planned for v2.0; currently no monetary transactions processed |
| R8 | No pagination on product/order lists | High | Medium | Add Django pagination for lists exceeding 20+ items |

### 4.6 Testing Strategy

#### Recommended Testing Approach

| Level | Tool | Coverage Area |
|---|---|---|
| **Unit Tests** | Django `TestCase` | Model methods, validators, vendor ID generation |
| **Integration Tests** | Django `Client` | View logic, form submissions, redirect flows |
| **Authentication Tests** | Custom test cases | Login/logout, session management, access control |
| **Email Tests** | Django `mail.outbox` | Verify email content and delivery for all 6 types |
| **Form Validation Tests** | POST requests | Required fields, password match, uniqueness constraints |
| **Cart Tests** | Session manipulation | Add/remove/checkout lifecycle |

#### Test Scenarios by Module

**Vendor Module:**
- Registration with valid/invalid KYC data
- Login with email vs. Vendor ID
- Blocked login for rejected/suspended vendors
- Product CRUD operations with ownership checks
- Order status transition validation

**User Module:**
- Registration with duplicate email
- Cart operations: add, increment, remove, checkout
- Stock validation during checkout
- Order creation and product quantity decrement
- Redirect to checkout after login

**Admin Module:**
- Vendor approval/rejection with email dispatch
- Vendor suspension and reactivation
- Status filter on vendor listing
- Access control for all admin endpoints

---

## 5. Conclusion & Next Steps

### 5.1 Project Summary

The Meeva Multi-Vendor E-Commerce Marketplace has been successfully developed as a fully functional Django-based web application. The platform delivers a complete multi-stakeholder experience with:

- **3 distinct user roles** each with dedicated authentication, dashboards, and workflows
- **23 responsive HTML pages** with a unified dark professional theme
- **5 database models** covering the core domain: vendors, products, orders, users, and admins
- **6 automated email notification types** for critical business events
- **A robust vendor KYC workflow** with document upload and admin review
- **A dual-path shopping experience** supporting both direct checkout and cart-based purchasing
- **Session-based cart architecture** requiring no additional database overhead

The application passes all Django system checks and provides a solid foundation for a production-ready marketplace platform.

### 5.2 Future Enhancements (Roadmap)

#### v2.0 — Payment & Search

| Feature | Description | Priority |
|---|---|---|
| Payment Gateway | Integrate Razorpay/Stripe for online payments | Critical |
| Product Search | Full-text search with filters (price, category, vendor) | High |
| Product Categories | Hierarchical category taxonomy for product organization | High |
| Pagination | Server-side pagination for all list views | High |
| Order Tracking | Real-time status tracking with timeline UI | Medium |

#### v3.0 — Engagement & Analytics

| Feature | Description | Priority |
|---|---|---|
| Reviews & Ratings | Customer product reviews with star ratings | High |
| Vendor Analytics | Charts and graphs for sales trends, top products | Medium |
| Wishlist | Customer wishlist / save for later | Medium |
| Notifications | In-app notification center (bell icon dropdown) | Medium |
| Coupons & Discounts | Vendor-created discount codes | Low |

#### v4.0 — Scale & Operations

| Feature | Description | Priority |
|---|---|---|
| PostgreSQL Migration | Production database upgrade | Critical |
| Docker Deployment | Containerized deployment with Docker Compose | High |
| Celery Task Queue | Async email delivery and background jobs | High |
| AWS S3 Storage | Cloud-based media file storage | High |
| API Layer | Django REST Framework for mobile app support | Medium |
| Admin Analytics | Platform-wide metrics dashboard | Medium |
| Multi-language | i18n/l10n support | Low |

### 5.3 Screenshots

> **[Screenshot Placeholder: Landing Page]**
> _The vibrant blue hero section with "COMMERCE REIMAGINED" headline and product grid below._

> **[Screenshot Placeholder: Vendor Registration]**
> _Multi-step registration form with KYC document upload fields._

> **[Screenshot Placeholder: Vendor Dashboard]**
> _Statistics overview showing total products, orders, and revenue._

> **[Screenshot Placeholder: Product Catalog]**
> _Customer-facing product grid with cart add buttons._

> **[Screenshot Placeholder: Shopping Cart]**
> _Session-based cart with product details and delivery form._

> **[Screenshot Placeholder: Admin Dashboard]**
> _Vendor statistics overview with pending, approved, rejected, and suspended counts._

> **[Screenshot Placeholder: Admin Vendor Detail]**
> _Full vendor profile view with KYC documents and action buttons._

> **[Screenshot Placeholder: Order Management]**
> _Vendor order list with status update dropdown._

---

## 6. Appendices

### Appendix A: Project Directory Structure

```
Meeva/
├── EMAIL_SETUP.md                      # Email configuration guide
├── requirements.txt                    # Python dependencies
├── PROJECT_REPORT.md                   # This document
│
└── meeva/                              # Django project root
    ├── manage.py                       # Django management script
    ├── db.sqlite3                      # SQLite database file
    │
    ├── meeva/                          # Project configuration
    │   ├── __init__.py
    │   ├── settings.py                 # Django settings (DB, email, media, static)
    │   ├── urls.py                     # Root URL configuration
    │   ├── wsgi.py                     # WSGI entry point
    │   └── asgi.py                     # ASGI entry point
    │
    ├── pages/                          # Public pages app
    │   ├── __init__.py
    │   ├── apps.py
    │   ├── models.py                   # (empty)
    │   ├── views.py                    # landing_page, role_login
    │   ├── urls.py                     # 2 URL patterns
    │   ├── admin.py
    │   ├── tests.py
    │   └── migrations/
    │
    ├── users/                          # Customer app
    │   ├── __init__.py
    │   ├── apps.py
    │   ├── models.py                   # User model
    │   ├── views.py                    # 11 view functions (443 lines)
    │   ├── urls.py                     # 11 URL patterns
    │   ├── admin.py
    │   ├── tests.py
    │   └── migrations/
    │       └── 0001_initial.py
    │
    ├── vendor/                         # Vendor app
    │   ├── __init__.py
    │   ├── apps.py
    │   ├── models.py                   # Vendor, Product, Order (173 lines)
    │   ├── views.py                    # 10 view functions (327 lines)
    │   ├── urls.py                     # 11 URL patterns
    │   ├── emails.py                   # 5 email functions (140 lines)
    │   ├── admin.py
    │   ├── tests.py
    │   ├── test_email.py               # Email testing utility
    │   └── migrations/
    │       ├── 0001_initial.py
    │       ├── 0002_vendor_vendor_id.py
    │       └── 0003_product_order.py
    │
    ├── admin/                          # Admin app
    │   ├── __init__.py
    │   ├── apps.py
    │   ├── models.py                   # Admin model
    │   ├── views.py                    # 7 view functions (234 lines)
    │   ├── urls.py                     # 8 URL patterns
    │   ├── admin.py
    │   ├── tests.py
    │   └── migrations/
    │       ├── 0001_initial.py
    │       ├── 0002_create_default_admin.py
    │       └── 0003_alter_admin_options.py
    │
    ├── templates/                      # All HTML templates (23 files)
    │   ├── pages/                      # 2 templates
    │   │   ├── landing.html
    │   │   └── role_login.html
    │   ├── users/                      # 8 templates
    │   │   ├── login.html
    │   │   ├── register.html
    │   │   ├── browse_products.html
    │   │   ├── cart.html
    │   │   ├── checkout.html
    │   │   ├── order_confirmation.html
    │   │   ├── cart_order_success.html
    │   │   └── my_orders.html
    │   ├── vendor/                     # 8 templates
    │   │   ├── login.html
    │   │   ├── register.html
    │   │   ├── dashboard.html
    │   │   ├── products.html
    │   │   ├── add_product.html
    │   │   ├── edit_product.html
    │   │   ├── orders.html
    │   │   └── sales_report.html
    │   └── admin/                      # 5 templates
    │       ├── login.html
    │       ├── dashboard.html
    │       ├── pending_vendors.html
    │       ├── all_vendors.html
    │       └── vendor_detail.html
    │
    ├── static/                         # Static assets (CSS, JS, images)
    │
    └── media/                          # User-uploaded files
        ├── products/                   # Product images
        └── vendor_documents/           # KYC documents
            ├── aadhar/
            ├── pan/
            └── license/
```

### Appendix B: Dependencies (requirements.txt)

```
asgiref==3.8.1
Django==5.2.11
django-cors-headers==4.9.0
pillow==11.1.0
python-dotenv==1.2.1
sqlparse==0.5.5
typing_extensions==4.14.0
tzdata==2025.2
```

### Appendix C: Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key for cryptographic signing | Hardcoded fallback (change in production) |
| `DEBUG` | Enable/disable debug mode | `True` |
| `EMAIL_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP server port | `587` |
| `EMAIL_USE_TLS` | Enable TLS encryption | `True` |
| `EMAIL_HOST_USER` | SMTP username (sender email) | Configured |
| `EMAIL_HOST_PASSWORD` | SMTP app password | Configured |
| `DEFAULT_FROM_EMAIL` | Default sender email address | Configured |

### Appendix D: Quick Start Guide

```bash
# 1. Clone the repository
git clone <repository-url>
cd Meeva

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
# Create .env file in meeva/ directory with email credentials

# 5. Run migrations
cd meeva
python manage.py migrate

# 6. Start development server
python manage.py runserver

# 7. Access the application
# Landing Page:     http://localhost:8000/
# User Login:       http://localhost:8000/user/login/
# Vendor Login:     http://localhost:8000/vendor/login/
# Admin Login:      http://localhost:8000/meevaadmin/login/
```

---

**End of Report**

*Meeva — Multi-Vendor E-Commerce Marketplace Platform*  
*Version 1.0 | July 2025*
