import sys
import os
import json

sys.path.append(os.getcwd())

from services.itinerary_service import generate_itinerary
from database.db_manager import save_trip, get_user_trips, delete_trip
from services.pdf_service import generate_trip_pdf

print("1. Generating Itinerary for Munnar (2 Days)...")
munnar_trip = generate_itinerary(
    destination="Munnar",
    days=2,
    travelers=2,
    budget=20000.0,
    travel_style="Nature",
    interests=["Mountains", "Nature", "Waterfalls"],
    food_preferences=["South Indian"],
    accommodation="Resorts",
    transportation="Taxi"
)
assert munnar_trip["success"] is True

print("2. Saving Munnar trip to SQLite...")
trip_id = save_trip(
    user_id=1,
    name="Munnar Misty Hills Getaway",
    destination="Munnar",
    duration_days=2,
    travelers=2,
    budget=20000.0,
    interests="Mountains;Nature",
    itinerary_json=json.dumps(munnar_trip["itinerary"]),
    hotel_json=json.dumps(munnar_trip["selected_hotel"]),
    restaurants_json=json.dumps(munnar_trip.get("selected_restaurants", []))
)
print(f"Saved with ID: {trip_id}")

print("3. Generating PDF for Munnar trip...")
os.makedirs("scratch", exist_ok=True)
pdf_path = f"scratch/test_munnar_{trip_id}.pdf"
generate_trip_pdf(munnar_trip, pdf_path)
assert os.path.exists(pdf_path)
print(f"PDF generated successfully at {pdf_path}")

print("4. Fetching user trips...")
trips = get_user_trips(1)
print(f"Total trips for User 1: {len(trips)}")
assert len(trips) > 0

print("FULL END-TO-END FLOW VERIFIED SUCCESSFULLY!")
