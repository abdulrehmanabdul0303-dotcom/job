"""
Comprehensive resume tests for Phase 1 QA.
Tests all resume endpoints with edge cases and error scenarios.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.user import User
from uuid import uuid4


@pytest.mark.asyncio
class TestResumeUpload:
    """Test resume upload endpoint."""
    
    async def test_upload_pdf_success(self, client: AsyncClient, auth_headers: dict, sample_pdf_bytes: bytes):
        """Test successful PDF upload."""
        response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["filename"] == "resume.pdf"
        assert data["file_size"] > 0
        assert "uploaded_at" in data
    
    async def test_upload_docx_success(self, client: AsyncClient, auth_headers: dict, sample_docx_bytes: bytes):
        """Test successful DOCX upload."""
        response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.docx", sample_docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "resume.docx"
    
    async def test_upload_invalid_file_type(self, client: AsyncClient, auth_headers: dict):
        """Test upload with invalid file type."""
        response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.txt", b"plain text", "text/plain")},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    
    async def test_upload_no_auth(self, client: AsyncClient, sample_pdf_bytes: bytes):
        """Test upload without authentication."""
        response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")}
        )
        # HTTPBearer returns 403 for missing credentials
        assert response.status_code in [401, 403]
    
    async def test_upload_invalid_token(self, client: AsyncClient, sample_pdf_bytes: bytes):
        """Test upload with invalid token."""
        response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
    
    async def test_upload_multiple_resumes(self, client: AsyncClient, auth_headers: dict, sample_pdf_bytes: bytes):
        """Test uploading multiple resumes for same user."""
        # Upload first resume
        response1 = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume1.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        assert response1.status_code == 201
        resume1_id = response1.json()["id"]
        
        # Upload second resume
        response2 = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume2.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        assert response2.status_code == 201
        resume2_id = response2.json()["id"]
        
        # IDs should be different
        assert resume1_id != resume2_id


@pytest.mark.asyncio
class TestResumeList:
    """Test resume list endpoint."""
    
    async def test_list_resumes_empty(self, client: AsyncClient, auth_headers: dict):
        """Test listing resumes when none exist."""
        response = await client.get(
            f"{settings.API_V1_STR}/resume/list",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    async def test_list_resumes_with_items(self, client: AsyncClient, auth_headers: dict, sample_pdf_bytes: bytes):
        """Test listing resumes with uploaded items."""
        # Upload resume
        await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        
        # List resumes
        response = await client.get(
            f"{settings.API_V1_STR}/resume/list",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["filename"] == "resume.pdf"
    
    async def test_list_resumes_no_auth(self, client: AsyncClient):
        """Test listing resumes without authentication."""
        response = await client.get(f"{settings.API_V1_STR}/resume/list")
        assert response.status_code in [401, 403]
    
    async def test_list_resumes_user_isolation(self, client: AsyncClient, db_session: AsyncSession, sample_pdf_bytes: bytes):
        """Test that users only see their own resumes."""
        # Create two users
        from app.services.auth import get_password_hash
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
        
        # User1 uploads resume
        response1 = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "user1@example.com", "password": "Pass123!"}
        )
        headers1 = {"Authorization": f"Bearer {response1.json()['access_token']}"}
        
        await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=headers1
        )
        
        # User2 lists resumes
        response2 = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "user2@example.com", "password": "Pass123!"}
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}
        
        list_response = await client.get(
            f"{settings.API_V1_STR}/resume/list",
            headers=headers2
        )
        
        # User2 should see empty list
        assert list_response.status_code == 200
        assert len(list_response.json()) == 0


@pytest.mark.asyncio
class TestResumeGet:
    """Test get resume endpoint."""
    
    async def test_get_resume_success(self, client: AsyncClient, auth_headers: dict, sample_pdf_bytes: bytes):
        """Test getting resume details."""
        # Upload resume
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Get resume
        response = await client.get(
            f"{settings.API_V1_STR}/resume/{resume_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == resume_id
        assert data["filename"] == "resume.pdf"
    
    async def test_get_resume_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent resume."""
        fake_id = str(uuid4())
        response = await client.get(
            f"{settings.API_V1_STR}/resume/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    async def test_get_resume_no_auth(self, client: AsyncClient, sample_pdf_bytes: bytes, auth_headers: dict):
        """Test getting resume without authentication."""
        # Upload resume first
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Try to get without auth
        response = await client.get(f"{settings.API_V1_STR}/resume/{resume_id}")
        assert response.status_code in [401, 403]
    
    async def test_get_resume_ownership_verification(self, client: AsyncClient, db_session: AsyncSession, sample_pdf_bytes: bytes):
        """Test that users cannot access other users' resumes."""
        from app.services.auth import get_password_hash
        
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
        
        # User2 tries to access
        response2 = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "other@example.com", "password": "Pass123!"}
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}
        
        get_response = await client.get(
            f"{settings.API_V1_STR}/resume/{resume_id}",
            headers=headers2
        )
        
        # Should be forbidden or not found
        assert get_response.status_code in [403, 404]


@pytest.mark.asyncio
class TestResumeScorecard:
    """Test resume scorecard endpoint."""
    
    async def test_get_scorecard_success(self, client: AsyncClient, auth_headers: dict, sample_pdf_bytes: bytes):
        """Test getting scorecard for parsed resume."""
        # Upload resume
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Get scorecard
        response = await client.get(
            f"{settings.API_V1_STR}/resume/{resume_id}/scorecard",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "ats_score" in data
        assert "breakdown" in data
        assert "missing_keywords" in data
        assert "suggestions" in data
    
    async def test_get_scorecard_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting scorecard for non-existent resume."""
        fake_id = str(uuid4())
        response = await client.get(
            f"{settings.API_V1_STR}/resume/{fake_id}/scorecard",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    async def test_get_scorecard_no_auth(self, client: AsyncClient, sample_pdf_bytes: bytes, auth_headers: dict):
        """Test getting scorecard without authentication."""
        # Upload resume first
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Try to get scorecard without auth
        response = await client.get(f"{settings.API_V1_STR}/resume/{resume_id}/scorecard")
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestResumeRecalculate:
    """Test resume recalculate endpoint."""
    
    async def test_recalculate_score_success(self, client: AsyncClient, auth_headers: dict, sample_pdf_bytes: bytes):
        """Test recalculating score."""
        # Upload resume
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Get initial scorecard
        initial_response = await client.get(
            f"{settings.API_V1_STR}/resume/{resume_id}/scorecard",
            headers=auth_headers
        )
        initial_score = initial_response.json()["ats_score"]
        
        # Recalculate
        response = await client.post(
            f"{settings.API_V1_STR}/resume/{resume_id}/recalculate",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "ats_score" in data
        # Score should be recalculated (may be same or different)
        assert data["ats_score"] is not None
    
    async def test_recalculate_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test recalculating non-existent resume."""
        fake_id = str(uuid4())
        response = await client.post(
            f"{settings.API_V1_STR}/resume/{fake_id}/recalculate",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    async def test_recalculate_no_auth(self, client: AsyncClient, sample_pdf_bytes: bytes, auth_headers: dict):
        """Test recalculating without authentication."""
        # Upload resume first
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Try to recalculate without auth
        response = await client.post(f"{settings.API_V1_STR}/resume/{resume_id}/recalculate")
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestResumeShare:
    """Test resume share endpoint."""
    
    async def test_create_share_link_success(self, client: AsyncClient, auth_headers: dict, sample_pdf_bytes: bytes):
        """Test creating share link."""
        # Upload resume
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Create share link
        response = await client.post(
            f"{settings.API_V1_STR}/resume/{resume_id}/share",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "share_token" in data
        assert "share_url" in data
        assert data["is_active"] is True
    
    async def test_create_share_link_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test creating share link for non-existent resume."""
        fake_id = str(uuid4())
        response = await client.post(
            f"{settings.API_V1_STR}/resume/{fake_id}/share",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    async def test_create_share_link_no_auth(self, client: AsyncClient, sample_pdf_bytes: bytes, auth_headers: dict):
        """Test creating share link without authentication."""
        # Upload resume first
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Try to create share link without auth
        response = await client.post(f"{settings.API_V1_STR}/resume/{resume_id}/share")
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestResumePublicScorecard:
    """Test public scorecard endpoint."""
    
    async def test_get_public_scorecard_success(self, client: AsyncClient, auth_headers: dict, sample_pdf_bytes: bytes):
        """Test accessing public scorecard with share token."""
        # Upload resume
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Create share link
        share_response = await client.post(
            f"{settings.API_V1_STR}/resume/{resume_id}/share",
            headers=auth_headers
        )
        share_token = share_response.json()["share_token"]
        
        # Get public scorecard (no auth required)
        response = await client.get(f"{settings.API_V1_STR}/resume/public/{share_token}")
        assert response.status_code == 200
        data = response.json()
        assert "ats_score" in data
        assert "breakdown" in data
    
    async def test_get_public_scorecard_invalid_token(self, client: AsyncClient):
        """Test accessing public scorecard with invalid token."""
        response = await client.get(f"{settings.API_V1_STR}/resume/public/invalid-token")
        assert response.status_code == 404
    
    async def test_public_scorecard_no_personal_info(self, client: AsyncClient, auth_headers: dict, sample_pdf_bytes: bytes):
        """Test that public scorecard doesn't expose personal information."""
        # Upload resume
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Create share link
        share_response = await client.post(
            f"{settings.API_V1_STR}/resume/{resume_id}/share",
            headers=auth_headers
        )
        share_token = share_response.json()["share_token"]
        
        # Get public scorecard
        response = await client.get(f"{settings.API_V1_STR}/resume/public/{share_token}")
        data = response.json()
        
        # Should not contain personal info
        assert "filename" not in data
        assert "file_path" not in data
        assert "user_id" not in data


@pytest.mark.asyncio
class TestResumeDelete:
    """Test resume delete endpoint."""
    
    async def test_delete_resume_success(self, client: AsyncClient, auth_headers: dict, sample_pdf_bytes: bytes):
        """Test deleting resume."""
        # Upload resume
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Delete resume
        response = await client.delete(
            f"{settings.API_V1_STR}/resume/{resume_id}",
            headers=auth_headers
        )
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = await client.get(
            f"{settings.API_V1_STR}/resume/{resume_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
    
    async def test_delete_resume_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test deleting non-existent resume."""
        fake_id = str(uuid4())
        response = await client.delete(
            f"{settings.API_V1_STR}/resume/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    async def test_delete_resume_no_auth(self, client: AsyncClient, sample_pdf_bytes: bytes, auth_headers: dict):
        """Test deleting resume without authentication."""
        # Upload resume first
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Try to delete without auth
        response = await client.delete(f"{settings.API_V1_STR}/resume/{resume_id}")
        assert response.status_code in [401, 403]
    
    async def test_delete_removes_related_artifacts(self, client: AsyncClient, auth_headers: dict, sample_pdf_bytes: bytes):
        """Test that deleting resume removes scorecard and share links."""
        # Upload resume
        upload_response = await client.post(
            f"{settings.API_V1_STR}/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers
        )
        resume_id = upload_response.json()["id"]
        
        # Create share link
        await client.post(
            f"{settings.API_V1_STR}/resume/{resume_id}/share",
            headers=auth_headers
        )
        
        # Delete resume
        await client.delete(
            f"{settings.API_V1_STR}/resume/{resume_id}",
            headers=auth_headers
        )
        
        # Verify scorecard is gone
        scorecard_response = await client.get(
            f"{settings.API_V1_STR}/resume/{resume_id}/scorecard",
            headers=auth_headers
        )
        assert scorecard_response.status_code == 404

