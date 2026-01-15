"""
Core configuration management for JobPilot AI API.
Uses pydantic-settings for environment variable validation.
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path
import json
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "JobPilot AI"
    VERSION: str = "1.0.0"
    
    # Environment Configuration - CRITICAL for test behavior
    ENV: str = os.getenv("ENV", "development").lower()
    
    # Rate Limiting Control - PATCH 13: Disable in test mode
    RATE_LIMIT_ENABLED: bool = True
    
    # JWT Configuration - SECURITY P0: Must be from environment
    JWT_SECRET: str = ""  # REQUIRED in production
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TTL_MIN: int = 15
    JWT_REFRESH_TTL_DAYS: int = 7
    
    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./jobpilot.db"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS Configuration - can be JSON string or comma-separated
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Rate Limiting - SECURITY P0
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10  # Stricter for auth endpoints
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 5  # Stricter for uploads
    RATE_LIMIT_AI_PER_MINUTE: int = 20  # Stricter for AI endpoints
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_CV_EXTENSIONS: List[str] = [".pdf", ".docx"]
    UPLOAD_DIR: str = "uploads/resumes"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Security - SECURITY P0: Trusted hosts
    TRUSTED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*.localhost"]
    
    class Config:
        # Try to load from .env file in project root
        env_file = [
            Path(__file__).parent.parent.parent / ".env",  # jobpilot-ai/.env
            Path(__file__).parent.parent.parent.parent / ".env",  # parent/.env
            ".env"
        ]
        case_sensitive = True
    
    def __init__(self, **data):
        super().__init__(**data)
        
        # SECURITY P0: Validate JWT_SECRET in production
        if self.ENVIRONMENT == "production":
            if not self.JWT_SECRET:
                raise ValueError("JWT_SECRET must be set in production environment")
            if len(self.JWT_SECRET) < 32:
                raise ValueError("JWT_SECRET must be at least 32 characters in production")
        
        # Generate a secure dev secret if not provided (development only)
        if not self.JWT_SECRET and self.ENVIRONMENT != "production":
            self.JWT_SECRET = secrets.token_urlsafe(32)
            print(f"[WARNING] Generated temporary JWT_SECRET for development: {self.JWT_SECRET}")
        
        # PATCH 13: Disable rate limiting in test environment
        if self.ENV == "test":
            self.RATE_LIMIT_ENABLED = False
            print(f"[TEST MODE] Rate limiting disabled for testing")
        
        # Parse BACKEND_CORS_ORIGINS if it's a string
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            try:
                # Try to parse as JSON
                self.BACKEND_CORS_ORIGINS = json.loads(self.BACKEND_CORS_ORIGINS)
            except (json.JSONDecodeError, TypeError):
                # Fall back to comma-separated
                self.BACKEND_CORS_ORIGINS = [
                    origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")
                ]
        
        # Parse ALLOWED_CV_EXTENSIONS if it's a string
        if isinstance(self.ALLOWED_CV_EXTENSIONS, str):
            try:
                # Try to parse as JSON
                self.ALLOWED_CV_EXTENSIONS = json.loads(self.ALLOWED_CV_EXTENSIONS)
            except (json.JSONDecodeError, TypeError):
                # Fall back to comma-separated
                self.ALLOWED_CV_EXTENSIONS = [
                    ext.strip() for ext in self.ALLOWED_CV_EXTENSIONS.split(",")
                ]
        
        # Parse TRUSTED_HOSTS if it's a string
        if isinstance(self.TRUSTED_HOSTS, str):
            try:
                self.TRUSTED_HOSTS = json.loads(self.TRUSTED_HOSTS)
            except (json.JSONDecodeError, TypeError):
                self.TRUSTED_HOSTS = [
                    host.strip() for host in self.TRUSTED_HOSTS.split(",")
                ]


settings = Settings()

# PATCH 13: Rate limiting decorator that respects test mode
def limit_if_enabled(rule: str):
    """Apply rate limiting only if enabled (disabled in test mode)."""
    def decorate(fn):
        if settings.RATE_LIMIT_ENABLED:
            from slowapi import Limiter
            from slowapi.util import get_remote_address
            limiter = Limiter(key_func=get_remote_address)
            return limiter.limit(rule)(fn)
        else:
            return fn
    return decorate
