import json
from typing import Optional, Any, Dict, List

from db import (
    get_user_file_path,
    load_user_data,
)

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve essential profile information for the chatbot context."""
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
    """Retrieve nutrition calculations (BMR, TDEE, Goal Calories, Macros)."""
    try:
        data = load_user_data(user_id)
        if not data:
            return None
        return data.get("nutrition", {})
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"[ERROR] Failed to get nutrition for {user_id}: {e}")
        return None


def get_user_chats(user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retrieve chat history for a user.
    If limit is provided, return only the last `limit` chats.
    """
    try:
        data = load_user_data(user_id)
        if not data:
            return []
        chats = data.get("chats", [])
        if limit is not None and limit > 0:
            return chats[-limit:]
        return chats
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"[ERROR] Failed to get chats for {user_id}: {e}")
        return []


def get_user_field(user_id: str, field: str) -> Optional[Any]:
    """Retrieve a single field (e.g., 'weight', 'goal')."""
    try:
        data = load_user_data(user_id)
        if not data:
            return None
        return data.get(field)
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        print(f"[ERROR] Failed to get field '{field}' for {user_id}: {e}")
        return None


def build_chatbot_context(user_id: str, chat_limit: int = 5) -> Dict[str, Any]:
    """Build a full context dictionary for the chatbot."""
    profile = get_user_profile(user_id) or {}
    nutrition = get_user_nutrition(user_id) or {}
    chats = get_user_chats(user_id, chat_limit)

    return {
        "profile": profile,
        "nutrition": nutrition,
        "recent_chats": chats
    }

#test for the code itself 
#from db import create_user_file, load_user_data

# # Create user file
# path = create_user_file("123", "Test User", age=25, weight=70, height=175, goal="maintenance", activity_level="moderate")
# print("Created:", path)

# # Check user data
# data = load_user_data("123")
# print("Data:", data)

# if __name__ == "__main__":
#     test_user_id = "123"  # change this to an existing user ID in the db i made 123 only for basic test 

#     print(f"🔎 Testing searchengine with user_id={test_user_id}\n")

#     profile = get_user_profile(test_user_id)
#     print("Profile:", profile, "\n")

#     nutrition = get_user_nutrition(test_user_id)
#     print("Nutrition:", nutrition, "\n")

#     chats = get_user_chats(test_user_id, limit=3)
#     print("Recent Chats:", chats, "\n")

#     field = get_user_field(test_user_id, "goal")
#     print("Field (goal):", field, "\n")

#     context = build_chatbot_context(test_user_id, chat_limit=3)
#     print("Full Chatbot Context:\n", json.dumps(context, indent=2))
# 