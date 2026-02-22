<p align="center">
  <img src="https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

<h1 align="center">🏪 MEEVA</h1>
<h3 align="center">Multi-Vendor E-Commerce Marketplace Platform</h3>

<p align="center">
  A full-stack multi-vendor marketplace built with Django, featuring dedicated portals for <strong>Customers</strong>, <strong>Vendors</strong>, and <strong>Administrators</strong> — complete with KYC verification, session-based cart, order lifecycle management, and automated email notifications.
</p>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Database Schema](#-database-schema)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Usage](#-usage)
- [URL Endpoints](#-url-endpoints)
- [Project Structure](#-project-structure)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 Overview

**Meeva** is a marketplace ecosystem where multiple vendors can register, get KYC-verified by an admin, list products, and fulfill orders — all within a single platform. Customers browse a unified catalog, manage a session-based cart, and track orders through a 5-stage lifecycle. Administrators oversee vendor onboarding with approval/rejection workflows and automated email notifications at every stage.

| Metric           | Value                                                 |
| ---------------- | ----------------------------------------------------- |
| Django Apps      | 4 — `pages` · `users` · `vendor` · `core_admin`       |
| Database Models  | 5 — `Admin` · `User` · `Vendor` · `Product` · `Order` |
| HTML Templates   | 23 pages across 4 template directories                |
| URL Endpoints    | 30+ distinct routes                                   |
| Automated Emails | 6 notification types                                  |
| Order Lifecycle  | Pending → Confirmed → Shipped → Delivered / Cancelled |

---

## ✨ Key Features

### 🛒 Customer Portal

- Account registration & login with hashed passwords
- Browse products with **search**, **category filter**, and **sort** (price / newest)
- Session-based shopping cart (add, remove, quantity management)
- Single-product quick checkout & multi-product cart checkout
- Order confirmation with email notification
- Order history dashboard

### 🏬 Vendor Portal

- Multi-step registration with **KYC document upload** (Aadhar, PAN, Business License)
- Login via **Email** or unique **Vendor ID** (`MEV` prefix)
- Dashboard with real-time statistics (products, orders, revenue)
- Full product CRUD — name, description, category, sizes, price, stock, images
- Order management with status updates
- Sales report with revenue analytics

### 🔐 Admin Portal

- Secure admin authentication
- Vendor lifecycle management — **Approve / Reject / Suspend / Reactivate**
- Pending applications queue with KYC document review
- Vendor directory with status-based filtering
- Rejection reason capture with email notification
- Dashboard with platform-wide statistics

### 📧 Automated Email Notifications

| Trigger                          | Recipient |
| -------------------------------- | --------- |
| Vendor Registration Confirmation | Vendor    |
| Vendor Approval                  | Vendor    |
| Vendor Rejection (with reason)   | Vendor    |
| Vendor Suspension                | Vendor    |
| Vendor Reactivation              | Vendor    |
| New Order Placed                 | Vendor    |

### 🔒 Security

- Passwords hashed via Django's `make_password` / `check_password`
- CSRF protection on all forms
- Custom password validator (uppercase, lowercase, digit, special character)
- Session-based authentication across all three portals
- Input validation with Django model validators (Aadhar, PAN, IFSC, phone)
- Environment variables for all secrets (`.env`)

---

## 🛠 Tech Stack

| Layer           | Technology                            |
| --------------- | ------------------------------------- |
| **Backend**     | Django 5.2, Python 3.x                |
| **Database**    | SQLite (development) / MySQL-ready    |
| **Frontend**    | Tailwind CSS, HTML5, Font Awesome 6.4 |
| **Typography**  | Clash Display (Fontshare)             |
| **Email**       | Django SMTP (Gmail App Passwords)     |
| **Media**       | Pillow for image handling             |
| **Server**      | Gunicorn (production-ready)           |
| **Environment** | python-dotenv                         |

---

### App Responsibilities

| App          | Purpose                                                               |
| ------------ | --------------------------------------------------------------------- |
| `pages`      | Landing page, role-based login selector, public product browsing      |
| `users`      | Customer auth, product browsing, cart, checkout, order history        |
| `vendor`     | Vendor auth, KYC registration, product CRUD, order & sales management |
| `core_admin` | Admin auth, vendor approval workflows, platform statistics            |

---

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- pip
- Git
- Gmail account with [App Password](https://myaccount.google.com/apppasswords) (for email notifications)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/meeva.git
cd meeva

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables (see section below)
cp .env.example .env
# Edit .env with your values

# 5. Navigate to the Django project
cd meeva

# 6. Run migrations
python manage.py makemigrations
python manage.py migrate

# 7. Start the development server
python manage.py runserver
```

The application will be available at **http://localhost:8000**

---

## 🔑 Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Default Admin Credentials
ADMIN_EMAIL=admin@meeva.com
ADMIN_PASSWORD=your-admin-password
```

> **Note:** For Gmail, you must use an [App Password](https://myaccount.google.com/apppasswords) — not your regular password. Enable 2-Step Verification first.

---

## 💡 Usage

### Access Points

| Portal            | URL                                       | Description                           |
| ----------------- | ----------------------------------------- | ------------------------------------- |
| Landing Page      | `http://localhost:8000/`                  | Public product catalog & hero section |
| Role Selector     | `http://localhost:8000/role-login/`       | Choose User or Vendor login           |
| Customer Login    | `http://localhost:8000/user/login/`       | Customer authentication               |
| Customer Register | `http://localhost:8000/user/register/`    | New customer sign-up                  |
| Vendor Login      | `http://localhost:8000/vendor/login/`     | Vendor authentication                 |
| Vendor Register   | `http://localhost:8000/vendor/register/`  | Vendor KYC registration               |
| Admin Login       | `http://localhost:8000/meevaadmin/login/` | Admin authentication                  |

### Quick Start Guide

1. **Admin Setup** — Log in at `/meevaadmin/login/` using credentials from `.env`
2. **Vendor Registration** — Register at `/vendor/register/` with KYC documents
3. **Admin Approval** — Approve the vendor from the admin dashboard
4. **Add Products** — Vendor logs in and adds products from the dashboard
5. **Customer Shopping** — Register/login as a customer and start shopping

---

## 🔗 URL Endpoints

<details>
<summary><strong>Pages App</strong> — Public Routes</summary>

| Method | URL            | View           | Description                       |
| ------ | -------------- | -------------- | --------------------------------- |
| GET    | `/`            | `landing_page` | Landing page with product catalog |
| GET    | `/role-login/` | `role_login`   | Role-based login selector         |

</details>

<details>
<summary><strong>Users App</strong> — Customer Routes</summary>

| Method   | URL                              | View                 | Description            |
| -------- | -------------------------------- | -------------------- | ---------------------- |
| GET/POST | `/user/login/`                   | `user_login`         | Customer login         |
| GET/POST | `/user/register/`                | `user_register`      | Customer registration  |
| GET      | `/user/logout/`                  | `user_logout`        | Customer logout        |
| GET      | `/user/products/`                | `browse_products`    | Browse product catalog |
| GET/POST | `/user/checkout/<id>/`           | `checkout`           | Product checkout       |
| GET      | `/user/order-confirmation/<id>/` | `order_confirmation` | Order confirmation     |
| GET      | `/user/cart/`                    | `view_cart`          | View cart              |
| POST     | `/user/cart/add/<id>/`           | `add_to_cart`        | Add product to cart    |
| POST     | `/user/cart/remove/<id>/`        | `remove_from_cart`   | Remove from cart       |
| GET      | `/user/cart/success/`            | `cart_order_success` | Cart order success     |
| GET      | `/user/my-orders/`               | `my_orders`          | Order history          |

</details>

<details>
<summary><strong>Vendor App</strong> — Vendor Routes</summary>

| Method   | URL                             | View                  | Description             |
| -------- | ------------------------------- | --------------------- | ----------------------- |
| GET/POST | `/vendor/register/`             | `vendor_register`     | Vendor KYC registration |
| GET/POST | `/vendor/login/`                | `vendor_login`        | Vendor login (email/ID) |
| GET      | `/vendor/logout/`               | `vendor_logout`       | Vendor logout           |
| GET      | `/vendor/dashboard/`            | `vendor_dashboard`    | Vendor dashboard        |
| GET      | `/vendor/products/`             | `vendor_products`     | Product listing         |
| GET/POST | `/vendor/products/add/`         | `add_product`         | Add new product         |
| GET/POST | `/vendor/products/edit/<id>/`   | `edit_product`        | Edit product            |
| POST     | `/vendor/products/delete/<id>/` | `delete_product`      | Delete product          |
| GET      | `/vendor/orders/`               | `vendor_orders`       | Order management        |
| POST     | `/vendor/orders/<id>/status/`   | `update_order_status` | Update order status     |
| GET      | `/vendor/sales-report/`         | `vendor_sales_report` | Sales analytics         |

</details>

<details>
<summary><strong>Admin App</strong> — Admin Routes</summary>

| Method   | URL                                 | View              | Description              |
| -------- | ----------------------------------- | ----------------- | ------------------------ |
| GET/POST | `/meevaadmin/login/`                | `admin_login`     | Admin login              |
| GET      | `/meevaadmin/dashboard/`            | `admin_dashboard` | Admin dashboard          |
| GET      | `/meevaadmin/logout/`               | `admin_logout`    | Admin logout             |
| GET      | `/meevaadmin/pending-vendors/`      | `pending_vendors` | Pending applications     |
| GET      | `/meevaadmin/vendors/`              | `all_vendors`     | All vendors directory    |
| GET      | `/meevaadmin/vendor/<id>/`          | `vendor_detail`   | Vendor detail + KYC docs |
| POST     | `/meevaadmin/vendor/<id>/approve/`  | `approve_vendor`  | Approve vendor           |
| POST     | `/meevaadmin/vendor/<id>/reject/`   | `reject_vendor`   | Reject vendor            |
| POST     | `/meevaadmin/vendor/<id>/suspend/`  | `suspend_vendor`  | Suspend vendor           |
| POST     | `/meevaadmin/vendor/<id>/activate/` | `activate_vendor` | Reactivate vendor        |

</details>

---

<p align="center">
  Built with ❤️ using Django
</p>
