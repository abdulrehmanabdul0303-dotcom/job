"""
User preferences API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db, AsyncSessionLocal
from app.services.auth import get_current_user_from_cookie
from app.services.preferences import PreferencesService
from app.services.preference_detector import PreferenceDetector
from app.services.match_service import MatchComputationService
from app.schemas.preferences import (
    PreferencesCreate,
    PreferencesUpdate,
    PreferencesResponse,
    PreferencesUpdateConfirmation,
)
from app.models.user import User
from app.models.resume import Resume
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Get current user from cookie-based auth."""
    return await get_current_user_from_cookie(request, db)


async def trigger_match_recomputation(user_id: str):
    """Background task to recompute matches after preference change."""
    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"Triggering match recomputation for user {user_id} after preference change")
            stats = await MatchComputationService.compute_matches_for_user(
                db=db,
                user_id=user_id,
                min_score=30,  # Default threshold
            )
            logger.info(f"Match recomputation complete for user {user_id}: {stats['matches_stored']} matches")
        except ValueError as e:
            # User has no resume - skip silently
            logger.debug(f"Skipping match recomputation for user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error recomputing matches for user {user_id}: {e}")


@router.get("/me", response_model=PreferencesResponse)
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's job search preferences.
    
    Returns:
        User preferences or 404 if not set
    """
    preferences_dict = await PreferencesService.get_preferences(db, current_user.id)
    
    if not preferences_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found. Please set your preferences first."
        )
    
    return PreferencesResponse(**preferences_dict)


@router.put("/me", response_model=PreferencesUpdateConfirmation)
async def update_my_preferences(
    preferences_data: PreferencesUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update job search preferences for current user.
    Creates new preferences if they don't exist.
    Automatically triggers match recomputation in background.
    
    Args:
        preferences_data: Updated preferences data
        
    Returns:
        Updated preferences with confirmation message
    """
    preferences_dict = await PreferencesService.update_preferences(
        db, current_user.id, preferences_data
    )
    await db.commit()
    
    # Trigger match recomputation in background
    background_tasks.add_task(trigger_match_recomputation, current_user.id)
    
    return PreferencesUpdateConfirmation(
        message="Preferences updated successfully. Job matches are being recalculated.",
        preferences=PreferencesResponse(**preferences_dict)
    )


@router.post("/auto-detect", response_model=PreferencesUpdateConfirmation)
async def auto_detect_preferences(
    resume_id: str = Query(..., description="Resume ID to analyze"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-detect job preferences from a resume.
    Uses simple rules and pattern matching to infer preferences.
    Automatically triggers match recomputation in background.
    
    Args:
        resume_id: ID of the resume to analyze
        
    Returns:
        Detected preferences with confirmation message
    """
    # Get the resume
    result = await db.execute(
        select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == current_user.id
        )
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    if not resume.raw_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume has not been parsed yet. Please wait for parsing to complete."
        )
    
    # Detect preferences from resume
    detected_prefs = PreferenceDetector.detect_from_resume(resume)
    
    # Update or create preferences
    preferences_dict = await PreferencesService.update_preferences(
        db, current_user.id, detected_prefs
    )
    await db.commit()
    
    # Trigger match recomputation in background
    if background_tasks:
        background_tasks.add_task(trigger_match_recomputation, current_user.id)
    
    return PreferencesUpdateConfirmation(
        message="Preferences auto-detected and saved successfully. Job matches are being recalculated.",
        preferences=PreferencesResponse(**preferences_dict)
    )
