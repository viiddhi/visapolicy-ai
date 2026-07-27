from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.api.schemas.profile import ProfileResponse, ProfileUpdate
from src.db.models import User

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("", response_model=ProfileResponse)
def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)

    # Keep legacy visa_categories in sync with primary_visa_type
    if body.primary_visa_type:
        categories = set(current_user.visa_categories or [])
        categories.add(body.primary_visa_type)
        if body.dependent_visa_types:
            categories.update(body.dependent_visa_types)
        current_user.visa_categories = list(categories)

    db.commit()
    db.refresh(current_user)
    return current_user
