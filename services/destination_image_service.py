"""
SmartTravel AI — Central Destination Image Service
Unified, central image resolution module for destinations, attractions, hotels, and restaurants.
Guarantees authentic photographs, Google Places API integration, verified curated fallbacks,
and zero 404 / zero placeholder / zero broken image rendering.
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
    clear_cache
)
from services.image_service import (
    CITY_IMAGES,
    ATTRACTION_SPECIFIC_IMAGES,
    CATEGORY_FALLBACKS,
    HOTEL_FALLBACKS,
    RESTAURANT_FALLBACKS,
    GENERAL_FALLBACK,
    get_destination_image as _get_curated_dest_img,
    get_attraction_image as _get_curated_attr_img,
    get_hotel_image as _get_curated_hotel_img,
    get_restaurant_image as _get_curated_rest_img
)

load_dotenv()

# Primary aliases for seamless compatibility across all pages
is_places_api_configured = is_api_configured


def get_destination_image(destination_name: str) -> str:
    """
    Main entry point for retrieving an authentic destination photo.
    First resolves via Google Places / Photo Service cache; falls back to curated verified 200 OK photo.
    Never returns placeholders, dummy IDs, or causes exceptions.
    """
    if not destination_name:
        return GENERAL_FALLBACK
    return get_destination_photo(str(destination_name).strip())


def get_attraction_image(category_name: str = "", attraction_name: str = "", city_name: str = "",
                         latitude: float = None, longitude: float = None) -> str:
    """Retrieves a matched attraction photo or a category fallback."""
    if attraction_name:
        return get_attraction_photo(attraction_name, city_name=city_name, category=category_name,
                                    latitude=latitude, longitude=longitude)
    return _get_curated_attr_img(category_name, attraction_name)


def get_hotel_image(category_name: str = "", hotel_name: str = "", city_name: str = "",
                    latitude: float = None, longitude: float = None) -> str:
    """Retrieves a matched hotel photo or a category fallback."""
    if hotel_name:
        return get_hotel_photo(hotel_name, city_name=city_name, category=category_name,
                               latitude=latitude, longitude=longitude)
    return _get_curated_hotel_img(category_name)


def get_restaurant_image(cuisine_name: str = "", restaurant_name: str = "", city_name: str = "",
                         latitude: float = None, longitude: float = None) -> str:
    """Retrieves a matched restaurant photo or a cuisine fallback."""
    if restaurant_name:
        return get_restaurant_photo(restaurant_name, city_name=city_name, cuisine=cuisine_name,
                                    latitude=latitude, longitude=longitude)
    return _get_curated_rest_img(cuisine_name)
