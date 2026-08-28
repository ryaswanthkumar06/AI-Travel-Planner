import sys
import os

sys.path.append(os.getcwd())

try:
    print("1. Testing database and data imports...")
    from database.db_manager import init_db
    from services.data_service import get_cities, get_attractions, get_hotels, get_restaurants, get_accident_zones
    init_db()
    cities = get_cities()
    print(f"Success! Cities count: {len(cities)}")
    assert len(cities) >= 30, f"Expected 30 cities, found {len(cities)}"
    
    print("2. Testing service imports...")
    from services.recommendation_service import score_attraction
    from services.routing_service import haversine_distance
    from services.weather_service import get_live_weather
    from services.safety_service import check_route_safety, get_safety_report
    from services.budget_service import validate_trip_budget
    from services.maps_service import get_google_maps_search_url, get_google_maps_directions_url, get_google_maps_route_url
    from services.image_service import get_destination_image, get_attraction_image
    print("Success! All core services imported.")

    print("3. Testing Maps and Image generators...")
    map_url = get_google_maps_search_url("Charminar, Hyderabad", 17.3616, 78.4747)
    assert "https://www.google.com/maps/search/" in map_url
    dir_url = get_google_maps_directions_url("Hotel", "Charminar", "driving")
    assert "https://www.google.com/maps/dir/" in dir_url
    img_url = get_destination_image("Munnar")
    assert img_url.startswith("http")
    print("Success! Maps and Image helpers verified.")

    print("4. Testing full itinerary builder with flexible signatures...")
    from services.itinerary_service import generate_itinerary, build_itinerary
    
    # Test call 1: using generate_itinerary with standard params
    trip1 = generate_itinerary(
        destination="Jaipur",
        days=3,
        travelers=2,
        budget=35000.0,
        travel_style="Cultural",
        interests=["Historical Places", "Architecture"],
        food_preferences=["Vegetarian"],
        accommodation="Mid-range Hotels",
        transportation="Taxi"
    )
    assert trip1["success"] is True, f"Failed trip1: {trip1.get('error_message')}"
    print(f"Success! Jaipur trip generated (Days: {len(trip1['itinerary'])}, Hotel: {trip1['selected_hotel']['name']})")

    # Test call 2: using build_itinerary with 'city_name' keyword alias
    trip2 = build_itinerary(
        city_name="Munnar",
        days=2,
        budget=20000.0,
        travelers=2,
        interests=["Nature", "Mountains"]
    )
    assert trip2["success"] is True, f"Failed trip2: {trip2.get('error_message')}"
    print(f"Success! Munnar trip generated via alias (Days: {len(trip2['itinerary'])})")

    print("5. Testing Safety and Weather reports...")
    s_rep = get_safety_report("Hyderabad")
    assert "status" in s_rep and "alerts" in s_rep
    w_rep = get_live_weather(17.385, 78.4867)
    assert "temp" in w_rep and "forecast" in w_rep
    print("Success! Safety and Weather reports verified.")

    print("ALL BACKEND INTEGRATION TESTS PASSED SUCCESSFULLY!")

except Exception as e:
    import traceback
    print("FAIL: Sanity tests failed with exception:")
    traceback.print_exc()
    sys.exit(1)
