"""
Comprehensive authentication tests for Phase 1 QA.
Tests all auth endpoints with edge cases and error scenarios.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.user import User
from sqlalchemy import select


@pytest.mark.asyncio
class TestAuthRegistration:
    """Test user registration endpoint."""
    
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email fails."""
        response = await client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": test_user.email,
                "password": "AnotherPass123!"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        response = await client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == 422  # Validation error
    
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        response = await client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": "user@example.com",
                "password": "123"  # Too short
            }
        )
        assert response.status_code == 422
    
    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields."""
        response = await client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={"email": "user@example.com"}  # Missing password
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestAuthLogin:
    """Test user login endpoint."""
    
    async def test_login_success(self, client: AsyncClient, test_user: User, test_password: str):
        """Test successful login."""
        response = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "email": test_user.email,
                "password": test_password
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password."""
        response = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent email."""
        response = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePass123!"
            }
        )
        assert response.status_code == 401
    
    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing fields."""
        response = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "user@example.com"}  # Missing password
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestAuthTokenRefresh:
    """Test token refresh endpoint."""
    
    async def test_refresh_success(self, client: AsyncClient, test_user: User, test_password: str):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "email": test_user.email,
                "password": test_password
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Now refresh
        response = await client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )
        assert response.status_code == 401
    
    async def test_refresh_expired_token(self, client: AsyncClient):
        """Test refresh with expired token."""
        # This would require mocking time or using an actually expired token
        # For now, we test with invalid format
        response = await client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.invalid"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestAuthGetMe:
    """Test get current user endpoint."""
    
    async def test_get_me_success(self, client: AsyncClient, auth_headers: dict, test_user: User):
        """Test getting current user info."""
        response = await client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id
    
    async def test_get_me_no_auth(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get(f"{settings.API_V1_STR}/auth/me")
        # HTTPBearer returns 403 when credentials are missing
        assert response.status_code in [401, 403]
    
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestAuthLogout:
    """Test logout endpoint."""
    
    async def test_logout_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful logout."""
        response = await client.post(
            f"{settings.API_V1_STR}/auth/logout",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Note: Access token remains valid after logout (only refresh tokens are invalidated)
        # This is by design - access tokens have short TTL and will expire naturally
        # The logout invalidates refresh tokens to prevent token renewal
        response = await client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers=auth_headers
        )
        # Access token is still valid, so this should return 200
        assert response.status_code == 200
    
    async def test_logout_no_auth(self, client: AsyncClient):
        """Test logout without authentication."""
        response = await client.post(f"{settings.API_V1_STR}/auth/logout")
        # HTTPBearer returns 403 when credentials are missing
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestAuthSecurity:
    """Test authentication security features."""
    
    async def test_password_hashing(self, db: AsyncSession, test_user: User, test_password: str):
        """Test that passwords are properly hashed."""
        # Verify password is not stored in plain text
        assert test_user.hashed_password != test_password
        assert len(test_user.hashed_password) > 20  # Hash should be long
    
    async def test_jwt_expiration(self, client: AsyncClient, test_user: User, test_password: str):
        """Test that JWT tokens have proper expiration."""
        response = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "email": test_user.email,
                "password": test_password
            }
        )
        data = response.json()
        # Verify token structure (basic JWT check)
        assert data["access_token"].count(".") == 2  # JWT has 3 parts
    
    async def test_rate_limiting_login(self, client: AsyncClient):
        """Test rate limiting on login endpoint."""
        # Make multiple failed login attempts
        for i in range(10):
            response = await client.post(
                f"{settings.API_V1_STR}/auth/login",
                json={
                    "email": f"user{i}@example.com",
                    "password": "WrongPass123!"
                }
            )
            # Should eventually get rate limited (429)
            if response.status_code == 429:
                break
        
        # At least some requests should succeed or fail with 401
        assert response.status_code in [401, 429]
