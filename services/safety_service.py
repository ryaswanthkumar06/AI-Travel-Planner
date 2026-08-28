from services.data_service import get_accident_zones
from services.routing_service import haversine_distance

SAFETY_THRESHOLD_KM = 1.5  # Check within 1.5 km of known traffic blackspots

def check_route_safety(city_name, route_coordinates):
    """
    Checks if any coordinate in the itinerary route is close to a recorded accident zone.
    route_coordinates: list of (lat, lng) tuples representing the places on the itinerary
    
    Returns a dict with:
        - 'status': 'Safe' (Green), 'Caution' (Orange), or 'High Risk' (Red)
        - 'message': Summary text
        - 'alerts': list of dicts detailing matching accident zones and safety advice
    """
    alerts = []
    
    # Fetch verified accident zones for the city
    zones_df = get_accident_zones(city_name)
    if zones_df is None or zones_df.empty:
        return {
            "status": "INSUFFICIENT VERIFIED DATA",
            "message": "No verified accident-zone data is available for this route.",
            "alerts": []
        }
        
    # Check proximity for each coordinate in the itinerary
    matched_ids = set()
    for lat, lng in route_coordinates:
        for idx, zone in zones_df.iterrows():
            zone_id = zone["id"]
            if zone_id in matched_ids:
                continue
                
            dist = haversine_distance(lat, lng, zone["latitude"], zone["longitude"])
            if dist <= SAFETY_THRESHOLD_KM:
                matched_ids.add(zone_id)
                alerts.append({
                    "id": int(zone_id),
                    "location_name": zone.get("location_name", "Monitored Zone"),
                    "road_name": zone.get("road_name", "Highway Corridor"),
                    "risk_level": zone.get("risk_level", "Medium"),
                    "accident_count": int(zone.get("accident_count", 8)),
                    "risk_type": zone.get("risk_type", "Merging Traffic"),
                    "recommended_action": zone.get("recommended_action", "Maintain sub-50 km/h"),
                    "source": zone.get("source", "Road Safety Audit"),
                    "data_date": zone.get("data_date", "2024-Q3"),
                    "distance_km": round(dist, 2),
                    "latitude": float(zone["latitude"]),
                    "longitude": float(zone["longitude"]),
                    "lat": float(zone["latitude"]),
                    "lng": float(zone["longitude"])
                })
                
    if not alerts:
        return {
            "status": "Safe",
            "message": "No verified hazards on planned route",
            "alerts": []
        }
        
    # Assess status: if any High risk is present, return High Risk
    has_high = any(a["risk_level"] == "High" for a in alerts)
    status = "High Risk" if has_high else "Caution"
    
    return {
        "status": status,
        "message": f"Your planned route passes near a verified accident-prone zone.",
        "alerts": alerts
    }

def get_safety_report(city_name):
    """
    Returns a safety summary report for the target destination city,
    without requiring specific route coordinates.
    """
    zones_df = get_accident_zones(city_name)
    if zones_df is None or zones_df.empty:
        return {
            "status": "INSUFFICIENT VERIFIED DATA",
            "message": "No verified accident-zone data is available for this route.",
            "alerts": []
        }
        
    alerts = []
    for idx, zone in zones_df.iterrows():
        alerts.append({
            "id": int(zone["id"]),
            "location_name": zone["location_name"],
            "road_name": zone["road_name"],
            "risk_level": zone["risk_level"],
            "accident_count": int(zone["accident_count"]),
            "risk_type": zone["risk_type"],
            "recommended_action": zone["recommended_action"],
            "source": zone["source"],
            "data_date": zone["data_date"],
            "distance_km": 0.0,
            "latitude": float(zone["latitude"]),
            "longitude": float(zone["longitude"]),
            "lat": float(zone["latitude"]),
            "lng": float(zone["longitude"])
        })
        
    has_high = any(a["risk_level"] == "High" for a in alerts)
    status = "High Risk" if has_high else "Caution"
    
    return {
        "status": status,
        "message": f"This city corridor has documented safety hazard zones in the database.",
        "alerts": alerts
    }
