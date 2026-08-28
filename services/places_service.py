import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

def is_google_places_available() -> bool:
    """Checks if a valid Google Maps / Places API key is configured."""
    return bool(GOOGLE_MAPS_API_KEY and GOOGLE_MAPS_API_KEY.strip() and GOOGLE_MAPS_API_KEY != "your_key_here")

def search_places_google(query: str, location_bias: tuple = None, max_results: int = 5) -> list:
    """
    Searches places using Google Places API (New) - Text Search.
    location_bias: (lat, lng) tuple
    """
    if not is_google_places_available():
        return []
        
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.googleMapsUri,places.photos,places.currentOpeningHours"
    }
    
    payload = {
        "textQuery": query,
        "maxResultCount": max_results
    }
    if location_bias:
        payload["locationBias"] = {
            "circle": {
                "center": {
                    "latitude": location_bias[0],
                    "longitude": location_bias[1]
                },
                "radius": 20000.0  # 20km radius
            }
        }
        
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            places = []
            for p in data.get("places", []):
                loc = p.get("location", {})
                places.append({
                    "place_id": p.get("id"),
                    "name": p.get("displayName", {}).get("text", query),
                    "address": p.get("formattedAddress", ""),
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude"),
                    "rating": p.get("rating"),
                    "reviews_count": p.get("userRatingCount"),
                    "maps_uri": p.get("googleMapsUri"),
                    "photos": p.get("photos", [])
                })
            return places
    except Exception:
        pass
    return []

def get_place_photo_url(photo_name: str, max_width: int = 400) -> str:
    """
    Constructs a Google Place Photo media URL from the photo resource name.
    """
    if not photo_name or not is_google_places_available():
        return ""
    return f"https://places.googleapis.com/v1/{photo_name}/media?maxHeightPx={max_width}&maxWidthPx={max_width}&key={GOOGLE_MAPS_API_KEY}"
