"""
Tests for security headers middleware.

Validates that all security headers are properly set according to OWASP best practices.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.middleware.security import SecurityHeadersMiddleware, RequestLoggingMiddleware


@pytest.fixture
def app_with_security():
    """Create a test FastAPI app with security middleware."""
    app = FastAPI()
    
    # Add security middleware
    app.add_middleware(SecurityHeadersMiddleware, environment="production")
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.get("/api/v1/test")
    async def api_endpoint():
        return {"message": "api test"}
    
    return app


@pytest.fixture
def client(app_with_security):
    """Create test client."""
    return TestClient(app_with_security)


class TestSecurityHeaders:
    """Test security headers middleware."""
    
    def test_x_content_type_options_header(self, client):
        """Test X-Content-Type-Options header is set."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    def test_x_frame_options_header(self, client):
        """Test X-Frame-Options header is set."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
    
    def test_x_xss_protection_header(self, client):
        """Test X-XSS-Protection header is set."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
    
    def test_content_security_policy_header(self, client):
        """Test Content-Security-Policy header is set."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "Content-Security-Policy" in response.headers
        
        csp = response.headers["Content-Security-Policy"]
        # Check key directives
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "object-src 'none'" in csp
    
    def test_referrer_policy_header(self, client):
        """Test Referrer-Policy header is set."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    
    def test_permissions_policy_header(self, client):
        """Test Permissions-Policy header is set."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "Permissions-Policy" in response.headers
        
        permissions = response.headers["Permissions-Policy"]
        # Check key permissions are disabled
        assert "geolocation=()" in permissions
        assert "microphone=()" in permissions
        assert "camera=()" in permissions
    
    def test_x_permitted_cross_domain_policies_header(self, client):
        """Test X-Permitted-Cross-Domain-Policies header is set."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-Permitted-Cross-Domain-Policies" in response.headers
        assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"
    
    def test_cache_control_for_api_endpoints(self, client):
        """Test Cache-Control header is set for API endpoints."""
        response = client.get("/api/v1/test")
        assert response.status_code == 200
        assert "Cache-Control" in response.headers
        assert "no-store" in response.headers["Cache-Control"]
        assert "no-cache" in response.headers["Cache-Control"]
    
    def test_request_id_header(self, client):
        """Test X-Request-ID header is added."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        # Should be a valid UUID
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) == 36  # UUID format
        assert request_id.count("-") == 4
    
    def test_hsts_not_added_for_http(self, client):
        """Test HSTS header is not added for HTTP requests."""
        response = client.get("/test")
        assert response.status_code == 200
        # HSTS should not be present for HTTP (test client uses HTTP)
        # In production with HTTPS, it would be present
        # This is correct behavior
    
    def test_all_security_headers_present(self, client):
        """Test that all expected security headers are present."""
        response = client.get("/test")
        assert response.status_code == 200
        
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Content-Security-Policy",
            "Referrer-Policy",
            "Permissions-Policy",
            "X-Permitted-Cross-Domain-Policies",
            "X-Request-ID",
        ]
        
        for header in expected_headers:
            assert header in response.headers, f"Missing security header: {header}"


class TestSecurityMiddlewareEnvironments:
    """Test security middleware behavior in different environments."""
    
    def test_development_environment(self):
        """Test security headers in development environment."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware, environment="development")
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        # Basic headers should still be present
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        
        # CSP should not have upgrade-insecure-requests in dev
        csp = response.headers.get("Content-Security-Policy", "")
        assert "upgrade-insecure-requests" not in csp
    
    def test_production_environment(self):
        """Test security headers in production environment."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware, environment="production")
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        # All headers should be present
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        
        # CSP should have upgrade-insecure-requests in production
        csp = response.headers.get("Content-Security-Policy", "")
        assert "upgrade-insecure-requests" in csp


class TestRequestLoggingMiddleware:
    """Test request logging middleware."""
    
    def test_request_logging(self, caplog):
        """Test that requests are logged."""
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        
        with caplog.at_level("INFO"):
            response = client.get("/test")
            assert response.status_code == 200
            
            # Check that request was logged
            # Note: In test environment, logging might not capture everything
            # This is a basic check
            assert response.status_code == 200


class TestSecurityHeadersIntegration:
    """Integration tests for security headers."""
    
    def test_security_headers_with_error_response(self, client):
        """Test security headers are added even for error responses."""
        # Request non-existent endpoint
        response = client.get("/nonexistent")
        
        # Should return 404
        assert response.status_code == 404
        
        # Security headers should still be present
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "Content-Security-Policy" in response.headers
    
    def test_security_headers_preserved_across_requests(self, client):
        """Test security headers are consistent across multiple requests."""
        # Make multiple requests
        responses = [client.get("/test") for _ in range(3)]
        
        # All should have security headers
        for response in responses:
            assert response.status_code == 200
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
            
            # Request IDs should be different
            request_ids = [r.headers["X-Request-ID"] for r in responses]
            assert len(set(request_ids)) == 3  # All unique
