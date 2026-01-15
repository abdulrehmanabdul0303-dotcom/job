"""
Tests for standardized error handling.

Verifies that all errors return consistent format with trace IDs.
"""
import pytest
from fastapi import status
from httpx import AsyncClient
from app.core.errors import (
    APIError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ServiceError,
    ExternalServiceError,
)


class TestErrorClasses:
    """Test custom error classes."""
    
    def test_api_error_basic(self):
        """Test basic APIError creation."""
        error = APIError("Test error", status_code=400)
        
        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.trace_id is not None
        assert error.timestamp is not None
    
    def test_api_error_with_detail(self):
        """Test APIError with detail."""
        error = APIError(
            "User-friendly message",
            detail="Technical detail for logging",
            status_code=500
        )
        
        assert error.message == "User-friendly message"
        assert error.detail == "Technical detail for logging"
    
    def test_api_error_to_dict(self):
        """Test APIError to_dict conversion."""
        error = APIError("Test error", status_code=400, extra_field="value")
        error_dict = error.to_dict()
        
        assert error_dict["error"] == "Test error"
        assert error_dict["status_code"] == 400
        assert "trace_id" in error_dict
        assert "timestamp" in error_dict
        assert error_dict["context"]["extra_field"] == "value"
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid email", field="email")
        
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.message == "Invalid email"
        assert error.context["field"] == "email"
    
    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid credentials")
        
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.message == "Invalid credentials"
    
    def test_authorization_error(self):
        """Test AuthorizationError."""
        error = AuthorizationError("Insufficient permissions")
        
        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert error.message == "Insufficient permissions"
    
    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError("User", resource_id="123")
        
        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert "User" in error.message
        assert "123" in error.message
    
    def test_conflict_error(self):
        """Test ConflictError."""
        error = ConflictError("Email already exists", resource="User")
        
        assert error.status_code == status.HTTP_409_CONFLICT
        assert error.message == "Email already exists"
    
    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError(retry_after=60)
        
        assert error.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert error.context["retry_after"] == 60
    
    def test_service_error(self):
        """Test ServiceError."""
        error = ServiceError("Database connection failed", service="database")
        
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert error.context["service"] == "database"
    
    def test_external_service_error(self):
        """Test ExternalServiceError."""
        error = ExternalServiceError("OpenAI", "API timeout")
        
        assert error.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "OpenAI" in error.message


@pytest.mark.asyncio
class TestErrorResponses:
    """Test error response format in API."""
    
    async def test_404_error_format(self, client: AsyncClient):
        """Test 404 error returns standardized format."""
        response = await client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        
        # Check standardized format
        assert "error" in data
        assert "trace_id" in data
        assert "timestamp" in data
        
        # Check trace ID in headers
        assert "X-Request-ID" in response.headers
    
    async def test_validation_error_format(self, client: AsyncClient):
        """Test validation error returns standardized format."""
        # Send invalid data to trigger validation error
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "invalid-email"}  # Missing password
        )
        
        assert response.status_code == 422
        data = response.json()
        
        # Check standardized format
        assert "error" in data
        assert "detail" in data
        assert "trace_id" in data
        assert "timestamp" in data
    
    async def test_authentication_error_format(self, client: AsyncClient):
        """Test authentication error returns standardized format."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@example.com", "password": "wrong"}
        )
        
        assert response.status_code == 401
        data = response.json()
        
        # Check standardized format
        assert "error" in data
        assert "trace_id" in data
        assert "timestamp" in data
    
    async def test_trace_id_consistency(self, client: AsyncClient):
        """Test trace ID is consistent between header and body."""
        response = await client.get("/api/v1/nonexistent")
        
        header_trace_id = response.headers.get("X-Request-ID")
        body_trace_id = response.json().get("trace_id")
        
        assert header_trace_id is not None
        assert body_trace_id is not None
        assert header_trace_id == body_trace_id
    
    async def test_custom_trace_id_preserved(self, client: AsyncClient):
        """Test custom trace ID from request is preserved."""
        custom_trace_id = "custom-trace-123"
        
        response = await client.get(
            "/api/v1/nonexistent",
            headers={"X-Request-ID": custom_trace_id}
        )
        
        # Trace ID should be preserved
        assert response.headers.get("X-Request-ID") == custom_trace_id
        assert response.json().get("trace_id") == custom_trace_id


@pytest.mark.asyncio
class TestErrorLogging:
    """Test error logging functionality."""
    
    def test_error_logging(self, caplog):
        """Test that errors are logged with trace ID."""
        import logging
        caplog.set_level(logging.ERROR)
        
        error = APIError("Test error", status_code=500)
        error.log()
        
        # Check log contains trace ID
        assert error.trace_id in caplog.text
        assert "Test error" in caplog.text
    
    def test_error_logging_levels(self, caplog):
        """Test different log levels."""
        import logging
        
        error = APIError("Warning error", status_code=400)
        
        # Log as warning
        caplog.set_level(logging.WARNING)
        error.log(level="warning")
        
        assert "Warning error" in caplog.text


class TestErrorHelpers:
    """Test error helper functions."""
    
    def test_raise_validation_error(self):
        """Test raise_validation_error helper."""
        from app.core.errors import raise_validation_error
        
        with pytest.raises(ValidationError) as exc_info:
            raise_validation_error("Invalid input", field="username")
        
        assert exc_info.value.message == "Invalid input"
        assert exc_info.value.context["field"] == "username"
    
    def test_raise_not_found(self):
        """Test raise_not_found helper."""
        from app.core.errors import raise_not_found
        
        with pytest.raises(NotFoundError) as exc_info:
            raise_not_found("User", resource_id="123")
        
        assert "User" in exc_info.value.message
        assert "123" in exc_info.value.message
    
    def test_raise_authentication_error(self):
        """Test raise_authentication_error helper."""
        from app.core.errors import raise_authentication_error
        
        with pytest.raises(AuthenticationError) as exc_info:
            raise_authentication_error("Invalid token")
        
        assert exc_info.value.message == "Invalid token"
    
    def test_raise_authorization_error(self):
        """Test raise_authorization_error helper."""
        from app.core.errors import raise_authorization_error
        
        with pytest.raises(AuthorizationError) as exc_info:
            raise_authorization_error("Insufficient permissions")
        
        assert exc_info.value.message == "Insufficient permissions"
    
    def test_raise_service_error(self):
        """Test raise_service_error helper."""
        from app.core.errors import raise_service_error
        
        with pytest.raises(ServiceError) as exc_info:
            raise_service_error("Database error", service="postgres")
        
        assert exc_info.value.message == "Database error"
        assert exc_info.value.context["service"] == "postgres"

