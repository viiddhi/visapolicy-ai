from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from src.api.dependencies import get_current_user, get_db
from src.api.schemas.changes import RuleChangeResponse
from src.db.models import RuleChange, User

router = APIRouter(prefix="/changes", tags=["changes"])


@router.get("", response_model=list[RuleChangeResponse])
def list_changes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    impact: str | None = Query(None, description="Filter by impact level: low|medium|high"),
    visa: str | None = Query(None, description="Filter by visa category, e.g. H-1B"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(RuleChange).options(joinedload(RuleChange.document))

    if impact:
        q = q.filter(RuleChange.impact_level == impact)
    if visa:
        q = q.filter(RuleChange.visa_categories_affected.contains([visa]))

    changes = q.order_by(RuleChange.created_at.desc()).offset(skip).limit(limit).all()

    return [
        RuleChangeResponse(
            id=c.id,
            document_id=c.document_id,
            document_title=c.document.title if c.document else None,
            document_source_url=c.document.source_url if c.document else None,
            section=c.section,
            topic=c.topic,
            old_rule=c.old_rule,
            new_rule=c.new_rule,
            plain_english_summary=c.plain_english_summary,
            impact_level=c.impact_level,
            action_required=c.action_required,
            action_description=c.action_description,
            visa_categories_affected=c.visa_categories_affected,
            who_is_affected=c.who_is_affected,
            tags=c.tags,
            published_at=c.document.published_at if c.document else None,
            effective_at=c.document.effective_at if c.document else None,
            created_at=c.created_at,
        )
        for c in changes
    ]


@router.get("/{change_id}", response_model=RuleChangeResponse)
def get_change(
    change_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    change = (
        db.query(RuleChange)
        .options(joinedload(RuleChange.document))
        .filter(RuleChange.id == change_id)
        .first()
    )
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    return RuleChangeResponse(
        id=change.id,
        document_id=change.document_id,
        document_title=change.document.title if change.document else None,
        document_source_url=change.document.source_url if change.document else None,
        section=change.section,
        topic=change.topic,
        old_rule=change.old_rule,
        new_rule=change.new_rule,
        plain_english_summary=change.plain_english_summary,
        impact_level=change.impact_level,
        action_required=change.action_required,
        action_description=change.action_description,
        visa_categories_affected=change.visa_categories_affected,
        who_is_affected=change.who_is_affected,
        tags=change.tags,
        published_at=change.document.published_at if change.document else None,
        effective_at=change.document.effective_at if change.document else None,
        created_at=change.created_at,
    )
