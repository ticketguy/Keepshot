import openai
from ..config import OPENAI_API_KEY
from .prompts import CHANGE_DETECTED_PROMPT, RELATED_SAVE_PROMPT, DUPLICATE_SAVE_PROMPT
from app.main import clients
import asyncio

openai.api_key = OPENAI_API_KEY

async def generate_reminder_message(reminder_type: str, **kwargs):
    """
    Generate AI reminder message based on type.
    reminder_type: 'change', 'related', 'duplicate'
    kwargs: context for the prompt
    """
    if reminder_type == "change":
        prompt = CHANGE_DETECTED_PROMPT.format(**kwargs)
    elif reminder_type == "related":
        prompt = RELATED_SAVE_PROMPT.format(**kwargs)
    elif reminder_type == "duplicate":
        prompt = DUPLICATE_SAVE_PROMPT.format(**kwargs)
    else:
        raise ValueError("Unknown reminder type")

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60
    )
    return response.choices[0].message.content.strip()


async def send_push_notification(user_id: int, message: str):
    """
    Push notification to all connected WebSocket clients.
    """
    for client in clients:
        try:
            await client.send_text(message)
        except:
            pass