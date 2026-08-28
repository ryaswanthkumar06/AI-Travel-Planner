import sys
import os

sys.path.append(os.getcwd())

from database.db_manager import init_db, get_user_by_email, save_user_preferences
from services.auth_service import register_user

init_db()

user = get_user_by_email("test@example.com")
if not user:
    try:
        user_id = register_user("Test Traveler", "test@example.com", "password123")
        save_user_preferences(user_id, {
            "travel_style": "Cultural / History Buff",
            "budget_preference": "Medium (Standard)",
            "food_preference": "Vegetarian",
            "transportation_preference": "Cab / Taxi Services",
            "accommodation_preference": "Mid-range Hotels",
            "interests": ["Historical Places", "Museums & Art"]
        })
        print(f"Default user test@example.com created with ID {user_id}")
    except Exception as e:
        print(f"User registration error: {e}")
else:
    print(f"User test@example.com already exists with ID {user['id']}")
