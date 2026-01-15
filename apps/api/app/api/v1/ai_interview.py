"""
AI Interview Preparation API endpoints.
Handles interview question generation, coaching, and preparation kits.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.ai.interview_prep import InterviewPreparationEngine
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response

class InterviewPrepRequest(BaseModel):
    """Request model for interview preparation generation."""
    difficulty_level: str = Field(
        default="intermediate",
        description="Difficulty level: beginner, intermediate, advanced"
    )
    include_company_research: bool = Field(
        default=True,
        description="Whether to include company research and insights"
    )

class InterviewKitResponse(BaseModel):
    """Response model for interview preparation kit."""
    id: str
    job_id: str
    questions: List[dict]
    talking_points: List[str]
    company_insights: dict
    star_examples: List[dict]
    preparation_checklist: List[str]
    difficulty_level: str
    estimated_prep_time: int
    created_at: str
    updated_at: Optional[str]

class AnswerAnalysisRequest(BaseModel):
    """Request model for answer analysis."""
    question_id: str = Field(description="ID of the interview question")
    answer: str = Field(description="User's answer to analyze")

class AnswerAnalysisResponse(BaseModel):
    """Response model for answer analysis."""
    question_id: str
    score: float
    feedback: dict
    suggestions: List[str]
    strengths: List[str]

class CompanyInsightsResponse(BaseModel):
    """Response model for company insights."""
    culture: dict
    values: List[str]
    interview_process: dict
    talking_points: List[str]
    questions_to_ask: List[str]

# Initialize the interview preparation engine
interview_engine = InterviewPreparationEngine()


@router.post("/interview/prepare/{job_id}", response_model=InterviewKitResponse)
async def generate_interview_preparation(
    job_id: str,
    request: InterviewPrepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate comprehensive interview preparation kit for a specific job.
    
    This endpoint creates a personalized interview preparation kit including:
    - Role-specific interview questions (technical, behavioral, company-specific)
    - Personalized talking points based on user's experience
    - STAR method examples from user's background
    - Company research and culture insights
    - Preparation checklist and timeline
    """
    try:
        logger.info(f"Generating interview preparation for user {current_user.id}, job {job_id}")
        
        # Validate difficulty level
        valid_levels = ["beginner", "intermediate", "advanced"]
        if request.difficulty_level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid difficulty level. Must be one of: {', '.join(valid_levels)}"
            )
        
        # Generate the interview kit
        kit_data = await interview_engine.generate_interview_kit(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
            difficulty_level=request.difficulty_level,
            include_company_research=request.include_company_research
        )
        
        logger.info(f"Interview kit generated successfully: {kit_data['id']}")
        return InterviewKitResponse(**kit_data)
        
    except ValueError as e:
        logger.error(f"ValueError in interview preparation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating interview preparation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate interview preparation. Please try again."
        )


@router.get("/interview/prepare/{job_id}", response_model=Optional[InterviewKitResponse])
async def get_interview_preparation(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get existing interview preparation kit for a specific job.
    
    Returns the most recent interview preparation kit created for the specified job,
    or null if no kit exists.
    """
    try:
        logger.info(f"Retrieving interview preparation for user {current_user.id}, job {job_id}")
        
        kit_data = await interview_engine.get_interview_kit(
            db=db,
            user_id=current_user.id,
            job_id=job_id
        )
        
        if kit_data:
            return InterviewKitResponse(**kit_data)
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving interview preparation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve interview preparation."
        )


@router.get("/interview/kits", response_model=List[InterviewKitResponse])
async def list_interview_kits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all interview preparation kits for the current user.
    
    Returns a list of all interview kits created by the user,
    ordered by creation date (most recent first).
    """
    try:
        logger.info(f"Listing interview kits for user {current_user.id}")
        
        from sqlalchemy import select
        from app.models.ai_interview import InterviewKit
        
        result = await db.execute(
            select(InterviewKit)
            .where(
                InterviewKit.user_id == current_user.id,
                InterviewKit.is_active == True
            )
            .order_by(InterviewKit.created_at.desc())
        )
        kits = result.scalars().all()
        
        kit_list = []
        for kit in kits:
            kit_data = await interview_engine._format_kit_response(kit)
            kit_list.append(InterviewKitResponse(**kit_data))
        
        logger.info(f"Found {len(kit_list)} interview kits")
        return kit_list
        
    except Exception as e:
        logger.error(f"Error listing interview kits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve interview kits."
        )


@router.post("/interview/analyze-answer", response_model=AnswerAnalysisResponse)
async def analyze_interview_answer(
    request: AnswerAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze user's practice answer and provide AI-powered feedback.
    
    This endpoint analyzes the user's answer to an interview question and provides:
    - Numerical score (0-100)
    - Detailed feedback on content and structure
    - Specific suggestions for improvement
    - Identified strengths in the answer
    """
    try:
        logger.info(f"Analyzing answer for user {current_user.id}, question {request.question_id}")
        
        if not request.answer.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Answer cannot be empty"
            )
        
        # Analyze the answer
        analysis_data = await interview_engine.analyze_answer(
            db=db,
            user_id=current_user.id,
            question_id=request.question_id,
            user_answer=request.answer
        )
        
        logger.info(f"Answer analyzed successfully, score: {analysis_data['score']}")
        return AnswerAnalysisResponse(**analysis_data)
        
    except ValueError as e:
        logger.error(f"ValueError in answer analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error analyzing answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze answer. Please try again."
        )


@router.get("/interview/company-insights/{company_name}", response_model=CompanyInsightsResponse)
async def get_company_insights(
    company_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get company research insights and culture information.
    
    Provides comprehensive company insights including:
    - Company culture and values
    - Interview process information
    - Key talking points for the interview
    - Thoughtful questions to ask the interviewer
    """
    try:
        logger.info(f"Getting company insights for {company_name}")
        
        if not company_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name cannot be empty"
            )
        
        # Get company insights
        insights_data = await interview_engine.get_company_insights(
            db=db,
            company_name=company_name.strip()
        )
        
        logger.info(f"Company insights retrieved for {company_name}")
        return CompanyInsightsResponse(**insights_data)
        
    except Exception as e:
        logger.error(f"Error getting company insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve company insights."
        )


@router.get("/interview/questions/{kit_id}")
async def get_interview_questions(
    kit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed interview questions for a specific kit.
    
    Returns all questions in the kit with detailed information including:
    - Question text and category
    - Suggested answer approaches
    - Key points to cover
    - Follow-up questions to expect
    - User's practice answers and feedback (if any)
    """
    try:
        logger.info(f"Getting interview questions for kit {kit_id}")
        
        from sqlalchemy import select
        from app.models.ai_interview import InterviewQuestion
        
        result = await db.execute(
            select(InterviewQuestion)
            .where(
                InterviewQuestion.kit_id == kit_id,
                InterviewQuestion.user_id == current_user.id
            )
            .order_by(InterviewQuestion.order_index)
        )
        questions = result.scalars().all()
        
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview kit not found or no questions available"
            )
        
        question_list = []
        for q in questions:
            question_data = {
                "id": q.id,
                "text": q.question_text,
                "category": q.category,
                "difficulty": q.difficulty,
                "suggested_answer": json.loads(q.suggested_answer) if q.suggested_answer else {},
                "key_points": json.loads(q.key_points) if q.key_points else [],
                "follow_up_questions": json.loads(q.follow_up_questions) if q.follow_up_questions else [],
                "user_answer": q.user_answer,
                "ai_feedback": json.loads(q.ai_feedback) if q.ai_feedback else {},
                "feedback_score": q.feedback_score,
                "is_practiced": q.is_practiced,
                "order_index": q.order_index
            }
            question_list.append(question_data)
        
        logger.info(f"Found {len(question_list)} questions for kit {kit_id}")
        return {
            "kit_id": kit_id,
            "total_questions": len(question_list),
            "questions": question_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interview questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve interview questions."
        )


@router.delete("/interview/kit/{kit_id}")
async def delete_interview_kit(
    kit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an interview preparation kit.
    
    Soft deletes an interview kit by marking it as inactive.
    The kit data is retained for audit purposes.
    """
    try:
        logger.info(f"Deleting interview kit {kit_id} for user {current_user.id}")
        
        from sqlalchemy import select, update
        from app.models.ai_interview import InterviewKit
        
        # Check if kit exists and belongs to user
        result = await db.execute(
            select(InterviewKit).where(
                InterviewKit.id == kit_id,
                InterviewKit.user_id == current_user.id
            )
        )
        kit = result.scalar_one_or_none()
        
        if not kit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview kit not found."
            )
        
        # Soft delete by marking as inactive
        await db.execute(
            update(InterviewKit)
            .where(InterviewKit.id == kit_id)
            .values(is_active=False)
        )
        
        await db.commit()
        
        logger.info(f"Interview kit {kit_id} deleted successfully")
        return {"message": "Interview kit deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting interview kit: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete interview kit."
        )


@router.get("/interview/analytics/{job_id}")
async def get_interview_analytics(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics for interview preparation for a specific job.
    
    Provides insights into interview preparation progress including:
    - Questions practiced vs total questions
    - Average scores across question categories
    - Time spent on preparation
    - Improvement trends over time
    """
    try:
        logger.info(f"Getting interview analytics for user {current_user.id}, job {job_id}")
        
        from sqlalchemy import select, func
        from app.models.ai_interview import InterviewKit, InterviewQuestion
        
        # Get interview kit for this job
        kit_result = await db.execute(
            select(InterviewKit)
            .where(
                InterviewKit.user_id == current_user.id,
                InterviewKit.job_id == job_id,
                InterviewKit.is_active == True
            )
            .order_by(InterviewKit.created_at.desc())
        )
        kit = kit_result.scalar_one_or_none()
        
        if not kit:
            return {
                "job_id": job_id,
                "kit_exists": False,
                "analytics": {}
            }
        
        # Get questions analytics
        questions_result = await db.execute(
            select(InterviewQuestion)
            .where(InterviewQuestion.kit_id == kit.id)
        )
        questions = questions_result.scalars().all()
        
        # Calculate analytics
        total_questions = len(questions)
        practiced_questions = len([q for q in questions if q.is_practiced])
        
        # Category breakdown
        category_stats = {}
        for q in questions:
            if q.category not in category_stats:
                category_stats[q.category] = {
                    "total": 0,
                    "practiced": 0,
                    "avg_score": 0,
                    "scores": []
                }
            
            category_stats[q.category]["total"] += 1
            if q.is_practiced:
                category_stats[q.category]["practiced"] += 1
                if q.feedback_score:
                    category_stats[q.category]["scores"].append(q.feedback_score)
        
        # Calculate average scores
        for category in category_stats:
            scores = category_stats[category]["scores"]
            if scores:
                category_stats[category]["avg_score"] = sum(scores) / len(scores)
        
        # Overall statistics
        all_scores = [q.feedback_score for q in questions if q.feedback_score is not None]
        overall_avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        analytics = {
            "kit_id": kit.id,
            "total_questions": total_questions,
            "practiced_questions": practiced_questions,
            "completion_rate": (practiced_questions / total_questions * 100) if total_questions > 0 else 0,
            "overall_avg_score": overall_avg_score,
            "category_breakdown": category_stats,
            "estimated_prep_time": kit.estimated_prep_time,
            "difficulty_level": kit.difficulty_level,
            "created_at": kit.created_at.isoformat()
        }
        
        return {
            "job_id": job_id,
            "kit_exists": True,
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error(f"Error getting interview analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve interview analytics."
        )