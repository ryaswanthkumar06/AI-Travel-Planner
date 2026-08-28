import sys
import os
sys.path.insert(0, os.path.abspath("."))
from services.itinerary_service import generate_itinerary
from services.data_service import get_city, resolve_canonical_city_name

destinations = [
    "Goa",
    "Bengaluru",
    "Bangalore",
    "Hyderabad",
    "Mumbai",
    "Delhi",
    "Jaipur",
    "Munnar",
    "Coorg",
    "Darjeeling",
    "Manali",
    "Gangtok",
    "Amritsar",
    "Chennai",
    "Kolkata"
]

all_passed = True

print("=== VERIFYING DESTINATION ITINERARY GENERATION ===")
for dest in destinations:
    canonical = resolve_canonical_city_name(dest)
    city_data = get_city(dest)
    if not city_data:
        print(f"❌ FAIL: get_city('{dest}') returned None (canonical: {canonical})")
        all_passed = False
        continue
    
    trip = generate_itinerary(destination=dest, days=2, budget=20000.0)
    if not trip.get("success"):
        print(f"[FAIL]: generate_itinerary('{dest}') returned error: {trip.get('error_message')}")
        all_passed = False
    else:
        num_days = len(trip.get("itinerary", []))
        hotel = trip.get("selected_hotel", {}).get("name", "Unknown")
        print(f"[PASS]: '{dest}' -> '{canonical}' (Days: {num_days}, Hotel: {hotel})")

if all_passed:
    print("\nALL 15 DESTINATIONS VERIFIED AND WORKING PERFECTLY!")
else:
    print("\nSOME DESTINATIONS FAILED!")
    sys.exit(1)
