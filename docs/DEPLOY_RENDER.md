# Render Deployment

## Services

Create two Render services:

- PostgreSQL database
- Web service for Django

The React frontend can be deployed as a Render static site, or built separately and served by a static host.

## Backend Environment Variables

- `DATABASE_URL`: Render PostgreSQL internal database URL
- `DJANGO_SECRET_KEY`: strong generated secret
- `DJANGO_DEBUG`: `false`
- `DJANGO_ALLOWED_HOSTS`: backend Render hostname
- `CORS_ALLOWED_ORIGINS`: frontend URL, for example `https://esg-workbench.onrender.com`

## Backend Build And Start

Build command:

```bash
pip install -r backend/requirements.txt && python backend/manage.py collectstatic --noinput && python backend/manage.py migrate && python backend/manage.py seed_demo
```

Start command:

```bash
cd backend && gunicorn config.wsgi:application
```

## Frontend Environment Variables

- `VITE_API_BASE_URL`: backend API URL ending in `/api`

Frontend build command:

```bash
cd frontend && npm install && npm run build
```

Publish directory:

```bash
frontend/dist
```

## CORS

`django-cors-headers` is configured in `settings.py`. Set `CORS_ALLOWED_ORIGINS` to the deployed frontend URL. Keep it explicit in production instead of using wildcard origins.

