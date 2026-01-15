"""
Authentication endpoints for user registration, login, and token management.
Includes rate limiting and audit logging.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.config import settings, limit_if_enabled
from app.core.cookies import set_auth_cookies, clear_auth_cookies
import os


def is_test_env() -> bool:
    """Check if running in test environment to disable rate limiting."""
    env = os.getenv("ENV", "development").lower()
    return env in {"test", "pytest", "testing"}


# Conditional rate limiting based on environment
def conditional_rate_limit(limit_str: str):
    """Apply rate limiting only in non-test environments."""
    def decorator(func):
        if is_test_env():
            return func
        else:
            return limiter.limit(limit_str)(func)
    return decorator


class CustomHTTPBearer(HTTPBearer):
    """Custom HTTPBearer that returns 401 instead of 403 for missing credentials."""
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        authorization = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


from app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    TokenRefresh,
    UserResponse,
    LogoutResponse
)
from app.services.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_expiry_seconds,
    get_current_user_from_cookie
)
from app.models.user import User, Session, AuditLog

# SECURITY P0: Rate limiter for auth endpoints
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()
security = CustomHTTPBearer()


async def create_audit_log(
    db: AsyncSession,
    user_id: Optional[str],
    action: str,
    request: Request,
    resource_type: Optional[str] = None
):
    """Helper function to create audit log entries."""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit)


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limit_if_enabled(f"{settings.RATE_LIMIT_AUTH_PER_MINUTE}/minute")
async def register(
    request: Request,
    response: Response,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account with httpOnly cookies.
    PATCH 14: Uses proper transactional patterns for concurrency safety.
    
    - Validates email uniqueness
    - Hashes password with argon2
    - Creates JWT tokens
    - Sets httpOnly cookies
    - Logs registration action
    """
    try:
        print(f"[REGISTER] Starting registration for {user_data.email}")
        
        # Check if user already exists
        print(f"[REGISTER] Checking if user exists...")
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        print(f"[REGISTER] User exists check complete: {existing_user is not None}")
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # PATCH 14: Atomic user creation with proper transaction management
        print(f"[REGISTER] Creating new user...")
        user = User(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=getattr(user_data, 'full_name', None),
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"[REGISTER] User created with ID: {user.id}")
        
        # Create audit log in separate transaction
        print(f"[REGISTER] Creating audit log...")
        await create_audit_log(db, str(user.id), "register", request, "user")
        
        # Create tokens after successful user creation
        print(f"[REGISTER] Creating tokens...")
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        print(f"[REGISTER] Tokens created")
        
        # Set httpOnly cookies
        set_auth_cookies(response, access_token, refresh_token)
        
        # Save refresh token session
        print(f"[REGISTER] Saving session...")
        session = Session(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
        )
        db.add(session)
        await db.commit()
        print(f"[REGISTER] Session saved")
        
        print(f"[REGISTER] Registration successful for {user_data.email}")
        return {"success": True, "message": "Registration successful"}
        
    except HTTPException:
        print(f"[REGISTER] HTTPException raised")
        raise
    except Exception as e:
        print(f"[REGISTER] Exception: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login")
@limit_if_enabled(f"{settings.RATE_LIMIT_AUTH_PER_MINUTE}/minute")
async def login(
    request: Request,
    response: Response,
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens via httpOnly cookies.
    
    - Validates credentials
    - Creates new token pair
    - Sets httpOnly cookies
    - Logs login action
    """
    try:
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        user = result.scalar_one_or_none()
        
        # Verify user exists and password is correct
        if not user or not verify_password(user_data.password, user.hashed_password):
            # Create audit log for failed login attempt
            await create_audit_log(db, None, "login_failed", request, "user")
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Set httpOnly cookies
        set_auth_cookies(response, access_token, refresh_token)
        
        # Save refresh token session
        session = Session(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
        )
        db.add(session)
        
        # Create audit log for successful login
        await create_audit_log(db, str(user.id), "login", request, "user")
        
        await db.commit()
        
        return {"success": True, "message": "Login successful"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using httpOnly refresh cookie.
    
    - Gets refresh token from cookie
    - Issues new access token
    - Keeps same refresh token (or rotates for better security)
    - Sets new access token cookie
    """
    from app.core.cookies import get_refresh_token_from_cookie
    
    # Get refresh token from cookie
    try:
        refresh_token = get_refresh_token_from_cookie(request)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token"
        )
    
    # Decode refresh token
    payload = decode_token(refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify refresh token exists in database
    result = await db.execute(
        select(Session).where(
            and_(
                Session.refresh_token == refresh_token,
                Session.user_id == user_id
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or already used"
        )
    
    # Check if refresh token is expired
    if session.expires_at < datetime.utcnow():
        await db.delete(session)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )
    
    # Verify user still exists and is active
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or inactive"
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Option 1: Keep same refresh token (simpler)
    # Set new access token cookie, keep refresh token
    set_auth_cookies(response, access_token, refresh_token)
    
    # Create audit log
    await create_audit_log(db, str(user.id), "token_refresh", request, "session")
    
    await db.commit()
    
    return {"ok": True}


@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    - Validates refresh token
    - Issues new token pair
    - Invalidates old refresh token
    """
    # Decode refresh token
    payload = decode_token(token_data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Verify refresh token exists in database
    result = await db.execute(
        select(Session).where(
            and_(
                Session.refresh_token == token_data.refresh_token,
                Session.user_id == user_id
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or already used"
        )
    
    # Check if refresh token is expired
    if session.expires_at < datetime.utcnow():
        await db.delete(session)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )
    
    # Verify user still exists and is active
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Delete old refresh token session
    await db.delete(session)
    
    # Create new refresh token session
    new_session = Session(
        user_id=user.id,
        refresh_token=new_refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    )
    db.add(new_session)
    
    # Create audit log
    await create_audit_log(db, str(user.id), "token_refresh", request, "session")
    
    await db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=get_token_expiry_seconds()
    )


@router.post("/refresh-cookie")
async def refresh_token_cookie(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using httpOnly cookie refresh token.
    
    - Gets refresh token from cookie
    - Issues new token pair
    - Sets new cookies
    - Invalidates old refresh token
    """
    from app.core.cookies import get_refresh_token_from_cookie
    
    # Get refresh token from cookie
    refresh_token = get_refresh_token_from_cookie(request)
    
    # Decode refresh token
    payload = decode_token(refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Verify refresh token exists in database
    result = await db.execute(
        select(Session).where(
            and_(
                Session.refresh_token == refresh_token,
                Session.user_id == user_id
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or already used"
        )
    
    # Check if refresh token is expired
    if session.expires_at < datetime.utcnow():
        await db.delete(session)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )
    
    # Verify user still exists and is active
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Set new cookies
    set_auth_cookies(response, access_token, new_refresh_token)
    
    # Delete old refresh token session
    await db.delete(session)
    
    # Create new refresh token session
    new_session = Session(
        user_id=user.id,
        refresh_token=new_refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    )
    db.add(new_session)
    
    # Create audit log
    await create_audit_log(db, str(user.id), "token_refresh", request, "session")
    
    await db.commit()
    
    return {"success": True, "message": "Tokens refreshed successfully"}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user information from httpOnly cookie.
    """
    current_user = await get_current_user_from_cookie(request, db)
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user by invalidating all refresh tokens and clearing cookies.
    """
    try:
        # Get current user from cookie
        current_user = await get_current_user_from_cookie(request, db)
        
        # Delete all refresh token sessions for this user
        result = await db.execute(
            select(Session).where(Session.user_id == current_user.id)
        )
        sessions = result.scalars().all()
        
        for session in sessions:
            await db.delete(session)
        
        # Create audit log
        await create_audit_log(db, str(current_user.id), "logout", request, "session")
        
        await db.commit()
        
    except HTTPException:
        # Even if user not found, clear cookies
        pass
    
    # Always clear cookies
    clear_auth_cookies(response)
    
    return LogoutResponse(message="Successfully logged out")
