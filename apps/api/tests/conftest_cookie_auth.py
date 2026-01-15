"""
Cookie authentication fixtures for pytest.
Use these fixtures for tests that need cookie-based auth.
"""
import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.fixture
def cookie_client(client: AsyncClient):
    """
    `client` should be your existing FastAPI TestClient fixture.
    This keeps cookies between requests.
    """
    return client


@pytest.fixture
def register_and_login(client: AsyncClient):
    """
    Fixture that registers and logs in a user, returning cookies.
    
    Usage:
        def test_something(register_and_login, client):
            cookies = register_and_login()
            response = client.get("/api/v1/auth/me", cookies=cookies)
    """
    async def _do(
        email="pytest1@jobpilot.ai", 
        password="Str0ng!Passw0rd_123", 
        full_name="Pytest User"
    ):
        # register (ignore if exists)
        r = await client.post(
            f"{settings.API_V1_STR}/auth/register", 
            json={"full_name": full_name, "email": email, "password": password}
        )
        if r.status_code not in (200, 201, 400):
            raise AssertionError(f"Register failed: {r.text}")

        # login must set cookie
        r2 = await client.post(
            f"{settings.API_V1_STR}/auth/login", 
            json={"email": email, "password": password}
        )
        assert r2.status_code == 200, f"Login failed: {r2.text}"

        # IMPORTANT: confirm Set-Cookie present (debug signal)
        cookies = r2.cookies
        assert "access_token" in cookies, "No access_token cookie on login (cookie auth broken)"
        assert "refresh_token" in cookies, "No refresh_token cookie on login"

        return cookies
    return _do


@pytest.fixture
async def authenticated_cookies(client: AsyncClient):
    """
    Fixture that provides authenticated cookies for a test user.
    Creates a unique user per test to avoid conflicts.
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    email = f"test-{unique_id}@jobpilot.ai"
    password = "TestPass123!"
    
    # Register
    await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": f"Test User {unique_id}"
        }
    )
    
    # Login
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email, "password": password}
    )
    
    return response.cookies
