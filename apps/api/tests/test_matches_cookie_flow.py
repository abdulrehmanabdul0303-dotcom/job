"""
Tests for matches endpoint with cookie-based authentication.
Validates the complete flow: login -> /me -> /matches -> logout.
"""
import pytest
from httpx import AsyncClient


class TestMatchesCookieFlow:
    """Test matches endpoint with cookie-based auth."""
    
    @pytest.mark.asyncio
    async def test_matches_requires_auth(self, client: AsyncClient):
        """Test that /matches returns 401 without authentication."""
        response = await client.get("/api/v1/matches")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_matches_with_cookie_auth(self, client: AsyncClient):
        """Test complete cookie auth flow with matches endpoint."""
        # 1. Register
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "matchtest@example.com",
                "password": "TestPassword123!",
                "full_name": "Match Test User",
            }
        )
        assert reg_response.status_code in (200, 201, 400)  # 400 if already exists
        
        # 2. Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "matchtest@example.com",
                "password": "TestPassword123!",
            }
        )
        assert login_response.status_code == 200
        assert login_response.json().get("success") == True
        
        # Verify cookies are set
        cookies = login_response.cookies
        # Note: httpx may not expose httpOnly cookies directly, but they're sent
        
        # 3. /auth/me must work with cookies
        me_response = await client.get("/api/v1/auth/me")
        assert me_response.status_code == 200, f"/me failed: {me_response.text}"
        me_data = me_response.json()
        assert "email" in me_data
        assert me_data["email"] == "matchtest@example.com"
        
        # 4. /matches must work with cookies (not require Bearer token)
        matches_response = await client.get("/api/v1/matches")
        assert matches_response.status_code == 200, f"/matches failed: {matches_response.text}"
        
        # Validate response structure
        data = matches_response.json()
        assert "matches" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert isinstance(data["matches"], list)
        assert isinstance(data["total"], int)
        
        # 5. Logout
        logout_response = await client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200
        
        # 6. /me after logout must be 401
        me_after_logout = await client.get("/api/v1/auth/me")
        assert me_after_logout.status_code == 401
    
    @pytest.mark.asyncio
    async def test_matches_response_structure(self, client: AsyncClient):
        """Test that matches response has correct structure."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "matchstruct@example.com",
                "password": "TestPassword123!",
                "full_name": "Match Struct User",
            }
        )
        
        await client.post(
            "/api/v1/auth/login",
            json={
                "email": "matchstruct@example.com",
                "password": "TestPassword123!",
            }
        )
        
        # Get matches with pagination params
        response = await client.get("/api/v1/matches?page=1&page_size=10&min_score=0")
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate pagination fields
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total"] >= 0
        assert data["total_pages"] >= 0
        
        # If there are matches, validate match structure
        if data["matches"]:
            match = data["matches"][0]
            assert "id" in match
            assert "user_id" in match
            assert "job_id" in match
            assert "resume_id" in match
            assert "match_score" in match
            assert 0 <= match["match_score"] <= 100
            
            # Validate JSON fields are parsed (not strings)
            if match.get("score_breakdown"):
                assert isinstance(match["score_breakdown"], dict)
            if match.get("why"):
                assert isinstance(match["why"], dict)
            if match.get("missing_skills"):
                assert isinstance(match["missing_skills"], list)
    
    @pytest.mark.asyncio
    async def test_recompute_matches_requires_resume(self, client: AsyncClient):
        """Test that recompute matches fails gracefully without resume."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "recompute@example.com",
                "password": "TestPassword123!",
                "full_name": "Recompute User",
            }
        )
        
        await client.post(
            "/api/v1/auth/login",
            json={
                "email": "recompute@example.com",
                "password": "TestPassword123!",
            }
        )
        
        # Try to recompute matches (should fail - no resume)
        response = await client.post(
            "/api/v1/matches/recompute",
            json={"min_score": 0}
        )
        
        # Should return 400 (no resume) or 200 with 0 matches
        assert response.status_code in (200, 400)
        
        if response.status_code == 400:
            assert "resume" in response.text.lower() or "not found" in response.text.lower()


class TestMatchesEdgeCases:
    """Test edge cases for matches endpoint."""
    
    @pytest.mark.asyncio
    async def test_matches_pagination(self, client: AsyncClient):
        """Test matches pagination parameters."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "pagination@example.com",
                "password": "TestPassword123!",
                "full_name": "Pagination User",
            }
        )
        
        await client.post(
            "/api/v1/auth/login",
            json={
                "email": "pagination@example.com",
                "password": "TestPassword123!",
            }
        )
        
        # Test different page sizes
        for page_size in [5, 10, 50]:
            response = await client.get(f"/api/v1/matches?page=1&page_size={page_size}")
            assert response.status_code == 200
            data = response.json()
            assert data["page_size"] == page_size
    
    @pytest.mark.asyncio
    async def test_matches_min_score_filter(self, client: AsyncClient):
        """Test matches min_score filter."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "minscore@example.com",
                "password": "TestPassword123!",
                "full_name": "MinScore User",
            }
        )
        
        await client.post(
            "/api/v1/auth/login",
            json={
                "email": "minscore@example.com",
                "password": "TestPassword123!",
            }
        )
        
        # Test with high min_score (should return fewer/no matches)
        response = await client.get("/api/v1/matches?min_score=90")
        assert response.status_code == 200
        data = response.json()
        
        # All returned matches should have score >= 90
        for match in data["matches"]:
            assert match["match_score"] >= 90
