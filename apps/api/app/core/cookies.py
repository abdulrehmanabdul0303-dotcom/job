"""
Cookie management utilities for secure authentication.
Handles httpOnly cookies for JWT tokens.
"""
from datetime import timedelta
from fastapi import Response, Request, HTTPException, status
from app.core.config import settings

# Cookie names
ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"

def set_auth_cookies(
    response: Response, 
    access_token: str, 
    refresh_token: str, 
    secure: bool = None
) -> None:
    """
    Set httpOnly authentication cookies.
    
    Args:
        response: FastAPI Response object
        access_token: JWT access token
        refresh_token: JWT refresh token  
        secure: Use secure cookies (auto-detect from environment if None)
    """
    if secure is None:
        secure = settings.ENVIRONMENT == "production"
    
    # Access token cookie (30 minutes)
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=int(timedelta(minutes=30).total_seconds()),
        path="/",
    )
    
    # Refresh token cookie (7 days)
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax", 
        max_age=int(timedelta(days=7).total_seconds()),
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies."""
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


def get_token_from_cookie(request: Request) -> str:
    """
    Extract JWT token from httpOnly cookie.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        JWT token string
        
    Raises:
        HTTPException: If token not found or invalid
    """
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def get_refresh_token_from_cookie(request: Request) -> str:
    """
    Extract refresh token from httpOnly cookie.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Refresh token string
        
    Raises:
        HTTPException: If refresh token not found
    """
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )
    return token