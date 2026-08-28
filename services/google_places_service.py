"""
SmartTravel AI — Google Places API Service (New & Legacy)
Centralized service layer with place search, place details, photo extraction,
Google Maps URL resolution, opening hours, reviews, and nearby place search.
Seamlessly integrated with services.photo_service.
"""

import os
import urllib.parse
from dotenv import load_dotenv
from services.photo_service import (
    resolve_place_photo,
    get_destination_photo,
    get_attraction_photo,
    get_hotel_photo,
    get_restaurant_photo,
    get_place_photo,
    get_place_photos,
    get_place_details_with_photos,
    is_api_configured,
    render_card_image_html,
    _fetch_places_new,
    _fetch_place_details_new,
    _build_new_photo_url
)

load_dotenv()

# Compatibility alias for home.py and other modules
is_places_api_configured = is_api_configured


def search_place_details(place_name: str, city_name: str = "", category: str = "") -> dict:
    """Full place search: resolves place to Google Place ID, photos, ratings, reviews, and Maps URI."""
    return resolve_place_photo(place_name, city_name=city_name, category=category)


def resolve_destination_place(city: str) -> dict:
    """Resolves a city/destination to a Google Place with photo, rating, reviews, and Maps URI."""
    return resolve_place_photo(city, city_name=city, category="city")


def get_place_photo_url(place_name: str, city_name: str = "", category: str = "", max_width: int = 800, max_height: int = 600) -> str:
    """Returns primary photo URL for a place."""
    res = resolve_place_photo(place_name, city_name=city_name, category=category, max_width=max_width, max_height=max_height)
    return res.get("photo_url", "")


def get_place_maps_url(place_name: str, city_name: str = "") -> str:
    """Returns a Google Maps URL for a place."""
    res = resolve_place_photo(place_name, city_name=city_name)
    return res.get("maps_url", f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(place_name)}")


def get_place_map_url(place_name: str, city_name: str = "") -> str:
    """Alias for get_place_maps_url."""
    return get_place_maps_url(place_name, city_name)


def get_place_reviews(place_name: str, city_name: str = "") -> list:
    """Returns verified place reviews."""
    res = resolve_place_photo(place_name, city_name=city_name)
    return res.get("reviews", [])


def get_opening_hours(place_name: str, city_name: str = "") -> list:
    """Returns opening hours for a place."""
    res = resolve_place_photo(place_name, city_name=city_name)
    return res.get("opening_hours", [])


def get_nearby_places(latitude: float, longitude: float, place_type: str = "tourist_attraction", radius: int = 5000) -> list:
    """Search nearby places using Google Places (New)."""
    if not is_api_configured():
        return []
    try:
        query = f"{place_type.replace('_', ' ')} near {latitude},{longitude}"
        return _fetch_places_new(query, max_results=5)
    except Exception:
        return []


def search_places(query: str, city_name: str = "", category: str = "") -> list:
    """Returns search result list for query."""
    return [resolve_place_photo(query, city_name=city_name, category=category)]


def get_place_details(place_id: str, place_name: str = "", city_name: str = "") -> dict:
    """Retrieves full details for a given place."""
    return resolve_place_photo(place_name or place_id, city_name=city_name)


def clear_cache():
    """Clears the session-level photo and place cache."""
    from services.photo_service import _PHOTO_CACHE
    _PHOTO_CACHE.clear()
