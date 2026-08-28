import math
import os
from dotenv import load_dotenv

load_dotenv()

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates estimated road distance in kilometers between two geographic coordinates
    using the Haversine formula multiplied by a road curvature factor (1.3x).
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0.0
        
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    straight_line_dist = R * c
    
    # Apply standard urban road network factor (1.3x)
    road_distance = straight_line_dist * 1.3
    return round(road_distance, 1)

def calculate_travel_time(distance_km: float, mode: str = "Driving") -> str:
    """
    Calculates approximate travel time for a given distance and transportation mode.
    Modes: Driving, Cab, Public Transit, Walking, Cycling
    """
    if distance_km <= 0:
        return "5 min"
        
    mode_lower = mode.lower()
    if "walk" in mode_lower:
        speed_kmh = 4.5
        mins = int((distance_km / speed_kmh) * 60)
        return f"{mins} min walking" if mins < 60 else f"{mins // 60}h {mins % 60}m walking"
    elif "bike" in mode_lower or "cycl" in mode_lower:
        speed_kmh = 15.0
        mins = int((distance_km / speed_kmh) * 60)
        return f"{mins} min" if mins < 60 else f"{mins // 60}h {mins % 60}m"
    elif "transit" in mode_lower or "bus" in mode_lower or "train" in mode_lower:
        speed_kmh = 22.0
        mins = int((distance_km / speed_kmh) * 60) + 5  # +5 min wait time
        return f"{mins} min (Transit)" if mins < 60 else f"{mins // 60}h {mins % 60}m (Transit)"
    else:  # Driving / Taxi / Cab
        speed_kmh = 30.0  # City traffic average in India
        mins = max(5, int((distance_km / speed_kmh) * 60))
        return f"{mins} min drive" if mins < 60 else f"{mins // 60}h {mins % 60}m drive"
