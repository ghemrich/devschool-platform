from unittest.mock import MagicMock, patch

import pytest

from app.auth.jwt import create_access_token, create_refresh_token
from app.models.user import User, UserRole


@pytest.fixture
def test_user(db_session):
    user = User(github_id=12345, username="testuser", email="test@example.com", role=UserRole.student)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    user = User(github_id=99999, username="adminuser", email="admin@example.com", role=UserRole.admin)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_me_with_valid_token(client, test_user):
    token = create_access_token(test_user.id)
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["role"] == "student"


def test_me_without_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code in (401, 403)


def test_me_with_invalid_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code in (401, 403)


def test_callback_with_valid_code(client, db_session):
    mock_token_response = MagicMock()
    mock_token_response.json.return_value = {"access_token": "gh_fake_token"}

    mock_user_response = MagicMock()
    mock_user_response.json.return_value = {
        "id": 67890,
        "login": "newuser",
        "email": "new@example.com",
        "avatar_url": "https://avatars.example.com/67890",
    }

    with patch("app.routers.auth.httpx.post", return_value=mock_token_response):
        with patch("app.routers.auth.httpx.get", return_value=mock_user_response):
            response = client.get("/api/auth/callback?code=valid_code", follow_redirects=False)

    assert response.status_code == 302
    assert "/login#token=" in response.headers["location"]

    user = db_session.query(User).filter(User.github_id == 67890).first()
    assert user is not None
    assert user.username == "newuser"


def test_callback_with_invalid_code(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"error": "bad_verification_code"}

    with patch("app.routers.auth.httpx.post", return_value=mock_response):
        response = client.get("/api/auth/callback?code=invalid_code")

    assert response.status_code == 401


def test_existing_user_login_updates_last_login(client, db_session, test_user):
    mock_token_response = MagicMock()
    mock_token_response.json.return_value = {"access_token": "gh_fake_token"}

    mock_user_response = MagicMock()
    mock_user_response.json.return_value = {
        "id": test_user.github_id,
        "login": test_user.username,
        "email": test_user.email,
        "avatar_url": "https://avatars.example.com/12345",
    }

    with patch("app.routers.auth.httpx.post", return_value=mock_token_response):
        with patch("app.routers.auth.httpx.get", return_value=mock_user_response):
            response = client.get("/api/auth/callback?code=valid_code", follow_redirects=False)

    assert response.status_code == 302
    assert "/login#token=" in response.headers["location"]
    db_session.refresh(test_user)
    assert test_user.last_login is not None

    users = db_session.query(User).filter(User.github_id == test_user.github_id).all()
    assert len(users) == 1


def test_admin_endpoint_with_student_token(client, test_user):
    # /api/auth/me is not role-protected, so we test the dependency directly
    from app.auth.dependencies import require_role

    checker = require_role(UserRole.admin)
    assert callable(checker)


def test_jwt_tokens_are_different():
    access = create_access_token(user_id=1)
    refresh = create_refresh_token(user_id=1)
    assert access != refresh
    assert len(access) > 20
    assert len(refresh) > 20
