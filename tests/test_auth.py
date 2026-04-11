from fastapi.testclient import TestClient


def test_register(test_client: TestClient):
    response = test_client.post(
        "/auth/register",
        json={
            "email": "pytest@skillbae.com",
            "first_name": "PyTest",
            "last_name": "User",
            "password": "StrongPassword@1",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "pytest@skillbae.com"
    assert data["full_name"] == "PyTest User"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email(test_client: TestClient):
    test_client.post(
        "/auth/register",
        json={"email": "duplicate@skillbae.com", "password": "Strong@pass1"},
    )
    response = test_client.post(
        "/auth/register",
        json={"email": "duplicate@skillbae.com", "password": "Strong@pass1"},
    )
    assert response.status_code == 409


def test_register_weak_password(test_client: TestClient):
    response = test_client.post(
        "/auth/register",
        json={"email": "weakpass@skillbae.com", "password": "password"},
    )
    assert response.status_code == 422


def test_register_password_no_special_char(test_client: TestClient):
    response = test_client.post(
        "/auth/register",
        json={
            "email": "weak@skillbae.com",
            "password": "NoSpecial123",
        },
    )
    assert response.status_code == 422


def test_register_invalid_email(test_client: TestClient):
    response = test_client.post(
        "/auth/register",
        json={
            "email": "notanemail",
            "password": "StrongPass1!",
        },
    )
    assert response.status_code == 422


def test_login_success(test_client: TestClient, override_settings: None):
    response = test_client.post(
        "/auth/login",
        json={"email": "pytest@skillbae.com", "password": "StrongPassword@1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "auth_refresh_token" in response.cookies


def test_login_wrong_password(test_client: TestClient):
    response = test_client.post(
        "/auth/login",
        json={
            "email": "login@skillbae.com",
            "password": "WrongPass1!",
        },
    )
    assert response.status_code == 401


def test_login_nonexistent_user(test_client: TestClient):
    response = test_client.post(
        "/auth/login",
        json={
            "email": "ghost@skillbae.com",
            "password": "StrongPass1!",
        },
    )
    assert response.status_code == 401
