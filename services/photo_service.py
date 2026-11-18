"""
SmartTravel AI — Centralized Place Photo Service
Unified architecture for resolving, caching, and rendering real Google Place Photos
for Destinations, Attractions, Hotels, Restaurants, and Itinerary stops.

Fallback Chain:
  Level 1: Google Place Photo (Primary)
  Level 2: Google Place Photo (Secondary from gallery)
  Level 3: Curated Landmark / Destination / Category photo
  Level 4: Dynamic styled gradient card with category iconography (Never broken)
"""

import os
import time
import hashlib
import logging
import re
from difflib import SequenceMatcher
import urllib.parse
import requests
from dotenv import load_dotenv
from services.image_service import (
    get_destination_image as _get_curated_dest_img,
    get_attraction_image as _get_curated_attr_img,
    get_hotel_image as _get_curated_hotel_img,
    get_restaurant_image as _get_curated_rest_img,
    GENERAL_FALLBACK
)

load_dotenv()
logger = logging.getLogger(__name__)

# ── API Credentials & Configuration ─────────────────────────────────────
GOOGLE_API_KEY = (
    os.getenv("GOOGLE_PLACES_API_KEY") or
    os.getenv("GOOGLE_MAPS_API_KEY") or
    ""
).strip()

PLACES_NEW_BASE    = "https://places.googleapis.com/v1"
PLACES_LEGACY_BASE = "https://maps.googleapis.com/maps/api/place"
REQUEST_TIMEOUT    = 5  # seconds

# In-memory session cache: key = place_id or hash(query), value = dict with TTL
_PHOTO_CACHE: dict = {}
_CACHE_TTL: int = 1800  # 30 minutes


def is_api_configured() -> bool:
    """Returns True if a valid Google API key is configured."""
    return bool(GOOGLE_API_KEY and GOOGLE_API_KEY not in ("", "your_key_here"))


def _make_cache_key(*args) -> str:
    raw = "|".join(str(a).strip().lower() for a in args if a is not None)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _get_from_cache(cache_key: str):
    entry = _PHOTO_CACHE.get(cache_key)
    if entry and (time.time() - entry["ts"] < _CACHE_TTL):
        return entry["data"]
    return None


def _set_in_cache(cache_key: str, data: dict, place_id: str = None):
    entry = {"ts": time.time(), "data": data}
    _PHOTO_CACHE[cache_key] = entry
    if place_id:
        _PHOTO_CACHE[f"place_id_{place_id.strip()}"] = entry


# ── Google Places API (New) Engine ──────────────────────────────────────
def _fetch_places_new(query: str, max_results: int = 5, location_bias: tuple = None) -> list:
    if not is_api_configured():
        return []
    try:
        url = f"{PLACES_NEW_BASE}/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.location,places.rating,places.userRatingCount,"
                "places.googleMapsUri,places.photos,places.currentOpeningHours,"
                "places.nationalPhoneNumber,places.websiteUri,places.reviews"
            )
        }
        body = {"textQuery": query, "maxResultCount": max(1, min(int(max_results), 10))}
        if location_bias and len(location_bias) == 2:
            body["locationBias"] = {
                "circle": {
                    "center": {
                        "latitude": float(location_bias[0]),
                        "longitude": float(location_bias[1])
                    },
                    "radius": 10000.0
                }
            }
        resp = requests.post(url, json=body, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            return resp.json().get("places", [])
    except Exception:
        pass
    return []


def _fetch_place_details_new(place_id: str) -> dict:
    if not is_api_configured() or not place_id:
        return {}
    try:
        url = f"{PLACES_NEW_BASE}/places/{place_id}"
        headers = {
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": (
                "id,displayName,formattedAddress,location,rating,userRatingCount,"
                "googleMapsUri,photos,currentOpeningHours,nationalPhoneNumber,websiteUri,reviews"
            )
        }
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}


def _build_new_photo_url(photo_name: str, max_width: int = 800, max_height: int = 600) -> str:
    """
    Resolve a Google photo reference on the server and return its temporary photo URI.
    The API key is never sent to the browser. Google photo URIs are intentionally
    not cached because photo resource names and media URIs can expire.
    """
    if not photo_name or not is_api_configured():
        return ""
    url = f"{PLACES_NEW_BASE}/{photo_name}/media"
    params = {
        "maxWidthPx": max(1, min(int(max_width), 4800)),
        "maxHeightPx": max(1, min(int(max_height), 4800)),
        "key": GOOGLE_API_KEY,
        "skipHttpRedirect": "true"
    }
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            photo_uri = response.json().get("photoUri", "")
            if photo_uri.startswith("https://"):
                return photo_uri
        logger.warning("Google photo media lookup failed with HTTP %s.", response.status_code)
    except requests.exceptions.RequestException as exc:
        logger.warning("Google photo media lookup failed: %s", type(exc).__name__)
    except (ValueError, TypeError):
        logger.warning("Google photo media lookup returned an invalid response.")
    return ""


# ── Google Places API (Legacy) Fallback Engine ──────────────────────────
def _fetch_places_legacy(query: str) -> list:
    if not is_api_configured():
        return []
    try:
        url = f"{PLACES_LEGACY_BASE}/textsearch/json"
        params = {"query": query, "key": GOOGLE_API_KEY}
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") in ("OK", "ZERO_RESULTS"):
                return data.get("results", [])
    except Exception:
        pass
    return []


def _normalise_match_text(value: str) -> str:
    """Normalise place names before comparing a Places result with the requested entity."""
    value = str(value or "").lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _candidate_match_score(candidate: dict, expected_name: str, city_name: str = "",
                           latitude: float = None, longitude: float = None) -> float:
    """Conservative identity check; rejects unrelated first-result matches."""
    returned_name = candidate.get("displayName", {}).get("text") or candidate.get("name") or ""
    expected = _normalise_match_text(expected_name)
    actual = _normalise_match_text(returned_name)
    city = _normalise_match_text(city_name)
    if not expected or not actual:
        return 0.0

    if expected == city and (actual == expected or expected in actual):
        return 1.0

    stop_words = {"the", "of", "and", "at", "in", "near", "india"}
    expected_tokens = [t for t in expected.split() if t not in stop_words and t != city]
    actual_tokens = [t for t in actual.split() if t not in stop_words and t != city]
    if not expected_tokens:
        expected_tokens = expected.split()
    if not actual_tokens:
        actual_tokens = actual.split()

    matched = sum(1 for token in expected_tokens if token in actual_tokens)
    recall = matched / max(1, len(expected_tokens))
    precision = matched / max(1, len(actual_tokens))
    token_f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    similarity = SequenceMatcher(None, expected, actual).ratio()
    score = max(similarity, token_f1)

    location = candidate.get("location") or (candidate.get("geometry") or {}).get("location") or {}
    candidate_lat = location.get("latitude", location.get("lat"))
    candidate_lng = location.get("longitude", location.get("lng"))
    if latitude is not None and longitude is not None and candidate_lat is not None and candidate_lng is not None:
        try:
            from services.routing_service import haversine_distance
            km = haversine_distance(float(latitude), float(longitude), float(candidate_lat), float(candidate_lng))
            if km > 20:
                score *= 0.65
        except (TypeError, ValueError):
            pass
    return score


def _select_matching_candidate(candidates: list, expected_name: str, city_name: str = "",
                               latitude: float = None, longitude: float = None):
    """Return the strongest name/location match, or None when confidence is too low."""
    if not candidates:
        return None
    ranked = sorted(
        candidates,
        key=lambda p: _candidate_match_score(p, expected_name, city_name, latitude, longitude),
        reverse=True
    )
    best = ranked[0]
    score = _candidate_match_score(best, expected_name, city_name, latitude, longitude)
    if score < 0.82:
        logger.info("Rejected uncertain Places match for %r in %r (score %.2f).",
                    expected_name, city_name, score)
        return None
    return best


def _build_legacy_photo_url(photo_ref: str, max_width: int = 800) -> str:
    if not photo_ref or not is_api_configured():
        return ""
    url = f"{PLACES_LEGACY_BASE}/photo"
    params = {
        "maxwidth": max_width,
        "photoreference": photo_ref,
        "key": GOOGLE_API_KEY
    }
    try:
        # Follow Google's redirect on the server so the API key is not exposed
        # in a browser-visible image URL.
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT,
                                allow_redirects=True, stream=True)
        try:
            if response.status_code == 200 and response.url.startswith("https://"):
                return response.url
            logger.warning("Legacy Google photo lookup failed with HTTP %s.", response.status_code)
        finally:
            response.close()
    except requests.exceptions.RequestException as exc:
        logger.warning("Legacy Google photo lookup failed: %s", type(exc).__name__)
    return ""


# ── Core Place & Photo Resolver ─────────────────────────────────────────
def resolve_place_photo(
    place_name: str,
    city_name: str = "",
    state: str = "",
    category: str = "",
    max_width: int = 800,
    max_height: int = 600,
    latitude: float = None,
    longitude: float = None
) -> dict:
    """
    Main entry point for resolving a place and retrieving its photos, place_id,
    ratings, reviews, address, and Google Maps URL.
    """
    clean_name = str(place_name or "").strip()
    clean_city = str(city_name or "").strip()
    clean_state = str(state or "").strip()
    clean_cat = str(category or "").strip().lower()

    if not clean_name and not clean_city:
        return {
            "success": False,
            "photo_url": GENERAL_FALLBACK,
            "gallery_photos": [GENERAL_FALLBACK],
            "source": "Default",
            "is_google_photo": False,
            "place_id": None,
            "name": "Unknown",
            "attribution": None,
            "rating": None,
            "reviews_count": None,
            "place_verified": False,
            "google_place_id": None,
            "address": "",
            "maps_url": "https://www.google.com/maps",
            "fallback_used": True
        }

    # 1. Determine Level 3 Curated Fallback
    is_hotel = any(k in clean_cat or k in clean_name.lower() for k in ("hotel", "stay", "resort", "inn", "palace & luxury", "hostel", "homestay", "suites"))
    is_dining = any(k in clean_cat or k in clean_name.lower() for k in ("dining", "restaurant", "food", "cafe", "bhavan", "durbar", "darbar", "chowk", "kitchen", "biryani", "bakery", "roastery"))

    if is_hotel:
        level3_photo = _get_curated_hotel_img(clean_cat or clean_name)
    elif is_dining:
        level3_photo = _get_curated_rest_img(clean_cat or clean_name)
    elif clean_name and clean_name.lower() != clean_city.lower():
        level3_photo = _get_curated_attr_img(clean_cat, clean_name)
    else:
        level3_photo = _get_curated_dest_img(clean_city or clean_name)

    ck = _make_cache_key("resolve_photo", clean_name, clean_city, clean_state, clean_cat,
                         latitude, longitude)
    # Do not cache Google Places responses or photo resource names: Google can
    # expire photo names/URIs and Places content is subject to storage restrictions.
    # Construct search query with sufficient geographic context
    query_parts = [clean_name]
    if clean_city and clean_city.lower() not in clean_name.lower():
        query_parts.append(clean_city)
    if clean_state and clean_state.lower() not in clean_name.lower():
        query_parts.append(clean_state)
    query_parts.append("India")
    query = ", ".join(query_parts)

    fallback_maps = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(query)}"

    fallback_result = {
        "success": True,
        "photo_url": level3_photo,
        "gallery_photos": [level3_photo],
        "source": "Curated Registry",
        "is_google_photo": False,
        "place_id": None,
        "name": clean_name or clean_city,
        "attribution": None,
        "rating": None,
        "reviews_count": None,
        "place_verified": False,
        "google_place_id": None,
        "address": f"{clean_name}, {clean_city}, India" if clean_city else clean_name,
        "maps_url": fallback_maps,
        "phone": None,
        "website": None,
        "opening_hours": None,
        "open_now": None,
        "reviews": [],
        "fallback_used": True
    }

    if not is_api_configured():
        _set_in_cache(ck, fallback_result)
        return fallback_result

    # ── Attempt A: Places API (New) ───────────────────────────────────
    location_bias = (latitude, longitude) if latitude is not None and longitude is not None else None
    new_results = _fetch_places_new(query, max_results=5, location_bias=location_bias)
    p = _select_matching_candidate(new_results, clean_name or clean_city, clean_city,
                                   latitude, longitude)
    if p:
        place_id = p.get("id")
        photos_raw = p.get("photos", [])
        gallery = []
        primary_photo = level3_photo
        attribution = None

        if photos_raw:
            for idx, pr in enumerate(photos_raw[:5]):
                p_name = pr.get("name", "")
                if p_name:
                    p_url = _build_new_photo_url(p_name, max_width, max_height)
                    if p_url:
                        gallery.append(p_url)
                        if idx == 0:
                            primary_photo = p_url
                            author_attribs = pr.get("authorAttributions", [])
                            if author_attribs:
                                attribution = author_attribs[0].get("displayName", "Google Maps Contributor")

        loc = p.get("location", {})
        hours_data = p.get("currentOpeningHours", {})
        open_now = hours_data.get("openNow")
        weekday_desc = hours_data.get("weekdayDescriptions", [])

        reviews_raw = p.get("reviews", [])
        reviews = []
        for r in reviews_raw[:3]:
            reviews.append({
                "author": r.get("authorAttribution", {}).get("displayName", "Verified Traveler"),
                "rating": r.get("rating", 5),
                "text": r.get("originalText", {}).get("text") or r.get("text", {}).get("text", ""),
                "relative_time": r.get("relativePublishTimeDescription", "Recently"),
            })

        result = {
            "success": True,
            "photo_url": primary_photo if gallery else level3_photo,
            "gallery_photos": gallery if gallery else [level3_photo],
            "source": "Google Places API (New)",
            "is_google_photo": bool(gallery),
            "place_id": place_id,
            "name": p.get("displayName", {}).get("text", clean_name),
            "attribution": attribution,
            "rating": p.get("rating"),
            "reviews_count": p.get("userRatingCount"),
            "place_verified": True,
            "google_place_id": place_id,
            "address": p.get("formattedAddress", fallback_result["address"]),
            "latitude": loc.get("latitude"),
            "longitude": loc.get("longitude"),
            "maps_url": p.get("googleMapsUri") or fallback_maps,
            "phone": p.get("nationalPhoneNumber"),
            "website": p.get("websiteUri"),
            "opening_hours": weekday_desc,
            "open_now": open_now,
            "reviews": reviews,
            "fallback_used": not bool(gallery)
        }
        return result

    # ── Attempt B: Places API (Legacy) ────────────────────────────────
    legacy_results = _fetch_places_legacy(query)
    p = _select_matching_candidate(legacy_results, clean_name or clean_city, clean_city,
                                   latitude, longitude)
    if p:
        place_id = p.get("place_id")
        photos_raw = p.get("photos", [])
        gallery = []
        primary_photo = level3_photo
        attribution = None

        if photos_raw:
            for idx, pr in enumerate(photos_raw[:5]):
                p_ref = pr.get("photo_reference", "")
                if p_ref:
                    p_url = _build_legacy_photo_url(p_ref, max_width)
                    if p_url:
                        gallery.append(p_url)
                        if idx == 0:
                            primary_photo = p_url
                            html_attribs = pr.get("html_attributions", [])
                            if html_attribs:
                                attribution = "Google Maps Contributor"

        geom = p.get("geometry", {}).get("location", {})
        result = {
            "success": True,
            "photo_url": primary_photo if gallery else level3_photo,
            "gallery_photos": gallery if gallery else [level3_photo],
            "source": "Google Places API (Legacy)",
            "is_google_photo": bool(gallery),
            "place_id": place_id,
            "name": p.get("name", clean_name),
            "attribution": attribution,
            "rating": p.get("rating"),
            "reviews_count": p.get("user_ratings_total"),
            "place_verified": True,
            "google_place_id": place_id,
            "address": p.get("formatted_address", fallback_result["address"]),
            "latitude": geom.get("lat"),
            "longitude": geom.get("lng"),
            "maps_url": f"https://www.google.com/maps/search/?api=1&query=place_id:{place_id}" if place_id else fallback_maps,
            "phone": None,
            "website": None,
            "opening_hours": None,
            "open_now": p.get("opening_hours", {}).get("open_now"),
            "reviews": [],
            "fallback_used": not bool(gallery)
        }
        return result

    # ── Fallback ──────────────────────────────────────────────────────
    _set_in_cache(ck, fallback_result)
    return fallback_result


# ── Specialized Helpers for Pages & Components ───────────────────────────
def get_destination_photo(city_name: str) -> str:
    """Returns the primary Google Place Photo URL or curated fallback for a destination."""
    res = resolve_place_photo(city_name, city_name=city_name, category="city")
    return res.get("photo_url") or _get_curated_dest_img(city_name)


def get_attraction_photo(attraction_name: str, city_name: str = "", category: str = "",
                         latitude: float = None, longitude: float = None) -> str:
    """Returns a matched Google photo or a relevant curated fallback."""
    res = resolve_place_photo(attraction_name, city_name=city_name, category=category or "attraction",
                              latitude=latitude, longitude=longitude)
    return res.get("photo_url") or _get_curated_attr_img(category, attraction_name)


def get_hotel_photo(hotel_name: str, city_name: str = "", category: str = "",
                    latitude: float = None, longitude: float = None) -> str:
    """Returns a matched Google photo or a relevant curated fallback."""
    res = resolve_place_photo(hotel_name, city_name=city_name, category=f"hotel {category or ''}",
                              latitude=latitude, longitude=longitude)
    return res.get("photo_url") or _get_curated_hotel_img(category)


def get_restaurant_photo(restaurant_name: str, city_name: str = "", cuisine: str = "",
                         latitude: float = None, longitude: float = None) -> str:
    """Returns a matched Google photo or a relevant curated fallback."""
    res = resolve_place_photo(restaurant_name, city_name=city_name, category=f"restaurant {cuisine or ''}",
                              latitude=latitude, longitude=longitude)
    return res.get("photo_url") or _get_curated_rest_img(cuisine)


def get_place_photo(place_id: str, max_width: int = 800, max_height: int = 600) -> str:
    """Retrieves the photo URL for a known place_id."""
    if not place_id:
        return GENERAL_FALLBACK
    cached = _get_from_cache(f"place_id_{place_id.strip()}")
    if cached and cached.get("photo_url"):
        return cached["photo_url"]

    # If details required
    details = _fetch_place_details_new(place_id)
    if details:
        photos = details.get("photos", [])
        if photos:
            return _build_new_photo_url(photos[0].get("name", ""), max_width, max_height)
    return GENERAL_FALLBACK


def get_place_photos(place_id_or_name: str, city_name: str = "", count: int = 5) -> list:
    """Retrieves up to `count` photo URLs for a place or destination."""
    res = resolve_place_photo(place_id_or_name, city_name=city_name)
    gallery = res.get("gallery_photos", [])
    if gallery:
        return gallery[:count]
    return [res.get("photo_url") or GENERAL_FALLBACK]


def get_place_details_with_photos(place_id_or_name: str, city_name: str = "") -> dict:
    """Returns full place metadata including ratings, hours, address, and photos."""
    return resolve_place_photo(place_id_or_name, city_name=city_name)


# ── HTML Image Renderer Helper (Zero Broken Images & Zero Markdown Leakage) ───
def render_card_image_html(
    photo_url: str,
    alt_name: str,
    height_px: int = 155,
    border_radius: str = "12px 12px 0 0",
    attribution: str = None,
    category_icon: str = "📍"
) -> str:
    """
    Renders an HTML <img> tag with a self-healing onerror javascript handler.
    If the image fails to load, it automatically transitions to a stylish gradient card.
    Never shows broken image icons, empty boxes, or leaks raw HTML into markdown.
    """
    safe_alt = str(alt_name or "Place").replace('"', '&quot;').replace("'", "&#39;")
    safe_url = photo_url or GENERAL_FALLBACK
    safe_icon = category_icon or "📍"

    attrib_html = ""
    if attribution:
        attrib_html = f'<div style="position:absolute;bottom:4px;right:6px;background:rgba(0,0,0,0.60);border-radius:4px;padding:2px 6px;font-size:0.62rem;color:rgba(255,255,255,0.75);">📸 {attribution}</div>'

    return (
        f'<div style="position:relative;width:100%;height:{height_px}px;overflow:hidden;border-radius:{border_radius};background:linear-gradient(135deg,#17243D,#284068);">'
        f'<img src="{safe_url}" alt="{safe_alt}" style="width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.3s ease;" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';" />'
        f'<div style="display:none;width:100%;height:100%;align-items:center;justify-content:center;background:linear-gradient(135deg,#17243D,#FF7A59);color:#FFFFFF;font-family:Outfit,sans-serif;font-size:1.1rem;font-weight:700;padding:12px;text-align:center;">{safe_icon} {safe_alt}</div>'
        f'{attrib_html}'
        f'</div>'
    )


def clear_cache():
    """Clears the session-level photo cache."""
    _PHOTO_CACHE.clear()


# ── Global Compatibility Aliases ──────────────────────────────────────────
is_places_api_configured = is_api_configured
get_destination_image = get_destination_photo
get_attraction_image = get_attraction_photo
get_hotel_image = get_hotel_photo
get_restaurant_image = get_restaurant_photo

