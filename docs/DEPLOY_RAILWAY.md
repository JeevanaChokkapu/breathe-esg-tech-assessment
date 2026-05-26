# Railway Deployment

Deploy this as three Railway services:

- PostgreSQL database
- Django backend service from `backend/`
- Vite React frontend service from `frontend/`

This keeps the deployment understandable for the assessment: the backend owns ingestion and audit workflows, the frontend is a separate analyst UI, and PostgreSQL is the production database.

## 1. Create The PostgreSQL Service

In Railway, create a new project and add a PostgreSQL database service.

Railway exposes database connection variables to services in the project. This backend uses `DATABASE_URL`, which Railway PostgreSQL provides.

## 2. Deploy The Backend

Create a new Railway service from the GitHub repository.

Set the service root directory to:

```bash
backend
```

Railway/Nixpacks should detect Python. Use these settings if Railway asks for explicit commands.

Build command:

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

Start command:

```bash
python manage.py migrate && python manage.py seed_demo && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

The committed `backend/Procfile` contains the same start command.

Backend variables:

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
DJANGO_SECRET_KEY=<generate-a-long-random-secret>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=<your-backend>.up.railway.app
CORS_ALLOWED_ORIGINS=https://<your-frontend>.up.railway.app
```

After deploy, open the backend URL at:

```bash
https://<your-backend>.up.railway.app/api/
```

You should see the DRF API root.

## 3. Deploy The Frontend

Create another Railway service from the same GitHub repository.

Set the service root directory to:

```bash
frontend
```

Build command:

```bash
npm install && npm run build
```

Start command:

```bash
npm run start
```

Frontend variables:

```bash
VITE_API_BASE_URL=https://<your-backend>.up.railway.app/api
```

Vite reads `VITE_` variables during build, so redeploy the frontend after changing `VITE_API_BASE_URL`.

## 4. Update CORS After Frontend Deploys

Once Railway gives the frontend a public URL, return to the backend service and set:

```bash
CORS_ALLOWED_ORIGINS=https://<your-frontend>.up.railway.app
```

Redeploy the backend after changing this variable.

## 5. Smoke Test

Open the frontend URL.

Use:

```text
Tenant: demo-corp
Analyst: analyst@example.com
```

Expected checks:

- Data source dropdown shows seeded sources.
- Upload `samples/sap_fuel.csv` against `SAP Fuel Export`.
- Review queue shows suspicious rows.
- Hold/approve/reject creates audit timeline entries.

## Notes

`seed_demo` runs on backend startup so the assessment environment is usable after deploy. In a real production system, seed/reference data would be managed through controlled migrations or admin workflows instead of every web process start.
