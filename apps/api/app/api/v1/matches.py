"""
Job matches API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.auth import get_current_user_from_cookie
from app.services.match_service import MatchDatabaseService, MatchComputationService
from app.schemas.match import (
    JobMatchResponse,
    JobMatchListResponse,
    RecomputeMatchesRequest,
    RecomputeMatchesResponse,
    MatchSuggestionsResponse,
    NoMatchesSuggestion,
)
from app.models.user import User
import math
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Get current user from cookie-based auth."""
    return await get_current_user_from_cookie(request, db)


@router.post("/matches/recompute", response_model=RecomputeMatchesResponse)
async def recompute_matches(
    request: RecomputeMatchesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Recompute job matches for current user.
    
    This endpoint:
    1. Clears existing matches for the user
    2. Computes matches against all active jobs
    3. Stores matches above the minimum score threshold
    
    Args:
        request: Recompute request with optional resume_id and min_score
        
    Returns:
        Statistics about the recomputation
    """
    try:
        stats = await MatchComputationService.compute_matches_for_user(
            db=db,
            user_id=current_user.id,
            resume_id=request.resume_id,
            min_score=request.min_score,
        )
        
        return RecomputeMatchesResponse(**stats)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error recomputing matches for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error recomputing matches"
        )


@router.get("/matches", response_model=JobMatchListResponse)
async def get_matches(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    min_score: float = Query(0, ge=0, le=100, description="Minimum match score filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get job matches for current user with pagination.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of matches per page
        min_score: Filter matches by minimum score
        
    Returns:
        Paginated list of job matches
    """
    try:
        matches, total = await MatchDatabaseService.get_matches_for_user(
            db=db,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            min_score=min_score,
        )
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return JobMatchListResponse(
            matches=matches,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
        
    except Exception as e:
        logger.error(f"Error fetching matches for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching matches"
        )


@router.get("/matches/{match_id}", response_model=JobMatchResponse)
async def get_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific job match by ID.
    
    Args:
        match_id: Match ID
        
    Returns:
        Job match details
    """
    try:
        match = await MatchDatabaseService.get_match(db, match_id)
        
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found"
            )
        
        # Verify ownership
        if match.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this match"
            )
        
        return match
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching match {match_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching match"
        )


@router.get("/matches/suggestions", response_model=MatchSuggestionsResponse)
async def get_match_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get suggestions for improving job matches.
    
    Returns suggestions when user has no or few matches,
    helping them improve their profile, resume, or preferences.
    
    Returns:
        Suggestions with match count and actionable items
    """
    try:
        # Get current match count
        matches, total = await MatchDatabaseService.get_matches_for_user(
            db=db,
            user_id=current_user.id,
            page=1,
            page_size=1,
            min_score=0,
        )
        
        # Generate suggestions
        suggestions_data = await MatchComputationService.generate_suggestions(
            db=db,
            user_id=current_user.id,
            match_count=total,
        )
        
        suggestions = [NoMatchesSuggestion(**s) for s in suggestions_data]
        
        if total == 0:
            message = "No matches found. Follow the suggestions below to improve your results."
        elif total < 5:
            message = f"Only {total} matches found. Consider the suggestions below for more opportunities."
        else:
            message = f"You have {total} matches. Keep your profile updated for the best results."
        
        return MatchSuggestionsResponse(
            has_matches=total > 0,
            match_count=total,
            suggestions=suggestions,
            message=message,
        )
        
    except Exception as e:
        logger.error(f"Error generating suggestions for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating suggestions"
        )
