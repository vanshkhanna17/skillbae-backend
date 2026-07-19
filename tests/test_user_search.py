import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.schemas.user import UserDetails

PASSWORD = "StrongPassword@1"

SEED_USERS = [
    {
        "email": "ali.owner@skillbae.com",
        "username": "ali_owner",
        "first_name": "Ali",
        "last_name": "Owner",
    },
    {
        "email": "alice@skillbae.com",
        "username": "alicewonder",
        "first_name": "Wendy",
        "last_name": "Wonder",
    },
    {
        "email": "zebra@skillbae.com",
        "username": "zebra_dev",
        "first_name": "Alice",
        "last_name": "Stripe",
    },
    {
        "email": "bob@skillbae.com",
        "username": "bobbytables",
        "first_name": "Bob",
        "last_name": "Tables",
    },
]


@pytest.fixture(scope="module")
def search_client(test_client: TestClient):
    # /auth/register is rate-limited to 3/minute; lift it while seeding
    app.state.limiter.enabled = False
    try:
        for user in SEED_USERS:
            resp = test_client.post(
                "/auth/register", json={**user, "password": PASSWORD}
            )
            assert resp.status_code == 201, resp.text
            if user["username"] == "ali_owner":
                owner = UserDetails.model_validate(resp.json())
    finally:
        app.state.limiter.enabled = True

    # search as ali_owner so exclusion is observable
    app.dependency_overrides[get_current_user] = lambda: owner
    yield test_client


@pytest.mark.integration
def test_search_matches_username_prefix(search_client: TestClient):
    resp = search_client.get("/users/search?q=bobby")
    assert resp.status_code == 200
    usernames = {u["username"] for u in resp.json()["items"]}
    assert usernames == {"bobbytables"}


@pytest.mark.integration
def test_search_matches_first_name_prefix(search_client: TestClient):
    resp = search_client.get("/users/search?q=wend")
    assert resp.status_code == 200
    usernames = {u["username"] for u in resp.json()["items"]}
    assert usernames == {"alicewonder"}


@pytest.mark.integration
def test_search_excludes_current_user(search_client: TestClient):
    resp = search_client.get("/users/search?q=ali")
    assert resp.status_code == 200
    usernames = {u["username"] for u in resp.json()["items"]}
    assert "ali_owner" not in usernames
    assert {"alicewonder", "zebra_dev"} <= usernames


@pytest.mark.integration
def test_search_respects_limit(search_client: TestClient):
    resp = search_client.get("/users/search?q=ali&limit=1")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1


@pytest.mark.integration
def test_search_does_not_leak_email(search_client: TestClient):
    resp = search_client.get("/users/search?q=ali")
    assert resp.status_code == 200
    assert all("email" not in item for item in resp.json()["items"])


def test_search_requires_auth():
    saved = dict(app.dependency_overrides)
    app.dependency_overrides.pop(get_current_user, None)
    try:
        # no context manager: lifespan (redis) is skipped, 401 happens before DB
        resp = TestClient(app).get("/users/search?q=abc")
        assert resp.status_code == 401
    finally:
        app.dependency_overrides = saved
