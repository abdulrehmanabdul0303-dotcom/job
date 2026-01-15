"""
Pydantic schemas for user preferences.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Union
from datetime import datetime


class PreferencesBase(BaseModel):
    """Base schema for preferences."""
    # COMPATIBILITY: Accept both singular and plural forms
    desired_role: Optional[str] = Field(None, max_length=255, description="Desired job role/title")
    desired_roles: Optional[List[str]] = Field(None, description="List of desired job roles/titles")
    
    # Extended fields to match test expectations
    desired_locations: Optional[List[str]] = Field(None, description="List of preferred locations")
    desired_seniority: Optional[List[str]] = Field(None, description="List of preferred seniority levels")
    desired_industries: Optional[List[str]] = Field(None, description="List of preferred industries")
    desired_company_size: Optional[List[str]] = Field(None, description="List of preferred company sizes")
    
    preferred_countries: Optional[List[str]] = Field(None, description="List of preferred country codes (e.g., ['US', 'CA', 'UK'])")
    min_salary: Optional[int] = Field(None, ge=0, description="Minimum salary expectation")
    max_salary: Optional[int] = Field(None, ge=0, description="Maximum salary expectation")
    work_type: Optional[str] = Field(None, description="Preferred work type: remote, full-time, part-time, hybrid, contract")
    
    # Additional fields from tests
    remote_preference: Optional[str] = Field(None, description="Remote work preference")
    willing_to_relocate: Optional[bool] = Field(None, description="Willing to relocate")
    job_types: Optional[List[str]] = Field(None, description="List of preferred job types")
    benefits_important: Optional[List[str]] = Field(None, description="List of important benefits")
    skills_to_develop: Optional[List[str]] = Field(None, description="List of skills to develop")
    
    @model_validator(mode='before')
    @classmethod
    def normalize_desired_roles(cls, values):
        """Normalize desired_role and desired_roles fields."""
        if isinstance(values, dict):
            # If both are provided, prefer desired_roles
            if values.get('desired_roles') and values.get('desired_role'):
                values['desired_role'] = ', '.join(values['desired_roles'])
            # If only desired_role is provided, create desired_roles
            elif values.get('desired_role') and not values.get('desired_roles'):
                values['desired_roles'] = [values['desired_role']]
            # If only desired_roles is provided, create desired_role
            elif values.get('desired_roles') and not values.get('desired_role'):
                values['desired_role'] = ', '.join(values['desired_roles'])
        return values
    
    @field_validator('work_type')
    @classmethod
    def validate_work_type(cls, v):
        """Validate work type is one of allowed values."""
        if v is not None:
            allowed = ['remote', 'full-time', 'part-time', 'hybrid', 'contract']
            if v not in allowed:
                raise ValueError(f"work_type must be one of: {', '.join(allowed)}")
        return v
    
    @field_validator('max_salary')
    @classmethod
    def validate_salary_range(cls, v, info):
        """Validate max_salary is greater than min_salary if both provided."""
        min_salary = info.data.get('min_salary')
        if v is not None and min_salary is not None and v < min_salary:
            raise ValueError("max_salary must be greater than or equal to min_salary")
        return v


class PreferencesCreate(PreferencesBase):
    """Schema for creating preferences."""
    pass


class PreferencesUpdate(PreferencesBase):
    """Schema for updating preferences (all fields optional)."""
    pass


class PreferencesResponse(PreferencesBase):
    """Schema for preferences response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PreferencesUpdateConfirmation(BaseModel):
    """Confirmation response after updating preferences."""
    message: str
    preferences: PreferencesResponse
