"""
Integration tests for JobPilot API.
Tests complete workflows across multiple endpoints.
Uses cookie-based authentication.
"""
import pytest
from httpx import AsyncClient
import json


class TestAuthIntegration:
    """Integration tests for authentication flow."""
    
    @pytest.mark.asyncio
    async def test_register_and_login_flow(self, client: AsyncClient):
        """Test complete registration and login flow with cookie auth."""
        # Register user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
            }
        )
        
        assert register_response.status_code == 201
        register_data = register_response.json()
        # Cookie-based auth returns success message, not tokens
        assert register_data.get("success") == True
        
        # Login user
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
            }
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        # Cookie-based auth returns success message
        assert login_data.get("success") == True
        
        # Verify /me works with cookies
        me_response = await client.get("/api/v1/auth/me")
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_invalid_login(self, client: AsyncClient):
        """Test login with invalid credentials."""
        # Register user first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
            }
        )
        
        # Try login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword",
            }
        )
        
        assert response.status_code == 401


class TestResumeIntegration:
    """Integration tests for resume upload and management."""
    
    @pytest.mark.asyncio
    async def test_resume_upload_and_retrieve(self, client: AsyncClient):
        """Test uploading and retrieving resume with cookie auth."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
            }
        )
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
            }
        )
        assert login_response.status_code == 200
        
        # Upload resume using parsed endpoint (cookies sent automatically)
        upload_response = await client.post(
            "/api/v1/resume/upload-parsed",
            json={
                "filename": "test_resume.pdf",
                "parsed_data": "John Doe\nSoftware Engineer\nPython, JavaScript\n5 years experience",
                "skills": ["Python", "JavaScript", "FastAPI"],
                "experience_years": 5
            },
        )
        
        assert upload_response.status_code == 201
        resume_data = upload_response.json()
        assert "id" in resume_data
        resume_id = resume_data["id"]
        
        # Retrieve resume (cookies sent automatically)
        get_response = await client.get(f"/api/v1/resume/{resume_id}")
        
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved["id"] == resume_id
    
    @pytest.mark.asyncio
    async def test_ats_score_calculation(self, client: AsyncClient):
        """Test ATS score calculation for resume with cookie auth."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
            }
        )
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
            }
        )
        assert login_response.status_code == 200
        
        # Upload resume using parsed endpoint
        upload_response = await client.post(
            "/api/v1/resume/upload-parsed",
            json={
                "filename": "test_resume.pdf",
                "parsed_data": "John Doe\nSoftware Engineer\nPython, JavaScript, React\n5 years experience",
                "skills": ["Python", "JavaScript", "React"],
                "experience_years": 5
            },
        )
        
        resume_id = upload_response.json()["id"]
        
        # Get ATS scorecard
        score_response = await client.get(f"/api/v1/resume/{resume_id}/scorecard")
        
        assert score_response.status_code == 200
        score_data = score_response.json()
        assert "ats_score" in score_data
        assert 0 <= score_data["ats_score"] <= 100


class TestPreferencesIntegration:
    """Integration tests for job preferences."""
    
    @pytest.mark.asyncio
    async def test_preferences_workflow(self, client: AsyncClient):
        """Test complete preferences workflow with cookie auth."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
            }
        )
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
            }
        )
        assert login_response.status_code == 200
        
        # Set preferences (cookies sent automatically)
        pref_response = await client.put(
            "/api/v1/preferences/me",
            json={
                "desired_roles": ["Senior Software Engineer"],
                "desired_locations": ["USA", "Canada"],
                "salary_min": 100000,
                "salary_max": 200000,
                "job_types": ["remote"],
            },
        )
        
        assert pref_response.status_code == 200
        prefs_data = pref_response.json()
        prefs = prefs_data["preferences"]
        assert "Senior Software Engineer" in prefs["desired_roles"]
        assert "remote" in prefs["job_types"]
        
        # Get preferences
        get_response = await client.get("/api/v1/preferences/me")
        
        assert get_response.status_code == 200
        retrieved_data = get_response.json()
        retrieved = retrieved_data["preferences"] if "preferences" in retrieved_data else retrieved_data
        assert "Senior Software Engineer" in retrieved["desired_roles"]


class TestJobSourcesIntegration:
    """Integration tests for job sources and fetching."""
    
    @pytest.mark.asyncio
    async def test_job_source_workflow(self, client: AsyncClient):
        """Test complete job source workflow with cookie auth."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
            }
        )
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
            }
        )
        assert login_response.status_code == 200
        
        # Create job source (cookies sent automatically)
        source_response = await client.post(
            "/api/v1/sources",
            json={
                "name": "Tech Jobs RSS",
                "source_type": "rss",
                "url": "https://example.com/jobs.rss",
                "is_active": True,
                "fetch_frequency_hours": 24,
            },
        )
        
        assert source_response.status_code == 201
        source_data = source_response.json()
        assert source_data["name"] == "Tech Jobs RSS"
        source_id = source_data["id"]
        
        # Get sources
        get_response = await client.get("/api/v1/sources")
        
        assert get_response.status_code == 200
        sources = get_response.json()
        assert len(sources) > 0
        assert sources[0]["id"] == source_id
        
        # Update source
        update_response = await client.put(
            f"/api/v1/sources/{source_id}",
            json={"is_active": False},
        )
        
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["is_active"] is False


class TestJobsIntegration:
    """Integration tests for job postings."""
    
    @pytest.mark.asyncio
    async def test_jobs_listing_and_filtering(self, client: AsyncClient):
        """Test job listing and filtering with cookie auth."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
            }
        )
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
            }
        )
        assert login_response.status_code == 200
        
        # Get jobs (cookies sent automatically)
        response = await client.get("/api/v1/jobs?page=1&page_size=20")
        
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert "page" in data


class TestMatchesIntegration:
    """Integration tests for job matching."""
    
    @pytest.mark.asyncio
    async def test_matches_workflow(self, client: AsyncClient):
        """Test complete matches workflow with cookie auth."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
            }
        )
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
            }
        )
        
        assert login_response.status_code == 200
        assert login_response.json().get("success") == True
        
        # Get matches (cookies sent automatically)
        response = await client.get("/api/v1/matches?page=1&page_size=20")
        
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert "total" in data
        assert data["total"] == 0


class TestHealthCheck:
    """Integration tests for health check."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestErrorHandling:
    """Integration tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test unauthorized access returns 401."""
        response = await client.get("/api/v1/preferences/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_not_found_error(self, client: AsyncClient):
        """Test not found error returns 404."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
            }
        )
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
            }
        )
        assert login_response.status_code == 200
        
        # Try to get non-existent resume
        response = await client.get("/api/v1/resume/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404
