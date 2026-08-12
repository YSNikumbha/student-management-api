# Student Management System

A production-oriented Student Management System with a FastAPI backend, Alembic-managed database schema, JWT authentication, and a React/Vite admin frontend.

## Modules

The admin frontend is organized around these primary modules:

- Dashboard
- Students
- Classes
- Attendance
- Fee Management
- Reports
- Settings

Backend domain concepts such as courses, academic years, semesters, batches, fee structures, user management, notifications, audit logs, and academic performance are integrated into those modules.

## Tech Stack

- Backend: FastAPI, SQLAlchemy 2.x, Pydantic v2, Alembic
- Frontend: React, TypeScript, Vite, Recharts
- Database: SQLite for local development, PostgreSQL for production
- Auth: JWT bearer tokens
- Tests: pytest
- Deployment: Docker and Docker Compose

## Project Structure

```text
student-management-api/
├── alembic/                 # Database migrations
├── app/
│   ├── core/                # Settings and security helpers
│   ├── database/            # SQLAlchemy engine/session
│   ├── dependencies/        # FastAPI dependencies
│   ├── models/              # ORM models
│   ├── routers/             # API routers
│   ├── schemas/             # Pydantic schemas
│   └── services/            # Business logic
├── frontend/                # React/Vite admin frontend
│   ├── src/
│   │   ├── api/             # API clients
│   │   ├── components/      # Dashboard modules and shared UI
│   │   ├── types/           # Shared TypeScript types
│   │   └── utils/           # Formatting helpers
│   └── package.json
├── tests/                   # Backend test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── alembic.ini
```

## Environment

Copy the example environment file and adjust values for your machine:

```bash
cp .env.example .env
```

Common variables:

```text
DATABASE_URL=sqlite:///./student_management.db
SECRET_KEY=change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ENVIRONMENT=development
APP_NAME=Student Management API
```

For PostgreSQL:

```text
DATABASE_URL=postgresql+psycopg://user:password@host:5432/database
```

The React frontend reads `VITE_API_BASE_URL` during local Vite development. If it is not set, it defaults to `http://127.0.0.1:8000`.

## Backend Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python scripts/create_admin.py
python -m uvicorn app.main:app --reload
```

Useful URLs:

- API docs: `http://127.0.0.1:8000/docs`
- Login: `http://127.0.0.1:8000/login`
- Admin app: `http://127.0.0.1:8000/admin`

## Frontend Setup

For frontend-only development:

```bash
cd frontend
npm install
npm run dev
```

For a production build served by FastAPI:

```bash
cd frontend
npm ci
npm run build
```

FastAPI serves the built SPA from `frontend/dist` for:

- `/login`
- `/admin`
- `/admin/students`
- `/admin/classes`
- `/admin/attendance`
- `/admin/fees`
- `/admin/reports`
- `/admin/settings`

API routes such as `/docs`, `/openapi.json`, and `/auth/*` remain backend routes.

## Database Migrations

Alembic is the only supported way to change the application schema.

```bash
alembic upgrade head
alembic current
alembic heads
```

Do not use `Base.metadata.create_all()` to repair or mutate existing application databases. It is only acceptable inside isolated test fixtures.

## Testing

Run the backend suite:

```bash
pytest -v
```

Run a production frontend build:

```bash
cd frontend
npm run build
```

Optional import and mapper check:

```bash
python -c "from app.main import app; from sqlalchemy.orm import configure_mappers; configure_mappers(); print(app.title); print('MAPPERS OK')"
```

## Docker

Build the production image:

```bash
docker build -t student-management-api .
```

Validate Compose configuration:

```bash
docker compose config
```

Run locally with PostgreSQL:

```bash
docker compose up --build
```

The Dockerfile builds the React frontend in a Node stage, then copies `frontend/dist` into the Python runtime image.

## Production Notes

- Use PostgreSQL for production.
- Set a strong `SECRET_KEY`.
- Run `alembic upgrade head` before starting the application.
- Create the first admin user with `scripts/create_admin.py`.
- Keep `.env`, local databases, backup databases, `node_modules`, `frontend/dist`, and temporary output files out of Git.
- Financial records are protected by backend business rules; avoid hard deletion where payment history exists.

## Current Functional Areas

- Dashboard analytics from live backend aggregates
- Student CRUD with class, fee, attendance, and academic performance context
- Classes backed by course, academic year, semester, batch, and teacher data
- Attendance sessions with subject-wise attendance and bulk marking
- Fee structures, installments, payments, invoices, and receipts
- Reports with preview, CSV export, and PDF export
- Settings for system profile, academic years, fee structures, notifications, security, users, and audit/admin tools
- Global search and notification APIs connected to the React top bar
