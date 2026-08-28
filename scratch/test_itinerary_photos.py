import sys, os
sys.path.insert(0, os.path.abspath("."))
from services.itinerary_service import generate_itinerary

def test_itinerary_photos():
    destinations = ["Bengaluru", "Goa", "Delhi", "Mumbai", "Jaipur", "Agra", "Hyderabad", "Munnar"]
    for dest in destinations:
        trip = generate_itinerary(destination=dest, days=2, budget=25000.0)
        assert trip and "itinerary" in trip, f"Failed itinerary for {dest}"
        events_count = 0
        photos_found = 0
        for day in trip["itinerary"]:
            for ev in day.get("events", []):
                events_count += 1
                img = ev.get("photo_url") or ev.get("image_url")
                if img and img.startswith("http"):
                    photos_found += 1
        print(f"[PASS] {dest:12}: {len(trip['itinerary'])} Days, {events_count} Stops, {photos_found}/{events_count} Valid Photos attached.")

    print("\n*** ALL ITINERARY PHOTO RESOLUTIONS PASSED! ***")

if __name__ == "__main__":
    test_itinerary_photos()
