from services.data_service import get_attractions, get_restaurants, get_hotels

def validate_generated_itinerary(itinerary_data):
    """
    Validates the generated itinerary against the database and budget constraints.
    Returns: (is_valid, errors_list)
    """
    errors = []
    destination = itinerary_data.get("destination")
    budget = float(itinerary_data.get("budget", 0.0))
    
    # 1. Fetch DB datasets to verify existence
    attractions_df = get_attractions(destination)
    restaurants_df = get_restaurants(destination)
    hotels_df = get_hotels(destination)
    
    db_attraction_ids = set(attractions_df["id"].tolist()) if not attractions_df.empty else set()
    db_restaurant_ids = set(restaurants_df["id"].tolist()) if not restaurants_df.empty else set()
    db_hotel_ids = set(hotels_df["id"].tolist()) if not hotels_df.empty else set()
    
    # 2. Check Hotel existence
    hotel = itinerary_data.get("selected_hotel")
    if not hotel:
        errors.append("Itinerary is missing a selected hotel.")
    else:
        if hotel.get("id") not in db_hotel_ids:
            errors.append(f"Hotel '{hotel.get('name')}' (ID {hotel.get('id')}) is not in the verified database.")
            
    # 3. Check Day-by-day events
    visited_attractions = set()
    
    for day in itinerary_data.get("itinerary", []):
        day_num = day.get("day")
        for event in day.get("events", []):
            ev_type = event.get("type")
            ev_name = event.get("name")
            ev_id = event.get("id")
            
            if ev_type == "Attraction":
                # Check DB existence
                if ev_id not in db_attraction_ids:
                    errors.append(f"Day {day_num}: Attraction '{ev_name}' (ID {ev_id}) is not in the verified database.")
                
                # Check duplicate visits
                if ev_id in visited_attractions:
                    errors.append(f"Day {day_num}: Attraction '{ev_name}' (ID {ev_id}) is duplicated in the itinerary.")
                visited_attractions.add(ev_id)
                
                # Verify coordinates exist
                if not event.get("lat") or not event.get("lng"):
                    errors.append(f"Day {day_num}: Attraction '{ev_name}' is missing coordinates.")
                    
            elif ev_type == "Restaurant":
                # Check DB existence
                if ev_id not in db_restaurant_ids:
                    errors.append(f"Day {day_num}: Restaurant '{ev_name}' (ID {ev_id}) is not in the verified database.")
                # Verify coordinates exist
                if not event.get("lat") or not event.get("lng"):
                    errors.append(f"Day {day_num}: Restaurant '{ev_name}' is missing coordinates.")
                    
    # 4. Check total cost
    breakdown = itinerary_data.get("budget_breakdown", {})
    total_cost = breakdown.get("total_cost", 0.0)
    if total_cost > budget:
        errors.append(f"Total calculated cost ₹{total_cost:,.2f} exceeds user budget limit of ₹{budget:,.2f}.")
        
    is_valid = len(errors) == 0
    return is_valid, errors
