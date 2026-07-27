from datetime import datetime

from loguru import logger
from sqlalchemy.orm import Session

from src.alerts.email import EmailSender
from src.db.models import AlertLog, PolicyDocument, RuleChange, User
from src.db.session import get_session, init_db
from src.ingestion.federal_register import FRDocument, FederalRegisterClient
from src.processing.extractor import ExtractionResult, RuleExtractor


class Pipeline:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.fetcher = FederalRegisterClient()
        self.extractor = RuleExtractor()
        self.mailer = EmailSender()

    async def run(self, lookback_days: int = 7) -> dict:
        init_db()
        db = get_session()
        stats = {"documents_fetched": 0, "documents_new": 0, "changes_extracted": 0, "emails_sent": 0}

        try:
            fr_docs = await self.fetcher.fetch_recent_uscis_documents(lookback_days)
            stats["documents_fetched"] = len(fr_docs)

            new_fr_docs = self._filter_new(db, fr_docs)
            stats["documents_new"] = len(new_fr_docs)
            logger.info(f"{len(new_fr_docs)} new documents to process")

            all_new_changes: list[RuleChange] = []
            doc_map: dict[str, PolicyDocument] = {}

            for fr_doc in new_fr_docs:
                db_doc, changes = await self._process_document(db, fr_doc)
                if db_doc and changes:
                    doc_map[db_doc.id] = db_doc
                    all_new_changes.extend(changes)
                    stats["changes_extracted"] += len(changes)

            if not self.dry_run and all_new_changes:
                stats["emails_sent"] = self._dispatch_alerts(db, all_new_changes, doc_map)

            logger.info(f"Pipeline complete: {stats}")
            return stats

        finally:
            db.close()

    # -------------------------------------------------------------------------

    def _filter_new(self, db: Session, fr_docs: list[FRDocument]) -> list[FRDocument]:
        existing = {
            row[0]
            for row in db.query(PolicyDocument.doc_number).filter(
                PolicyDocument.doc_number.in_([d.doc_number for d in fr_docs])
            )
        }
        return [d for d in fr_docs if d.doc_number not in existing]

    async def _process_document(
        self, db: Session, fr_doc: FRDocument
    ) -> tuple[PolicyDocument | None, list[RuleChange]]:
        if not fr_doc.body_url:
            logger.warning(f"No body URL for {fr_doc.doc_number}, skipping")
            return None, []

        full_text = await self.fetcher.fetch_document_text(fr_doc.body_url)
        extraction: ExtractionResult = await self.extractor.extract_changes(fr_doc, full_text)

        db_doc = PolicyDocument(
            doc_number=fr_doc.doc_number,
            title=fr_doc.title,
            source_url=fr_doc.source_url,
            body_url=fr_doc.body_url,
            published_at=fr_doc.published_at,
            effective_at=fr_doc.effective_at,
            rule_type=fr_doc.rule_type,
            overall_impact_level=extraction.overall_impact_level,
            raw_text=full_text,
            processed=True,
        )
        db.add(db_doc)
        db.flush()

        db_changes = []
        for c in extraction.changes:
            db_change = RuleChange(
                document_id=db_doc.id,
                section=c.get("section"),
                topic=c["topic"],
                old_rule=c["old_rule"],
                new_rule=c["new_rule"],
                plain_english_summary=c["plain_english_summary"],
                impact_level=c["impact_level"],
                action_required=c.get("action_required", False),
                action_description=c.get("action_description"),
                visa_categories_affected=c.get("visa_categories_affected", []),
                who_is_affected=c.get("who_is_affected", []),
                tags=extraction.tags,
            )
            db.add(db_change)
            db_changes.append(db_change)

        db.commit()
        logger.info(f"Saved {len(db_changes)} changes for {fr_doc.doc_number}")
        return db_doc, db_changes

    def _dispatch_alerts(
        self,
        db: Session,
        changes: list[RuleChange],
        doc_map: dict[str, PolicyDocument],
    ) -> int:
        active_users: list[User] = db.query(User).filter(User.is_active == True).all()
        emails_sent = 0

        for user in active_users:
            matched = self._match_changes_to_user(user, changes)
            if not matched:
                continue

            matched_docs = list({
                doc_map[c.document_id]
                for c in matched
                if c.document_id in doc_map
            })

            # Sort: high impact first
            matched.sort(key=lambda c: {"high": 0, "medium": 1, "low": 2}.get(c.impact_level, 3))

            ok = self.mailer.send_digest(user, matched, matched_docs)
            if ok:
                emails_sent += 1
                now = datetime.utcnow()
                for change in matched:
                    db.add(AlertLog(
                        user_id=user.id,
                        rule_change_id=change.id,
                        alert_type="email",
                        status="sent",
                        sent_at=now,
                    ))
                db.commit()

        return emails_sent

    def _match_changes_to_user(self, user: User, changes: list[RuleChange]) -> list[RuleChange]:
        user_visas = set(v.upper() for v in (user.visa_categories or []))
        if not user_visas:
            return changes  # No filter set — send everything

        matched = []
        for change in changes:
            affected = set(v.upper() for v in (change.visa_categories_affected or []))
            if affected & user_visas or "ALL" in affected:
                matched.append(change)
        return matched
