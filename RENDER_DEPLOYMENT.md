# Render Deployment (GitHub Auto-Deploy)

This repo is already configured to use Postgres when `DATABASE_URL` is set (see `meeva/meeva/settings.py`).

## 1) Render commands (copy/paste)

If you can edit your Render service settings, use:

- **Build Command**: `bash render-build.sh`
- **Start Command**: `bash render-start.sh`

These scripts:
- Install requirements
- Run `collectstatic` (static files)
- Run `migrate` (applies new migrations, including indexes)
- Start Gunicorn bound to `$PORT`

If you *cannot* edit build/start commands, do a one-off run in Render Shell after deploy:

- `cd meeva && python manage.py migrate`
- `cd meeva && python manage.py collectstatic --noinput`

## 2) Required environment variables (Render dashboard)

At minimum:

- `SECRET_KEY` (required; never use the default)
- `DEBUG=False`
- `ALLOWED_HOSTS=your-service.onrender.com` (add your custom domain too if you have one)
- `DATABASE_URL=postgres://...` (from your Render Postgres)

Recommended:

- `CSRF_TRUSTED_ORIGINS=https://your-service.onrender.com`
- `CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com` (only if you have a separate frontend)
- `DB_SSL_REQUIRE=True` (if your DB connection requires SSL)

Email (for OTP + notifications):

- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`

## 3) Post-deploy verification

- `GET /api/v1/health/`
- `GET /api/v1/docs/`

## 4) Important production note about uploads

User/vendor uploads are stored under `MEDIA_ROOT` (local filesystem). Many Render setups have an ephemeral filesystem, so uploads can be lost on redeploy unless you attach a persistent disk or use external object storage.
