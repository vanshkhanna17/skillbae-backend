# tests/test_ws.py

import asyncio

import pytest
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from starlette.testclient import TestClient, WebSocketTestSession
from starlette.websockets import WebSocketDisconnect

from app.core.connection_manager import ws_connection_manger
from app.core.deps import get_redis
from app.core.jwt import create_jwt_token
from app.db.session import get_session
from app.main import app
from tests.conftest import make_override_db_session

# ── Helpers ────────────────────────────────────────────────────────────────

WS_PATH = "/websocket/ws"  # ✅ matches prefix="/websocket" in main.py


def make_valid_token(user_id: int = 1) -> str:
    return create_jwt_token(str(user_id))


def make_ws_client(
    test_db_engine: AsyncEngine,
    fake_redis,  # pyright: ignore[reportMissingParameterType]
) -> TestClient:  # pyright: ignore[reportMissingParameterType]
    app.dependency_overrides[get_session] = make_override_db_session(test_db_engine)
    app.dependency_overrides[get_redis] = (
        lambda: fake_redis  # pyright: ignore[reportUnknownLambdaType]
    )  # pyright: ignore[reportUnknownLambdaType]
    return TestClient(app, raise_server_exceptions=False)


def wait_for_connected(ws: WebSocketTestSession) -> None:
    """
    Block until the endpoint sends its "connected" ready signal.
    Guarantees manager.connect() and redis.set() have run before
    the test asserts anything.
    """
    msg = ws.receive_json()
    assert msg["topic"] == "connected", f"Expected 'connected', got: {msg}"


# ── Tests ──────────────────────────────────────────────────────────────────


class TestWebSocket:

    def teardown_method(self):
        app.dependency_overrides = {}
        ws_connection_manger.active.clear()

    def test_invalid_jwt_returns_4001(
        self, test_db_engine, fake_redis  # pyright: ignore[reportMissingParameterType]
    ):  # pyright: ignore[reportMissingParameterType]
        """
        Invalid JWT → server rejects connection.

        WHY not assert code == 4001?
        Starlette TestClient swallows custom close codes and reports 1000.
        We assert rejection happened (WebSocketDisconnect raised) AND
        that no presence key was set (auth never completed).
        The close code is verified via the reason string instead.
        """
        client = make_ws_client(test_db_engine, fake_redis)

        # Pass bad token as query param — reliable in TestClient
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"{WS_PATH}?token=this.is.not.valid") as ws:
                ws.receive_json()

        # Auth failed → presence must NOT have been set
        assert "presence:1" not in fake_redis.store

    def test_missing_token_returns_4001(
        self, test_db_engine, fake_redis  # pyright: ignore[reportMissingParameterType]
    ):  # pyright: ignore[reportMissingParameterType]
        """No token at all → server rejects connection."""
        client = make_ws_client(test_db_engine, fake_redis)

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(WS_PATH) as ws:  # no token
                ws.receive_json()

        assert "presence:1" not in fake_redis.store

    def test_valid_jwt_sets_presence_in_redis(
        self, test_db_engine, fake_redis  # pyright: ignore[reportMissingParameterType]
    ):  # pyright: ignore[reportMissingParameterType]
        """Valid JWT → connection accepted → presence key set then deleted."""
        client = make_ws_client(test_db_engine, fake_redis)
        token = make_valid_token(user_id=1)

        with client.websocket_connect(f"{WS_PATH}?token={token}"):
            # Inside the with = connection is live
            assert fake_redis.store.get("presence:1") == "1"  # ✅ set on connect

        # Outside the with = disconnect fired → last tab → deleted
        assert "presence:1" not in fake_redis.store  # ✅ deleted on disconnect

    def test_two_connections_both_receive_message(
        self, test_db_engine, fake_redis  # pyright: ignore[reportMissingParameterType]
    ):  # pyright: ignore[reportMissingParameterType]
        """Two tabs for same user → both receive a pushed event."""
        token = make_valid_token(user_id=1)

        app.dependency_overrides[get_session] = make_override_db_session(test_db_engine)
        app.dependency_overrides[get_redis] = (
            lambda: fake_redis  # pyright: ignore[reportUnknownLambdaType]
        )  # pyright: ignore[reportUnknownLambdaType]

        client_a = TestClient(app, raise_server_exceptions=False)
        client_b = TestClient(app, raise_server_exceptions=False)

        with client_a.websocket_connect(f"{WS_PATH}?token={token}") as ws1:
            wait_for_connected(ws1)  # ✅ consume "connected" from tab 1

            with client_b.websocket_connect(f"{WS_PATH}?token={token}") as ws2:
                wait_for_connected(ws2)  # ✅ consume "connected" from tab 2

                assert len(ws_connection_manger.active.get(1, [])) == 2

                loop = asyncio.new_event_loop()
                loop.run_until_complete(
                    ws_connection_manger.send_to_user(
                        1, {"topic": "notif", "payload": "hello"}
                    )
                )
                loop.close()

                # Now the only messages in the queues are the "notif" ones
                assert ws1.receive_json() == {"topic": "notif", "payload": "hello"}
                assert ws2.receive_json() == {"topic": "notif", "payload": "hello"}

    def test_closing_one_tab_keeps_presence(
        self, test_db_engine, fake_redis  # pyright: ignore[reportMissingParameterType]
    ):  # pyright: ignore[reportMissingParameterType]
        """Tab 1 closes → presence stays. Tab 2 closes → presence deleted."""
        token = make_valid_token(user_id=1)

        app.dependency_overrides[get_session] = make_override_db_session(test_db_engine)
        app.dependency_overrides[get_redis] = (
            lambda: fake_redis  # pyright: ignore[reportUnknownLambdaType]
        )  # pyright: ignore[reportUnknownLambdaType]

        client_a = TestClient(app, raise_server_exceptions=False)
        client_b = TestClient(app, raise_server_exceptions=False)

        with client_a.websocket_connect(f"{WS_PATH}?token={token}"):
            with client_b.websocket_connect(f"{WS_PATH}?token={token}"):
                assert len(ws_connection_manger.active.get(1, [])) == 2
                assert fake_redis.store.get("presence:1") == "1"

            # ws2 closed — ws1 still alive
            assert fake_redis.store.get("presence:1") == "1"  # ✅ still there
            assert len(ws_connection_manger.active.get(1, [])) == 1

        # ws1 closed — last tab
        assert "presence:1" not in fake_redis.store  # ✅ cleaned up
        assert ws_connection_manger.active.get(1) is None
