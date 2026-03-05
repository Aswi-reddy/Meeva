# Meeva Backend Implementation Phases (Tracking)

This document tracks the planned backend phases and what has actually been implemented.

## Phase 1 — REST API Completion (Keep Existing Flow)

**Goal:** Fill the essential REST surface while preserving current auth model (JWT principal with `role`, `entity_id`, `email`), permissions, and optional pagination behavior.

**Status:** Completed ✅

**Delivered:**

- Customer registration API: `POST /api/v1/auth/register/`
- OTP password reset APIs (OTP via email):
  - `POST /api/v1/auth/forgot-password/`
  - `POST /api/v1/auth/verify-otp/`
  - `POST /api/v1/auth/reset-password/`
- Orders:
  - `GET /api/v1/orders/<id>/`
  - `POST /api/v1/orders/<id>/cancel/`

**Key files:**

- `meeva/api/serializers.py`
- `meeva/api/views.py`
- `meeva/api/urls.py`
- `meeva/api/tests.py`

**Verification:**

- `python manage.py test`

---

## Phase 2 — Django-Native Ops + Security

### Item 1 — Django Admin registrations

**Goal:** Make Django Admin useful for real operations/inspection.

**Status:** Completed ✅

**Key files:**

- `meeva/vendor/admin.py` (Vendor/Product/Order/ProductSizeStock)
- `meeva/users/admin.py` (User/Wishlist/PasswordResetOTP)
- `meeva/core_admin/admin.py` (custom Admin)

---

### Item 2 — Superuser bootstrap command

**Goal:** Create/update a Django superuser for `/admin/` in an idempotent way.

**Status:** Completed ✅

**Key file:**

- `meeva/core_admin/management/commands/bootstrap_superuser.py`

**Usage:**

- Env vars:
  - `DJANGO_SUPERUSER_USERNAME`
  - `DJANGO_SUPERUSER_EMAIL`
  - `DJANGO_SUPERUSER_PASSWORD`
- Run:
  - `python manage.py bootstrap_superuser --update-password`

---

### Item 3 — DRF throttling for sensitive endpoints

**Goal:** Protect login + OTP endpoints from abuse without changing other APIs.

**Status:** Completed ✅

**Key files:**

- `meeva/meeva/settings.py` (scoped throttle rates)
- `meeva/api/views.py` (scopes applied to auth/OTP views)

**Configuration (override via env):**

- `THROTTLE_AUTH_LOGIN` (default: `10/min`)
- `THROTTLE_AUTH_OTP` (default: `5/min`)

---

### Item 4 — OTP cleanup command

**Goal:** Periodic hygiene to delete expired OTP rows.

**Status:** Completed ✅

**Key files:**

- `meeva/users/management/commands/cleanup_otps.py`
- `meeva/users/tests.py`

**Usage:**

- Dry run: `python manage.py cleanup_otps --dry-run`
- Execute: `python manage.py cleanup_otps`

---

## Next Work

No further phases will be implemented without explicit confirmation from the project owner.

---

## Phase 3 — Scalable REST + Production Readiness

**Goal:** Improve API scalability and backend operability using Django/DRF-native tooling without changing existing auth/response flows.

**Status:** Completed ✅

### Item 1 — OpenAPI schema + docs

**Goal:** Provide a machine-readable API contract and interactive documentation.

**Status:** Completed ✅

**Target endpoints:**

- `GET /api/v1/schema/`
- `GET /api/v1/docs/`

---

### Item 2 — Database indexes (safe migrations)

**Goal:** Add indexes for high-frequency queries to keep performance stable as data grows.

**Status:** Completed ✅

---

### Item 3 — Health endpoint

**Goal:** Add an ops-friendly health check endpoint.

**Status:** Completed ✅

**Target endpoint:**

- `GET /api/v1/health/`
