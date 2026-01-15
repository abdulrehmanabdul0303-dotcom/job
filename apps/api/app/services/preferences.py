"""
User preferences service.
Handles CRUD operations for job search preferences.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.preferences import UserPreferences
from app.schemas.preferences import PreferencesCreate, PreferencesUpdate
from typing import Optional, Dict, Any
import json


# Define JSON fields that need serialization
JSON_FIELDS = {
    'preferred_countries', 'desired_roles', 'desired_locations',
    'desired_seniority', 'desired_industries', 'desired_company_size',
    'job_types', 'benefits_important', 'skills_to_develop'
}


class PreferencesService:
    """Service for managing user job search preferences."""
    
    @staticmethod
    def _serialize_json_fields(data: dict) -> dict:
        """Serialize list fields to JSON strings for database storage."""
        out = dict(data)
        for field in JSON_FIELDS:
            if field in out and out[field] is not None and isinstance(out[field], list):
                out[field] = json.dumps(out[field])
        return out
    
    @staticmethod
    def _parsed_view(pref_obj: UserPreferences) -> Dict[str, Any]:
        """Create a parsed view of preferences without mutating the ORM object."""
        # Extract all column values without mutating the original object
        data = {c.name: getattr(pref_obj, c.name) for c in pref_obj.__table__.columns}
        
        # Parse JSON fields
        for field in JSON_FIELDS:
            value = data.get(field)
            if isinstance(value, str):
                try:
                    data[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    data[field] = []
            elif value is None:
                data[field] = []
        
        return data
    
    @staticmethod
    async def get_preferences(db: AsyncSession, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user preferences by user_id.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Preferences dict or None if not found
        """
        result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()
        
        if not preferences:
            return None
        
        return PreferencesService._parsed_view(preferences)
    
    @staticmethod
    async def create_preferences(
        db: AsyncSession,
        user_id: str,
        preferences_data: PreferencesCreate
    ) -> Dict[str, Any]:
        """
        Create new user preferences.
        
        Args:
            db: Database session
            user_id: User ID
            preferences_data: Preferences data
            
        Returns:
            Created preferences dict
        """
        # Serialize list fields to JSON strings for storage
        data_dict = preferences_data.model_dump(exclude_unset=True)
        data_dict = PreferencesService._serialize_json_fields(data_dict)
        
        preferences = UserPreferences(
            user_id=user_id,
            **data_dict
        )
        
        db.add(preferences)
        await db.flush()
        await db.refresh(preferences)
        
        # Return parsed view without mutating the ORM object
        return PreferencesService._parsed_view(preferences)
    
    @staticmethod
    async def update_preferences(
        db: AsyncSession,
        user_id: str,
        preferences_data: PreferencesUpdate
    ) -> Dict[str, Any]:
        """
        Update existing user preferences or create if not exists.
        
        Args:
            db: Database session
            user_id: User ID
            preferences_data: Updated preferences data
            
        Returns:
            Updated preferences dict
        """
        # Get existing preferences (raw, without JSON parsing)
        result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            # Create new if doesn't exist
            return await PreferencesService.create_preferences(db, user_id, preferences_data)
        
        # Update existing - serialize lists to JSON strings
        update_data = preferences_data.model_dump(exclude_unset=True)
        update_data = PreferencesService._serialize_json_fields(update_data)
        
        # Update the ORM object with JSON strings only
        for field, value in update_data.items():
            setattr(existing, field, value)
        
        await db.flush()
        await db.refresh(existing)
        
        # Return parsed view without mutating the ORM object
        return PreferencesService._parsed_view(existing)
    
    @staticmethod
    async def delete_preferences(db: AsyncSession, user_id: str) -> bool:
        """
        Delete user preferences.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()
        
        if not preferences:
            return False
        
        await db.delete(preferences)
        await db.flush()
        return True
