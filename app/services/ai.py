"""AI service for watchpoint extraction and change analysis.

Supports multiple LLM providers via the LLM_PROVIDER environment variable:
  - openai   (default) — requires OPENAI_API_KEY
  - claude            — requires ANTHROPIC_API_KEY
"""
import json
from typing import List, Dict, Any
from app.config import settings
from app.core.logging import get_logger
from app.models.bookmark import ContentType

logger = get_logger(__name__)


# ── Provider clients ──────────────────────────────────────────────────────────

def _make_client():
    provider = settings.llm_provider.lower()
    if provider == "claude":
        import anthropic
        return "claude", anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    else:
        from openai import AsyncOpenAI
        return "openai", AsyncOpenAI(api_key=settings.openai_api_key)


async def _chat(messages: list[dict], temperature: float = 0.3) -> str:
    """Send messages to whichever provider is configured, return text."""
    provider, client = _make_client()

    if provider == "claude":
        system = next((m["content"] for m in messages if m["role"] == "system"), None)
        user_messages = [m for m in messages if m["role"] != "system"]
        kwargs = dict(
            model=settings.llm_model,
            max_tokens=1024,
            messages=user_messages,
            temperature=temperature,
        )
        if system:
            kwargs["system"] = system
        response = await client.messages.create(**kwargs)
        return response.content[0].text
    else:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content


# ── AI Service ────────────────────────────────────────────────────────────────

class AIService:
    """LLM-agnostic AI service for intelligent content analysis."""

    async def extract_watchpoints(
        self,
        content: str,
        content_type: ContentType,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        try:
            prompt = self._build_watchpoint_prompt(content, content_type, metadata)
            result = json.loads(await _chat([
                {"role": "system", "content": "You are an AI assistant that analyzes content and identifies key fields worth monitoring for changes."},
                {"role": "user", "content": prompt},
            ], temperature=0.3))
            watchpoints = result.get("watchpoints", [])
            logger.info("watchpoints_extracted", content_type=content_type, count=len(watchpoints))
            return watchpoints
        except Exception as e:
            logger.error("watchpoint_extraction_failed", error=str(e))
            return [{
                "field_name": "content",
                "field_value": content[:500],
                "field_type": "text",
                "is_primary": True,
                "reasoning": "Fallback: monitoring full content",
            }]

    async def analyze_change_significance(
        self,
        field_name: str,
        old_value: str,
        new_value: str,
        content_type: ContentType
    ) -> Dict[str, Any]:
        try:
            prompt = f"""Analyze the significance of this change:

Field: {field_name}
Old Value: {old_value[:500]}
New Value: {new_value[:500]}
Content Type: {content_type}

Rate the significance from 0.0 to 1.0 where:
- 0.0 = trivial (typo fix, minor formatting)
- 0.3 = minor (small content update, minor metric change)
- 0.5 = moderate (notable content change, significant metric change)
- 0.7 = important (major update, price change, availability change)
- 1.0 = critical (sold out, massive price drop, major breaking news)

Also determine the change type: increase, decrease, modified, added, or removed.

Respond in JSON format:
{{
    "significance_score": 0.0-1.0,
    "change_type": "increase|decrease|modified|added|removed",
    "reasoning": "brief explanation"
}}"""
            result = json.loads(await _chat([
                {"role": "system", "content": "You are an AI that analyzes content changes and determines their significance."},
                {"role": "user", "content": prompt},
            ], temperature=0.2))
            logger.info("change_analyzed", field=field_name,
                        significance=result.get("significance_score"),
                        change_type=result.get("change_type"))
            return result
        except Exception as e:
            logger.error("change_analysis_failed", error=str(e))
            return {"significance_score": 0.5, "change_type": "modified", "reasoning": "Could not analyze change"}

    async def generate_notification_message(
        self,
        bookmark_title: str,
        changes: List[Dict[str, Any]],
        content_type: ContentType
    ) -> Dict[str, str]:
        try:
            changes_text = "\n".join([
                f"- {c['field_name']}: {c['old_value'][:100]} → {c['new_value'][:100]}"
                for c in changes
            ])
            prompt = f"""Generate a concise, user-friendly notification message for these changes:

Bookmark: {bookmark_title}
Content Type: {content_type}
Changes:
{changes_text}

Create a notification with:
1. A short, attention-grabbing title (max 60 characters)
2. A clear message explaining what changed and why it matters (max 200 characters)

Respond in JSON format:
{{
    "title": "short title",
    "message": "clear explanation"
}}"""
            result = json.loads(await _chat([
                {"role": "system", "content": "You are an AI that creates helpful, concise notifications for users."},
                {"role": "user", "content": prompt},
            ], temperature=0.7))
            return {
                "title": result.get("title", "Bookmark Updated"),
                "message": result.get("message", "Your bookmark has changed."),
            }
        except Exception as e:
            logger.error("notification_generation_failed", error=str(e))
            return {"title": "Bookmark Updated", "message": f"{bookmark_title} has changed."}

    async def detect_duplicate(
        self,
        content1: str,
        content2: str,
        metadata1: Dict[str, Any],
        metadata2: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            if metadata1.get("url") and metadata1.get("url") == metadata2.get("url"):
                return {"is_duplicate": True, "similarity_score": 1.0, "reasoning": "Identical URLs"}

            prompt = f"""Compare these two bookmarks and determine if they're duplicates:

Bookmark 1:
Title: {metadata1.get('title', 'N/A')}
URL: {metadata1.get('url', 'N/A')}
Content: {content1[:500]}

Bookmark 2:
Title: {metadata2.get('title', 'N/A')}
URL: {metadata2.get('url', 'N/A')}
Content: {content2[:500]}

Respond in JSON format:
{{
    "is_duplicate": true|false,
    "similarity_score": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""
            result = json.loads(await _chat([
                {"role": "system", "content": "You are an AI that detects duplicate or similar content."},
                {"role": "user", "content": prompt},
            ], temperature=0.2))
            return result
        except Exception as e:
            logger.error("duplicate_detection_failed", error=str(e))
            return {"is_duplicate": False, "similarity_score": 0.0, "reasoning": "Could not analyze"}

    def _build_watchpoint_prompt(self, content: str, content_type: ContentType, metadata: Dict[str, Any]) -> str:
        content_preview = content[:2000] if len(content) > 2000 else content
        return f"""Analyze this content and extract 3-5 key fields that should be monitored for changes.

Content Type: {content_type}
Metadata: {json.dumps(metadata, indent=2)}
Content:
{content_preview}

Examples of watchpoints by content type:
- E-commerce: price, availability, rating, shipping_cost
- Article: title, publication_date, content_summary
- Social post: text, likes, replies, shares
- Job posting: status, salary, location, closing_date
- PDF: page_count, key_sections, metadata

For each watchpoint, provide:
1. field_name: Short identifier (snake_case)
2. field_value: Current value (as string)
3. field_type: Data type (currency, number, text, date, status, etc.)
4. is_primary: true if this is the most important field to monitor
5. reasoning: Why this field matters

Respond in JSON format:
{{
    "watchpoints": [
        {{
            "field_name": "example",
            "field_value": "value",
            "field_type": "text",
            "is_primary": false,
            "reasoning": "why it matters"
        }}
    ]
}}"""


# Global AI service instance
ai_service = AIService()
