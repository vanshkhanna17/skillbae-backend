import base64
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_chats_service, get_current_user, get_user_repo
from app.main import app
from app.schemas.chats import (
    ConversationCreateResponse,
    ConversationList,
    ConversationListItem,
    Message,
)
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
    mock_chat_service.create_conversation.return_value = ConversationCreateResponse(
        conversation_id=conv_id, created=True
    )

    response = client.post("/conversations/create", json={"target_user_id": 2})

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
    mock_chat_service.create_conversation.return_value = ConversationCreateResponse(
        conversation_id=conv_id, created=False
    )

    response = client.post("/conversations/create", json={"target_user_id": 2})

    assert response.status_code == 200
    assert response.json()["created"] is False


def test_cannot_create_conversation_with_self(client: TestClient):
    response = client.post("/conversations/create", json={"target_user_id": 1})

    assert response.status_code == 403


def test_target_user_not_found(client: TestClient, mock_user_repo: AsyncMock):
    mock_user_repo.get_by_id.return_value = None

    response = client.post("/conversations/create", json={"target_user_id": 999})

    assert response.status_code == 404


def test_missing_target_user_id(client: TestClient):
    response = client.post("/conversations/create", json={})

    assert response.status_code == 422


# ── Send Message ────────────────────────────────────────────────────


MOCK_MESSAGE_OUT = Message(
    id=str(uuid.uuid4()),
    conversation_id=str(uuid.uuid4()),
    sender_id=1,
    content="hello",
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
    is_deleted=False,
    message_type="text",
)


def test_send_message_success(client: TestClient, mock_chat_service: AsyncMock):
    mock_chat_service.is_conversation_member.return_value = True
    mock_chat_service.send_message.return_value = MOCK_MESSAGE_OUT
    conv_id = MOCK_MESSAGE_OUT.conversation_id

    response = client.post(
        f"/conversations/{conv_id}/message", json={"content": "hello"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "hello"
    assert data["sender_id"] == 1
    assert data["message_type"] == "text"
    mock_chat_service.is_conversation_member.assert_awaited_once_with(conv_id, 1)
    mock_chat_service.send_message.assert_awaited_once()


def test_send_message_not_a_member(client: TestClient, mock_chat_service: AsyncMock):
    mock_chat_service.is_conversation_member.return_value = False
    conv_id = str(uuid.uuid4())

    response = client.post(
        f"/conversations/{conv_id}/message", json={"content": "hello"}
    )

    assert response.status_code == 403
    mock_chat_service.send_message.assert_not_awaited()


def test_send_message_missing_content(client: TestClient, mock_chat_service: AsyncMock):
    mock_chat_service.is_conversation_member.return_value = True
    conv_id = str(uuid.uuid4())

    response = client.post(f"/conversations/{conv_id}/message", json={})

    assert response.status_code == 422


# ── List Conversations ─────────────────────────────────────────────


OTHER_USER = UserDetails(
    id=2,
    email="other@skillbae.com",
    username="other_user",
    first_name="Other",
    last_name="User",
    created_at=datetime.now(timezone.utc),
)


def _make_conversation_list(
    count: int = 1, next_cursor: str | None = None
) -> ConversationList:
    now = datetime.now(timezone.utc)
    items = [
        ConversationListItem(
            conversation_id=str(uuid.uuid4()),
            other_user=OTHER_USER,
            last_message=f"message {i}",
            last_message_at=now,
            unread_count=i,
        )
        for i in range(count)
    ]
    return ConversationList(conversations=items, next_cursor=next_cursor)


def test_list_conversations_success(client: TestClient, mock_chat_service: AsyncMock):
    conv_list = _make_conversation_list(count=2)
    mock_chat_service.get_conversations_list.return_value = conv_list

    response = client.get("/conversations/list")

    assert response.status_code == 200
    data = response.json()
    assert len(data["conversations"]) == 2
    assert data["next_cursor"] is None
    assert data["conversations"][0]["other_user"]["username"] == "other_user"
    assert data["conversations"][0]["unread_count"] == 0
    assert data["conversations"][1]["unread_count"] == 1
    mock_chat_service.get_conversations_list.assert_awaited_once_with(1, 20, None)


def test_list_conversations_empty(client: TestClient, mock_chat_service: AsyncMock):
    mock_chat_service.get_conversations_list.return_value = ConversationList(
        conversations=[], next_cursor=None
    )

    response = client.get("/conversations/list")

    assert response.status_code == 200
    data = response.json()
    assert data["conversations"] == []
    assert data["next_cursor"] is None


def test_list_conversations_with_cursor(
    client: TestClient, mock_chat_service: AsyncMock
):
    cursor = base64.b64encode(
        json.dumps({
            "last_message_at": "2026-01-01T00:00:00",
            "conversation_id": "abc",
        }).encode()
    ).decode()
    conv_list = _make_conversation_list(count=1, next_cursor=cursor)
    mock_chat_service.get_conversations_list.return_value = conv_list

    response = client.get(f"/conversations/list?cursor={cursor}")

    assert response.status_code == 200
    data = response.json()
    assert data["next_cursor"] == cursor
    mock_chat_service.get_conversations_list.assert_awaited_once_with(1, 20, cursor)


def test_list_conversations_with_pagination(
    client: TestClient, mock_chat_service: AsyncMock
):
    next_cursor = "some_encoded_cursor"
    conv_list = _make_conversation_list(count=3, next_cursor=next_cursor)
    mock_chat_service.get_conversations_list.return_value = conv_list

    response = client.get("/conversations/list?limit=3")

    assert response.status_code == 200
    data = response.json()
    assert len(data["conversations"]) == 3
    assert data["next_cursor"] == next_cursor
    mock_chat_service.get_conversations_list.assert_awaited_once_with(1, 3, None)


def test_list_conversations_custom_limit(
    client: TestClient, mock_chat_service: AsyncMock
):
    conv_list = _make_conversation_list(count=5)
    mock_chat_service.get_conversations_list.return_value = conv_list

    response = client.get("/conversations/list?limit=50")

    assert response.status_code == 200
    mock_chat_service.get_conversations_list.assert_awaited_once_with(1, 50, None)


def test_list_conversations_limit_too_high(client: TestClient):
    response = client.get("/conversations/list?limit=101")

    assert response.status_code == 422


def test_list_conversations_limit_too_low(client: TestClient):
    response = client.get("/conversations/list?limit=0")

    assert response.status_code == 422
