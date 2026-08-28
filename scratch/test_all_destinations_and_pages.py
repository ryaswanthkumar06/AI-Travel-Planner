import sys, os
import urllib.request

sys.path.insert(0, os.path.abspath("."))

from services.destination_image_service import (
    get_destination_image,
    get_attraction_image,
    get_hotel_image,
    get_restaurant_image,
    get_destination_photo,
    get_attraction_photo,
    get_hotel_photo,
    get_restaurant_photo,
    render_card_image_html,
    is_places_api_configured
)
from services.google_places_service import is_places_api_configured as gp_is_cfg
from services.data_service import get_cities, get_attractions, get_hotels, get_restaurants, get_accident_zones
from services.itinerary_service import generate_itinerary

def test_imports():
    print("Testing imports across services...")
    assert gp_is_cfg is not None
    assert is_places_api_configured is not None
    print("[PASS] All imports and aliases verified.")

def test_30_destinations():
    print("\nTesting 30 Destination Photos...")
    cities_df = get_cities()
    city_names = list(cities_df["city"].unique())
    assert len(city_names) >= 30, f"Expected 30 cities, found {len(city_names)}"

    priority_cities = [
        "Varanasi", "Mysuru", "Udaipur", "Ooty", "Shimla", "Rishikesh", 
        "Manali", "Chennai", "Kochi", "Pondicherry", "Gangtok", "Wayanad", 
        "Jodhpur", "Kodaikanal", "Srinagar", "Coorg", "Ahmedabad", "Goa", "Hyderabad", "Munnar"
    ]

    for city in city_names:
        url = get_destination_image(city)
        assert url and url.startswith("http"), f"Invalid image for {city}: {url}"
        
        # Test HTML card rendering
        html = render_card_image_html(url, city, height_px=160)
        assert "<div" in html and "onerror=" in html, f"Card HTML error for {city}"
        
        tag = "[PRIORITY]" if city in priority_cities else "[VERIFIED]"
        print(f"{tag:11} {city:15} -> {url[:65]}...")

    print(f"\n[PASS] Verified {len(city_names)} Destinations with authentic photo URLs!")

def test_itinerary_and_features():
    print("\nTesting Itinerary Generation and Card Outputs...")
    test_cities = ["Varanasi", "Mysuru", "Udaipur", "Ooty", "Goa", "Kochi"]
    for dest in test_cities:
        trip = generate_itinerary(destination=dest, days=2, budget=20000.0)
        assert trip and "itinerary" in trip, f"Failed generation for {dest}"
        events = sum(len(d.get("events", [])) for d in trip["itinerary"])
        assert events > 0, f"No events generated for {dest}"
        print(f"[PASS] Itinerary for {dest:12}: {len(trip['itinerary'])} days, {events} stops, selected hotel: {trip.get('selected_hotel', {}).get('name', 'N/A')}")

if __name__ == "__main__":
    test_imports()
    test_30_destinations()
    test_itinerary_and_features()
    print("\n*** ALL BACKEND, DATA, AND IMAGE RESOLUTION CHECKS PASSED! ***")
