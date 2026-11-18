import pandas as pd

INTEREST_CATEGORY_MAP = {
    "Historical Places": ["Historical", "Heritage"],
    "Nature": ["Nature", "Garden", "Viewpoint"],
    "Adventure": ["Adventure"],
    "Beaches": ["Beach"],
    "Museums": ["Museums", "Historical"],
    "Culture": ["Culture", "Historical"],
    "Shopping": ["Shopping"],
    "Local Food": ["Food"],
    "Street Food": ["Food"],
    "Photography": ["Viewpoint", "Nature", "Garden"],
    "Religious Places": ["Religious Places"],
    "Nightlife": ["Entertainment"],
    "Family Activities": ["Family", "Entertainment", "Wildlife", "Garden"],
    "Wildlife": ["Wildlife", "Nature"],
    "Relaxation": ["Nature", "Garden", "Beach"]
}

def score_attraction(attraction, user_interests, budget_allowance=1000):
    """
    attraction: dict representing an attraction record
    user_interests: list of strings
    budget_allowance: approximate allowance for single monument entry fee
    
    Returns final_score (0-100).
    """
    # 1. Interest Score (35%)
    interest_match = 0.0
    for interest in user_interests:
        mapped_categories = INTEREST_CATEGORY_MAP.get(interest, [])
        if attraction.get("category") in mapped_categories:
            interest_match = 1.0
            break
    interest_score = interest_match * 100.0
    
    # 2. Rating Score (15%)
    rating = attraction.get("google_rating")
    if rating is None or pd.isna(rating):
        rating_score = 50.0  # Neutral until a live, verified rating is available.
    else:
        rating_score = (float(rating) / 5.0) * 100.0
    
    # 3. Budget Compatibility (15%)
    price = float(attraction.get("price", 0.0) or 0.0)
    if price == 0.0:
        budget_score = 100.0
    else:
        if price <= budget_allowance:
            budget_score = 100.0 - (price / budget_allowance) * 30.0  # slightly lower for higher prices
        else:
            budget_score = max(0.0, 70.0 - ((price - budget_allowance) / budget_allowance) * 50.0)
            
    # 4. Timing Compatibility (10%)
    time_score = 100.0  # defaults high, scheduling overlaps handled in routing
    
    # 5. Distance (15%) and Visit Duration (10%)
    distance_score = 80.0  # baseline, updated when specific routes are ordered
    duration_score = 100.0
    
    final_score = (
        (interest_score * 0.35) +
        (rating_score * 0.15) +
        (budget_score * 0.15) +
        (time_score * 0.10) +
        (distance_score * 0.15) +
        (duration_score * 0.10)
    )
    
    return round(final_score, 2)

def score_restaurant(restaurant, food_preference, budget_level="Medium"):
    """
    restaurant: dict representing a restaurant record
    food_preference: string representing diet
    budget_level: string (Low, Medium, High)
    """
    # 1. Food Type Diet Match (40%) - STRICT VETO FOR VEGETARIANS
    diet = restaurant.get("food_type", "Mixed")
    if food_preference == "Pure Vegetarian" and diet != "Vegetarian":
        return 0.0  # Zero score - vetoed
    elif food_preference == "Vegan" and diet not in ["Vegan", "Vegetarian"]:
        return 0.0  # Zero score - vetoed
    else:
        food_score = 100.0
        
    # 2. Rating Score (40%)
    rating = restaurant.get("google_rating")
    if rating is None or pd.isna(rating):
        rating_score = 50.0  # Do not rank sample catalogue rows using invented stars.
    else:
        rating_score = (float(rating) / 5.0) * 100.0
    
    # 3. Price Tier Match (20%)
    price_tier = restaurant.get("price_range", "Mid-range")
    
    # Standardize names
    budget_level = budget_level.lower()
    if "low" in budget_level or "budget" in budget_level:
        target_tier = "Budget"
    elif "high" in budget_level or "luxury" in budget_level:
        target_tier = "High"
    else:
        target_tier = "Mid-range"
        
    if price_tier == target_tier:
        price_score = 100.0
    elif (target_tier == "Mid-range") or (target_tier == "High" and price_tier == "Mid-range") or (target_tier == "Budget" and price_tier == "Mid-range"):
        price_score = 60.0  # partially matching mid
    else:
        price_score = 30.0  # low compatibility
        
    final_score = (food_score * 0.40) + (rating_score * 0.40) + (price_score * 0.20)
    return round(final_score, 2)

def score_hotel(hotel, preferred_category, budget_limit=5000):
    """
    hotel: dict representing a hotel record
    preferred_category: string category preferred
    budget_limit: per night maximum
    """
    # 1. Category Match (40%)
    category = hotel.get("category", "Mid-range")
    
    # Check overlaps
    pref = preferred_category.lower()
    if "hostel" in pref or "budget" in pref or "homestay" in pref:
        is_match = category in ["Budget", "Hostel", "Homestay"]
    elif "luxury" in pref:
        is_match = category == "Luxury"
    else:
        is_match = category == "Mid-range"
        
    cat_score = 100.0 if is_match else 40.0
        
    # 2. Rating Score (40%)
    rating = hotel.get("google_rating")
    if rating is None or pd.isna(rating):
        rating_score = 50.0  # Do not rank sample catalogue rows using invented stars.
    else:
        rating_score = (float(rating) / 5.0) * 100.0
    
    # 3. Price Compatibility (20%)
    price = hotel.get("price_per_night")
    if pd.isna(price) or price is None:
        price_score = 50.0
    else:
        price = float(price)
        if price <= budget_limit:
            # fits beautifully
            price_score = 100.0
        else:
            # exceeds, compute penalty factor
            price_score = max(0.0, 100.0 - ((price - budget_limit) / budget_limit) * 100.0)
            
    final_score = (cat_score * 0.40) + (rating_score * 0.40) + (price_score * 0.20)
    return round(final_score, 2)

def get_recommendations(candidates, scorer_fn, **kwargs):
    """
    Generic helper to score and sort lists of candidates.
    candidates: list of dicts or DataFrame rows
    scorer_fn: scoring function
    """
    scored = []
    for item in candidates:
        item_dict = dict(item)
        score = scorer_fn(item_dict, **kwargs)
        if score > 0:  # ignore strict vetoes
            item_dict["score"] = score
            scored.append(item_dict)
            
    # Sort descending
    return sorted(scored, key=lambda x: x["score"], reverse=True)
