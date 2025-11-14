import openai
from ..config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

async def extract_watchpoints(snapshot_content: str):
    """
    Sends snapshot content to OpenAI to extract watch points.
    """
    prompt = f"Extract key watch points from this content:\n{snapshot_content}"
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}],
        max_tokens=500
    )
    
    content = response.choices[0].message.content.strip()
    # Return as a list of dicts for WatchPoints
    # Simple example: split by line
    watchpoints = [{"field_name": f"point_{i}", "value": line} for i, line in enumerate(content.split("\n")) if line]
    return watchpoints