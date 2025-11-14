"""AI service for watchpoint extraction and change analysis"""
import json
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

from app.config import settings
from app.core.logging import get_logger
from app.models.bookmark import ContentType

logger = get_logger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.openai_api_key)


class AIService:
    """AI service for intelligent content analysis"""

    async def extract_watchpoints(
        self,
        content: str,
        content_type: ContentType,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract key watchpoints from content using AI.

        Returns list of watchpoints:
        [
            {
                "field_name": str,
                "field_value": str,
                "field_type": str,
                "is_primary": bool,
                "reasoning": str
            }
        ]
        """
        try:
            prompt = self._build_watchpoint_prompt(content, content_type, metadata)

            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that analyzes content and identifies key fields worth monitoring for changes."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Low temperature for consistent results
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            watchpoints = result.get("watchpoints", [])

            logger.info(
                "watchpoints_extracted",
                content_type=content_type,
                count=len(watchpoints)
            )

            return watchpoints

        except Exception as e:
            logger.error("watchpoint_extraction_failed", error=str(e))
            # Return basic watchpoint as fallback
            return [{
                "field_name": "content",
                "field_value": content[:500],
                "field_type": "text",
                "is_primary": True,
                "reasoning": "Fallback: monitoring full content"
            }]

    async def analyze_change_significance(
        self,
        field_name: str,
        old_value: str,
        new_value: str,
        content_type: ContentType
    ) -> Dict[str, Any]:
        """
        Analyze how significant a change is (0.0 to 1.0).

        Returns:
        {
            "significance_score": float,  # 0.0 to 1.0
            "change_type": str,  # increase, decrease, modified, etc.
            "reasoning": str
        }
        """
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

            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI that analyzes content changes and determines their significance."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            logger.info(
                "change_analyzed",
                field=field_name,
                significance=result.get("significance_score"),
                change_type=result.get("change_type")
            )

            return result

        except Exception as e:
            logger.error("change_analysis_failed", error=str(e))
            # Default to moderate significance
            return {
                "significance_score": 0.5,
                "change_type": "modified",
                "reasoning": "Could not analyze change"
            }

    async def generate_notification_message(
        self,
        bookmark_title: str,
        changes: List[Dict[str, Any]],
        content_type: ContentType
    ) -> Dict[str, str]:
        """
        Generate a user-friendly notification message.

        Returns:
        {
            "title": str,  # Short title
            "message": str  # Detailed message
        }
        """
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

Use appropriate tone based on significance:
- High significance: Urgent, action-oriented
- Medium: Informative, helpful
- Low: Casual, FYI

Respond in JSON format:
{{
    "title": "short title",
    "message": "clear explanation"
}}"""

            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI that creates helpful, concise notifications for users."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,  # More creative for better messages
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return {
                "title": result.get("title", "Bookmark Updated"),
                "message": result.get("message", "Your bookmark has changed.")
            }

        except Exception as e:
            logger.error("notification_generation_failed", error=str(e))
            return {
                "title": "Bookmark Updated",
                "message": f"{bookmark_title} has changed."
            }

    async def detect_duplicate(
        self,
        content1: str,
        content2: str,
        metadata1: Dict[str, Any],
        metadata2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect if two bookmarks are duplicates or very similar.

        Returns:
        {
            "is_duplicate": bool,
            "similarity_score": float,  # 0.0 to 1.0
            "reasoning": str
        }
        """
        try:
            # Quick check: exact URL match
            if metadata1.get("url") and metadata1.get("url") == metadata2.get("url"):
                return {
                    "is_duplicate": True,
                    "similarity_score": 1.0,
                    "reasoning": "Identical URLs"
                }

            prompt = f"""Compare these two bookmarks and determine if they're duplicates:

Bookmark 1:
Title: {metadata1.get('title', 'N/A')}
URL: {metadata1.get('url', 'N/A')}
Content: {content1[:500]}

Bookmark 2:
Title: {metadata2.get('title', 'N/A')}
URL: {metadata2.get('url', 'N/A')}
Content: {content2[:500]}

Determine:
1. Are they duplicates? (same content, just saved twice)
2. Similarity score (0.0 to 1.0)
3. Brief reasoning

Respond in JSON format:
{{
    "is_duplicate": true|false,
    "similarity_score": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI that detects duplicate or similar content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            logger.error("duplicate_detection_failed", error=str(e))
            return {
                "is_duplicate": False,
                "similarity_score": 0.0,
                "reasoning": "Could not analyze"
            }

    def _build_watchpoint_prompt(
        self,
        content: str,
        content_type: ContentType,
        metadata: Dict[str, Any]
    ) -> str:
        """Build the prompt for watchpoint extraction"""

        # Truncate content if too long
        content_preview = content[:2000] if len(content) > 2000 else content

        prompt = f"""Analyze this content and extract 3-5 key fields that should be monitored for changes.

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

        return prompt


# Global AI service instance
ai_service = AIService()
