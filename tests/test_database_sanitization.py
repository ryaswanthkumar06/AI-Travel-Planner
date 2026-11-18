"""Tests that saved trips retain Google Place IDs but not transient Places content."""

import json

from database.db_manager import _sanitize_json_for_storage


def test_sanitizer_preserves_place_ids_and_removes_google_content():
    payload = {
        "destination": "Goa",
        "selected_hotel": {
            "name": "Example Hotel",
            "google_place_id": "places/abc123",
            "rating": 4.6,
            "review_count": 1200,
            "photo_url": "https://lh3.googleusercontent.com/temporary",
            "photo_attribution": "Photo Author",
            "latitude": 15.1,
            "longitude": 73.9,
        },
        "itinerary": [
            {
                "name": "Fort Example",
                "google_place_id": "places/fort456",
                "rating": 4.8,
                "rating_source": "Google Places",
                "photo_url": "https://lh3.googleusercontent.com/temporary2",
            }
        ],
    }

    saved = json.loads(_sanitize_json_for_storage(payload))

    hotel = saved["selected_hotel"]
    event = saved["itinerary"][0]

    assert hotel["google_place_id"] == "places/abc123"
    assert event["google_place_id"] == "places/fort456"
    assert "rating" not in hotel
    assert "review_count" not in hotel
    assert "photo_url" not in hotel
    assert "photo_attribution" not in hotel
    assert "rating" not in event
    assert "rating_source" not in event
    assert "photo_url" not in event
    # Non-Google coordinates remain intact because they are part of the app's
    # own local catalogue and are not replaced with a Place Details coordinate.
    assert hotel["latitude"] == 15.1
    assert hotel["longitude"] == 73.9


def test_sanitizer_accepts_json_string_input():
    source = json.dumps({"google_place_id": "places/abc", "rating": 4.5})

    saved = json.loads(_sanitize_json_for_storage(source))

    assert saved == {"google_place_id": "places/abc"}
