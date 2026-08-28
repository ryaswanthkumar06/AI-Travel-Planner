import sys, os
sys.path.insert(0, os.path.abspath("."))
from services.photo_service import (
    get_destination_photo,
    get_attraction_photo,
    get_hotel_photo,
    get_restaurant_photo,
    resolve_place_photo,
    render_card_image_html,
    is_api_configured
)

def test_photo_system():
    print(f"API Configured: {is_api_configured()}")
    
    # 1. Test 15 Destinations
    destinations = [
        "Goa", "Hyderabad", "Munnar", "Varanasi", "Delhi",
        "Mumbai", "Bengaluru", "Jaipur", "Udaipur", "Agra",
        "Mysuru", "Ooty", "Manali", "Shimla", "Rishikesh"
    ]
    print("\n--- 1. Testing Destinations ---")
    for dest in destinations:
        url = get_destination_photo(dest)
        assert url and url.startswith("http"), f"Failed for {dest}: {url}"
        print(f"[PASS] Destination: {dest:15} -> {url[:60]}...")
        
    # 2. Test 10 Attractions
    attractions = [
        ("Lalbagh Botanical Garden", "Bengaluru"),
        ("Bangalore Palace", "Bengaluru"),
        ("Charminar", "Hyderabad"),
        ("Golconda Fort", "Hyderabad"),
        ("Taj Mahal", "Agra"),
        ("Agra Fort", "Agra"),
        ("Gateway of India", "Mumbai"),
        ("Amber Fort", "Jaipur"),
        ("Hawa Mahal", "Jaipur"),
        ("Red Fort", "Delhi")
    ]
    print("\n--- 2. Testing Attractions ---")
    for att, city in attractions:
        url = get_attraction_photo(att, city_name=city)
        assert url and url.startswith("http"), f"Failed for {att}: {url}"
        print(f"[PASS] Attraction: {att:30} -> {url[:60]}...")
        
    # 3. Test 5 Hotels
    hotels = [
        ("The Taj Mahal Palace", "Mumbai", "Luxury"),
        ("The Leela Palace", "Bengaluru", "Luxury"),
        ("Lemon Tree Premier", "Hyderabad", "Mid-range"),
        ("Zostel Goa", "Goa", "Hostel"),
        ("ITC Grand Chola", "Chennai", "Luxury")
    ]
    print("\n--- 3. Testing Hotels ---")
    for name, city, cat in hotels:
        url = get_hotel_photo(name, city_name=city, category=cat)
        assert url and url.startswith("http"), f"Failed for {name}: {url}"
        print(f"[PASS] Hotel: {name:25} -> {url[:60]}...")
        
    # 4. Test 5 Restaurants
    restaurants = [
        ("Vidyarthi Bhavan", "Bengaluru", "South Indian"),
        ("Paradise Biryani", "Hyderabad", "North Indian"),
        ("Britannia & Co", "Mumbai", "Cafe"),
        ("Karim's", "Delhi", "North Indian"),
        ("Fisherman's Wharf", "Goa", "Seafood")
    ]
    print("\n--- 4. Testing Restaurants ---")
    for name, city, cui in restaurants:
        url = get_restaurant_photo(name, city_name=city, cuisine=cui)
        assert url and url.startswith("http"), f"Failed for {name}: {url}"
        print(f"[PASS] Restaurant: {name:25} -> {url[:60]}...")
        
    # 5. Test Card HTML generation
    sample_html = render_card_image_html(url, "Sample Place", height_px=150, category_icon="*")
    assert "<img" in sample_html and "onerror" in sample_html
    print(f"\n[PASS] Safe Card HTML generation passed.")
    
    print("\n*** ALL 35 PHOTO TESTS PASSED PERFECTLY! ***")

if __name__ == "__main__":
    test_photo_system()
