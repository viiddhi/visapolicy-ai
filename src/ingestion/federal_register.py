from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import html2text
import httpx
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings

USCIS_AGENCY_SLUGS = [
    "u-s-citizenship-and-immigration-services",
    "executive-office-for-immigration-review",
    "homeland-security-department",
    "u-s-customs-and-border-protection",
    "u-s-immigration-and-customs-enforcement",
]
DOCUMENT_TYPES = ["RULE", "PRORULE", "NOTICE"]
USCIS_KEYWORDS = ["uscis", "immigration", "alien", "nonimmigrant", "h-1b", "f-1", "green card", "i-94"]


@dataclass
class FRDocument:
    doc_number: str
    title: str
    rule_type: str
    source_url: str
    body_url: Optional[str]
    published_at: date
    effective_at: Optional[date]
    abstract: str


class FederalRegisterClient:
    def __init__(self):
        self._h2t = html2text.HTML2Text()
        self._h2t.ignore_links = False
        self._h2t.ignore_images = True
        self._h2t.body_width = 0

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_recent_uscis_documents(self, days_back: int = 7) -> list[FRDocument]:
        since = (date.today() - timedelta(days=days_back)).isoformat()
        params = {
            "conditions[agencies][]": USCIS_AGENCY_SLUGS,
            "conditions[type][]": DOCUMENT_TYPES,
            "conditions[publication_date][gte]": since,
            "fields[]": [
                "document_number",
                "title",
                "type",
                "publication_date",
                "effective_on",
                "agencies",
                "abstract",
                "html_url",
                "body_html_url",
            ],
            "per_page": 100,
            "order": "newest",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{settings.federal_register_base_url}/documents.json",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        documents = []
        for item in data.get("results", []):
            if not self._is_immigration_relevant(item):
                continue
            effective_raw = item.get("effective_on")
            documents.append(
                FRDocument(
                    doc_number=item["document_number"],
                    title=item["title"],
                    rule_type=item.get("type", "Notice"),
                    source_url=item.get("html_url", ""),
                    body_url=item.get("body_html_url"),
                    published_at=date.fromisoformat(item["publication_date"]),
                    effective_at=date.fromisoformat(effective_raw) if effective_raw else None,
                    abstract=item.get("abstract", ""),
                )
            )

        logger.info(f"Fetched {len(documents)} relevant documents since {since}")
        return documents

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_document_text(self, body_url: str) -> str:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(body_url)
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        # Remove navigation, headers, footers that add noise for Claude
        for tag in soup.select("nav, header, footer, .print-only, .hidden-print, script, style"):
            tag.decompose()

        main = soup.select_one("#full-text-body, .document-content, article, main") or soup.body
        clean_html = str(main) if main else html
        text = self._h2t.handle(clean_html)
        # Truncate to ~80k chars to stay within Claude's context safely
        return text[:80_000]

    def _is_immigration_relevant(self, item: dict) -> bool:
        combined = ((item.get("title") or "") + " " + (item.get("abstract") or "")).lower()
        return any(kw in combined for kw in USCIS_KEYWORDS)
