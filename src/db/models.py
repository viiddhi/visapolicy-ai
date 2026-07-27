import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id = Column(String(64), primary_key=True, default=_uuid)
    doc_number = Column(String(32), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    body_url = Column(Text)
    published_at = Column(Date, nullable=False)
    effective_at = Column(Date)
    rule_type = Column(String(32))
    overall_impact_level = Column(String(16))
    raw_text = Column(Text)
    processed = Column(Boolean, default=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    changes = relationship("RuleChange", back_populates="document")


class RuleChange(Base):
    __tablename__ = "rule_changes"

    id = Column(String(64), primary_key=True, default=_uuid)
    document_id = Column(String(64), ForeignKey("policy_documents.id"), nullable=False)
    section = Column(Text)
    topic = Column(Text, nullable=False)
    old_rule = Column(Text, nullable=False)
    new_rule = Column(Text, nullable=False)
    plain_english_summary = Column(Text, nullable=False)
    impact_level = Column(String(16), nullable=False)
    action_required = Column(Boolean, default=False)
    action_description = Column(Text)
    visa_categories_affected = Column(JSON)
    who_is_affected = Column(JSON)
    tags = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("PolicyDocument", back_populates="changes")


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=_uuid)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    password_hash = Column(String(255))
    reset_token = Column(String(128), unique=True)
    reset_token_expires = Column(DateTime)

    # ----- Visa status -----
    # Legacy list kept for Phase 1 email pipeline compatibility
    visa_categories = Column(JSON)
    primary_visa_type = Column(String(32))          # H-1B | F-1 | O-1 | L-1 | TN | J-1
    visa_status = Column(String(32))                # active | pending | expired
    authorized_until = Column(Date)                 # I-94 expiry

    # ----- Green card journey -----
    gc_stage = Column(String(32))                   # none | perm_filed | i140_filed | i140_approved | i485_filed | gc_approved
    priority_date = Column(Date)
    preference_category = Column(String(16))        # EB-1 | EB-2 | EB-3 | EB-2-NIW
    country_of_birth = Column(String(64))           # "India" | "China" | etc. — affects EB backlog

    # ----- Employment -----
    employer_type = Column(String(32))              # big_tech | small_company | nonprofit | consulting | staffing | university
    placement_type = Column(String(32))             # direct | third_party | bench
    degree_field = Column(String(128))              # "Computer Science" — matters for specialty occupation
    job_title = Column(String(128))

    # ----- OPT (F-1 students) -----
    on_opt = Column(Boolean, default=False)
    opt_type = Column(String(16))                   # regular | stem
    opt_expiry = Column(Date)

    # ----- Dependents -----
    dependent_visa_types = Column(JSON)             # ["H-4", "H-4 EAD"]

    # ----- Alert preferences -----
    alert_frequency = Column(String(16), default="daily")     # realtime | daily | weekly
    min_impact_level = Column(String(16), default="medium")   # low | medium | high

    onboarding_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(String(64), primary_key=True, default=_uuid)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    rule_change_id = Column(String(64), ForeignKey("rule_changes.id"), nullable=False)
    alert_type = Column(String(32), default="email")
    status = Column(String(32), default="pending")
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
