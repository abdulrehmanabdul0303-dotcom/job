"""
Main API router that combines all v1 endpoints.
"""
from fastapi import APIRouter
from app.api.v1 import auth, health, resume, preferences, jobs, matches, apply, notifications, ai_resume, ai_interview, ai_skills

api_router = APIRouter()

# Include health check routes
api_router.include_router(
    health.router,
    tags=["health"]
)

# Include authentication routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

# Include resume routes
api_router.include_router(
    resume.router,
    prefix="/resume",
    tags=["resume"]
)

# Include AI resume routes
api_router.include_router(
    ai_resume.router,
    prefix="/ai",
    tags=["ai-resume"]
)

# Include AI interview routes
api_router.include_router(
    ai_interview.router,
    prefix="/ai",
    tags=["ai-interview"]
)

# Include AI skill analysis routes
api_router.include_router(
    ai_skills.router,
    prefix="/ai/skills",
    tags=["ai-skills"]
)

# Include preferences routes
api_router.include_router(
    preferences.router,
    prefix="/preferences",
    tags=["preferences"]
)

# Include jobs routes
api_router.include_router(
    jobs.router,
    tags=["jobs"]
)

# Include matches routes
api_router.include_router(
    matches.router,
    tags=["matches"]
)

# Include apply routes
api_router.include_router(
    apply.router,
    tags=["apply"]
)

# Include notifications routes
api_router.include_router(
    notifications.router,
    tags=["notifications"]
)
