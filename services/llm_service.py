"""
SmartTravel AI — Gemini AI LLM Service
Handles AI-powered travel itinerary enrichment and assistant queries using the Google Gemini API.
Configurable via GEMINI_MODEL (defaults to gemini-3.8-flash).
Uses secure x-goog-api-key request header, robust timeouts, and silent fallback
to preserve verified database itineraries when AI is unavailable.
"""

import os
import json
import re
import copy
import logging
import requests

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Connect timeout = 3.5s, Read timeout = 12.0s
DEFAULT_TIMEOUT = (3.5, 12.0)


def get_gemini_api_key() -> str:
    """
    Retrieves the Gemini API key securely from environment variables.
    Checks GEMINI_API_KEY first, then LLM_API_KEY.
    Returns an empty string if missing or if set to a placeholder.
    """
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY", "")
    key = key.strip()
    if not key or key in ("your_gemini_api_key_here", "your_key_here"):
        return ""
    return key


def is_gemini_configured() -> bool:
    """Returns True if a non-placeholder Gemini API key is configured."""
    return bool(get_gemini_api_key())


def get_gemini_model() -> str:
    """
    Returns the configured Gemini model name from GEMINI_MODEL env var,
    falling back to DEFAULT_GEMINI_MODEL (gemini-3.8-flash).
    """
    model = os.environ.get("GEMINI_MODEL", "").strip()
    return model if model else DEFAULT_GEMINI_MODEL


def get_gemini_endpoint(model: str = None) -> str:
    """
    Constructs the Gemini REST API endpoint for generateContent.
    Never appends the API key as a query parameter.
    """
    selected_model = model or get_gemini_model()
    return f"{GEMINI_API_BASE_URL}/{selected_model}:generateContent"


def _build_request_headers(api_key: str) -> dict:
    """
    Constructs the HTTP request headers using x-goog-api-key.
    Never exposes credentials in logs.
    """
    return {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }


def call_gemini_api(
    prompt: str,
    json_mode: bool = False,
    model: str = None,
    timeout: tuple = DEFAULT_TIMEOUT
) -> str | None:
    """
    Executes a direct REST call to Gemini using secure header authentication.
    Returns the generated response text on success, or None on any failure.
    Logs HTTP status codes and errors safely without exposing the API key.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        logger.debug("Gemini API call skipped: API key is not configured.")
        return None

    endpoint = get_gemini_endpoint(model)
    headers = _build_request_headers(api_key)

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    if json_mode:
        payload["generationConfig"] = {
            "responseMimeType": "application/json"
        }

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"]
            logger.warning("Gemini returned HTTP 200 but response contained no candidate parts.")
            return None
        elif response.status_code == 429:
            logger.warning("Gemini API rate limit exceeded (HTTP 429). Falling back to verified database.")
        elif response.status_code in (401, 403):
            logger.warning("Gemini API authentication failed (HTTP %s). Check your API key.", response.status_code)
        elif response.status_code >= 500:
            logger.warning("Gemini service unavailable (HTTP %s). Falling back to database.", response.status_code)
        else:
            logger.warning("Gemini API responded with unexpected HTTP %s.", response.status_code)
        return None

    except requests.exceptions.Timeout:
        logger.warning("Gemini API request timed out after %s seconds.", timeout)
        return None
    except requests.exceptions.RequestException as e:
        logger.warning("Gemini API network request failed: %s", type(e).__name__)
        return None
    except Exception as e:
        logger.warning("Unexpected error during Gemini API request: %s", type(e).__name__)
        return None


def polish_itinerary_with_llm(itinerary_data: dict) -> dict:
    """
    Enriches candidate itinerary descriptions, personalized 'why_recommended'
    reasons, and day-level travel tips using Google Gemini.

    Strict Safety Rules:
    - If API key is missing or invalid, returns the original itinerary unchanged.
    - If the call times out or fails, returns original itinerary unchanged.
    - Matches events strictly by (type, ID) or (type, name) to prevent cross-matching.
    - Preserves ALL factual data (coordinates, prices, ratings, hours, hotel, weather, safety, budget).
    - Never lets Gemini add, remove, or modify places or factual fields.
    """
    if not itinerary_data or not isinstance(itinerary_data, dict):
        return itinerary_data

    # Return immediately if not configured
    if not is_gemini_configured():
        itinerary_data["llm_polished"] = False
        itinerary_data["llm_warning"] = "API key not configured. Using verified database descriptions."
        return itinerary_data

    days = itinerary_data.get("itinerary", [])
    if not days:
        itinerary_data["llm_polished"] = False
        return itinerary_data

    # Build sanitized prompt payload: omit coordinates, prices, and internal flags
    # to avoid tampering with factual fields
    selected_hotel = itinerary_data.get("selected_hotel", {}) or {}
    prompt_data = {
        "destination": itinerary_data.get("destination", "India"),
        "days": itinerary_data.get("days", len(days)),
        "travelers": itinerary_data.get("travelers", 2),
        "interests": itinerary_data.get("interests", []),
        "travel_style": itinerary_data.get("travel_style", "Balanced"),
        "hotel": {
            "name": selected_hotel.get("name", "Hotel"),
            "category": selected_hotel.get("category", "Standard"),
        },
        "itinerary": []
    }

    for day in days:
        day_events = []
        for e in day.get("events", []):
            ev_type = e.get("type", "Activity")
            if ev_type in ["Attraction", "Restaurant"]:
                day_events.append({
                    "id": e.get("id"),
                    "type": ev_type,
                    "name": e.get("name", ""),
                    "category": e.get("category", ""),
                    "current_description": e.get("description", "")
                })
        prompt_data["itinerary"].append({
            "day": day.get("day", 1),
            "theme": day.get("theme", ""),
            "events": day_events
        })

    prompt = f"""You are a senior India travel coordinator AI for SmartTravel AI.
Polish the travel itinerary supplied below by enhancing place descriptions and adding personalized insights.

CRITICAL CONSTRAINTS:
1. DO NOT invent or add any new attractions, hotels, restaurants, coordinates, prices, ratings, or hours.
2. Use ONLY the places provided in the input JSON. Keep all 'type', 'id', and 'name' fields exactly identical.
3. Enhance the 'description' field for each Attraction and Restaurant with rich historical context, cultural tips, or visitor secrets (2-3 engaging sentences).
4. Add a new string field 'why_recommended' for each Attraction and Restaurant explaining how it matches user interests: {prompt_data['interests']}.
5. Add a new string field 'travel_tip' under each Day object providing practical advice (attire, crowd avoidance, weather precautions).
6. Return ONLY a valid JSON object matching this schema:
   {{
     "itinerary": [
       {{
         "day": 1,
         "travel_tip": "...",
         "events": [
           {{
             "id": 1,
             "type": "Attraction",
             "name": "...",
             "description": "...",
             "why_recommended": "..."
           }}
         ]
       }}
     ]
   }}

Input Itinerary Data:
{json.dumps(prompt_data, indent=2)}
"""

    raw_response = call_gemini_api(prompt, json_mode=True)
    if not raw_response:
        itinerary_data["llm_polished"] = False
        itinerary_data["llm_warning"] = "AI enhancement unavailable. Showing verified database itinerary."
        return itinerary_data

    try:
        # Strip potential markdown fences if present
        cleaned_text = re.sub(r"^```(?:json)?\s*", "", raw_response.strip(), flags=re.IGNORECASE)
        cleaned_text = re.sub(r"\s*```$", "", cleaned_text)

        parsed_llm = json.loads(cleaned_text)
        llm_days = parsed_llm.get("itinerary", [])
        if not isinstance(llm_days, list) or not llm_days:
            itinerary_data["llm_polished"] = False
            itinerary_data["llm_warning"] = "AI response format invalid. Showing verified database itinerary."
            return itinerary_data

        # Merge descriptions, why_recommended, and travel_tip strictly without mutating factual fields
        for idx_day, orig_day in enumerate(itinerary_data["itinerary"]):
            matched_llm_day = None
            orig_day_num = orig_day.get("day")
            for ld in llm_days:
                if ld.get("day") == orig_day_num:
                    matched_llm_day = ld
                    break
            if not matched_llm_day and idx_day < len(llm_days):
                matched_llm_day = llm_days[idx_day]

            if matched_llm_day:
                tip = matched_llm_day.get("travel_tip")
                if tip and isinstance(tip, str):
                    orig_day["travel_tip"] = tip.strip()

                llm_events = matched_llm_day.get("events", [])
                for orig_ev in orig_day.get("events", []):
                    orig_type = orig_ev.get("type")
                    orig_id = orig_ev.get("id")
                    orig_name = str(orig_ev.get("name", "")).strip().lower()

                    if orig_type in ["Attraction", "Restaurant"]:
                        # Stable matching: must match type AND (id or name)
                        matched_llm_ev = None
                        for lev in llm_events:
                            lev_type = lev.get("type")
                            if lev_type != orig_type:
                                # Never match attraction with restaurant even if id is the same
                                continue

                            # Match by ID first if present
                            if orig_id is not None and lev.get("id") is not None:
                                if str(lev.get("id")) == str(orig_id):
                                    matched_llm_ev = lev
                                    break

                            # Match by name as fallback
                            lev_name = str(lev.get("name", "")).strip().lower()
                            if lev_name and lev_name == orig_name:
                                matched_llm_ev = lev
                                break

                        if matched_llm_ev:
                            new_desc = matched_llm_ev.get("description")
                            if new_desc and isinstance(new_desc, str) and len(new_desc.strip()) > 10:
                                orig_ev["description"] = new_desc.strip()

                            why_rec = matched_llm_ev.get("why_recommended")
                            if why_rec and isinstance(why_rec, str):
                                orig_ev["why_recommended"] = why_rec.strip()

        itinerary_data["llm_polished"] = True
        itinerary_data.pop("llm_warning", None)
        return itinerary_data

    except json.JSONDecodeError:
        logger.warning("Failed to decode JSON from Gemini response.")
    except Exception as e:
        logger.warning("Error during Gemini itinerary enrichment: %s", type(e).__name__)

    itinerary_data["llm_polished"] = False
    itinerary_data["llm_warning"] = "AI response parsing failed. Showing verified database itinerary."
    return itinerary_data


def query_gemini_assistant(prompt: str) -> str | None:
    """
    Executes a direct conversational query to Gemini for the Travel Assistant.
    Returns response text on success, or None on failure to trigger local fallback.
    """
    return call_gemini_api(prompt, json_mode=False)
