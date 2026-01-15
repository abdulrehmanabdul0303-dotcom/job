"""
Core authentication utilities.
Re-exports authentication functions for easy access.
"""
from app.api.v1.auth import get_current_user

__all__ = ["get_current_user"]