# SkillBae Backend API

Backend API for SkillBae — built with FastAPI, PostgreSQL, and deployed on AWS.

---

## Tech Stack

| Layer            | Technology                                          |
| ---------------- | --------------------------------------------------- |
| Framework        | FastAPI (Python 3.12)                               |
| Database         | PostgreSQL 18 (async via asyncpg, sync via psycopg) |
| ORM / Migrations | SQLAlchemy + Alembic                                |
| Auth             | JWT (access + refresh tokens), HttpOnly cookies     |
| Rate Limiting    | SlowAPI                                             |
| Reverse Proxy    | Nginx                                               |
| Containerization | Docker + Docker Compose                             |
| Registry         | AWS ECR                                             |
| Compute          | AWS EC2 (Amazon Linux 2023, ARM64)                  |
| Secrets          | AWS SSM Parameter Store                             |
| IaC              | Terraform                                           |
| CI/CD            | GitHub Actions (OIDC → AWS)                         |

---

## Project Structure

```
app/
├── api/
│   ├── deps.py           # Dependency injection (DB session, services)
│   └── v1/
│       ├── auth.py       # Auth routes (register, login, refresh, logout)
│       ├── users.py      # User profile routes
│       └── feed.py       # Feed routes
├── core/
│   ├── config.py         # Pydantic settings (loaded from env / SSM)
│   ├── jwt.py            # JWT encode/decode helpers
│   ├── security.py       # Password hashing
│   ├── limiter.py        # SlowAPI rate limiter setup
│   └── exceptions.py     # Custom exception handlers
├── db/
│   ├── session.py        # Async SQLAlchemy engine + session factory
│   ├── base.py           # Import all models for Alembic discovery
│   └── base_class.py     # Declarative base
├── models/               # SQLAlchemy ORM models
├── schemas/              # Pydantic request/response schemas
├── services/             # Business logic layer
└── main.py               # FastAPI app factory, middleware, routers
alembic/                  # Database migrations
terraform/                # AWS infrastructure (EC2, ECR, VPC, SSM, IAM)
nginx.conf                # Nginx reverse proxy config
docker-compose.yml        # Multi-container setup (nginx + api + postgres)
Dockerfile                # API container image
```

---

## Local Development

### Prerequisites

- Python 3.12
- PostgreSQL running locally (or via Docker)

### Setup

````bash
# Clone the repo
git clone https://github.com/vanshkhanna/skillbae-backend.git
cd skillbae-backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

### Run Locally

```bash
# Apply database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --host localhost --port 8000 --reload
````

| URL                           | Description |
| ----------------------------- | ----------- |
| `http://127.0.0.1:8000`       | API root    |
| `http://127.0.0.1:8000/docs`  | Swagger UI  |
| `http://127.0.0.1:8000/redoc` | ReDoc       |

### Database Migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## Running with Docker Compose

For local testing with the full stack (nginx + api + postgres):

```bash
# Build and start all services
docker compose up --build

# Stop all services
docker compose down
```

> The `api` service expects an `ECR_IMAGE` env var pointing to a pre-built image.
> For local dev, build the image first: `docker build -t skillbae-api:local .`
> then set `ECR_IMAGE=skillbae-api:local` in your `.env`.

---

## Infrastructure (Terraform)

All AWS infrastructure is managed via Terraform in `terraform/main/`.

| Resource            | Description                                  |
| ------------------- | -------------------------------------------- |
| VPC + Subnets       | Isolated network with public subnet          |
| EC2 (ARM64)         | App server running Amazon Linux 2023         |
| ECR                 | Private container registry                   |
| SSM Parameter Store | Encrypted environment variables              |
| IAM Roles           | EC2 instance profile with ECR + SSM access   |
| Security Group      | Port 80 open, port 22 restricted to admin IP |

### Deploy Infrastructure

```bash
# Plan
terraform -chdir=terraform/main plan -var-file=staging.tfvars

# Apply
terraform -chdir=terraform/main apply -var-file=staging.tfvars
```

Or trigger the **Terraform Infra deployment** GitHub Actions workflow manually.

---

## CI/CD Pipeline

The pipeline runs via GitHub Actions (`.github/workflows/ci-cd.yml`).

### Triggers

| Event                               | Jobs                                  |
| ----------------------------------- | ------------------------------------- |
| Pull request to `main` or `staging` | Lint & Test only                      |
| Manual `workflow_dispatch`          | Full pipeline (lint → build → deploy) |

### Pipeline Jobs

```
validate-inputs → lint-and-test → build-and-push → deploy
```

| Job               | Description                                                                        |
| ----------------- | ---------------------------------------------------------------------------------- |
| `validate-inputs` | Enforces branch/env pairing (`staging` → `staging`, `main` → `prod`)               |
| `lint-and-test`   | Runs ruff linter and pytest against a live Postgres service container              |
| `build-and-push`  | Builds ARM64 image via Docker Buildx (with GHA layer cache), pushes to ECR         |
| `deploy`          | Pushes `docker-compose.yml` + `nginx.conf` to EC2 via SSM, then runs deploy script |

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## License

Private — all rights reserved.
