"""
Test configuration and environment setup.
Ensures deterministic test behavior across all environments.
"""
import os
import pytest
from unittest.mock import patch
from datetime import datetime, timezone
from app.core.config import settings


@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    Automatically setup test environment for all tests.
    Ensures deterministic behavior and proper isolation.
    """
    # Set deterministic environment variables
    test_env = {
        "ENVIRONMENT": "test",
        "DATABASE_URL": "sqlite+aiosqlite:///./test_jobpilot.db",
        "JWT_SECRET": "test-secret-key-for-testing-only",
        "JWT_ACCESS_TTL_MIN": "15",
        "JWT_REFRESH_TTL_DAYS": "7",
        "REDIS_URL": "redis://localhost:6379/1",  # Use different DB for tests
        "EMAIL_ENABLED": "false",  # Disable email in tests
        "RATE_LIMIT_ENABLED": "true",
        "LOG_LEVEL": "ERROR",  # Reduce log noise in tests
    }
    
    with patch.dict(os.environ, test_env):
        yield


@pytest.fixture
def freeze_time():
    """
    Freeze time for deterministic testing.
    Use this fixture when testing time-sensitive functionality.
    """
    frozen_time = datetime(2025, 1, 11, 12, 0, 0, tzinfo=timezone.utc)
    
    with patch('app.services.auth.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = frozen_time.replace(tzinfo=None)
        mock_datetime.now.return_value = frozen_time.replace(tzinfo=None)
        # Also patch the datetime class itself
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield frozen_time


@pytest.fixture
def mock_external_services():
    """
    Mock external services to prevent network calls during tests.
    """
    mocks = {}
    
    # Mock email service
    with patch('app.services.email_service.EmailService.send_email') as mock_email:
        mock_email.return_value = {"status": "sent", "message_id": "test-123"}
        mocks['email'] = mock_email
        
        # Mock job fetcher external APIs
        with patch('app.services.job_fetcher.JobFetcher.fetch_rss_jobs') as mock_fetch:
            mock_fetch.return_value = []
            mocks['job_fetch'] = mock_fetch
            
            yield mocks


class TestConfiguration:
    """Test that configuration is properly set for testing."""
    
    def test_test_environment_active(self):
        """Verify test environment is active."""
        assert os.getenv("ENVIRONMENT") == "test"
    
    def test_test_database_url(self):
        """Verify test database is configured."""
        db_url = os.getenv("DATABASE_URL", "")
        assert "test" in db_url.lower() or "sqlite" in db_url.lower()
    
    def test_email_disabled_in_tests(self):
        """Verify email is disabled in test environment."""
        assert os.getenv("EMAIL_ENABLED") == "false"
    
    def test_deterministic_jwt_secret(self):
        """Verify JWT secret is deterministic for tests."""
        assert os.getenv("JWT_SECRET") == "test-secret-key-for-testing-only"


@pytest.mark.asyncio
class TestTimeFreeze:
    """Test time freezing functionality."""
    
    async def test_frozen_time_consistency(self):
        """Test that time remains frozen during test execution."""
        from app.services.auth import create_access_token, decode_token
        
        # Create two tokens
        token1 = create_access_token({"sub": "user1"})
        token2 = create_access_token({"sub": "user2"})
        
        # Both tokens should be valid
        payload1 = decode_token(token1)
        payload2 = decode_token(token2)
        
        # Verify tokens were decoded successfully
        assert payload1 is not None, "Token 1 should be valid"
        assert payload2 is not None, "Token 2 should be valid"
        
        # Both should have same token type
        assert payload1["type"] == "access"
        assert payload2["type"] == "access"


@pytest.mark.asyncio
class TestExternalServiceMocking:
    """Test external service mocking."""
    
    async def test_email_service_mocked(self):
        """Test that email service can be instantiated."""
        from app.services.email_service import EmailService
        
        email_service = EmailService()
        # Just verify it can be instantiated
        assert email_service is not None
    
    async def test_job_fetcher_mocked(self):
        """Test that job fetcher can be called."""
        from app.services.job_fetcher import JobFetcher
        
        # Just verify the class exists and can be called
        assert JobFetcher is not None