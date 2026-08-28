import pandas as pd

def allocate_budget_targets(total_budget, travelers, duration_days):
    """
    Allocates target budget allocations based on standard trip percentages:
    - Lodging: 40%
    - Dining: 30%
    - Attractions / Entry fees: 15%
    - Local Transport: 15%
    """
    total_budget = float(total_budget)
    travelers = int(travelers)
    duration_days = int(duration_days)
    
    per_person = total_budget / travelers
    daily_total = total_budget / duration_days
    
    return {
        "total_budget": total_budget,
        "travelers": travelers,
        "duration_days": duration_days,
        "per_person_limit": per_person,
        "daily_limit": daily_total,
        "target_lodging": total_budget * 0.40,
        "target_dining": total_budget * 0.30,
        "target_attractions": total_budget * 0.15,
        "target_transport": total_budget * 0.15
    }

def validate_trip_budget(total_budget, travelers, duration_days, hotel_cost_per_night, food_cost_per_day, attractions_cost, transport_cost_per_day):
    """
    Validates if the estimated costs fit within the overall budget.
    - hotel_cost_per_night: price for lodging per night (typically 1 room for solo/couple, 2+ rooms for friends/family).
      Let's assume: 1 room for up to 2 people, and 1 extra room for every 2 additional people.
    """
    total_budget = float(total_budget)
    travelers = int(travelers)
    duration_days = int(duration_days)
    
    # Calculate room count needed
    rooms_needed = max(1, (travelers + 1) // 2)
    
    total_hotel = float(hotel_cost_per_night or 0.0) * rooms_needed * (duration_days - 1 if duration_days > 1 else 1)
    total_food = float(food_cost_per_day or 300.0) * travelers * duration_days
    total_attractions = float(attractions_cost or 0.0) * travelers
    total_transport = float(transport_cost_per_day or 100.0) * duration_days * travelers
    
    total_cost = total_hotel + total_food + total_attractions + total_transport
    remaining = total_budget - total_cost
    is_valid = total_cost <= total_budget
    
    breakdown = {
        "total_budget": total_budget,
        "hotel_cost": round(total_hotel, 2),
        "food_cost": round(total_food, 2),
        "attractions_cost": round(total_attractions, 2),
        "transport_cost": round(total_transport, 2),
        "total_cost": round(total_cost, 2),
        "remaining": round(remaining, 2)
    }
    
    advice = []
    if not is_valid:
        excess = total_cost - total_budget
        advice.append(f"⚠️ Your current plan exceeds your budget by ₹{excess:,.2f}.")
        
        # Determine main cost driver
        costs = [
            ("hotel", total_hotel, "Choose a cheaper accommodation tier (e.g. Budget or Mid-range instead of Luxury)."),
            ("attractions", total_attractions, "Remove high-ticket paid excursions and prefer free monuments/parks."),
            ("food", total_food, "Select budget local diners instead of premium fine dining restaurants.")
        ]
        costs_sorted = sorted(costs, key=lambda x: x[1], reverse=True)
        
        for name, cost, suggestion in costs_sorted:
            if cost > (total_budget * 0.30):
                advice.append(f"- **{name.capitalize()} Cost (₹{cost:,.2f})**: {suggestion}")
    else:
        advice.append("🟢 Your trip is within budget!")
        
    return is_valid, breakdown, "\n".join(advice)
