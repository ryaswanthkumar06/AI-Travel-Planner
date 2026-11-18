"""
Unit & Integration Tests for Gemini AI Integration (Phase 1)
All HTTP requests to Gemini are mocked using unittest.mock. No real API calls are executed.
"""

import os
import json
import copy
import pytest
import requests
from unittest.mock import patch, MagicMock

from services.llm_service import (
    get_gemini_api_key,
    get_gemini_model,
    get_gemini_endpoint,
    is_gemini_configured,
    call_gemini_api,
    polish_itinerary_with_llm,
    query_gemini_assistant,
    DEFAULT_GEMINI_MODEL
)
from services.itinerary_service import generate_itinerary


@pytest.fixture
def sample_itinerary():
    """Returns a realistic candidate itinerary dictionary generated from the database."""
    return {
        "success": True,
        "destination": "Goa",
        "days": 2,
        "travelers": 2,
        "budget": 25000.0,
        "interests": ["Beaches", "Historical Places"],
        "trip_pace": "Balanced",
        "travel_style": "Balanced",
        "selected_hotel": {
            "id": 1,
            "name": "The Goa Palace & Luxury Suites",
            "city": "Goa",
            "category": "Luxury",
            "price_per_night": 14500.0,
            "rating": 4.1,
            "latitude": 15.2963,
            "longitude": 74.126
        },
        "selected_restaurants": [
            {
                "id": 1,
                "name": "Goa South Bhavan",
                "cuisine": "South Indian",
                "food_type": "Vegetarian",
                "rating": 4.2
            }
        ],
        "weather_summary": {
            "temp": 28.5,
            "condition": "Clear",
            "humidity": 65,
            "wind": 12.0
        },
        "weather_forecast": [
            {"date": "Day 1", "condition": "Sunny", "max_temp": 30.0, "min_temp": 24.0},
            {"date": "Day 2", "condition": "Partly Cloudy", "max_temp": 29.0, "min_temp": 23.0}
        ],
        "budget_breakdown": {
            "total_budget": 25000.0,
            "hotel_cost": 14500.0,
            "food_cost": 2800.0,
            "attractions_cost": 500.0,
            "transport_cost": 1000.0,
            "total_cost": 18800.0,
            "remaining": 6200.0
        },
        "is_budget_valid": True,
        "budget_advice": ["🟢 Your trip is within budget!"],
        "safety_status": "Safe",
        "safety_message": "No verified hazards on planned route.",
        "safety_alerts": [],
        "itinerary": [
            {
                "day": 1,
                "theme": "Day 1: Beach Highlights",
                "weather": "Sunny (☀️)",
                "rain_prob": 10,
                "distance_km": 12.4,
                "travel_time_mins": 35,
                "day_route_url": "https://www.google.com/maps/dir/...",
                "events": [
                    {
                        "id": 101,
                        "time": "10:00 AM",
                        "name": "Baga Beach",
                        "type": "Attraction",
                        "category": "Beach",
                        "description": "Vibrant beach famous for water sports and beach shacks.",
                        "duration": 90,
                        "cost": 0.0,
                        "rating": 4.3,
                        "latitude": 15.5553,
                        "longitude": 73.7517,
                        "maps_url": "https://www.google.com/maps/search/?api=1&query=Baga+Beach"
                    },
                    {
                        "id": 201,
                        "time": "01:00 PM",
                        "name": "Goa South Bhavan",
                        "type": "Restaurant",
                        "category": "Dining",
                        "description": "Authentic vegetarian meals with coastal flavors.",
                        "duration": 60,
                        "cost": 450.0,
                        "rating": 4.2,
                        "latitude": 15.3033,
                        "longitude": 74.121,
                        "maps_url": "https://www.google.com/maps/search/?api=1&query=Goa+South+Bhavan"
                    }
                ]
            },
            {
                "day": 2,
                "theme": "Day 2: Historical Highlights",
                "weather": "Partly Cloudy (⛅)",
                "rain_prob": 20,
                "distance_km": 18.2,
                "travel_time_mins": 45,
                "day_route_url": "https://www.google.com/maps/dir/...",
                "events": [
                    {
                        "id": 102,
                        "time": "10:00 AM",
                        "name": "Fort Aguada",
                        "type": "Attraction",
                        "category": "Historical",
                        "description": "17th-century Portuguese fortress and lighthouse overlooking the Arabian Sea.",
                        "duration": 90,
                        "cost": 25.0,
                        "rating": 4.6,
                        "latitude": 15.4920,
                        "longitude": 73.7737,
                        "maps_url": "https://www.google.com/maps/search/?api=1&query=Fort+Aguada"
                    }
                ]
            }
        ]
    }


def make_mock_gemini_response(status_code=200, text_content=None, json_dict=None):
    """Helper to build a mock requests.Response object."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    if text_content is not None:
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": text_content}]
                    }
                }
            ]
        }
    elif json_dict is not None:
        mock_resp.json.return_value = json_dict
    else:
        mock_resp.json.return_value = {}
    return mock_resp


# ----------------------------------------------------------------------
# 1. Configuration & Security Tests
# ----------------------------------------------------------------------

def test_missing_api_key(sample_itinerary, monkeypatch):
    """Ensures Gemini is not called if API key is missing."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    assert not is_gemini_configured()
    assert get_gemini_api_key() == ""

    with patch("requests.post") as mock_post:
        result = polish_itinerary_with_llm(sample_itinerary)
        assert result["llm_polished"] is False
        assert "API key not configured" in result.get("llm_warning", "")
        mock_post.assert_not_called()


def test_placeholder_api_key(sample_itinerary, monkeypatch):
    """Ensures placeholders like 'your_gemini_api_key_here' are treated as missing."""
    monkeypatch.setenv("GEMINI_API_KEY", "your_gemini_api_key_here")
    assert not is_gemini_configured()

    with patch("requests.post") as mock_post:
        result = polish_itinerary_with_llm(sample_itinerary)
        assert result["llm_polished"] is False
        mock_post.assert_not_called()


def test_api_key_acceptance_does_not_enforce_arbitrary_prefix(monkeypatch):
    """
    Ensures get_gemini_api_key and is_gemini_configured do NOT reject valid Google AI
    Studio authorization keys based on an assumed or hardcoded key prefix.
    """
    for candidate in [
        "AQ.Ab8RN6-MockArbitraryTokenFormat-xyz",
        "AIzaSyD-ExampleGoogleAIStudioKey998877",
        "custom_google_authorization_token_abc123"
    ]:
        monkeypatch.setenv("GEMINI_API_KEY", candidate)
        assert is_gemini_configured() is True
        assert get_gemini_api_key() == candidate


def test_configurable_model_selection(monkeypatch):
    """Verifies GEMINI_MODEL env var controls the model endpoint."""
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert get_gemini_model() == DEFAULT_GEMINI_MODEL
    assert f"/models/{DEFAULT_GEMINI_MODEL}:generateContent" in get_gemini_endpoint()

    monkeypatch.setenv("GEMINI_MODEL", "gemini-custom-test")
    assert get_gemini_model() == "gemini-custom-test"
    assert "/models/gemini-custom-test:generateContent" in get_gemini_endpoint()


def test_secure_header_usage(monkeypatch):
    """Verifies API key is sent via x-goog-api-key header and NOT in the URL."""
    fake_key = "AIzaSyTestSecretKey12345"
    monkeypatch.setenv("GEMINI_API_KEY", fake_key)

    mock_resp = make_mock_gemini_response(200, text_content="AI answer")
    with patch("requests.post", return_value=mock_resp) as mock_post:
        call_gemini_api("Hello")
        assert mock_post.called
        call_args = mock_post.call_args

        # URL must NOT contain the key
        url = call_args[0][0]
        assert "key=" not in url
        assert fake_key not in url

        # Headers must contain x-goog-api-key
        headers = call_args[1]["headers"]
        assert headers.get("x-goog-api-key") == fake_key


# ----------------------------------------------------------------------
# 2. Itinerary Enrichment & Event Matching Tests
# ----------------------------------------------------------------------

def test_valid_gemini_response_enrichment(sample_itinerary, monkeypatch):
    """Tests successful enrichment with descriptions, why_recommended, and travel tips."""
    monkeypatch.setenv("GEMINI_API_KEY", "valid_mock_key_12345")

    llm_payload = {
        "itinerary": [
            {
                "day": 1,
                "travel_tip": "Wear comfortable sandals and sunscreen for beach hopping.",
                "events": [
                    {
                        "id": 101,
                        "type": "Attraction",
                        "name": "Baga Beach",
                        "description": "Baga Beach offers golden sands and thrilling watersports with scenic beach shacks.",
                        "why_recommended": "Perfect match for your Beaches interest and relaxed pace."
                    },
                    {
                        "id": 201,
                        "type": "Restaurant",
                        "name": "Goa South Bhavan",
                        "description": "Renowned coastal dining serving authentic vegetarian delicacies.",
                        "why_recommended": "Provides authentic local vegetarian cuisine in a cozy ambience."
                    }
                ]
            },
            {
                "day": 2,
                "travel_tip": "Visit Fort Aguada early morning to avoid afternoon heat.",
                "events": [
                    {
                        "id": 102,
                        "type": "Attraction",
                        "name": "Fort Aguada",
                        "description": "Magnificent 17th-century bastion with panoramic views of Sinquerim Beach.",
                        "why_recommended": "Rich Portuguese heritage matching your Historical interest."
                    }
                ]
            }
        ]
    }

    mock_resp = make_mock_gemini_response(200, text_content=json.dumps(llm_payload))

    with patch("requests.post", return_value=mock_resp):
        enriched = polish_itinerary_with_llm(sample_itinerary)

        assert enriched["llm_polished"] is True
        assert "llm_warning" not in enriched

        # Day 1 checks
        day1 = enriched["itinerary"][0]
        assert day1.get("travel_tip") == "Wear comfortable sandals and sunscreen for beach hopping."

        ev1 = day1["events"][0]
        assert "golden sands" in ev1["description"]
        assert "Perfect match for your Beaches interest" in ev1["why_recommended"]

        # Day 2 checks
        day2 = enriched["itinerary"][1]
        assert "Fort Aguada early" in day2.get("travel_tip")
        ev3 = day2["events"][0]
        assert "Magnificent 17th-century" in ev3["description"]
        assert "Rich Portuguese heritage" in ev3["why_recommended"]


def test_factual_fields_preserved_after_enrichment(sample_itinerary, monkeypatch):
    """
    CRITICAL: Validates that IDs, coordinates, prices, ratings, durations,
    hotel, weather, budget, and safety data remain STRICTLY unchanged.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "valid_mock_key_12345")
    original = copy.deepcopy(sample_itinerary)

    llm_payload = {
        "itinerary": [
            {
                "day": 1,
                "travel_tip": "Stay hydrated.",
                "events": [
                    {
                        "id": 101,
                        "type": "Attraction",
                        "name": "Baga Beach",
                        "description": "Enriched description here.",
                        "why_recommended": "Recommended for beach lovers."
                    }
                ]
            }
        ]
    }
    mock_resp = make_mock_gemini_response(200, text_content=json.dumps(llm_payload))

    with patch("requests.post", return_value=mock_resp):
        enriched = polish_itinerary_with_llm(sample_itinerary)

        # 1. Hotel unchanged
        assert enriched["selected_hotel"] == original["selected_hotel"]

        # 2. Weather unchanged
        assert enriched["weather_summary"] == original["weather_summary"]
        assert enriched["weather_forecast"] == original["weather_forecast"]

        # 3. Budget unchanged
        assert enriched["budget_breakdown"] == original["budget_breakdown"]
        assert enriched["is_budget_valid"] == original["is_budget_valid"]

        # 4. Safety unchanged
        assert enriched["safety_status"] == original["safety_status"]
        assert enriched["safety_message"] == original["safety_message"]
        assert enriched["safety_alerts"] == original["safety_alerts"]

        # 5. Day metrics unchanged
        assert enriched["itinerary"][0]["day"] == original["itinerary"][0]["day"]
        assert enriched["itinerary"][0]["weather"] == original["itinerary"][0]["weather"]
        assert enriched["itinerary"][0]["distance_km"] == original["itinerary"][0]["distance_km"]
        assert enriched["itinerary"][0]["travel_time_mins"] == original["itinerary"][0]["travel_time_mins"]
        assert enriched["itinerary"][0]["day_route_url"] == original["itinerary"][0]["day_route_url"]

        # 6. Event factual fields unchanged
        ev_orig = original["itinerary"][0]["events"][0]
        ev_new = enriched["itinerary"][0]["events"][0]
        assert ev_new["id"] == ev_orig["id"]
        assert ev_new["name"] == ev_orig["name"]
        assert ev_new["type"] == ev_orig["type"]
        assert ev_new["category"] == ev_orig["category"]
        assert ev_new["cost"] == ev_orig["cost"]
        assert ev_new["duration"] == ev_orig["duration"]
        assert ev_new["rating"] == ev_orig["rating"]
        assert ev_new["latitude"] == ev_orig["latitude"]
        assert ev_new["longitude"] == ev_orig["longitude"]
        assert ev_new["maps_url"] == ev_orig["maps_url"]


def test_event_matching_strictly_by_type_and_id(monkeypatch):
    """
    Ensures that an Attraction and a Restaurant sharing the same ID (e.g. id=10)
    are matched to their respective types and not cross-contaminated.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "valid_mock_key_12345")

    itinerary_with_collision = {
        "destination": "Delhi",
        "itinerary": [
            {
                "day": 1,
                "events": [
                    {
                        "id": 10,
                        "type": "Attraction",
                        "name": "Red Fort",
                        "description": "Original Red Fort description"
                    },
                    {
                        "id": 10,
                        "type": "Restaurant",
                        "name": "Karim's",
                        "description": "Original Karim's description"
                    }
                ]
            }
        ]
    }

    llm_payload = {
        "itinerary": [
            {
                "day": 1,
                "events": [
                    {
                        "id": 10,
                        "type": "Attraction",
                        "name": "Red Fort",
                        "description": "Magnificent Mughal citadel of red sandstone.",
                        "why_recommended": "Historical interest match."
                    },
                    {
                        "id": 10,
                        "type": "Restaurant",
                        "name": "Karim's",
                        "description": "Historic Old Delhi dining since 1913.",
                        "why_recommended": "Famous culinary destination."
                    }
                ]
            }
        ]
    }

    mock_resp = make_mock_gemini_response(200, text_content=json.dumps(llm_payload))

    with patch("requests.post", return_value=mock_resp):
        res = polish_itinerary_with_llm(itinerary_with_collision)
        attraction_ev = res["itinerary"][0]["events"][0]
        restaurant_ev = res["itinerary"][0]["events"][1]

        # Verify correct matching
        assert "Mughal citadel" in attraction_ev["description"]
        assert "Old Delhi dining" in restaurant_ev["description"]


# ----------------------------------------------------------------------
# 3. Error Handling & Failure Scenarios
# ----------------------------------------------------------------------

def test_invalid_api_key_response_403(sample_itinerary, monkeypatch):
    """Tests HTTP 403 Forbidden falls back to database itinerary."""
    monkeypatch.setenv("GEMINI_API_KEY", "invalid_key_403")
    original_desc = sample_itinerary["itinerary"][0]["events"][0]["description"]

    mock_resp = make_mock_gemini_response(403)
    with patch("requests.post", return_value=mock_resp):
        res = polish_itinerary_with_llm(sample_itinerary)
        assert res["llm_polished"] is False
        assert res["itinerary"][0]["events"][0]["description"] == original_desc


def test_rate_limit_response_429(sample_itinerary, monkeypatch):
    """Tests HTTP 429 Rate Limit falls back gracefully."""
    monkeypatch.setenv("GEMINI_API_KEY", "valid_key")
    original_desc = sample_itinerary["itinerary"][0]["events"][0]["description"]

    mock_resp = make_mock_gemini_response(429)
    with patch("requests.post", return_value=mock_resp):
        res = polish_itinerary_with_llm(sample_itinerary)
        assert res["llm_polished"] is False
        assert res["itinerary"][0]["events"][0]["description"] == original_desc


def test_server_error_response_500(sample_itinerary, monkeypatch):
    """Tests HTTP 500 Server Error falls back gracefully."""
    monkeypatch.setenv("GEMINI_API_KEY", "valid_key")
    original_desc = sample_itinerary["itinerary"][0]["events"][0]["description"]

    mock_resp = make_mock_gemini_response(500)
    with patch("requests.post", return_value=mock_resp):
        res = polish_itinerary_with_llm(sample_itinerary)
        assert res["llm_polished"] is False
        assert res["itinerary"][0]["events"][0]["description"] == original_desc


def test_request_timeout(sample_itinerary, monkeypatch):
    """Tests network request timeout falls back without crashing."""
    monkeypatch.setenv("GEMINI_API_KEY", "valid_key")
    original_desc = sample_itinerary["itinerary"][0]["events"][0]["description"]

    with patch("requests.post", side_effect=requests.exceptions.Timeout("Read timeout")):
        res = polish_itinerary_with_llm(sample_itinerary)
        assert res["llm_polished"] is False
        assert res["itinerary"][0]["events"][0]["description"] == original_desc


def test_invalid_json_response(sample_itinerary, monkeypatch):
    """Tests invalid JSON returned by Gemini falls back gracefully."""
    monkeypatch.setenv("GEMINI_API_KEY", "valid_key")
    original_desc = sample_itinerary["itinerary"][0]["events"][0]["description"]

    mock_resp = make_mock_gemini_response(200, text_content="Not JSON at all! {invalid syntax")
    with patch("requests.post", return_value=mock_resp):
        res = polish_itinerary_with_llm(sample_itinerary)
        assert res["llm_polished"] is False
        assert res["itinerary"][0]["events"][0]["description"] == original_desc


def test_empty_gemini_response(sample_itinerary, monkeypatch):
    """Tests HTTP 200 with empty candidate parts falls back gracefully."""
    monkeypatch.setenv("GEMINI_API_KEY", "valid_key")
    original_desc = sample_itinerary["itinerary"][0]["events"][0]["description"]

    mock_resp = make_mock_gemini_response(200, json_dict={"candidates": []})
    with patch("requests.post", return_value=mock_resp):
        res = polish_itinerary_with_llm(sample_itinerary)
        assert res["llm_polished"] is False
        assert res["itinerary"][0]["events"][0]["description"] == original_desc


# ----------------------------------------------------------------------
# 4. Travel Assistant Query Tests
# ----------------------------------------------------------------------

def test_assistant_query_success(monkeypatch):
    """Tests assistant query returns formatted markdown answer."""
    monkeypatch.setenv("GEMINI_API_KEY", "valid_key")
    expected_answer = "Here are the top 3 spots in Goa: 1. Baga Beach 2. Fort Aguada 3. Dudhsagar Falls"

    mock_resp = make_mock_gemini_response(200, text_content=expected_answer)
    with patch("requests.post", return_value=mock_resp):
        resp = query_gemini_assistant("Best places in Goa?")
        assert resp == expected_answer


def test_assistant_query_failure_returns_none(monkeypatch):
    """Tests assistant query returns None on failure to trigger local rule-engine."""
    monkeypatch.setenv("GEMINI_API_KEY", "valid_key")

    with patch("requests.post", side_effect=requests.exceptions.RequestException("Network down")):
        resp = query_gemini_assistant("Best places in Goa?")
        assert resp is None


# ----------------------------------------------------------------------
# 5. Integration Tests with generate_itinerary()
# ----------------------------------------------------------------------

def test_integration_generate_itinerary_with_failing_gemini(monkeypatch):
    """
    Integration test: Calling generate_itinerary() when Gemini fails must still
    succeed and return the verified database-generated itinerary with llm_polished=False.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "valid_key_failing")

    mock_resp = make_mock_gemini_response(500)
    with patch("requests.post", return_value=mock_resp), patch(
        "services.itinerary_service.get_live_weather",
        return_value={"current": {}, "forecast": []}
    ):
        trip = generate_itinerary(destination="Goa", days=2, budget=20000.0)

        assert trip["success"] is True
        assert trip["llm_polished"] is False
        assert trip["destination"] == "Goa"
        assert len(trip["itinerary"]) == 2
        assert trip["selected_hotel"] is not None
        assert trip["budget_breakdown"]["total_cost"] > 0
        assert trip["safety_status"] in ["Safe", "Caution", "High Risk"]


def test_integration_generate_itinerary_with_successful_gemini(monkeypatch):
    """
    Integration test: Calling generate_itinerary() when Gemini succeeds must
    mark llm_polished=True and preserve all coordinates and factual fields.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "valid_key_working")

    llm_payload = {
        "itinerary": [
            {
                "day": 1,
                "travel_tip": "Wear cotton attire and keep water handy.",
                "events": [
                    {
                        "id": 4,
                        "type": "Attraction",
                        "name": "Fort Aguada",
                        "description": "Polished scenic experience with coastal breeze.",
                        "why_recommended": "Matches your travel pace."
                    }
                ]
            }
        ]
    }
    mock_resp = make_mock_gemini_response(200, text_content=json.dumps(llm_payload))

    with patch("requests.post", return_value=mock_resp), patch(
        "services.itinerary_service.get_live_weather",
        return_value={"current": {}, "forecast": []}
    ):
        trip = generate_itinerary(destination="Goa", days=1, budget=20000.0)

        assert trip["success"] is True
        assert trip["llm_polished"] is True
        assert trip["itinerary"][0].get("travel_tip") == "Wear cotton attire and keep water handy."

        # Find Fort Aguada attraction event
        enriched_event = next(e for e in trip["itinerary"][0]["events"] if e.get("name") == "Fort Aguada")
        assert "Polished scenic experience" in enriched_event["description"]
        assert enriched_event["why_recommended"] == "Matches your travel pace."

        # Verify factual fields
        assert enriched_event["id"] == 4
        assert enriched_event["type"] == "Attraction"
        assert enriched_event["latitude"] == 15.4920
        assert enriched_event["longitude"] == 73.7737
        assert enriched_event["cost"] == 25.0
