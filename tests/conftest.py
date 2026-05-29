from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.base_class import Base
from app.db.session import get_session
from app.main import app
from app.models import *  # noqa: F403
from app.schemas.user import UserDetails

TEST_DB_URL: str = (
    "postgresql+asyncpg://skillbae_admin:SkillBaeAdmin@localhost:5432/skillbae_test"
)


@pytest.fixture(scope="session")
def test_db_engine():
    import asyncio

    engine: AsyncEngine = create_async_engine(TEST_DB_URL, poolclass=NullPool)

    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def teardown():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    asyncio.new_event_loop().run_until_complete(setup())
    yield engine
    asyncio.new_event_loop().run_until_complete(teardown())


def make_override_db_session(engine: AsyncEngine):
    TestSession = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_db_session():
        async with TestSession() as session:
            yield session

    return override_db_session


async def override_current_user():
    return UserDetails(
        id=1,
        email="test@skillbae.com",
        username="test_user",
        first_name="PyTest",
        last_name="User",
        created_at=datetime.now(),
    )


@pytest.fixture
def override_settings():
    original_secure = settings.cookie_secure
    original_domain = settings.cookie_domain

    settings.cookie_secure = False
    settings.cookie_domain = ""
    yield
    settings.cookie_secure = original_secure
    settings.cookie_domain = original_domain


@pytest.fixture(scope="module")
def test_client(test_db_engine: AsyncEngine):
    app.dependency_overrides[get_session] = make_override_db_session(test_db_engine)
    app.dependency_overrides[get_current_user] = override_current_user

    with TestClient(app) as client:
        yield client
    app.dependency_overrides = {}
