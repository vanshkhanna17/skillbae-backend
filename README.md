start local server - "uvicorn app.main:app --reload"

http://127.0.0.1:8000 → local server

http://127.0.0.1:8000/docs → Swagger docs

http://127.0.0.1:8000/redoc → ReDoc docs

generate migration - alembic revision --autogenerate -m "comment"

apply migration - alembic upgrade head
