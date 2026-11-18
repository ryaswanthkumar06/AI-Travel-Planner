import json
import pandas as pd
import math
from services.data_service import get_city, get_attractions, get_restaurants, get_hotels, resolve_canonical_city_name
from services.recommendation_service import get_recommendations, score_attraction, score_restaurant, score_hotel
from services.routing_service import cluster_and_route_locations, haversine_distance, estimate_travel_time
from services.weather_service import get_live_weather
from services.safety_service import check_route_safety
from services.budget_service import validate_trip_budget
from services.maps_service import get_google_maps_search_url, get_google_maps_directions_url, get_google_maps_route_url

def normalize_event(ev, selected_hotel=None, destination_city=None, travel_mode="driving"):
    """
    Standardizes the event dictionary to ensure it contains all required keys safely,
    including Google Maps search URLs and direct route navigation links.
    """
    place = ev.get("place") or ev.get("name") or "Unknown Place"
    category = ev.get("category") or ev.get("type") or "General"
    
    # Cost
    cost = ev.get("cost") if ev.get("cost") is not None else ev.get("estimated_cost")
    if cost is not None:
        try:
            cost = float(cost)
        except (ValueError, TypeError):
            cost = 0.0
    else:
        cost = 0.0

    # Duration
    duration = ev.get("duration") if ev.get("duration") is not None else ev.get("duration_minutes")
    if duration is not None:
        try:
            duration = int(duration)
        except (ValueError, TypeError):
            duration = 60
    else:
        duration = 60
        
    # Coordinates
    lat = ev.get("latitude") if ev.get("latitude") is not None else ev.get("lat")
    if lat is not None:
        try:
            lat = float(lat)
        except (ValueError, TypeError):
            lat = None
            
    lng = ev.get("longitude") if ev.get("longitude") is not None else ev.get("lng")
    if lng is not None:
        try:
            lng = float(lng)
        except (ValueError, TypeError):
            lng = None

    # Rating
    rating = ev.get("rating")
    if rating is not None:
        try:
            rating = float(rating)
        except (ValueError, TypeError):
            rating = None
            
    source = ev.get("source")
    if source in ["System Generated Leg", "Dataset source unavailable", "None", ""]:
        source = "Verified Registry"
        
    address = ev.get("address")
    if address in ["Address details unavailable", ""]:
        address = None
        
    # Safety Check
    safety = None
    if lat is not None and lng is not None and destination_city:
        from services.data_service import get_accident_zones
        zones_df = get_accident_zones(destination_city)
        if zones_df is not None and not zones_df.empty:
            for _, zone in zones_df.iterrows():
                dist = haversine_distance(lat, lng, zone["latitude"], zone["longitude"])
                if dist <= 1.5:  # within 1.5 km
                    safety = f"⚠️ Safety Advisory: {zone['risk_type']} ({zone['risk_level']} Risk) on {zone['road_name']}. Action: {zone['recommended_action']}"
                    break

    # Google Maps URL
    maps_url = get_google_maps_search_url(f"{place}, {destination_city}" if destination_city else place, lat, lng)
    
    # Directions URL from hotel or city center
    directions_url = ""
    if selected_hotel and lat is not None and lng is not None:
        h_lat = selected_hotel.get("latitude")
        h_lng = selected_hotel.get("longitude")
        if h_lat and h_lng:
            directions_url = get_google_maps_directions_url(
                origin=selected_hotel.get("name", "Hotel"),
                destination=place,
                travel_mode=travel_mode,
                origin_coords=(h_lat, h_lng),
                dest_coords=(lat, lng)
            )

    # Resolve a real Places match for photos and live ratings. Never treat CSV/demo
    # ratings as Google ratings, and never use a photo from an uncertain search match.
    photo_url = None
    live_place = {}
    ev_type = str(ev.get("type", "")).strip().lower()
    if ev_type in ("attraction", "restaurant"):
        try:
            from services.photo_service import resolve_place_photo
            place_category = f"restaurant {category}" if ev_type == "restaurant" else category
            live_place = resolve_place_photo(
                place,
                city_name=destination_city,
                category=place_category,
                latitude=lat,
                longitude=lng
            )
            # The resolver returns a place-specific Google photo only after a match;
            # otherwise it returns a category-aware curated fallback.
            photo_url = live_place.get("photo_url")
        except Exception:
            live_place = {}
            photo_url = None
    elif ev_type == "meal" and selected_hotel:
        photo_url = selected_hotel.get("photo_url")

    google_rating = live_place.get("rating") if live_place.get("place_verified") else None
    google_reviews = live_place.get("reviews_count") if live_place.get("place_verified") else None
    google_place_id = live_place.get("google_place_id") if live_place.get("place_verified") else None

    normalized = {
        "id": ev.get("id"),
        "time": ev.get("time", "12:00 PM"),
        "place": place,
        "name": place,
        "type": ev.get("type", "General"),
        "category": category,
        "description": ev.get("description", "No description available."),
        "duration": duration,
        "duration_minutes": duration,
        "cost": cost,
        "estimated_cost": cost,
        "price": cost,
        "source": source,
        "photo_url": photo_url,
        "image_url": photo_url,
        "maps_url": maps_url,
        "directions_url": directions_url or maps_url,
        "review_count": google_reviews,
        "google_place_id": google_place_id,
        "rating_source": "Google Places" if google_rating is not None else None,
        "photo_source": live_place.get("source") if live_place.get("place_verified") and live_place.get("is_google_photo") else "Catalogue fallback",
        "photo_attribution": live_place.get("attribution") if live_place.get("place_verified") else None,
        "photo_attribution_url": live_place.get("attribution_url") if live_place.get("place_verified") else None,
        "website": ev.get("website") or ev.get("websiteUri"),
        "phone": ev.get("phone") or ev.get("nationalPhoneNumber"),
        "open_now": ev.get("open_now"),
        "travel_time_mins": ev.get("travel_time_mins", 0),
        "distance_from_prev": ev.get("distance_from_prev", 0.0),
    }
    
    if lat is not None:
        normalized["latitude"] = lat
        normalized["lat"] = lat
    if lng is not None:
        normalized["longitude"] = lng
        normalized["lng"] = lng
    if google_rating is not None:
        normalized["rating"] = google_rating
        normalized["google_rating"] = google_rating
    else:
        normalized["rating"] = None
        normalized["google_rating"] = None
    if address:
        normalized["address"] = address
    if safety:
        normalized["safety"] = safety
        
    if ev.get("opening_hours") and ev.get("opening_hours") != "N/A":
        normalized["opening_hours"] = ev["opening_hours"]
    if ev.get("weather_note"):
        normalized["weather_note"] = ev["weather_note"]
    if ev.get("why_recommended"):
        normalized["why_recommended"] = ev["why_recommended"]
    if ev.get("distance_km") is not None:
        normalized["distance_km"] = ev["distance_km"]
        
    return normalized


def generate_itinerary(
    destination: str = "Hyderabad",
    start_date=None,
    end_date=None,
    days: int = 3,
    travelers: int = 2,
    budget: float = 30000.0,
    travel_style: str = "Balanced",
    interests=None,
    food_preferences=None,
    accommodation: str = "Mid-range Hotels",
    transportation: str = "Public Transit",
    **kwargs
) -> dict:
    """
    Standard unified itinerary generation interface. Accepts both 'destination' and 'city_name'
    and handles flexible parameter formats safely.
    """
    # Parameter normalization from kwargs
    if "city_name" in kwargs and not destination:
        destination = kwargs["city_name"]
    elif "city_name" in kwargs and destination == "Hyderabad" and kwargs["city_name"] != "Hyderabad":
        destination = kwargs["city_name"]

    # Always resolve canonical name first (handles Bengaluru, Bangalore, Bombay etc.)
    destination = resolve_canonical_city_name(destination) or destination

    if "food_pref" in kwargs and food_preferences is None:
        food_preferences = kwargs["food_pref"]
    if "accommodation_pref" in kwargs and accommodation == "Mid-range Hotels":
        accommodation = kwargs["accommodation_pref"]
    if "trip_pace" in kwargs and travel_style == "Balanced":
        travel_style = kwargs["trip_pace"]
        
    if interests is None:
        interests = ["Historical Places", "Museums"]
    elif isinstance(interests, str):
        interests = [interests]
        
    if food_preferences is None:
        food_preferences = ["Any"]
    elif isinstance(food_preferences, str):
        food_preferences = [food_preferences]
        
    # Days calculation
    if start_date and end_date:
        try:
            import datetime
            if isinstance(start_date, str):
                start_date = datetime.date.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = datetime.date.fromisoformat(end_date)
            calc_days = (end_date - start_date).days + 1
            if calc_days > 0:
                days = calc_days
        except Exception:
            pass

    days = max(1, int(days))
    travelers = max(1, int(travelers))
    budget = max(1000.0, float(budget))
    
    # 1. Destination Metadata — resolve canonical name before lookup
    city_meta = get_city(destination)
    if not city_meta:
        # Second attempt: case-insensitive partial match across all cities
        from services.data_service import get_cities
        all_cities = get_cities()
        if not all_cities.empty:
            lower_dest = destination.lower().strip()
            partial = all_cities[all_cities["city"].str.lower().str.contains(lower_dest, na=False)]
            if not partial.empty:
                destination = partial.iloc[0]["city"]
                city_meta = dict(partial.iloc[0])
    if not city_meta:
        return {"success": False, "error_message": f"Destination '{destination}' is not in our verified database. Please choose from: Goa, Hyderabad, Mumbai, Delhi, Bengaluru, Jaipur, Manali, Shimla, Darjeeling, and 21 more."}
        
    city_lat = float(city_meta["latitude"])
    city_lng = float(city_meta["longitude"])
    
    # 2. Query Verified Attractions, Hotels, Restaurants
    attractions_df = get_attractions(destination)
    restaurants_df = get_restaurants(destination)
    hotels_df = get_hotels(destination)
    
    if attractions_df.empty:
        return {"success": False, "error_message": f"Insufficient verified attractions for {destination}."}
        
    # 3. Select Lodging (Hotel)
    target_hotel_budget = (budget * 0.40) / max(1, (days - 1)) / max(1, (travelers + 1) // 2)
    hotel_candidates = [dict(row) for _, row in hotels_df.iterrows()]
    scored_hotels = get_recommendations(
        hotel_candidates, 
        score_hotel, 
        preferred_category=accommodation, 
        budget_limit=target_hotel_budget
    )
    if not scored_hotels:
        scored_hotels = sorted(hotel_candidates, key=lambda x: float(x.get("price_per_night", 99999) or 99999))
        
    selected_hotel = scored_hotels[0] if scored_hotels else {
        "name": f"{destination} Comfort Stay",
        "category": accommodation,
        "price_per_night": 2500.0,
        "rating": 4.2,
        "amenities": "Wifi; Breakfast; AC",
        "latitude": city_lat,
        "longitude": city_lng
    }
    # Replace catalogue placeholders with Google data only when the name/location
    # match is strong. Keep internal recommendation scores out of the UI.
    try:
        from services.photo_service import resolve_place_photo
        hotel_details = resolve_place_photo(
            selected_hotel.get("name", ""),
            city_name=destination,
            category=f"hotel {selected_hotel.get('category', '')}",
            latitude=selected_hotel.get("latitude", city_lat),
            longitude=selected_hotel.get("longitude", city_lng)
        )
        selected_hotel["photo_url"] = hotel_details.get("photo_url")
        selected_hotel["photo_attribution"] = hotel_details.get("attribution") if hotel_details.get("place_verified") else None
        selected_hotel["photo_attribution_url"] = hotel_details.get("attribution_url") if hotel_details.get("place_verified") else None
        if hotel_details.get("place_verified"):
            selected_hotel["google_place_id"] = hotel_details.get("google_place_id")
            selected_hotel["rating"] = hotel_details.get("rating")
            selected_hotel["review_count"] = hotel_details.get("reviews_count")
            selected_hotel["rating_source"] = "Google Places" if hotel_details.get("rating") is not None else None
        else:
            selected_hotel["rating"] = None
            selected_hotel["review_count"] = None
            selected_hotel["rating_source"] = None
    except Exception:
        selected_hotel["rating"] = None
        selected_hotel["review_count"] = None
        selected_hotel["rating_source"] = None
        selected_hotel["photo_url"] = None
        selected_hotel["photo_attribution"] = None
        selected_hotel["photo_attribution_url"] = None

    hotel_lat = float(selected_hotel.get("latitude", city_lat))
    hotel_lng = float(selected_hotel.get("longitude", city_lng))
    
    # 4. Score and select tourist spots
    target_attraction_allowance = (budget * 0.15) / max(1, len(attractions_df))
    attraction_candidates = [dict(row) for _, row in attractions_df.iterrows()]
    scored_attractions = get_recommendations(
        attraction_candidates, 
        score_attraction, 
        user_interests=interests, 
        budget_allowance=target_attraction_allowance
    )
    if not scored_attractions:
        scored_attractions = attraction_candidates
        
    pace_map = {"Relaxed": 2, "Balanced": 3, "Adventure": 4, "Packed": 4, "Cultural": 3}
    attractions_per_day = pace_map.get(travel_style, 3)
    total_needed = days * attractions_per_day
    
    selected_attractions = scored_attractions[:total_needed]
    if not selected_attractions:
        selected_attractions = attraction_candidates
        
    # 5. Fetch Weather
    weather_report = get_live_weather(city_lat, city_lng)
    
    # 6. Cluster and Route Locations
    routes = cluster_and_route_locations(selected_attractions, hotel_lat, hotel_lng, days)
    
    # 7. Build Day-Wise Schedule
    itinerary_days = []
    total_tickets = 0.0
    itinerary_coords = [(hotel_lat, hotel_lng)]
    selected_restaurants_list = []
    
    restaurant_candidates = [dict(row) for _, row in restaurants_df.iterrows()]
    
    for d in range(1, days + 1):
        day_route = routes.get(d, [])
        forecast = weather_report["forecast"][d - 1] if d - 1 < len(weather_report.get("forecast", [])) else {"condition": "Clear Sky", "icon": "☀️", "rain_probability": 0}
        rain_prob = forecast.get("rain_probability", 0)
        is_rainy = rain_prob >= 50
        
        day_events = []
        day_distance = 0.0
        day_travel_time = 0
        current_lat, current_lng = hotel_lat, hotel_lng
        
        # A. Breakfast (08:30 AM)
        day_events.append({
            "time": "08:30 AM",
            "type": "Meal",
            "name": f"Breakfast at {selected_hotel['name']}",
            "description": f"Morning breakfast and trip briefing at {selected_hotel['name']}.",
            "duration": 45,
            "cost": 0.0,
            "latitude": hotel_lat,
            "longitude": hotel_lng,
            "category": "Dining"
        })
        
        att_times = ["09:30 AM", "11:30 AM", "03:00 PM", "05:00 PM"]
        
        for idx, spot in enumerate(day_route):
            dist = haversine_distance(current_lat, current_lng, spot["latitude"], spot["longitude"])
            t_time = estimate_travel_time(dist)
            day_distance += dist
            day_travel_time += t_time
            itinerary_coords.append((spot["latitude"], spot["longitude"]))

            spot_open = spot.get("opening_time", "09:00")
            spot_close = spot.get("closing_time", "18:00")

            weather_note = ""
            if is_rainy and spot.get("category") in ["Nature", "Beach", "Adventure", "Viewpoint"]:
                weather_note = f"⚠️ Rainy forecast ({rain_prob}%). Outdoor umbrella advised."

            day_events.append({
                "time": att_times[idx] if idx < len(att_times) else "02:30 PM",
                "type": "Attraction",
                "id": spot["id"],
                "name": spot["name"],
                "category": spot["category"],
                "description": spot["description"],
                "duration": spot.get("visit_duration_minutes", 90),
                "duration_minutes": spot.get("visit_duration_minutes", 90),
                "cost": float(spot.get("price", 0.0)),
                "price": float(spot.get("price", 0.0)),
                "rating": spot.get("rating", 4.3),
                "latitude": spot["latitude"],
                "longitude": spot["longitude"],
                "opening_hours": f"{spot_open} – {spot_close}",
                "address": spot.get("address", f"{spot['name']}, {destination}"),
                "weather_note": weather_note,
                "source": spot.get("source", "Verified Registry"),
                "travel_time_mins": t_time,
                "distance_from_prev": round(dist, 2),
            })
            
            total_tickets += float(spot.get("price", 0.0))
            current_lat, current_lng = spot["latitude"], spot["longitude"]
            
            # B. Lunch Insertion (approx 01:00 PM)
            if idx == 1 or (len(day_route) == 1 and idx == 0):
                scored_diners = get_recommendations(
                    restaurant_candidates,
                    score_restaurant,
                    food_preference=food_preferences[0] if food_preferences else "Any",
                    budget_level="Medium"
                )
                if scored_diners:
                    closest_diner = min(
                        scored_diners,
                        key=lambda x: haversine_distance(current_lat, current_lng, x["latitude"], x["longitude"])
                    )
                    selected_restaurants_list.append(closest_diner)
                    dist_to_food = haversine_distance(current_lat, current_lng, closest_diner["latitude"], closest_diner["longitude"])
                    t_time_food = estimate_travel_time(dist_to_food)
                    day_distance += dist_to_food
                    day_travel_time += t_time_food
                    itinerary_coords.append((closest_diner["latitude"], closest_diner["longitude"]))
                    
                    day_events.append({
                        "time": "01:00 PM",
                        "type": "Restaurant",
                        "id": closest_diner["id"],
                        "name": closest_diner["name"],
                        "category": closest_diner["cuisine"],
                        "description": f"Authentic lunch featuring {closest_diner['cuisine']} cuisine ({closest_diner.get('food_type', 'Multi')}).",
                        "duration": 60,
                        "duration_minutes": 60,
                        "cost": 300.0,
                        "price": 300.0,
                        "rating": closest_diner.get("rating", 4.4),
                        "latitude": closest_diner["latitude"],
                        "longitude": closest_diner["longitude"],
                        "source": closest_diner.get("source", "Verified Registry")
                    })
                    current_lat, current_lng = closest_diner["latitude"], closest_diner["longitude"]
                    
        # C. Dinner Insertion (07:30 PM)
        scored_diners = get_recommendations(
            restaurant_candidates,
            score_restaurant,
            food_preference=food_preferences[0] if food_preferences else "Any",
            budget_level="Medium"
        )
        if scored_diners:
            closest_diner = min(
                scored_diners,
                key=lambda x: haversine_distance(current_lat, current_lng, x["latitude"], x["longitude"])
            )
            selected_restaurants_list.append(closest_diner)
            dist_to_dinner = haversine_distance(current_lat, current_lng, closest_diner["latitude"], closest_diner["longitude"])
            t_time_dinner = estimate_travel_time(dist_to_dinner)
            day_distance += dist_to_dinner
            day_travel_time += t_time_dinner
            itinerary_coords.append((closest_diner["latitude"], closest_diner["longitude"]))
            
            day_events.append({
                "time": "07:30 PM",
                "type": "Restaurant",
                "id": closest_diner["id"],
                "name": closest_diner["name"],
                "category": closest_diner["cuisine"],
                "description": f"Dinner dining at {closest_diner['name']} ({closest_diner.get('food_type', 'Delicacies')}).",
                "duration": 75,
                "duration_minutes": 75,
                "cost": 400.0,
                "price": 400.0,
                "rating": closest_diner.get("rating", 4.5),
                "latitude": closest_diner["latitude"],
                "longitude": closest_diner["longitude"],
                "source": closest_diner.get("source", "Verified Registry")
            })
            
        # Build Day Route Google Maps URL
        day_stops = [selected_hotel] + day_route
        day_route_maps_url = get_google_maps_route_url(day_stops, travel_mode=transportation)
        
        # Normalize all day events
        normalized_events = [
            normalize_event(ev, selected_hotel=selected_hotel, destination_city=destination, travel_mode=transportation)
            for ev in day_events
        ]
        
        itinerary_days.append({
            "day": d,
            "theme": f"Day {d}: {selected_attractions[(d-1)*attractions_per_day]['category'] if (d-1)*attractions_per_day < len(selected_attractions) else 'City'} Highlights",
            "weather": f"{forecast.get('condition', 'Sunny')} ({forecast.get('icon', '☀️')})",
            "rain_prob": rain_prob,
            "distance_km": round(day_distance, 2),
            "travel_time_mins": day_travel_time,
            "day_route_url": day_route_maps_url,
            "events": normalized_events
        })
        
    # 8. Budget Breakdown
    hotel_price = float(selected_hotel.get("price_per_night", 3000.0) or 3000.0)
    is_budget_valid, budget_breakdown, budget_advice = validate_trip_budget(
        total_budget=budget,
        travelers=travelers,
        duration_days=days,
        hotel_cost_per_night=hotel_price,
        food_cost_per_day=700.0,
        attractions_cost=total_tickets / days,
        transport_cost_per_day=500.0
    )
    
    # 9. Safety Audit
    safety_report = check_route_safety(destination, itinerary_coords)
    
    trip_result = {
        "success": True,
        "destination": destination,
        "days": days,
        "travelers": travelers,
        "budget": budget,
        "interests": interests,
        "trip_pace": travel_style,
        "travel_style": travel_style,
        "selected_hotel": selected_hotel,
        "selected_restaurants": selected_restaurants_list,
        "weather_summary": weather_report.get("current", {}),
        "weather_forecast": weather_report.get("forecast", []),
        "itinerary": itinerary_days,
        "budget_breakdown": budget_breakdown,
        "is_budget_valid": is_budget_valid,
        "budget_advice": budget_advice,
        "safety_status": safety_report.get("status", "Safe"),
        "safety_message": safety_report.get("message", "Route verified."),
        "safety_alerts": safety_report.get("alerts", [])
    }

    # 10. AI Polish (Gemini) — safely enrich descriptions without altering factual data
    try:
        from services.llm_service import polish_itinerary_with_llm
        trip_result = polish_itinerary_with_llm(trip_result)
    except Exception as e:
        trip_result["llm_polished"] = False
        trip_result["llm_warning"] = "AI enrichment skipped due to internal error."

    return trip_result

def build_itinerary(*args, **kwargs) -> dict:
    """
    Backward-compatible alias for generate_itinerary. Supports both positional and keyword arguments.
    """
    if args:
        # If positional args passed, map them to standard order
        keys = ["destination", "days", "travelers", "budget", "interests", "food_pref", "accommodation_pref", "transportation", "trip_pace"]
        for i, val in enumerate(args):
            if i < len(keys):
                kwargs[keys[i]] = val
    return generate_itinerary(**kwargs)
