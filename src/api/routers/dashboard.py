from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from src.api.dependencies import get_current_user, get_db
from src.api.schemas.changes import DashboardResponse, DashboardStats, FeedItem, RuleChangeResponse
from src.db.models import PolicyDocument, RuleChange, User
from src.matching.engine import match_changes_for_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    changes = (
        db.query(RuleChange)
        .options(joinedload(RuleChange.document))
        .order_by(RuleChange.created_at.desc())
        .limit(500)
        .all()
    )

    matched = match_changes_for_user(current_user, changes)[:limit]

    feed = []
    for m in matched:
        doc: PolicyDocument | None = m.change.document
        change_resp = RuleChangeResponse(
            id=m.change.id,
            document_id=m.change.document_id,
            document_title=doc.title if doc else None,
            document_source_url=doc.source_url if doc else None,
            section=m.change.section,
            topic=m.change.topic,
            old_rule=m.change.old_rule,
            new_rule=m.change.new_rule,
            plain_english_summary=m.change.plain_english_summary,
            impact_level=m.change.impact_level,
            action_required=m.change.action_required,
            action_description=m.change.action_description,
            visa_categories_affected=m.change.visa_categories_affected,
            who_is_affected=m.change.who_is_affected,
            tags=m.change.tags,
            published_at=doc.published_at if doc else None,
            effective_at=doc.effective_at if doc else None,
            created_at=m.change.created_at,
        )
        feed.append(FeedItem(
            relevance_score=m.score,
            relevance_reasons=m.reasons,
            change=change_resp,
        ))

    stats = DashboardStats(
        total_relevant=len(matched),
        high_impact=sum(1 for m in matched if m.change.impact_level == "high"),
        action_required=sum(1 for m in matched if m.change.action_required),
    )

    return DashboardResponse(feed=feed, stats=stats)
