import json
from typing import Optional, Any, Dict, List


from db import (
    get_user_file_path,
    load_user_data,
)

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve essential profile information for the chatbot context.
    """
    try:
        data = load_user_data(user_id)
        if not data:
            return None
        return {
            "user_id": data.get("user_id"),
            "name": data.get("name"),
            "age": data.get("age"),
            "weight": data.get("weight"),
            "height": data.get("height"),
            "goal": data.get("goal"),
            "activity_level": data.get("activity_level"),
            "language": data.get("language", "en")
        }
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        print(f"[ERROR] Failed to get profile for {user_id}: {e}")
        return None


def get_user_nutrition(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve nutrition calculations (BMR, TDEE, Goal Calories, Macros).
    """
    try:
        data = load_user_data(user_id)
        if not data:
            return None
        return data.get("nutrition", {})
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"[ERROR] Failed to get nutrition for {user_id}: {e}")
        return None


def get_user_chats(user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve full chat history for a user.
    """
    try:
        data = load_user_data(user_id)
        if not data:
            return []
        return data.get("chats", [])
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"[ERROR] Failed to get chats for {user_id}: {e}")
        return []


def get_user_field(user_id: str, field: str) -> Optional[Any]:
    """
    Retrieve a single field (e.g., 'weight', 'goal').
    """
    try:
        data = load_user_data(user_id)
        if not data:
            return None
        return data.get(field)
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        print(f"[ERROR] Failed to get field '{field}' for {user_id}: {e}")
        return None
    
def build_chatbot_context(user_id: str, chat_limit: int = 5) -> Dict[str, Any]:
    """
    Build a full context dictionary for the chatbot.
    Includes: profile, nutrition, and recent chats.
    """
    profile = get_user_profile(user_id) or {}
    nutrition = get_user_nutrition(user_id) or {}
    chats = get_user_chats(user_id, chat_limit)

    return {
        "profile": profile,
        "nutrition": nutrition,
        "recent_chats": chats
    }