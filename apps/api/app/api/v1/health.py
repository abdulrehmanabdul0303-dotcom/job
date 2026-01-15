"""
Health check endpoints for monitoring and status verification.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
import redis.asyncio as redis

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns service status without dependencies.
    """
    return {
        "status": "healthy",
        "service": "jobpilot-api",
        "version": settings.VERSION
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check including database and Redis connectivity.
    """
    health_status = {
        "status": "healthy",
        "service": "jobpilot-api",
        "version": settings.VERSION,
        "checks": {}
    }
    
    # Check database connection
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
    
    # Check Redis connection (handle empty REDIS_URL)
    if not settings.REDIS_URL:
        health_status["checks"]["redis"] = "disabled"
        return health_status
    
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
    
    return health_status
