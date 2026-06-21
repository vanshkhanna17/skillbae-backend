import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_chats_service, get_current_user, get_user_repo
from app.main import app
from app.schemas.chats import ConversationOut
from app.schemas.user import UserDetails

MOCK_USER = UserDetails(
    id=1,
    email="test@skillbae.com",
    username="test_user",
    first_name="Test",
    last_name="User",
    created_at=datetime.now(),
)


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_chat_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(mock_user_repo: AsyncMock, mock_chat_service: AsyncMock):
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True

    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    app.dependency_overrides[get_user_repo] = lambda: mock_user_repo
    app.dependency_overrides[get_chats_service] = lambda: mock_chat_service

    with patch("app.main.get_redis_client", return_value=mock_redis):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides = {}


def test_create_conversation_success(
    client: TestClient, mock_user_repo: AsyncMock, mock_chat_service: AsyncMock
):
    conv_id = str(uuid.uuid4())
    mock_user_repo.get_by_id.return_value = True
    mock_chat_service.create_conversation.return_value = ConversationOut(
        conversation_id=conv_id, created=True
    )

    response = client.post("/conversation/create", json={"target_user_id": 2})

    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == conv_id
    assert data["created"] is True
    mock_chat_service.create_conversation.assert_awaited_once_with(1, 2)


def test_create_conversation_returns_existing(
    client: TestClient, mock_user_repo: AsyncMock, mock_chat_service: AsyncMock
):
    conv_id = str(uuid.uuid4())
    mock_user_repo.get_by_id.return_value = True
    mock_chat_service.create_conversation.return_value = ConversationOut(
        conversation_id=conv_id, created=False
    )

    response = client.post("/conversation/create", json={"target_user_id": 2})

    assert response.status_code == 200
    assert response.json()["created"] is False


def test_cannot_create_conversation_with_self(client: TestClient):
    response = client.post("/conversation/create", json={"target_user_id": 1})

    assert response.status_code == 403


def test_target_user_not_found(client: TestClient, mock_user_repo: AsyncMock):
    mock_user_repo.get_by_id.return_value = None

    response = client.post("/conversation/create", json={"target_user_id": 999})

    assert response.status_code == 404


def test_missing_target_user_id(client: TestClient):
    response = client.post("/conversation/create", json={})

    assert response.status_code == 422
