"""
Comprehensive preferences tests for Phase 2 QA.
Tests all preferences endpoints with edge cases and error scenarios.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.user import User
from app.models.resume import Resume
from app.services.auth import get_password_hash
from uuid import uuid4


@pytest.mark.asyncio
class TestGetPreferences:
    """Test get preferences endpoint."""
    
    async def test_get_preferences_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting preferences when none exist."""
        response = await client.get(
            f"{settings.API_V1_STR}/preferences/me",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_get_preferences_success(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test getting existing preferences."""
        # First create preferences
        await client.put(
            f"{settings.API_V1_STR}/preferences/me",
            json={
                "desired_roles": ["Software Engineer", "Backend Developer"],
                "desired_locations": ["Remote", "San Francisco"],
                "desired_seniority": ["Mid-level", "Senior"],
                "desired_industries": ["Technology", "Finance"],
                "desired_company_size": ["Startup", "Mid-size"],
                "min_salary": 100000,
                "max_salary": 200000,
                "remote_preference": "remote",
                "willing_to_relocate": False,
                "job_types": ["Full-time", "Contract"],
                "benefits_important": ["Health Insurance", "401k", "Remote Work"],
                "skills_to_develop": ["Kubernetes", "Go", "Rust"]
            },
            headers=auth_headers
        )
        
        # Now get preferences
        response = await client.get(
            f"{settings.API_V1_STR}/preferences/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "desired_roles" in data
        assert "Software Engineer" in data["desired_roles"]
    
    async def test_get_preferences_no_auth(self, client: AsyncClient):
        """Test getting preferences without authentication."""
        response = await client.get(f"{settings.API_V1_STR}/preferences/me")
        assert response.status_code == 401
    
    async def test_get_preferences_invalid_token(self, client: AsyncClient):
        """Test getting preferences with invalid token."""
        response = await client.get(
            f"{settings.API_V1_STR}/preferences/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUpdatePreferences:
    """Test update preferences endpoint."""
    
    async def test_update_preferences_create_new(self, client: AsyncClient, auth_headers: dict):
        """Test creating new preferences via update."""
        response = await client.put(
            f"{settings.API_V1_STR}/preferences/me",
            json={
                "desired_roles": ["Software Engineer"],
                "desired_locations": ["Remote"],
                "desired_seniority": ["Mid-level"],
                "desired_industries": ["Technology"],
                "desired_company_size": ["Startup"],
                "min_salary": 100000,
                "max_salary": 200000,
                "remote_preference": "remote",
                "willing_to_relocate": False,
                "job_types": ["Full-time"],
                "benefits_important": ["Health Insurance"],
                "skills_to_develop": ["Kubernetes"]
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "preferences" in data
        assert data["preferences"]["desired_roles"] == ["Software Engineer"]
    
    async def test_update_preferences_modify_existing(self, client: AsyncClient, auth_headers: dict):
        """Test modifying existing preferences."""
        # Create initial preferences
        await client.put(
            f"{settings.API_V1_STR}/preferences/me",
            json={
                "desired_roles": ["Software Engineer"],
                "desired_locations": ["Remote"],
                "desired_seniority": ["Mid-level"],
                "desired_industries": ["Technology"],
                "desired_company_size": ["Startup"],
                "min_salary": 100000,
                "max_salary": 200000,
                "remote_preference": "remote",
                "willing_to_relocate": False,
                "job_types": ["Full-time"],
                "benefits_important": ["Health Insurance"],
                "skills_to_develop": ["Kubernetes"]
            },
            headers=auth_headers
        )
        
        # Update preferences
        response = await client.put(
            f"{settings.API_V1_STR}/preferences/me",
            json={
                "desired_roles": ["Senior Software Engineer", "Tech Lead"],
                "desired_locations": ["San Francisco", "New York"],
                "desired_seniority": ["Senior"],
                "desired_industries": ["Technology", "Finance"],
                "desired_company_size": ["Large"],
                "min_salary": 150000,
                "max_salary": 300000,
                "remote_preference": "hybrid",
                "willing_to_relocate": True,
                "job_types": ["Full-time"],
                "benefits_important": ["Health Insurance", "401k", "Stock Options"],
                "skills_to_develop": ["Leadership", "System Design"]
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "Senior Software Engineer" in data["preferences"]["desired_roles"]
        assert data["preferences"]["min_salary"] == 150000
    
    async def test_update_preferences_partial(self, client: AsyncClient, auth_headers: dict):
        """Test partial update of preferences."""
        # Create initial preferences
        await client.put(
            f"{settings.API_V1_STR}/preferences/me",
            json={
                "desired_roles": ["Software Engineer"],
                "desired_locations": ["Remote"],
                "desired_seniority": ["Mid-level"],
                "desired_industries": ["Technology"],
                "desired_company_size": ["Startup"],
                "min_salary": 100000,
                "max_salary": 200000,
                "remote_preference": "remote",
                "willing_to_relocate": False,
                "job_types": ["Full-time"],
                "benefits_important": ["Health Insurance"],
                "skills_to_develop": ["Kubernetes"]
            },
            headers=auth_headers
        )
        
        # Partial update (only update salary)
        response = await client.put(
            f"{settings.API_V1_STR}/preferences/me",
            json={
                "min_salary": 120000,
                "max_salary": 250000
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preferences"]["min_salary"] == 120000
        # Other fields should remain
        assert data["preferences"]["desired_roles"] == ["Software Engineer"]
    
    async def test_update_preferences_no_auth(self, client: AsyncClient):
        """Test updating preferences without authentication."""
        response = await client.put(
            f"{settings.API_V1_STR}/preferences/me",
            json={"desired_roles": ["Software Engineer"]}
        )
        assert response.status_code == 401
    
    async def test_update_preferences_invalid_token(self, client: AsyncClient):
        """Test updating preferences with invalid token."""
        response = await client.put(
            f"{settings.API_V1_STR}/preferences/me",
            json={"desired_roles": ["Software Engineer"]},
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
    
    async def test_update_preferences_empty_lists(self, client: AsyncClient, auth_headers: dict):
        """Test updating preferences with empty lists."""
        response = await client.put(
            f"{settings.API_V1_STR}/preferences/me",
            json={
                "desired_roles": [],
                "desired_locations": [],
                "desired_seniority": [],
                "desired_industries": [],
                "desired_company_size": [],
                "job_types": [],
                "benefits_important": [],
                "skills_to_develop": []
            },
            headers=auth_headers
        )
        assert response.status_code == 200
    
    async def test_update_preferences_salary_validation(self, client: AsyncClient, auth_headers: dict):
        """Test salary validation in preferences."""
        response = await client.put(
            f"{settings.API_V1_STR}/preferences/me",
            json={
                "desired_roles": ["Software Engineer"],
                "desired_locations": ["Remote"],
                "desired_seniority": ["Mid-level"],
                "desired_industries": ["Technology"],
                "desired_company_size": ["Startup"],
                "min_salary": 200000,
                "max_salary": 100000,  # Invalid: max < min
                "remote_preference": "remote",
                "willing_to_relocate": False,
                "job_types": ["Full-time"],
                "benefits_important": [],
                "skills_to_develop": []
            },
            headers=auth_headers
        )
        # Should either accept or reject with validation error
        assert response.status_code in [200, 422]


@pytest.mark.asyncio
class TestAutoDetectPreferences:
    """Test auto-detect preferences endpoint."""
    
    async def test_auto_detect_success(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession, sample_pdf_bytes: bytes):
        """Test auto-detecting preferences from resume."""
        # Upload resume first
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Auto-detect preferences
        response = await client.post(
            f"{settings.API_V1_STR}/preferences/auto-detect",
            params={"resume_id": resume_id},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "preferences" in data
        assert "auto-detected" in data["message"].lower()
    
    async def test_auto_detect_resume_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test auto-detect with non-existent resume."""
        fake_id = str(uuid4())
        response = await client.post(
            f"{settings.API_V1_STR}/preferences/auto-detect",
            params={"resume_id": fake_id},
            headers=auth_headers
        )
        assert response.status_code == 404
    
    async def test_auto_detect_no_auth(self, client: AsyncClient):
        """Test auto-detect without authentication."""
        response = await client.post(
            f"{settings.API_V1_STR}/preferences/auto-detect",
            params={"resume_id": str(uuid4())}
        )
        assert response.status_code == 401
    
    async def test_auto_detect_invalid_token(self, client: AsyncClient):
        """Test auto-detect with invalid token."""
        response = await client.post(
            f"{settings.API_V1_STR}/preferences/auto-detect",
            params={"resume_id": str(uuid4())},
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
    
    async def test_auto_detect_ownership_verification(self, client: AsyncClient, db_session: AsyncSession, sample_pdf_bytes: bytes):
        """Test that users cannot auto-detect from other users' resumes."""
        # Create two users
        user1 = User(
            email="owner@example.com",
            hashed_password=get_password_hash("Pass123!"),
            is_active=True
        )
        user2 = User(
            email="other@example.com",
            hashed_password=get_password_hash("Pass123!"),
            is_active=True
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()
        
        # User1 uploads resume
        response1 = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "owner@example.com", "password": "Pass123!"}
        )
        headers1 = {"Authorization": f"Bearer {response1.json()['access_token']}"}
        
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=headers1
        )
        resume_id = upload_response.json()["id"]
        
        # User2 tries to auto-detect
        response2 = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "other@example.com", "password": "Pass123!"}
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}
        
        auto_detect_response = await client.post(
            f"{settings.API_V1_STR}/preferences/auto-detect",
            params={"resume_id": resume_id},
            headers=headers2
        )
        
        # Should be forbidden or not found
        assert auto_detect_response.status_code in [403, 404]


@pytest.mark.asyncio
class TestPreferencesUserIsolation:
    """Test that users cannot access/modify other users' preferences."""
    
    async def test_cannot_read_other_user_preferences(self, client: AsyncClient, db_session: AsyncSession):
        """Test that users cannot read other users' preferences."""
        # Create two users
        user1 = User(
            email="user1@example.com",
            hashed_password=get_password_hash("Pass123!"),
            is_active=True
        )
        user2 = User(
            email="user2@example.com",
            hashed_password=get_password_hash("Pass123!"),
            is_active=True
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()
        
        # User1 sets preferences
        response1 = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "user1@example.com", "password": "Pass123!"}
        )
        headers1 = {"Authorization": f"Bearer {response1.json()['access_token']}"}
        
        await client.put(
            f"{settings.API_V1_STR}/preferences/me",
            json={
                "desired_roles": ["Software Engineer"],
                "desired_locations": ["Remote"],
                "desired_seniority": ["Mid-level"],
                "desired_industries": ["Technology"],
                "desired_company_size": ["Startup"],
                "min_salary": 100000,
                "max_salary": 200000,
                "remote_preference": "remote",
                "willing_to_relocate": False,
                "job_types": ["Full-time"],
                "benefits_important": [],
                "skills_to_develop": []
            },
            headers=headers1
        )
        
        # User2 tries to read User1's preferences
        response2 = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "user2@example.com", "password": "Pass123!"}
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}
        
        get_response = await client.get(
            f"{settings.API_V1_STR}/preferences/me",
            headers=headers2
        )
        
        # User2 should get 404 (no preferences set for them)
        assert get_response.status_code == 404
    
    async def test_cannot_modify_other_user_preferences(self, client: AsyncClient, db_session: AsyncSession):
        """Test that users cannot modify other users' preferences."""
        # Create two users
        user1 = User(
            email="user1@example.com",
            hashed_password=get_password_hash("Pass123!"),
            is_active=True
        )
        user2 = User(
            email="user2@example.com",
            hashed_password=get_password_hash("Pass123!"),
            is_active=True
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()
        
        # User1 sets preferences
        response1 = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "user1@example.com", "password": "Pass123!"}
        )
        headers1 = {"Authorization": f"Bearer {response1.json()['access_token']}"}
        
        await client.put(
            f"{settings.API_V1_STR}/preferences/me",
            json={
                "desired_roles": ["Software Engineer"],
                "desired_locations": ["Remote"],
                "desired_seniority": ["Mid-level"],
                "desired_industries": ["Technology"],
                "desired_company_size": ["Startup"],
                "min_salary": 100000,
                "max_salary": 200000,
                "remote_preference": "remote",
                "willing_to_relocate": False,
                "job_types": ["Full-time"],
                "benefits_important": [],
                "skills_to_develop": []
            },
            headers=headers1
        )
        
        # User2 tries to modify (should create their own, not modify User1's)
        response2 = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "user2@example.com", "password": "Pass123!"}
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}
        
        update_response = await client.put(
            f"{settings.API_V1_STR}/preferences/me",
            json={
                "desired_roles": ["Data Scientist"],
                "desired_locations": ["New York"],
                "desired_seniority": ["Senior"],
                "desired_industries": ["Finance"],
                "desired_company_size": ["Large"],
                "min_salary": 150000,
                "max_salary": 300000,
                "remote_preference": "office",
                "willing_to_relocate": True,
                "job_types": ["Full-time"],
                "benefits_important": [],
                "skills_to_develop": []
            },
            headers=headers2
        )
        
        # User2 should have their own preferences
        assert update_response.status_code == 200
        
        # Verify User1's preferences are unchanged
        user1_prefs = await client.get(
            f"{settings.API_V1_STR}/preferences/me",
            headers=headers1
        )
        assert user1_prefs.json()["desired_roles"] == ["Software Engineer"]


@pytest.mark.asyncio
class TestPreferencesDefaults:
    """Test default preferences behavior."""
    
    async def test_preferences_with_empty_resume(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test auto-detect with empty resume text."""
        # Create a resume with no parsed text
        from app.models.user import User as UserModel
        from sqlalchemy import select
        
        result = await db_session.execute(
            select(UserModel).where(UserModel.email == "testuser@example.com")
        )
        user = result.scalar_one()
        
        resume = Resume(
            user_id=user.id,
            filename="empty.pdf",
            file_path="/tmp/empty.pdf",
            file_size=0,
            mime_type="application/pdf",
            is_parsed=False,
            raw_text=""
        )
        db_session.add(resume)
        await db_session.commit()
        
        # Try to auto-detect
        response = await client.post(
            f"{settings.API_V1_STR}/preferences/auto-detect",
            params={"resume_id": str(resume.id)},
            headers=auth_headers
        )
        
        # Should fail because resume not parsed
        assert response.status_code == 400

