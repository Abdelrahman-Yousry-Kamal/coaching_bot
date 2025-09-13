import json
import os
import re
from datetime import datetime
from typing import Optional

DATA_DIR = "data"
USERS_DIR = os.path.join(DATA_DIR, "users")
INDEX_FILE = os.path.join(DATA_DIR, "index.json")
MENUS_FILE = os.path.join(DATA_DIR, "menus.json")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_DIR):
        os.makedirs(USERS_DIR, exist_ok=True)
    if not os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

def load_index():
    ensure_data_dir()
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_index(index: dict):
    tmp = INDEX_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=4)
    os.replace(tmp, INDEX_FILE)

def sanitize_filename(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^\w\u0600-\u06FF\-]", "", name)
    if not name:
        name = "unknown"
    return name

def user_filename(user_id: str, name: str) -> str:
    safe = sanitize_filename(name)
    filename = f"{safe}_{user_id}.json"
    return os.path.join(USERS_DIR, filename)

def create_user_file(user_id: str, name: str, age: Optional[int]=None,
                     weight: Optional[float]=None, height: Optional[float]=None,
                     goal: Optional[str]=None, activity_level: Optional[str]=None) -> str:
    ensure_data_dir()
    index = load_index()
    if user_id in index:
        return index[user_id]

    path = user_filename(user_id, name)
    initial_data = {
        "user_id": user_id,
        "name": name,
        "age": age,
        "weight": weight,
        "height": height,
        "goal": goal,
        "activity_level": activity_level,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "language": "en",  
        "chats": [],
        "nutrition": {}
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(initial_data, f, ensure_ascii=False, indent=4)
    os.replace(tmp, path)

    index[user_id] = path
    save_index(index)
    return path

def get_user_file_path(user_id: str) -> Optional[str]:
    ensure_data_dir()
    index = load_index()
    return index.get(user_id)

def load_user_data(user_id: str) -> Optional[dict]:
    path = get_user_file_path(user_id)
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_data(user_id: str, data: dict) -> bool:
    path = get_user_file_path(user_id)
    if not path:
        return False
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(tmp, path)
    return True

def add_chat(user_id: str, user_message: str, bot_response: str):
    data = load_user_data(user_id)
    if data is None:
        create_user_file(user_id, "unknown")
        data = load_user_data(user_id)

    data.setdefault("chats", []).append({
        "user": user_message,
        "bot": bot_response,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_user_data(user_id, data)

def get_chats(user_id: str):
    data = load_user_data(user_id)
    if not data:
        return []
    return data.get("chats", [])

def rename_user_file(user_id: str, new_name: str) -> Optional[str]:
    path = get_user_file_path(user_id)
    if not path or not os.path.exists(path):
        return None
    new_path = user_filename(user_id, new_name)
    if os.path.exists(new_path):
        os.remove(new_path)
    os.replace(path, new_path)
    index = load_index()
    index[user_id] = new_path
    save_index(index)
    data = load_user_data(user_id)
    if data:
        data["name"] = new_name
        save_user_data(user_id, data)
    return new_path

def validate_inputs(weight, height, age, gender, activity_level, goal, surplus=400):
    if not (30 <= weight <= 300):
        raise ValueError("Weight must be between 30kg and 300kg")
    if not (120 <= height <= 250):
        raise ValueError("Height must be between 120cm and 250cm")
    if not (15 <= age <= 90):
        raise ValueError("Age must be between 15 and 90 years")
    if gender.lower() not in ["male", "female"]:
        raise ValueError("Gender must be 'male' or 'female'")
    if activity_level not in ["sedentary", "light", "moderate", "very_active", "extra_active"]:
        raise ValueError("Invalid activity level")
    if goal.lower() not in ["loss", "gain", "maintenance"]:
        raise ValueError("Invalid goal")
    if goal.lower() == "gain" and not (300 <= surplus <= 500):
        raise ValueError("For muscle gain, surplus must be between 300 and 500 kcal")
    return True

def calculate_bmr(weight, height, age, gender):
    if gender.lower() == "male":
        return (10 * weight) + (6.25 * height) - (5 * age) + 5
    elif gender.lower() == "female":
        return (10 * weight) + (6.25 * height) - (5 * age) - 161
    else:
        raise ValueError("Gender must be 'male' or 'female'")

def calculate_tdee(bmr, activity_level):
    factors = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9,
    }
    if activity_level not in factors:
        raise ValueError("Invalid activity level")
    return bmr * factors[activity_level]

def adjust_calories_for_goal(tdee, goal, surplus=400):
    goal = goal.lower()
    if goal == "loss":
        return tdee - 500
    elif goal == "gain":
        if not (300 <= surplus <= 500):
            raise ValueError("For muscle gain, surplus must be between 300 and 500 kcal")
        return tdee + surplus
    elif goal == "maintenance":
        return tdee
    else:
        raise ValueError("Goal must be 'loss', 'gain', or 'maintenance'")

def calculate_macros(total_calories, goal):
    goal = goal.lower()
    if goal == "loss":
        split = {"protein": 0.40, "carbs": 0.30, "fat": 0.30}
    elif goal == "gain":
        split = {"protein": 0.35, "carbs": 0.40, "fat": 0.25}
    else:  
        split = {"protein": 0.30, "carbs": 0.40, "fat": 0.30}

    return {
        "protein_g": round((total_calories * split["protein"]) / 4),
        "carbs_g": round((total_calories * split["carbs"]) / 4),
        "fat_g": round((total_calories * split["fat"]) / 9),
    }

def calculate_nutrition(user_id: str):
    data = load_user_data(user_id)
    if not data or not all([data.get("weight"), data.get("height"), data.get("age"), data.get("gender"), data.get("activity_level"), data.get("goal")]):
        return "Please provide all required data (weight, height, age, gender, activity level, goal)"

    weight = data["weight"]
    height = data["height"]
    age = data["age"]
    gender = data["gender"]
    activity_level = data["activity_level"]
    goal = data["goal"]
    surplus = data.get("surplus", 400)

    try:
        validate_inputs(weight, height, age, gender, activity_level, goal, surplus)
        bmr = calculate_bmr(weight, height, age, gender)
        tdee = calculate_tdee(bmr, activity_level)
        goal_calories = adjust_calories_for_goal(tdee, goal, surplus)
        macros = calculate_macros(goal_calories, goal)

        results = {
            "BMR": round(bmr),
            "TDEE": round(tdee),
            "Goal Calories": round(goal_calories),
            "Goal": goal.capitalize(),
            "Macros": macros
        }
        data["nutrition"] = results
        save_user_data(user_id, data)
        return results
    except ValueError as e:
        return str(e)

if __name__ == "__main__":
    print("=== Dietitian: Your Nutrition Assistant ===")
    print("Welcome to Dietitian! I'm your smart assistant designed to guide you step-by-step in your health journey...")

    user_id = input("Enter user ID: ").strip()
    name = input("Enter your name: ").strip()
    create_user_file(user_id, name)

    data = load_user_data(user_id)
    data["weight"] = float(input("Enter weight (kg): "))
    data["height"] = float(input("Enter height (cm): "))
    data["age"] = int(input("Enter age (years): "))
    data["gender"] = input("Enter gender (male/female): ").strip().lower()
    data["activity_level"] = input("Enter activity level (sedentary/light/moderate/very_active/extra_active): ").strip().lower()
    data["goal"] = input("Enter goal (loss/gain/maintenance): ").strip().lower()
    if data["goal"] == "gain":
        data["surplus"] = int(input("Enter surplus calories (300–500): "))
    else:
        data["surplus"] = 400
    save_user_data(user_id, data)

    results = calculate_nutrition(user_id)
    if isinstance(results, dict):
        bot_response = (
            f"Your data has been analyzed successfully:\n"
            f"Calories: {results['Goal Calories']} kcal\n"
            f"Protein: {results['Macros']['protein_g']}g\n"
            f"Carbs: {results['Macros']['carbs_g']}g\n"
            f"Fats: {results['Macros']['fat_g']}g\n"
            f"Your daily goal has been set precisely!"
        )
        add_chat(user_id, "Calculate my nutrition needs", bot_response)
        print(f"\n=== Results for {name} ===")
        print(f"- Basal Metabolic Rate (BMR): {results['BMR']} calories/day")
        print(f"- Total Daily Energy Expenditure (TDEE): {results['TDEE']} calories/day")
        print(f"- Goal Calories: {results['Goal Calories']} kcal/day ({results['Goal']})")
        print(f"- Macros: {results['Macros']['protein_g']}g protein, {results['Macros']['carbs_g']}g carbs, {results['Macros']['fat_g']}g fat")
        print(f"✅ Data and results saved to {get_user_file_path(user_id)}")
        print("Chats:", get_chats(user_id))
    else:
        print(f"Error: {results}")
