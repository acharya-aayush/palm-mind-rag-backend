import json
import redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL)

def get_chat_history(session_id: str) -> list[dict[str, str]]:
    history = redis_client.get(f"chat:{session_id}")
    if history:
        return json.loads(history)
    return []

def save_chat_history(session_id: str, history: list[dict[str, str]]) -> None:
    redis_client.setex(f"chat:{session_id}", 3600, json.dumps(history))