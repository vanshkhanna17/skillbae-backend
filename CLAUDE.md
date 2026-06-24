# CLAUDE.md — SkillBae Backend

## Project Overview

SkillBae is a social platform backend built with FastAPI, async SQLAlchemy, PostgreSQL, and Redis. Features include authentication, user profiles, feed/posts, and real-time chat via WebSockets.

## Commands

```bash
# Run locally (Docker)
docker compose -f docker-compose.local.yml up --build

# Run tests (unit only, no external services)
.venv/bin/python -m pytest tests/ -x -q -m "not integration"

# Run all tests including integration
.venv/bin/python -m pytest tests/ -x -q

# Lint and format
ruff check --fix .
ruff format .

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Architecture

```
app/
├── api/v1/          # Route handlers (thin — validate, call service, return)
├── core/            # Config, deps, JWT, security, Redis, exceptions
├── db/              # Engine, session, base class
├── models/          # SQLAlchemy ORM models
├── repo/            # Data access layer (all DB queries live here)
├── schemas/         # Pydantic request/response models
├── services/        # Business logic (orchestrates repos)
└── structures/      # Typed dicts and data structures
tests/
├── conftest.py      # Fixtures: test DB, fake Redis, test client
└── test_*.py        # Test files
alembic/             # Database migrations
terraform/           # AWS infrastructure (EC2, ECR, CloudFront, SSM)
```

### Layering: API → Service → Repo

- **API layer** (`api/v1/`): Route definitions, input validation, auth checks (membership guards), dependency injection. Returns Pydantic response models.
- **Service layer** (`services/`): Business logic, orchestration across repos, Redis pub/sub for real-time events.
- **Repo layer** (`repo/`): Raw SQLAlchemy queries. Each repo takes an `AsyncSession` in its constructor. All database access goes through repos.

## Conventions

### Datetime handling
All datetimes are stored as **naive UTC** (`DateTime` without timezone). Use `utc_now()` from `app.models.user` which returns `datetime.now(timezone.utc).replace(tzinfo=None)`. Never use `datetime.utcnow()` (deprecated) or `datetime.now(UTC)` (produces timezone-aware, incompatible with the DB column types).

### Schema naming
Request schemas: `*Request` (e.g., `ConversationCreateRequest`, `MessageCreateRequest`, `MarkReadRequest`)
Response schemas: `*Response` (e.g., `ConversationCreateResponse`, `MarkReadResponse`)
All schemas inherit from `BaseSchema` which sets `from_attributes=True`.

### UUID primary keys
Models like `Messages`, `Conversations` use UUID primary keys (`uuid.uuid4`). UUIDs are not orderable — never compare them for chronological ordering. Use the `sequence` column (backed by a Postgres `Sequence`) on `Messages` for ordering and cursor-based pagination.

### Cursor-based pagination
Pagination uses base64-encoded JSON cursors. For messages, the cursor contains `{"sequence": N}` using the monotonic `sequence` column. For conversation lists, the cursor uses `{"last_message_at": ..., "conversation_id": ...}` with keyset pagination.

### Deleted message tombstoning
Never expose deleted message content to clients. When `is_deleted=True`, return `content="This message was deleted"` instead of the real content.

### Read cursor (mark-as-read)
- `last_read_message_id`: FK to `Messages` — used for unread count computation. The forward-only guard compares `sequence` values via a correlated subquery to prevent regression.
- `last_read_at`: Wall-clock time of the read action (for UI display like "last seen"). Not used for unread counting.

### Alembic migrations
- Alembic autogenerate does NOT detect standalone `Sequence` objects. When adding a column backed by a `Sequence`, manually add `op.execute("CREATE SEQUENCE ...")` before the `add_column` in the migration, and `op.execute("DROP SEQUENCE ...")` in the downgrade.
- Always give explicit names to unique constraints (e.g., `uq_messages_sequence`) so downgrades work.

### Error handling
Use `AppException` (from `app.core.exceptions`) with `status_code`, `error`, and `message` fields. Common patterns:
- 403 for membership violations
- 404 for missing resources
- 500 with rollback for DB errors

## Formatting and Linting

- Formatter: **ruff-format** (not Black). Configured in `ruff.toml` with `preview = true` and `line-length = 88`.
- Linter: **ruff** with rules `E`, `F`, `ASYNC`, `I`.
- Pre-commit runs both `ruff --fix` and `ruff-format` plus unit tests.
- IDE formatter should be set to **ruff** (not Black) to avoid formatting conflicts with pre-commit.

## Testing

- Tests use a separate `skillbae_test` database with tables created/dropped per session.
- `get_session` and `get_current_user` are overridden via FastAPI dependency injection.
- Redis is mocked with `AsyncMock` + a fake in-memory store (see `conftest.py:fake_redis`).
- Mark integration tests with `@pytest.mark.integration`.
- Pre-commit hook runs unit tests only (`-m "not integration"`).

## Database

- PostgreSQL with async driver (`asyncpg` via SQLAlchemy async).
- Session config: `autoflush=False`, `expire_on_commit=False`.
- Connection pool: `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`.
