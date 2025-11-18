import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    user_data = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "password123",
        "full_name": "New User",
    }

    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "password" not in data


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    """Test user login."""
    # First register
    user_data = {
        "email": "logintest@example.com",
        "username": "loginuser",
        "password": "password123",
    }
    await client.post("/api/v1/auth/register", json=user_data)

    # Then login
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"],
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_user):
    """Test getting current user info."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["username"] == test_user["user_data"]["username"]
    assert data["email"] == test_user["user_data"]["email"]


@pytest.mark.asyncio
async def test_invalid_login(client: AsyncClient):
    """Test login with invalid credentials."""
    login_data = {
        "username": "nonexistent",
        "password": "wrongpass",
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
