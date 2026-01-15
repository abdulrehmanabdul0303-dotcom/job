"""
Tests for Apply Kit generation and management.
"""
import pytest
import json
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.resume import Resume
from app.models.job import JobPosting
from app.models.apply import ApplyKit, JobActivity, ActivityStatus
from app.services.apply_service import ApplyKitService, ActivityService
from app.services.apply_kit import ApplyKitGenerator
from datetime import datetime


@pytest.mark.asyncio
class TestApplyKitGeneration:
    """Test apply kit generation."""
    
    async def test_generate_cover_letter(self):
        """Test cover letter generation."""
        cover_letter = ApplyKitGenerator.generate_cover_letter(
            user_name="John Doe",
            job_title="Senior Software Engineer",
            company_name="Tech Corp",
            resume_text="Python, JavaScript, React, FastAPI, Docker",
            job_description="Looking for Senior Software Engineer with Python and React experience",
        )
        
        assert cover_letter is not None
        assert "John Doe" in cover_letter
        assert "Senior Software Engineer" in cover_letter
        assert "Tech Corp" in cover_letter
        assert len(cover_letter) > 100
    
    async def test_generate_tailored_bullets(self):
        """Test tailored resume bullets generation."""
        bullets = ApplyKitGenerator.generate_tailored_bullets(
            resume_text="Python, JavaScript, React, FastAPI, Docker, Kubernetes",
            job_description="Senior role requiring Python, React, Docker, and Kubernetes",
            job_title="Senior Software Engineer",
        )
        
        assert bullets is not None
        assert isinstance(bullets, list)
        assert len(bullets) > 0
        assert len(bullets) <= 5
        assert all(isinstance(b, str) for b in bullets)
    
    async def test_generate_interview_qa(self):
        """Test interview Q&A generation."""
        qa = ApplyKitGenerator.generate_interview_qa(
            resume_text="Python developer with 5 years experience",
            job_description="Senior Python developer role",
            job_title="Senior Python Developer",
        )
        
        assert qa is not None
        assert isinstance(qa, dict)
        assert len(qa) > 0
        assert "Tell me about yourself" in qa
        assert all(isinstance(v, str) for v in qa.values())


@pytest.mark.asyncio
class TestApplyKitService:
    """Test apply kit service."""
    
    async def test_generate_apply_kit(self, db: AsyncSession, test_user: User, test_resume: Resume):
        """Test generating an apply kit."""
        # Create a job
        job = JobPosting(
            title="Senior Software Engineer",
            company="Tech Corp",
            location="San Francisco, CA",
            description="We are looking for a senior software engineer",
            requirements="5+ years Python experience",
            salary_min=150000,
            salary_max=200000,
            work_type="full-time",
            application_url="https://example.com/apply",
        )
        db.add(job)
        await db.flush()
        await db.refresh(job)
        
        # Generate apply kit
        result = await ApplyKitService.generate_apply_kit(
            db=db,
            user_id=test_user.id,
            job_id=job.id,
            resume_id=test_resume.id,
        )
        
        assert result is not None
        assert result['apply_kit_id'] is not None
        assert result['job_id'] == job.id
        assert result['cover_letter'] is not None
        assert result['tailored_bullets'] is not None
        assert result['qa'] is not None
        assert isinstance(result['tailored_bullets'], list)
        assert isinstance(result['qa'], dict)
    
    async def test_get_apply_kit(self, db: AsyncSession, test_user: User, test_resume: Resume):
        """Test retrieving an apply kit."""
        # Create a job
        job = JobPosting(
            title="Senior Software Engineer",
            company="Tech Corp",
            location="San Francisco, CA",
            description="We are looking for a senior software engineer",
            requirements="5+ years Python experience",
            salary_min=150000,
            salary_max=200000,
            work_type="full-time",
            application_url="https://example.com/apply",
        )
        db.add(job)
        await db.flush()
        await db.refresh(job)
        
        # Generate apply kit
        await ApplyKitService.generate_apply_kit(
            db=db,
            user_id=test_user.id,
            job_id=job.id,
            resume_id=test_resume.id,
        )
        
        # Retrieve apply kit
        apply_kit = await ApplyKitService.get_apply_kit(
            db=db,
            user_id=test_user.id,
            job_id=job.id,
        )
        
        assert apply_kit is not None
        assert apply_kit.user_id == test_user.id
        assert apply_kit.job_id == job.id
        assert apply_kit.cover_letter is not None
    
    async def test_update_apply_kit(self, db: AsyncSession, test_user: User, test_resume: Resume):
        """Test updating an apply kit."""
        # Create a job
        job = JobPosting(
            title="Senior Software Engineer",
            company="Tech Corp",
            location="San Francisco, CA",
            description="We are looking for a senior software engineer",
            requirements="5+ years Python experience",
            salary_min=150000,
            salary_max=200000,
            work_type="full-time",
            application_url="https://example.com/apply",
        )
        db.add(job)
        await db.flush()
        await db.refresh(job)
        
        # Generate apply kit
        await ApplyKitService.generate_apply_kit(
            db=db,
            user_id=test_user.id,
            job_id=job.id,
            resume_id=test_resume.id,
        )
        
        # Update apply kit
        new_cover_letter = "Updated cover letter"
        new_bullets = ["Updated bullet 1", "Updated bullet 2"]
        
        updated_kit = await ApplyKitService.update_apply_kit(
            db=db,
            user_id=test_user.id,
            job_id=job.id,
            cover_letter=new_cover_letter,
            tailored_bullets=new_bullets,
        )
        
        assert updated_kit is not None
        assert updated_kit.cover_letter == new_cover_letter
        assert json.loads(updated_kit.tailored_bullets_json) == new_bullets
    
    async def test_delete_apply_kit(self, db: AsyncSession, test_user: User, test_resume: Resume):
        """Test deleting an apply kit."""
        # Create a job
        job = JobPosting(
            title="Senior Software Engineer",
            company="Tech Corp",
            location="San Francisco, CA",
            description="We are looking for a senior software engineer",
            requirements="5+ years Python experience",
            salary_min=150000,
            salary_max=200000,
            work_type="full-time",
            application_url="https://example.com/apply",
        )
        db.add(job)
        await db.flush()
        await db.refresh(job)
        
        # Generate apply kit
        await ApplyKitService.generate_apply_kit(
            db=db,
            user_id=test_user.id,
            job_id=job.id,
            resume_id=test_resume.id,
        )
        
        # Delete apply kit
        deleted = await ApplyKitService.delete_apply_kit(
            db=db,
            user_id=test_user.id,
            job_id=job.id,
        )
        
        assert deleted is True
        
        # Verify it's deleted
        apply_kit = await ApplyKitService.get_apply_kit(
            db=db,
            user_id=test_user.id,
            job_id=job.id,
        )
        
        assert apply_kit is None


@pytest.mark.asyncio
class TestActivityService:
    """Test job activity service."""
    
    async def test_set_activity_status(self, db: AsyncSession, test_user: User):
        """Test setting activity status."""
        job_id = "test-job-123"
        
        activity = await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id=job_id,
            status=ActivityStatus.INTERESTED,
            notes="Looks interesting",
        )
        
        assert activity is not None
        assert activity.user_id == test_user.id
        assert activity.job_id == job_id
        assert activity.status == ActivityStatus.INTERESTED
        assert activity.notes == "Looks interesting"
    
    async def test_update_activity_status(self, db: AsyncSession, test_user: User):
        """Test updating activity status."""
        job_id = "test-job-456"
        
        # Create initial activity
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id=job_id,
            status=ActivityStatus.INTERESTED,
        )
        
        # Update status
        updated = await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id=job_id,
            status=ActivityStatus.APPLIED,
            notes="Applied on company website",
        )
        
        assert updated.status == ActivityStatus.APPLIED
        assert updated.notes == "Applied on company website"
    
    async def test_get_activity(self, db: AsyncSession, test_user: User):
        """Test retrieving activity."""
        job_id = "test-job-789"
        
        # Create activity
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id=job_id,
            status=ActivityStatus.INTERVIEW,
        )
        
        # Retrieve activity
        activity = await ActivityService.get_activity(
            db=db,
            user_id=test_user.id,
            job_id=job_id,
        )
        
        assert activity is not None
        assert activity.status == ActivityStatus.INTERVIEW
    
    async def test_get_activities_with_pagination(self, db: AsyncSession, test_user: User):
        """Test retrieving activities with pagination."""
        # Create multiple activities
        for i in range(5):
            await ActivityService.set_activity_status(
                db=db,
                user_id=test_user.id,
                job_id=f"job-{i}",
                status=ActivityStatus.INTERESTED,
            )
        
        # Get first page
        activities, total = await ActivityService.get_activities(
            db=db,
            user_id=test_user.id,
            page=1,
            page_size=2,
        )
        
        assert len(activities) == 2
        assert total == 5
    
    async def test_get_activities_by_status(self, db: AsyncSession, test_user: User):
        """Test filtering activities by status."""
        # Create activities with different statuses
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-1",
            status=ActivityStatus.INTERESTED,
        )
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-2",
            status=ActivityStatus.APPLIED,
        )
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-3",
            status=ActivityStatus.APPLIED,
        )
        
        # Get only applied activities
        activities, total = await ActivityService.get_activities(
            db=db,
            user_id=test_user.id,
            status=ActivityStatus.APPLIED,
        )
        
        assert len(activities) == 2
        assert total == 2
        assert all(a.status == ActivityStatus.APPLIED for a in activities)
    
    async def test_get_activity_summary(self, db: AsyncSession, test_user: User):
        """Test getting activity summary."""
        # Create activities with different statuses
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-1",
            status=ActivityStatus.INTERESTED,
        )
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-2",
            status=ActivityStatus.APPLIED,
        )
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-3",
            status=ActivityStatus.APPLIED,
        )
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-4",
            status=ActivityStatus.INTERVIEW,
        )
        
        # Get summary
        summary = await ActivityService.get_activity_summary(
            db=db,
            user_id=test_user.id,
        )
        
        assert summary["interested"] == 1
        assert summary["applied"] == 2
        assert summary["interview"] == 1


@pytest.mark.asyncio
class TestApplyKitEndpoints:
    """Test apply kit API endpoints."""
    
    async def test_generate_apply_kit_endpoint(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test POST /api/v1/applykit/{job_id}/generate endpoint."""
        # This is a placeholder test - the endpoint requires a valid job_id
        # and resume to be set up first. For now, we test that the endpoint
        # returns appropriate error for non-existent job.
        from uuid import uuid4
        fake_job_id = str(uuid4())
        
        response = await client.post(
            f"/api/v1/apply/{fake_job_id}/generate",
            headers=auth_headers
        )
        # Should return 404 for non-existent job
        assert response.status_code in [404, 400, 422]
    
    async def test_get_apply_kit_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test GET /api/v1/applykit/{job_id} endpoint."""
        from uuid import uuid4
        fake_job_id = str(uuid4())
        
        response = await client.get(
            f"/api/v1/apply/{fake_job_id}",
            headers=auth_headers
        )
        # Should return 404 for non-existent job
        assert response.status_code in [404, 400, 422]
    
    async def test_update_apply_kit_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test PUT /api/v1/applykit/{job_id} endpoint."""
        # Placeholder for integration test
        pass
    
    async def test_delete_apply_kit_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test DELETE /api/v1/applykit/{job_id} endpoint."""
        # Placeholder for integration test
        pass
    
    async def test_download_apply_kit_pdf_endpoint(
        self,
        client: AsyncClient,
        test_user: User,
        test_resume: Resume,
        auth_headers: dict,
        db: AsyncSession,
    ):
        """
        Test GET /api/v1/applykit/{job_id}/download/pdf endpoint.
        
        Task 2.5: PDF download endpoint test.
        """
        # Create a job
        job = JobPosting(
            title="Senior Software Engineer",
            company="Tech Corp",
            location="San Francisco, CA",
            description="We are looking for a senior software engineer",
            requirements="5+ years Python experience",
            salary_min=150000,
            salary_max=200000,
            work_type="full-time",
            application_url="https://example.com/apply",
        )
        db.add(job)
        await db.flush()
        await db.refresh(job)
        
        # Generate apply kit
        await ApplyKitService.generate_apply_kit(
            db=db,
            user_id=test_user.id,
            job_id=job.id,
            resume_id=test_resume.id,
        )
        await db.commit()
        
        # Download PDF
        response = await client.get(
            f"/api/v1/apply/applykit/{job.id}/download/pdf",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # Check content type (either PDF or text fallback)
        assert response.headers["content-type"] in ["application/pdf", "text/plain"]
        # Check content disposition header
        assert "attachment" in response.headers["content-disposition"]
        assert "ApplyKit" in response.headers["content-disposition"]
        # Check that we got content
        assert len(response.content) > 0


@pytest.mark.asyncio
class TestActivityEndpoints:
    """Test job activity API endpoints."""
    
    async def test_set_activity_status_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test POST /api/v1/tracker/{job_id} endpoint."""
        # Placeholder for integration test
        pass
    
    async def test_get_activities_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test GET /api/v1/tracker endpoint."""
        # Placeholder for integration test
        pass
    
    async def test_get_activity_summary_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test GET /api/v1/tracker/summary endpoint."""
        # Placeholder for integration test
        pass
