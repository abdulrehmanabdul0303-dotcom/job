"""
Security Headers Middleware

Adds comprehensive security headers to all HTTP responses following OWASP best practices.
Protects against common web vulnerabilities including XSS, clickjacking, MIME sniffing, etc.

References:
- OWASP Secure Headers Project: https://owasp.org/www-project-secure-headers/
- Mozilla Observatory: https://observatory.mozilla.org/
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking attacks
    - X-XSS-Protection: Enables browser XSS protection
    - Strict-Transport-Security: Enforces HTTPS (production only)
    - Content-Security-Policy: Controls resource loading
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    - X-Permitted-Cross-Domain-Policies: Controls cross-domain policies
    """
    
    def __init__(self, app, environment: str = "development"):
        """
        Initialize security headers middleware.
        
        Args:
            app: FastAPI application instance
            environment: Environment name (development, staging, production)
        """
        super().__init__(app)
        self.environment = environment
        self.is_production = environment == "production"
        
        logger.info(f"Security headers middleware initialized for {environment} environment")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers to response.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response with security headers added
        """
        # Process request
        response: Response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(request, response)
        
        return response
    
    def _add_security_headers(self, request: Request, response: Response) -> None:
        """
        Add all security headers to the response.
        
        Args:
            request: HTTP request (used for conditional headers)
            response: HTTP response to modify
        """
        # 1. X-Content-Type-Options: Prevent MIME type sniffing
        # Prevents browsers from interpreting files as a different MIME type
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # 2. X-Frame-Options: Prevent clickjacking
        # Prevents the page from being embedded in iframes
        response.headers["X-Frame-Options"] = "DENY"
        
        # 3. X-XSS-Protection: Enable browser XSS filter
        # Legacy header but still useful for older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # 4. Strict-Transport-Security (HSTS): Enforce HTTPS
        # Only add in production with HTTPS
        if self.is_production and request.url.scheme == "https":
            # max-age=31536000 = 1 year
            # includeSubDomains = apply to all subdomains
            # preload = allow inclusion in browser HSTS preload lists
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # 5. Content-Security-Policy (CSP): Control resource loading
        # Strict policy to prevent XSS and data injection attacks
        csp_directives = [
            "default-src 'self'",  # Only load resources from same origin by default
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Allow scripts (relaxed for API docs)
            "style-src 'self' 'unsafe-inline'",  # Allow styles (needed for API docs)
            "img-src 'self' data: https:",  # Allow images from same origin, data URIs, and HTTPS
            "font-src 'self' data:",  # Allow fonts from same origin and data URIs
            "connect-src 'self' https:",  # Allow API calls to same origin and HTTPS
            "frame-ancestors 'none'",  # Don't allow embedding (same as X-Frame-Options)
            "base-uri 'self'",  # Restrict base tag URLs
            "form-action 'self'",  # Restrict form submissions
            "object-src 'none'",  # Block plugins (Flash, Java, etc.)
            "upgrade-insecure-requests",  # Upgrade HTTP to HTTPS (production only)
        ]
        
        # Remove upgrade-insecure-requests in development
        if not self.is_production:
            csp_directives = [d for d in csp_directives if not d.startswith("upgrade-insecure-requests")]
        
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # 6. Referrer-Policy: Control referrer information
        # strict-origin-when-cross-origin = send full URL for same-origin, only origin for cross-origin
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 7. Permissions-Policy: Control browser features
        # Disable potentially dangerous features
        permissions = [
            "geolocation=()",  # Disable geolocation
            "microphone=()",  # Disable microphone
            "camera=()",  # Disable camera
            "payment=()",  # Disable payment API
            "usb=()",  # Disable USB
            "magnetometer=()",  # Disable magnetometer
            "gyroscope=()",  # Disable gyroscope
            "accelerometer=()",  # Disable accelerometer
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)
        
        # 8. X-Permitted-Cross-Domain-Policies: Control cross-domain policies
        # Prevents Adobe Flash and PDF from loading data cross-domain
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        # 9. Cache-Control: Control caching behavior
        # For API responses, generally don't cache
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # 10. X-Request-ID: Add request ID for tracing (if not already present)
        if "X-Request-ID" not in response.headers:
            # Generate or use existing request ID
            request_id = request.headers.get("X-Request-ID", self._generate_request_id())
            response.headers["X-Request-ID"] = request_id
    
    def _generate_request_id(self) -> str:
        """
        Generate a unique request ID for tracing.
        
        Returns:
            Unique request ID string
        """
        import uuid
        return str(uuid.uuid4())


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests for security monitoring.
    
    Logs:
    - Request method and path
    - Client IP address
    - Response status code
    - Request duration
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request details and process request.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from handler
        """
        import time
        
        # Record start time
        start_time = time.time()
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path} "
            f"from {client_ip} "
            f"-> {response.status_code} "
            f"({duration:.3f}s)"
        )
        
        return response


class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add rate limit information to responses.
    
    Headers added:
    - X-RateLimit-Limit: Maximum requests allowed
    - X-RateLimit-Remaining: Requests remaining
    - X-RateLimit-Reset: Time when limit resets
    """
    
    def __init__(self, app, rate_limit_per_minute: int = 60):
        """
        Initialize rate limit headers middleware.
        
        Args:
            app: FastAPI application instance
            rate_limit_per_minute: Rate limit per minute
        """
        super().__init__(app)
        self.rate_limit = rate_limit_per_minute
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add rate limit headers to response.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response with rate limit headers
        """
        response = await call_next(request)
        
        # Add rate limit headers
        # Note: These are informational. Actual rate limiting is done by slowapi
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        
        # These would need to be calculated based on actual rate limiting state
        # For now, just add the limit header
        
        return response
