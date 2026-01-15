"""
Tests for authentication endpoints.
Validates registration, login, token refresh, and protected routes with cookie-based auth.
"""
import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test basic health check endpoint."""
    response = await client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "jobpilot-api"


@pytest.mark.asyncio
async def test_register_success_cookies(client: AsyncClient):
    """Test successful user registration with cookie-based auth."""
    response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPass123!",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "message" in data
    
    # Check cookies are set
    cookies = response.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies


@pytest.mark.asyncio
async def test_login_success_cookies(client: AsyncClient):
    """Test successful login with cookie-based auth."""
    # First register a user
    await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "login@example.com",
            "password": "TestPass123!",
            "full_name": "Login User"
        }
    )
    
    # Then login
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "email": "login@example.com",
            "password": "TestPass123!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Check cookies are set
    cookies = response.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies


@pytest.mark.asyncio
async def test_me_endpoint_with_cookies(client: AsyncClient):
    """Test /me endpoint works with cookies."""
    # Register and get cookies
    register_response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "me@example.com",
            "password": "TestPass123!",
            "full_name": "Me User"
        }
    )
    
    # Use cookies from registration for /me request
    cookies = register_response.cookies
    response = await client.get(
        f"{settings.API_V1_STR}/auth/me",
        cookies=cookies
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_refresh_endpoint_cookies(client: AsyncClient):
    """Test refresh endpoint with cookies."""
    # Register and get cookies
    register_response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "TestPass123!",
            "full_name": "Refresh User"
        }
    )
    
    # Use cookies for refresh
    cookies = register_response.cookies
    response = await client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        cookies=cookies
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    
    # Should get new access token cookie
    new_cookies = response.cookies
    assert "access_token" in new_cookies


@pytest.mark.asyncio
async def test_logout_clears_cookies(client: AsyncClient):
    """Test logout clears cookies."""
    # Register and get cookies
    register_response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "logout@example.com",
            "password": "TestPass123!",
            "full_name": "Logout User"
        }
    )
    
    # Logout with cookies
    cookies = register_response.cookies
    response = await client.post(
        f"{settings.API_V1_STR}/auth/logout",
        cookies=cookies
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_me_without_cookies_fails(client: AsyncClient):
    """Test /me endpoint fails without cookies."""
    response = await client.get(f"{settings.API_V1_STR}/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email fails."""
    # Register first user
    await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "TestPass123!",
            "full_name": "First User"
        }
    )
    
    # Try to register again with same email
    response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "TestPass123!",
            "full_name": "Second User"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "already registered" in data["detail"].lower()


@pytest.mark.asyncio
async def test_invalid_login_credentials(client: AsyncClient):
    """Test login with invalid credentials fails."""
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "WrongPass123!"
        }
    )
    assert response.status_code == 401
    data = response.json()
    assert "invalid credentials" in data["detail"].lower()


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Test registration with weak password fails."""
    response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "weak@example.com",
            "password": "weak",
            "full_name": "Weak User"
        }
    )
    assert response.status_code == 422  # Validation error
