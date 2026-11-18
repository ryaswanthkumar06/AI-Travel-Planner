"""Regression tests for optional live ratings and neutral recommendation scoring."""

import pandas as pd
import pytest

from utils.data_validator import validate_dataframe
from services.recommendation_service import score_attraction, score_hotel, score_restaurant


@pytest.mark.parametrize(
    ("dataset_type", "row"),
    [
        (
            "attractions",
            {
                "id": 1, "name": "Test Fort", "city": "Test City",
                "latitude": 12.0, "longitude": 77.0, "rating": None,
                "price": 0, "opening_time": "09:00", "closing_time": "17:00",
            },
        ),
        (
            "restaurants",
            {
                "id": 1, "name": "Sample Restaurant", "city": "Test City",
                "latitude": 12.0, "longitude": 77.0, "rating": None,
                "opening_time": "10:00", "closing_time": "22:00",
            },
        ),
        (
            "hotels",
            {
                "id": 1, "name": "Sample Hotel", "city": "Test City",
                "latitude": 12.0, "longitude": 77.0,
                "price_per_night": 2500, "rating": None,
            },
        ),
    ],
)
def test_missing_provider_rating_does_not_invalidate_catalogue_row(dataset_type, row):
    report = validate_dataframe(pd.DataFrame([row]), dataset_type)

    assert report["metrics"]["valid"] == 1
    assert report["metrics"]["invalid"] == 0
    assert report["valid_df"].shape[0] == 1


def test_unverified_hotel_stars_do_not_change_recommendation_score():
    base = {"category": "Mid-range", "price_per_night": 2500}
    low = {**base, "rating": 1.0}
    high = {**base, "rating": 5.0}

    assert score_hotel(low, "Mid-range", 5000) == score_hotel(high, "Mid-range", 5000)


def test_unverified_restaurant_stars_do_not_change_recommendation_score():
    base = {"food_type": "Vegetarian", "price_range": "Mid-range"}
    low = {**base, "rating": 1.0}
    high = {**base, "rating": 5.0}

    assert score_restaurant(low, "Any", "Medium") == score_restaurant(high, "Any", "Medium")


def test_unverified_attraction_stars_do_not_change_recommendation_score():
    base = {"category": "Historical", "price": 0}
    low = {**base, "rating": 1.0}
    high = {**base, "rating": 5.0}

    assert score_attraction(low, ["Historical Places"]) == score_attraction(
        high, ["Historical Places"]
    )
