"""
Main FastAPI application entry point.
Configures middleware, CORS, routes, and error handlers.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api.v1.router import api_router
from app.core.config import settings, limit_if_enabled
from app.services.scheduler import start_scheduler, stop_scheduler
from app.middleware.security import SecurityHeadersMiddleware, RequestLoggingMiddleware
from app.core.errors import (
    APIError,
    api_error_handler,
    http_exception_handler,
    generic_exception_handler,
    create_error_response,
    get_trace_id,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Initializes database, starts the job scheduler on startup and stops it on shutdown.
    """
    # Startup
    from app.core.database import init_db
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="24/7 Job Agent Platform - Free job automation for everyone",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Add rate limiting state and error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add standardized error handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Add validation error handler
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with trace IDs."""
    from datetime import datetime
    trace_id = get_trace_id(request)
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "detail": exc.errors(),
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
        headers={"X-Request-ID": trace_id}
    )

# Security headers middleware - MUST be added first to apply to all responses
app.add_middleware(
    SecurityHeadersMiddleware,
    environment=settings.ENVIRONMENT
)

# Request logging middleware for security monitoring
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware - allows frontend to communicate with API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware for security - SECURITY P0: No wildcards in production
if settings.ENVIRONMENT == "production":
    # Production: strict host validation
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.TRUSTED_HOSTS
    )
else:
    # Development: allow all for convenience
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
@limit_if_enabled(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def root(request: Request):
    """Root endpoint - API information."""
    return {
        "message": "JobPilot AI API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "status": "operational"
    }


@app.get("/docs")
async def docs_redirect():
    """Redirect /docs to /api/v1/docs for convenience."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"{settings.API_V1_STR}/docs")


@app.get("/health")
@limit_if_enabled("120/minute")  # Higher limit for health checks
async def health_check(request: Request):
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "jobpilot-api",
        "version": settings.VERSION
    }


@app.get("/api/v1/scheduler/health")
@limit_if_enabled("120/minute")
async def scheduler_health_check(request: Request):
    """
    Scheduler health check endpoint.
    
    Returns health status of all background jobs including:
    - Overall health status
    - Individual job statuses
    - Recent failures
    - Execution metrics
    """
    from app.services.scheduler_monitor import get_monitor
    
    monitor = get_monitor()
    
    # Get overall health summary
    health_summary = monitor.get_health_summary()
    
    # Get detailed status for all jobs
    jobs_status = monitor.get_all_jobs_status()
    
    # Get recent failures
    recent_failures = monitor.get_recent_failures(limit=5)
    
    return {
        "status": "healthy" if health_summary["is_healthy"] else "unhealthy",
        "service": "jobpilot-scheduler",
        "summary": health_summary,
        "jobs": jobs_status,
        "recent_failures": recent_failures,
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler with trace ID."""
    trace_id = get_trace_id(request)
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": "The requested resource was not found",
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
        headers={"X-Request-ID": trace_id}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 handler with trace ID."""
    trace_id = get_trace_id(request)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later.",
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
        headers={"X-Request-ID": trace_id}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
