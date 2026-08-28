import sys, os
import json

sys.path.insert(0, os.path.abspath("."))

from database.db_manager import save_trip, get_user_trips, get_trip_by_id, delete_trip, init_db
from services.itinerary_service import generate_itinerary
from services.pdf_service import generate_trip_pdf_bytes, generate_trip_pdf

def test_save_trip_flow():
    print("1. Initializing DB schema...")
    init_db()
    
    print("2. Generating test Goa itinerary...")
    trip = generate_itinerary(destination="Goa", days=3, budget=27000.0)
    assert trip and "itinerary" in trip, "Failed to generate itinerary"
    
    print("3. Testing save_trip with start_date & end_date keyword arguments...")
    trip_id = save_trip(
        user_id=1,
        name="Goa 3-Day Adventure Test",
        destination="Goa",
        start_date="2026-09-03",
        end_date="2026-09-05",
        duration_days=3,
        travelers=2,
        budget=27000.0,
        interests=["Beaches", "Historical Places"],
        itinerary_json=json.dumps(trip["itinerary"]),
        hotel_json=json.dumps(trip.get("selected_hotel", {})),
        restaurants_json=json.dumps(trip.get("selected_restaurants", [])),
        travel_style="Balanced",
        food_preferences=["Seafood", "Any"],
        accommodation="Mid-range Hotels",
        transportation="Public Transit"
    )
    assert trip_id > 0, "Expected valid trip_id"
    print(f"   [PASS] Saved trip successfully with ID: {trip_id}")
    
    print("4. Testing get_user_trips...")
    trips = get_user_trips(1)
    saved = next((t for t in trips if t["id"] == trip_id), None)
    assert saved is not None, "Trip not found in user trips"
    assert saved["start_date"] == "2026-09-03", f"Wrong start_date: {saved['start_date']}"
    assert saved["end_date"] == "2026-09-05", f"Wrong end_date: {saved['end_date']}"
    print(f"   [PASS] Retrieved trip: {saved['name']} (Dates: {saved['start_date']} to {saved['end_date']})")
    
    print("5. Testing PDF bytes generation...")
    pdf_bytes = generate_trip_pdf_bytes(trip)
    assert pdf_bytes and len(pdf_bytes) > 500, f"PDF bytes generation failed (len={len(pdf_bytes)})"
    assert pdf_bytes.startswith(b"%PDF"), "Generated file is not a valid PDF header"
    print(f"   [PASS] Generated PDF in-memory: {len(pdf_bytes):,} bytes")
    
    print("6. Testing clean delete_trip...")
    delete_trip(trip_id)
    trips_after = get_user_trips(1)
    assert not any(t["id"] == trip_id for t in trips_after), "Trip was not deleted"
    print("   [PASS] Deleted test trip cleanly.")
    
    print("\n*** ALL SAVE TRIP AND PDF TESTS PASSED 100%! ***")

if __name__ == "__main__":
    test_save_trip_flow()
