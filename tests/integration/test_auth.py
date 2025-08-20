import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import jwt
from datetime import datetime, timedelta, timezone
import json

from app.routers.auth import router, TOKEN_KEY, ALGORITHM
from app.models.auth import UserInDB
from app.service.user_db import UserDB


@pytest.fixture
def app():
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app, mock_user_db):
    from app.api.dependencies import get_user_db
    app.dependency_overrides[get_user_db] = lambda: mock_user_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_db():
    return AsyncMock(spec=UserDB)


@pytest.fixture
def sample_user():
    return UserInDB(
        user_id="testuser",
        hashed_password="$2b$12$DnpgpyAPldIBcNRnaYZNS.Bqo8yjaTni6xoiWXhWYNenNimaU2TOm"
    )


@pytest.fixture
def valid_token():
    payload = {
        "sub": "testuser",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    return jwt.encode(payload, TOKEN_KEY, algorithm=ALGORITHM)


@pytest.fixture
def expired_token():
    payload = {
        "sub": "testuser",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=30)
    }
    return jwt.encode(payload, TOKEN_KEY, algorithm=ALGORITHM)


@pytest.mark.asyncio
async def test_signup_success(client, mock_user_db):
    mock_user_db.get_user_by_userid.return_value = None
    mock_user_db.create_user.return_value = None

    response = client.post(
        "/auth/signup",
        json={"user_id": "newuser", "password": "password123"}
    )

    assert response.status_code == 201
    assert response.json() == {"message": "User created successfully"}
    mock_user_db.get_user_by_userid.assert_called_once_with(user_id="newuser")
    mock_user_db.create_user.assert_called_once()


@pytest.mark.asyncio
async def test_signup_user_already_exists(client, mock_user_db, sample_user):
    mock_user_db.get_user_by_userid.return_value = sample_user

    response = client.post(
        "/auth/signup",
        json={"user_id": "testuser", "password": "password123"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"


@pytest.mark.asyncio
async def test_signup_invalid_data(client, mock_user_db):
    response = client.post(
        "/auth/signup",
        json={"user_id": "", "password": ""}
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client, mock_user_db, sample_user):
    mock_user_db.get_user_by_userid.return_value = sample_user

    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "password123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    token = data["access_token"]
    payload = jwt.decode(token, TOKEN_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "testuser"


@pytest.mark.asyncio
async def test_login_invalid_user(client, mock_user_db):
    mock_user_db.get_user_by_userid.return_value = None

    response = client.post(
        "/auth/login",
        data={"username": "nonexistent", "password": "password123"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_invalid_password(client, mock_user_db, sample_user):
    mock_user_db.get_user_by_userid.return_value = sample_user

    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrongpassword"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_get_current_user_success(client, mock_user_db, sample_user, valid_token):
    mock_user_db.get_user_by_userid.return_value = sample_user

    response = client.get(
        "/auth/users/me/",
        headers={"Authorization": f"Bearer {valid_token}"}
    )

    assert response.status_code == 200
    assert response.json() == "testuser"


@pytest.mark.asyncio
async def test_get_current_user_no_token(client, mock_user_db):
    response = client.get("/auth/users/me/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_expired_token(client, mock_user_db, expired_token):
    response = client.get(
        "/auth/users/me/",
        headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client, mock_user_db):
    response = client.get(
        "/auth/users/me/",
        headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


@pytest.mark.asyncio
async def test_get_current_user_user_not_found(client, mock_user_db, valid_token):
    mock_user_db.get_user_by_userid.return_value = None

    response = client.get(
        "/auth/users/me/",
        headers={"Authorization": f"Bearer {valid_token}"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_google_login_missing_token(client, mock_user_db):
    response = client.get("/auth/google-login")
    assert response.status_code == 400
    assert response.json()["detail"] == "Token missing"


@pytest.mark.asyncio
async def test_google_login_invalid_token(client, mock_user_db):
    mock_user_db.get_user_by_userid.return_value = None

    response = client.get("/auth/google-login?token=invalid_token")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_hash_and_verify_password():
    from app.routers.auth import hash_password, verify_password

    password = "test_password_123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_create_access_token():
    from app.routers.auth import create_access_token

    data = {"sub": "testuser"}
    token = create_access_token(data)

    payload = jwt.decode(token, TOKEN_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "testuser"
    assert "exp" in payload


def test_create_access_token_with_expiry():
    from app.routers.auth import create_access_token

    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=60)
    token = create_access_token(data, expires_delta)

    payload = jwt.decode(token, TOKEN_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "testuser"

    exp_time = datetime.fromtimestamp(payload["exp"], timezone.utc)
    expected_exp = datetime.now(timezone.utc) + expires_delta
    time_diff = abs((exp_time - expected_exp).total_seconds())
    assert time_diff < 5


@pytest.mark.asyncio
async def test_database_error_during_signup(client, mock_user_db):
    mock_user_db.get_user_by_userid.return_value = None
    mock_user_db.create_user.side_effect = Exception("Database error")

    with pytest.raises(Exception):
        client.post(
            "/auth/signup",
            json={"user_id": "testuser", "password": "password123"}
        )


@pytest.mark.asyncio
async def test_database_error_during_login(client, mock_user_db):
    mock_user_db.get_user_by_userid.side_effect = Exception("Database error")

    with pytest.raises(Exception):
        client.post(
            "/auth/login",
            data={"username": "testuser", "password": "password123"}
        )


@pytest.mark.asyncio
async def test_login_with_json_content_type(client, mock_user_db, sample_user):
    mock_user_db.get_user_by_userid.return_value = sample_user

    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "password123"}
    )

    assert response.status_code == 422
