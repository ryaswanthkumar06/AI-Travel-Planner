import sqlite3
import os
import json

# Google Places content (photos, ratings, reviews, and details) must be refreshed
# when the user views a saved place. Place IDs are the durable lookup identifiers.
_GOOGLE_TRANSIENT_FIELDS = {
    "photo_url", "image_url", "photos", "photo_source",
    "photo_attribution", "photo_attribution_url", "attribution", "attribution_url",
    "rating", "google_rating", "rating_source", "review_count", "reviews_count",
    "user_rating_count", "reviews", "place_verified",
    "googleMapsUri", "google_maps_uri", "google_maps_url", "maps_uri"
}


def _strip_transient_google_content(value):
    """Remove non-persistable Places response fields while retaining place IDs."""
    if isinstance(value, dict):
        return {
            key: _strip_transient_google_content(item)
            for key, item in value.items()
            if key not in _GOOGLE_TRANSIENT_FIELDS
        }
    if isinstance(value, list):
        return [_strip_transient_google_content(item) for item in value]
    return value


def _sanitize_json_for_storage(value):
    """Sanitize dict/list values or JSON strings before persisting trip payloads."""
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return value
        return json.dumps(_strip_transient_google_content(parsed), ensure_ascii=False)
    if isinstance(value, (dict, list)):
        return json.dumps(_strip_transient_google_content(value), ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False)

DB_DIR = "data"
DB_NAME = "travel_planner.db"
DB_PATH = os.path.join(DB_DIR, DB_NAME)

def get_connection():
    """Returns a SQLite connection. Creates the data directory if needed."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    """Initializes the database schema if tables do not exist and applies migrations."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create user preferences table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id INTEGER PRIMARY KEY,
        interests TEXT,
        food_preference TEXT,
        transportation_preference TEXT,
        accommodation_preference TEXT,
        travel_style TEXT,
        budget_preference TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    
    # Create trips table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        destination TEXT NOT NULL,
        duration_days INTEGER NOT NULL,
        travelers INTEGER NOT NULL,
        budget REAL NOT NULL,
        interests TEXT,
        itinerary_json TEXT NOT NULL,
        hotel_json TEXT,
        restaurants_json TEXT,
        start_date TEXT,
        end_date TEXT,
        travel_style TEXT,
        food_preferences TEXT,
        accommodation TEXT,
        transportation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    
    # Safe column migration for existing databases
    cursor.execute("PRAGMA table_info(trips)")
    existing_cols = {col["name"] for col in cursor.fetchall()}
    
    new_columns = [
        ("start_date", "TEXT"),
        ("end_date", "TEXT"),
        ("travel_style", "TEXT"),
        ("food_preferences", "TEXT"),
        ("accommodation", "TEXT"),
        ("transportation", "TEXT")
    ]
    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE trips ADD COLUMN {col_name} {col_type}")
    
    conn.commit()
    conn.close()

def create_user(name, email, password_hash):
    """Creates a new user. Returns the user's ID or raises ValueError if email already exists."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email.lower().strip(), password_hash)
        )
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        raise ValueError(f"An account with email {email} already exists.")
    finally:
        conn.close()

def get_user_by_email(email):
    """Retrieves a user profile by email. Returns a dict or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_user_by_id(user_id):
    """Retrieves a user profile by user_id. Returns a dict or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def save_user_preferences(user_id, interests=None, food_preference=None, transportation_preference=None, accommodation_preference=None, travel_style=None, budget_preference=None):
    """Inserts or updates user travel preferences."""
    conn = get_connection()
    cursor = conn.cursor()
    
    interests_str = json.dumps(interests) if isinstance(interests, list) else str(interests or "")
    
    cursor.execute("""
    INSERT INTO user_preferences (user_id, interests, food_preference, transportation_preference, accommodation_preference, travel_style, budget_preference)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        interests=excluded.interests,
        food_preference=excluded.food_preference,
        transportation_preference=excluded.transportation_preference,
        accommodation_preference=excluded.accommodation_preference,
        travel_style=excluded.travel_style,
        budget_preference=excluded.budget_preference
    """, (
        user_id,
        interests_str,
        food_preference,
        transportation_preference,
        accommodation_preference,
        travel_style,
        budget_preference
    ))
    conn.commit()
    conn.close()

def get_user_preferences(user_id):
    """Fetches user preferences. Returns a dictionary with defaults if not configured."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        pref = dict(row)
        try:
            if pref.get("interests") and pref["interests"].startswith("["):
                pref["interests"] = json.loads(pref["interests"])
        except Exception:
            pass
        return pref
        
    return {
        "user_id": user_id,
        "interests": ["Historical Places", "Local Street Food"],
        "food_preference": "No Preference (Everything)",
        "transportation_preference": "Walking & Public Transit",
        "accommodation_preference": "Mid-range Hotels",
        "travel_style": "Casual",
        "budget_preference": "Medium"
    }

def save_trip(
    user_id,
    name,
    destination,
    duration_days=3,
    travelers=2,
    budget=30000.0,
    interests=None,
    itinerary_json="[]",
    hotel_json="{}",
    restaurants_json="[]",
    start_date=None,
    end_date=None,
    travel_style=None,
    food_preferences=None,
    accommodation=None,
    transportation=None,
    **kwargs
):
    """Saves a generated itinerary to the database. Supports all optional metadata parameters safely."""
    conn = get_connection()
    cursor = conn.cursor()
    
    interests_str = json.dumps(interests) if isinstance(interests, (list, tuple)) else str(interests or "")
    food_pref_str = json.dumps(food_preferences) if isinstance(food_preferences, (list, tuple)) else str(food_preferences or "")
    itin_str = _sanitize_json_for_storage(itinerary_json)
    hotel_str = _sanitize_json_for_storage(hotel_json)
    rest_str = _sanitize_json_for_storage(restaurants_json)
    
    cursor.execute("""
    INSERT INTO trips (
        user_id, name, destination, duration_days, travelers, budget, interests,
        itinerary_json, hotel_json, restaurants_json, start_date, end_date,
        travel_style, food_preferences, accommodation, transportation
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        name,
        destination,
        int(duration_days or 3),
        int(travelers or 2),
        float(budget or 0.0),
        interests_str,
        itin_str,
        hotel_str,
        rest_str,
        str(start_date or ""),
        str(end_date or ""),
        str(travel_style or ""),
        food_pref_str,
        str(accommodation or ""),
        str(transportation or "")
    ))
    
    trip_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return trip_id

def get_user_trips(user_id):
    """Retrieves all trips saved by a specific user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_trip_by_id(trip_id):
    """Retrieves a specific trip by its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def delete_trip(trip_id):
    """Deletes a trip from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    conn.commit()
    conn.close()

# Initialize database on module load
init_db()
