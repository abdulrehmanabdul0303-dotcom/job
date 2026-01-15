"""
Standardized Error Handling

Provides consistent error responses with trace IDs, user-friendly messages,
and proper logging for all API errors.

Features:
- Consistent error format across all endpoints
- Automatic trace ID generation and logging
- User-friendly error messages
- Detailed error logging for debugging
- HTTP status code mapping
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class APIError(Exception):
    """
    Base exception class for API errors.
    
    Provides consistent error handling with trace IDs and user-friendly messages.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[str] = None,
        trace_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize API error.
        
        Args:
            message: User-friendly error message
            status_code: HTTP status code
            detail: Detailed error information (for logging)
            trace_id: Request trace ID
            **kwargs: Additional error context
        """
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        self.trace_id = trace_id or str(uuid.uuid4())
        self.context = kwargs
        self.timestamp = datetime.utcnow().isoformat()
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary for JSON response.
        
        Returns:
            Dictionary with error details
        """
        error_dict = {
            "error": self.message,
            "status_code": self.status_code,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
        }
        
        # Add detail if different from message
        if self.detail != self.message:
            error_dict["detail"] = self.detail
        
        # Add additional context
        if self.context:
            error_dict["context"] = self.context
        
        return error_dict
    
    def log(self, level: str = "error") -> None:
        """
        Log error with appropriate level.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
        """
        log_func = getattr(logger, level, logger.error)
        log_func(
            f"API Error: {self.message} trace_id={self.trace_id}",
            extra={
                "trace_id": self.trace_id,
                "status_code": self.status_code,
                "detail": self.detail,
                "context": self.context,
            }
        )


# Specific error classes for common scenarios

class ValidationError(APIError):
    """Error for validation failures."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            field=field,
            **kwargs
        )


class AuthenticationError(APIError):
    """Error for authentication failures."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            **kwargs
        )


class AuthorizationError(APIError):
    """Error for authorization failures."""
    
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            **kwargs
        )


class NotFoundError(APIError):
    """Error for resource not found."""
    
    def __init__(self, resource: str, resource_id: Optional[str] = None, **kwargs):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with ID '{resource_id}' not found"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            resource=resource,
            resource_id=resource_id,
            **kwargs
        )


class ConflictError(APIError):
    """Error for resource conflicts."""
    
    def __init__(self, message: str, resource: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            resource=resource,
            **kwargs
        )


class RateLimitError(APIError):
    """Error for rate limit exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            retry_after=retry_after,
            **kwargs
        )


class ServiceError(APIError):
    """Error for internal service failures."""
    
    def __init__(
        self,
        message: str = "An internal error occurred. Please try again later.",
        service: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            service=service,
            **kwargs
        )


class ExternalServiceError(APIError):
    """Error for external service failures."""
    
    def __init__(
        self,
        service: str,
        message: str = "External service unavailable",
        **kwargs
    ):
        super().__init__(
            message=f"{service}: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            service=service,
            **kwargs
        )


# Error response helpers

def get_trace_id(request: Request) -> str:
    """
    Get or generate trace ID for request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Trace ID string
    """
    # Try to get from request headers
    trace_id = request.headers.get("X-Request-ID")
    
    # Try to get from request state (set by middleware)
    if not trace_id and hasattr(request.state, "trace_id"):
        trace_id = request.state.trace_id
    
    # Generate new if not found
    if not trace_id:
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
    
    return trace_id


def create_error_response(
    request: Request,
    error: Exception,
    status_code: Optional[int] = None,
) -> JSONResponse:
    """
    Create standardized error response.
    
    Args:
        request: FastAPI request object
        error: Exception that occurred
        status_code: HTTP status code (optional, inferred from error)
        
    Returns:
        JSONResponse with error details
    """
    trace_id = get_trace_id(request)
    
    # Handle APIError instances
    if isinstance(error, APIError):
        error.trace_id = trace_id
        error.log()
        return JSONResponse(
            status_code=error.status_code,
            content=error.to_dict(),
            headers={"X-Request-ID": trace_id}
        )
    
    # Handle HTTPException
    if isinstance(error, HTTPException):
        error_dict = {
            "error": error.detail,
            "status_code": error.status_code,
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Log error
        logger.error(
            f"HTTP Error: {error.detail}",
            extra={
                "trace_id": trace_id,
                "status_code": error.status_code,
            }
        )
        
        return JSONResponse(
            status_code=error.status_code,
            content=error_dict,
            headers={"X-Request-ID": trace_id}
        )
    
    # Handle generic exceptions
    error_dict = {
        "error": "An unexpected error occurred. Please try again later.",
        "status_code": status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
        "trace_id": trace_id,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Log error with full details
    logger.error(
        f"Unexpected error: {type(error).__name__}: {str(error)}",
        extra={
            "trace_id": trace_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=error_dict["status_code"],
        content=error_dict,
        headers={"X-Request-ID": trace_id}
    )


# Exception handlers for FastAPI

async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """
    Handle APIError exceptions.
    
    Args:
        request: FastAPI request
        exc: APIError exception
        
    Returns:
        JSON error response
    """
    return create_error_response(request, exc)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTPException exceptions.
    
    Args:
        request: FastAPI request
        exc: HTTPException
        
    Returns:
        JSON error response
    """
    return create_error_response(request, exc)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle generic exceptions.
    
    Args:
        request: FastAPI request
        exc: Exception
        
    Returns:
        JSON error response
    """
    return create_error_response(request, exc)


# Utility functions

def raise_validation_error(message: str, field: Optional[str] = None, **kwargs):
    """
    Raise a validation error.
    
    Args:
        message: Error message
        field: Field name that failed validation
        **kwargs: Additional context
    """
    raise ValidationError(message, field=field, **kwargs)


def raise_not_found(resource: str, resource_id: Optional[str] = None, **kwargs):
    """
    Raise a not found error.
    
    Args:
        resource: Resource type (e.g., "User", "Job")
        resource_id: Resource ID
        **kwargs: Additional context
    """
    raise NotFoundError(resource, resource_id=resource_id, **kwargs)


def raise_authentication_error(message: str = "Authentication failed", **kwargs):
    """
    Raise an authentication error.
    
    Args:
        message: Error message
        **kwargs: Additional context
    """
    raise AuthenticationError(message, **kwargs)


def raise_authorization_error(message: str = "Access denied", **kwargs):
    """
    Raise an authorization error.
    
    Args:
        message: Error message
        **kwargs: Additional context
    """
    raise AuthorizationError(message, **kwargs)


def raise_service_error(
    message: str = "An internal error occurred",
    service: Optional[str] = None,
    **kwargs
):
    """
    Raise a service error.
    
    Args:
        message: Error message
        service: Service name
        **kwargs: Additional context
    """
    raise ServiceError(message, service=service, **kwargs)

