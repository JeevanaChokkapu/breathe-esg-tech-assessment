# Breathe ESG Ingestion Prototype

Production-style prototype for ingesting ESG activity data from SAP CSV exports, utility CSV exports, and mocked Concur-style travel JSON payloads.

The project is intentionally compact:

- `backend/` contains Django, Django REST Framework, PostgreSQL-ready models, ingestion services, validation, audit logging, and review APIs.
- `frontend/` contains a Vite React analyst interface built with TailwindCSS, React Query, and Axios.
- `docs/` explains modeling choices, decisions, tradeoffs, data sources, and Render deployment.

The system focuses on raw-to-normalized traceability, row-level review, tenant isolation, and immutable audit history rather than generic CRUD screens.

## Local Run

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Use tenant `demo-corp` and analyst `analyst@example.com`. Seeded data sources can be viewed at `/api/data-sources/?tenant=demo-corp`; copy the UUID for the upload form. Example payloads live in `samples/`.

## Implementation Order

The code is deliberately organized around the assessment priorities:

1. Relational model and provenance: `backend/ingestion/models.py`
2. Source parsers and normalization: `backend/ingestion/services/`
3. Review and audit APIs: `backend/ingestion/views.py`
4. Analyst workbench: `frontend/src/App.jsx`
5. Design documentation: `docs/`
