"""Regression tests for exact-place photo resolution and rating accuracy."""

from unittest.mock import MagicMock

import pytest

from services import photo_service


def test_place_name_normalization():
    assert photo_service._normalise_match_text("The Taj Mahal & Museum!") == "the taj mahal and museum"


def test_candidate_match_selects_exact_place_over_near_match():
    candidates = [
        {
            "displayName": {"text": "Red Fort Cafe"},
            "formattedAddress": "Near Red Fort, Delhi, India",
        },
        {
            "displayName": {"text": "The Red Fort"},
            "formattedAddress": "Netaji Subhash Marg, Delhi, India",
        },
    ]

    selected = photo_service._select_matching_candidate(candidates, "Red Fort", "Delhi")

    assert selected is candidates[1]


def test_candidate_match_rejects_similarly_named_unrelated_place():
    candidate = {
        "displayName": {"text": "Red Fort Cafe"},
        "formattedAddress": "Red Fort Road, Delhi, India",
    }

    selected = photo_service._select_matching_candidate([candidate], "Red Fort", "Delhi")

    assert selected is None


def test_candidate_match_rejects_unrelated_search_result():
    candidate = {
        "displayName": {"text": "City Centre Mall"},
        "formattedAddress": "Jaipur, Rajasthan, India",
    }

    assert photo_service._select_matching_candidate([candidate], "Hawa Mahal", "Jaipur") is None


def test_fallback_does_not_fabricate_google_ratings(monkeypatch):
    monkeypatch.setattr(photo_service, "GOOGLE_API_KEY", "")
    photo_service.clear_cache()

    result = photo_service.resolve_place_photo(
        "Unique Example Monument 987",
        city_name="Example City",
        category="Historical"
    )

    assert result["place_verified"] is False
    assert result["rating"] is None
    assert result["reviews_count"] is None
    assert result["google_place_id"] is None
    assert result["fallback_used"] is True


def test_new_photo_uri_does_not_expose_api_key(monkeypatch):
    monkeypatch.setattr(photo_service, "GOOGLE_API_KEY", "server-only-test-key")
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"photoUri": "https://lh3.googleusercontent.com/test-photo"}
    get_mock = MagicMock(return_value=response)
    monkeypatch.setattr(photo_service.requests, "get", get_mock)

    result = photo_service._build_new_photo_url("places/example/photos/example-photo")

    assert result == "https://lh3.googleusercontent.com/test-photo"
    assert "server-only-test-key" not in result
    assert get_mock.call_args.kwargs["params"]["key"] == "server-only-test-key"
    assert get_mock.call_args.kwargs["params"]["skipHttpRedirect"] == "true"


def test_legacy_photo_redirect_does_not_expose_api_key(monkeypatch):
    monkeypatch.setattr(photo_service, "GOOGLE_API_KEY", "server-only-test-key")
    response = MagicMock()
    response.status_code = 200
    response.url = "https://lh3.googleusercontent.com/legacy-photo"
    response.close = MagicMock()
    get_mock = MagicMock(return_value=response)
    monkeypatch.setattr(photo_service.requests, "get", get_mock)

    result = photo_service._build_legacy_photo_url("legacy-photo-reference")

    assert result == "https://lh3.googleusercontent.com/legacy-photo"
    assert "server-only-test-key" not in result
    assert get_mock.call_args.kwargs["params"]["key"] == "server-only-test-key"
    assert get_mock.call_args.kwargs["stream"] is True


def test_google_photo_attribution_is_rendered():
    html = photo_service.render_card_image_html(
        "https://example.com/photo.jpg",
        "A landmark",
        attribution="Photo by Example Contributor"
    )

    assert "Photo by Example Contributor" in html
