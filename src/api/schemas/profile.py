from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    primary_visa_type: Optional[str] = None
    visa_status: Optional[str] = None
    authorized_until: Optional[date] = None
    gc_stage: Optional[str] = None
    priority_date: Optional[date] = None
    preference_category: Optional[str] = None
    country_of_birth: Optional[str] = None
    employer_type: Optional[str] = None
    placement_type: Optional[str] = None
    degree_field: Optional[str] = None
    job_title: Optional[str] = None
    on_opt: Optional[bool] = None
    opt_type: Optional[str] = None
    opt_expiry: Optional[date] = None
    dependent_visa_types: Optional[list[str]] = None
    alert_frequency: Optional[str] = None
    min_impact_level: Optional[str] = None
    onboarding_completed: Optional[bool] = None


class ProfileResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    primary_visa_type: Optional[str]
    visa_status: Optional[str]
    authorized_until: Optional[date]
    gc_stage: Optional[str]
    priority_date: Optional[date]
    preference_category: Optional[str]
    country_of_birth: Optional[str]
    employer_type: Optional[str]
    placement_type: Optional[str]
    degree_field: Optional[str]
    job_title: Optional[str]
    on_opt: Optional[bool]
    opt_type: Optional[str]
    opt_expiry: Optional[date]
    dependent_visa_types: Optional[list[str]]
    alert_frequency: Optional[str]
    min_impact_level: Optional[str]
    onboarding_completed: bool

    model_config = {"from_attributes": True}
