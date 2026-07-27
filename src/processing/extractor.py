import json
from dataclasses import dataclass

from groq import AsyncGroq
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.ingestion.federal_register import FRDocument

EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_rule_changes",
        "description": (
            "Extract every distinct rule change from this USCIS Federal Register document. "
            "For each change, capture the exact old rule text, the exact new rule text, "
            "and a plain English explanation for a non-lawyer immigrant."
        ),
        "parameters": {
            "type": "object",
            "required": ["changes", "overall_impact_level", "affected_visa_categories", "tags"],
            "properties": {
                "changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": [
                            "section", "topic", "old_rule", "new_rule",
                            "plain_english_summary", "impact_level",
                            "action_required", "visa_categories_affected", "who_is_affected",
                        ],
                        "properties": {
                            "section": {
                                "type": "string",
                                "description": "CFR section being amended, e.g. '8 CFR 214.2(h)(4)'",
                            },
                            "topic": {
                                "type": "string",
                                "description": "Short label for this change, e.g. 'Specialty Occupation Definition'",
                            },
                            "old_rule": {
                                "type": "string",
                                "description": "The exact prior rule text before this amendment",
                            },
                            "new_rule": {
                                "type": "string",
                                "description": "The exact new rule text after this amendment",
                            },
                            "plain_english_summary": {
                                "type": "string",
                                "description": (
                                    "2-4 sentence explanation written for a non-lawyer immigrant. "
                                    "What changed, why it matters, and who is affected."
                                ),
                            },
                            "impact_level": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "How significantly this affects immigrants",
                            },
                            "action_required": {
                                "type": "boolean",
                                "description": "Whether affected immigrants need to take any action",
                            },
                            "action_description": {
                                "type": "string",
                                "description": "Specific steps immigrants should take (if action_required is true)",
                            },
                            "visa_categories_affected": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "e.g. ['H-1B', 'H-4 EAD', 'F-1 OPT']",
                            },
                            "who_is_affected": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Plain-language groups, e.g. 'H-1B workers at third-party sites'",
                            },
                        },
                    },
                },
                "overall_impact_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
                "affected_visa_categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "All visa categories touched by this document",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keyword tags, e.g. ['h1b-extension', 'site-visits']",
                },
            },
        },
    },
}

SYSTEM_PROMPT = """You are an expert U.S. immigration law analyst working for Visapolicy.ai.

Your job is to read Federal Register documents and extract every specific rule change with surgical precision.

Rules:
- Quote old_rule and new_rule verbatim from the document when possible.
- If the document proposes a new rule with no prior rule, set old_rule to "No prior rule — this is a new requirement."
- Write plain_english_summary for someone who is not a lawyer and may be anxious about their immigration status.
- Be conservative: if you are unsure about impact_level, go one level higher.
- Only include visa categories you are certain are directly affected.
- If the document has no substantive rule changes (e.g., it is purely administrative), return an empty changes array."""


@dataclass
class ExtractionResult:
    changes: list[dict]
    overall_impact_level: str
    affected_visa_categories: list[str]
    tags: list[str]


# Groq's free tier caps requests at 12,000 tokens/minute (org-level), and that budget
# covers prompt + tool schema + completion in a single request. ~20k chars (~5k tokens)
# of document text leaves enough headroom for the system prompt, tool schema, and the
# 4096-token completion without tripping the per-request TPM ceiling.
MAX_CHUNK_CHARS = 20_000
_IMPACT_RANK = {"low": 0, "medium": 1, "high": 2}


def _chunk_text(full_text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    if len(full_text) <= max_chars:
        return [full_text]

    paragraphs = full_text.split("\n\n")
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(para) <= max_chars:
            current = para
        else:
            # A single paragraph is itself too long — hard-slice it.
            for i in range(0, len(para), max_chars):
                chunks.append(para[i : i + max_chars])
            current = ""
    if current:
        chunks.append(current)
    return chunks


def _merge_results(results: list[ExtractionResult]) -> ExtractionResult:
    if len(results) == 1:
        return results[0]

    changes: list[dict] = []
    impact = "low"
    categories: list[str] = []
    tags: list[str] = []
    for r in results:
        changes.extend(r.changes)
        if _IMPACT_RANK.get(r.overall_impact_level, 0) > _IMPACT_RANK.get(impact, 0):
            impact = r.overall_impact_level
        for v in r.affected_visa_categories:
            if v not in categories:
                categories.append(v)
        for t in r.tags:
            if t not in tags:
                tags.append(t)

    return ExtractionResult(
        changes=changes,
        overall_impact_level=impact,
        affected_visa_categories=categories,
        tags=tags,
    )


class RuleExtractor:
    def __init__(self):
        self._client = AsyncGroq(api_key=settings.groq_api_key)

    async def extract_changes(self, doc: FRDocument, full_text: str) -> ExtractionResult:
        chunks = _chunk_text(full_text)
        if len(chunks) > 1:
            logger.info(f"{doc.doc_number} is large ({len(full_text)} chars) — splitting into {len(chunks)} chunks")

        results = [
            await self._extract_chunk(doc, chunk, part=i + 1, total=len(chunks))
            for i, chunk in enumerate(chunks)
        ]
        return _merge_results(results)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30))
    async def _extract_chunk(self, doc: FRDocument, text: str, part: int, total: int) -> ExtractionResult:
        logger.info(f"Extracting rule changes from: {doc.doc_number} — {doc.title} (part {part}/{total})")

        part_note = (
            f"\nNote: this is part {part} of {total} of the document — it has been split to fit the model's "
            "request size limit. Only extract changes visible in this part; do not assume context from other parts."
            if total > 1
            else ""
        )
        user_message = f"""Document: {doc.title}
Published: {doc.published_at}
Effective: {doc.effective_at or 'Not specified'}
Document Number: {doc.doc_number}
Source: {doc.source_url}
{part_note}
Abstract:
{doc.abstract}

Full Document Text:
{text}

Extract all rule changes from this document."""

        response = await self._client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=4096,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            tools=[EXTRACTION_TOOL],
            tool_choice={"type": "function", "function": {"name": "extract_rule_changes"}},
        )

        tool_call = response.choices[0].message.tool_calls
        if not tool_call:
            logger.warning(f"No tool call in response for {doc.doc_number} (part {part}/{total})")
            return ExtractionResult(changes=[], overall_impact_level="low", affected_visa_categories=[], tags=[])

        result = json.loads(tool_call[0].function.arguments)
        for change in result.get("changes", []):
            if isinstance(change.get("action_required"), str):
                change["action_required"] = change["action_required"].lower() == "true"
        logger.info(
            f"Extracted {len(result['changes'])} changes from {doc.doc_number} part {part}/{total} "
            f"(impact: {result['overall_impact_level']})"
        )
        return ExtractionResult(
            changes=result["changes"],
            overall_impact_level=result["overall_impact_level"],
            affected_visa_categories=result["affected_visa_categories"],
            tags=result["tags"],
        )
