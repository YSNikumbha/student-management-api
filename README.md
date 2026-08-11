# Student Management System

A full-stack educational administration system built with FastAPI for managing students, courses, attendance, fees, authentication, and analytics.

## Problem Statement

Small educational institutions often manage students, courses, attendance, and fees through spreadsheets, registers, and disconnected tools. This project centralizes these workflows into a single, maintainable web application with role-based access control, reducing administrative overhead and improving data consistency.

## Features

- Student CRUD operations
- Course management
- Student-Course relationship
- JWT authentication
- Admin/Staff role-based access control
- Attendance management
- Bulk attendance marking
- Attendance summaries and analytics
- Fee management
- Partial payment tracking
- Payment history
- Search, filter, sort, and pagination
- Dashboard analytics
- Reports with CSV and PDF export
- Admin UI
- Swagger API documentation
- Automated test suite

## Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- Alembic

### Database
- SQLite (development)
- PostgreSQL (production)

### Frontend
- HTML
- CSS
- Bootstrap
- Vanilla JavaScript

### Testing
- pytest
- httpx/TestClient

### Deployment
- Docker
- Compatible with Render, Railway, Fly.io, or any Python/Docker platform

## Architecture

```
Frontend (HTML/CSS/JS)
    ↓
FastAPI Routers
    ↓
Service Layer
    ↓
SQLAlchemy ORM
    ↓
PostgreSQL / SQLite
```

Additional components:
- Pydantic validation
- JWT authentication
- Alembic migrations

## Project Structure

```
student-management-api/
├── alembic/                  # Database migrations
├── app/
│   ├── core/                 # Configuration and security
│   ├── database/             # Database connection and session
│   ├── dependencies/         # FastAPI dependencies
│   ├── models/               # SQLAlchemy models
│   ├── routers/              # API route handlers
│   ├── schemas/              # Pydantic schemas
│   └── services/             # Business logic
├── frontend/                 # Admin UI static files
├── scripts/                  # Utility scripts
├── tests/                    # Automated tests
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Installation

```bash
git clone <repository-url>
cd student-management-api
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection URL | `sqlite:///./student_management.db` |
| `SECRET_KEY` | JWT signing secret | Must be set in production |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `60` |
| `ENVIRONMENT` | Runtime environment | `development` |
| `APP_NAME` | Application name | `Student Management API` |

### Database URLs

**SQLite (local development):**
```
DATABASE_URL=sqlite:///./student_management.db
```

**PostgreSQL (production):**
```
DATABASE_URL=postgresql+psycopg://user:password@host:5432/database
```

## Database Migrations

This project uses Alembic for schema management.

```bash
# Run pending migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# View current migration state
alembic current
```

## Running Locally

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Create initial admin user
python scripts/create_admin.py

# Start development server
python -m uvicorn app.main:app --reload
```

Then open:
- Admin dashboard: http://localhost:8000/admin
- Login page: http://localhost:8000/login
- API docs: http://localhost:8000/docs

## Running Tests

```bash
pytest -v
```

The test suite uses an isolated SQLite database and does not require PostgreSQL.

## Docker

### Using Docker Compose (recommended for local development with PostgreSQL)

```bash
docker compose up --build
```

This starts:
- PostgreSQL on port 5432
- FastAPI app on port 8000

After the app starts, create an admin user:

```bash
docker compose exec app python scripts/create_admin.py
```

### Building Docker Image

```bash
docker build -t student-management-api .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg://user:password@host:5432/database \
  -e SECRET_KEY=your-secret-key \
  student-management-api
```

## API Documentation

FastAPI provides interactive API documentation:

- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Admin Dashboard

The admin UI is served by FastAPI and provides interfaces for:
- Dashboard analytics
- Student management
- Course management
- Attendance tracking
- Fee management
- Reports with CSV/PDF export

Access requires authentication with admin or staff role.

## Authentication and Roles

- JWT-based authentication
- Two roles: `admin` and `staff`
- Protected endpoints require valid JWT token
- Admin users have full access
- Staff users have limited access based on permissions

## Deployment

### Generic Docker Deployment

1. Build the Docker image
2. Set environment variables (especially `DATABASE_URL` and `SECRET_KEY`)
3. Run database migrations: `alembic upgrade head`
4. Start the application

### Platform-Specific Notes

**Render:**
- Use Docker runtime
- Set `DATABASE_URL` to provided PostgreSQL connection
- Run migrations as a separate job or in startup script
- Health check endpoint: `/health`

**Railway:**
- Connect PostgreSQL service
- Set environment variables
- Deploy with Dockerfile

**Fly.io:**
- Deploy with Dockerfile
- Set secrets via `fly secrets`
- Ensure PostgreSQL volume is provisioned

### Production Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Set a strong, unique `SECRET_KEY`
- [ ] Configure PostgreSQL `DATABASE_URL`
- [ ] Run `alembic upgrade head`
- [ ] Create admin user via `scripts/create_admin.py`
- [ ] Verify `/health` endpoint returns healthy status
- [ ] Configure CORS if serving frontend from different origin
- [ ] Enable HTTPS
- [ ] Set appropriate `ACCESS_TOKEN_EXPIRE_MINUTES`

## Screenshots

*Screenshots of the admin dashboard and UI will be added here.*

## Future Improvements

- Email notifications
- Multi-language support
- REST API versioning
- Enhanced audit logging
- File upload for student photos
- SMS notifications
- Calendar integration

## License

This project is provided as-is for educational and administrative purposes.