"""
Smoke tests for cookie-based authentication.
These tests verify the complete cookie auth flow works correctly.
"""
import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_cookie_auth_full_flow(client: AsyncClient):
    """
    Test complete cookie auth flow:
    1. Register → cookies set
    2. /me with cookies → 200
    3. Logout → cookies cleared
    4. /me without cookies → 401
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    email = f"smoke-{unique_id}@jobpilot.ai"
    password = "Str0ng!Passw0rd_123"
    
    # 1. Register
    register_response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Smoke Test User"
        }
    )
    assert register_response.status_code == 201, f"Register failed: {register_response.text}"
    
    # Verify cookies are set
    cookies = register_response.cookies
    assert "access_token" in cookies, "No access_token cookie after register"
    assert "refresh_token" in cookies, "No refresh_token cookie after register"
    
    # 2. /me with cookies should work
    me_response = await client.get(
        f"{settings.API_V1_STR}/auth/me",
        cookies=cookies
    )
    assert me_response.status_code == 200, f"/me failed: {me_response.text}"
    me_data = me_response.json()
    assert me_data["email"] == email
    
    # 3. Logout
    logout_response = await client.post(
        f"{settings.API_V1_STR}/auth/logout",
        cookies=cookies
    )
    assert logout_response.status_code == 200, f"Logout failed: {logout_response.text}"
    
    # 4. /me without cookies should fail
    me_after_logout = await client.get(f"{settings.API_V1_STR}/auth/me")
    assert me_after_logout.status_code == 401, f"/me should fail after logout: {me_after_logout.status_code}"


@pytest.mark.asyncio
async def test_login_sets_cookies(client: AsyncClient):
    """Test that login endpoint sets httpOnly cookies."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    email = f"login-cookie-{unique_id}@jobpilot.ai"
    password = "Str0ng!Passw0rd_123"
    
    # Register first
    await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Login Cookie Test"
        }
    )
    
    # Login
    login_response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email, "password": password}
    )
    
    assert login_response.status_code == 200
    
    # Verify cookies
    cookies = login_response.cookies
    assert "access_token" in cookies, "No access_token cookie on login"
    assert "refresh_token" in cookies, "No refresh_token cookie on login"


@pytest.mark.asyncio
async def test_refresh_endpoint_with_cookies(client: AsyncClient):
    """Test that refresh endpoint works with cookies."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    email = f"refresh-{unique_id}@jobpilot.ai"
    password = "Str0ng!Passw0rd_123"
    
    # Register and get cookies
    register_response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Refresh Test User"
        }
    )
    cookies = register_response.cookies
    
    # Call refresh endpoint
    refresh_response = await client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        cookies=cookies
    )
    
    assert refresh_response.status_code == 200, f"Refresh failed: {refresh_response.text}"
    
    # Should get new access token cookie
    new_cookies = refresh_response.cookies
    assert "access_token" in new_cookies, "No new access_token after refresh"


@pytest.mark.asyncio
async def test_me_without_cookies_returns_401(client: AsyncClient):
    """Test that /me returns 401 without cookies."""
    response = await client.get(f"{settings.API_V1_STR}/auth/me")
    assert response.status_code == 401
