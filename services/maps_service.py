import urllib.parse

def get_google_maps_search_url(query: str, lat: float = None, lng: float = None) -> str:
    """
    Generates a Google Maps search URL.
    If coordinates are provided, centers or targets exact lat,lng.
    """
    if lat is not None and lng is not None:
        q = f"{query} {lat},{lng}" if query else f"{lat},{lng}"
    else:
        q = query or ""
    encoded = urllib.parse.quote_plus(q)
    return f"https://www.google.com/maps/search/?api=1&query={encoded}"

def get_google_maps_directions_url(
    origin: str,
    destination: str,
    travel_mode: str = "driving",
    origin_coords: tuple = None,
    dest_coords: tuple = None
) -> str:
    """
    Generates a Google Maps directions URL between two locations.
    travel_mode options: driving, walking, bicycling, transit
    """
    mode_map = {
        "walking": "walking",
        "public transit": "transit",
        "bus": "transit",
        "train": "transit",
        "taxi": "driving",
        "rental car": "driving",
        "personal vehicle": "driving",
        "driving": "driving"
    }
    mode = mode_map.get(str(travel_mode).lower().strip(), "driving")
    
    orig_str = f"{origin_coords[0]},{origin_coords[1]}" if origin_coords else origin
    dest_str = f"{dest_coords[0]},{dest_coords[1]}" if dest_coords else destination
    
    encoded_orig = urllib.parse.quote_plus(str(orig_str))
    encoded_dest = urllib.parse.quote_plus(str(dest_str))
    
    return f"https://www.google.com/maps/dir/?api=1&origin={encoded_orig}&destination={encoded_dest}&travelmode={mode}"

def get_google_maps_route_url(
    stops: list,
    travel_mode: str = "driving"
) -> str:
    """
    Generates a multi-stop Google Maps directions URL.
    stops: list of dicts with 'name', 'latitude', 'longitude' or list of strings
    """
    if not stops:
        return "https://www.google.com/maps"
    if len(stops) == 1:
        s = stops[0]
        if isinstance(s, dict):
            return get_google_maps_search_url(s.get("name", ""), s.get("latitude"), s.get("longitude"))
        return get_google_maps_search_url(str(s))
        
    mode_map = {
        "walking": "walking",
        "public transit": "transit",
        "bus": "transit",
        "train": "transit",
        "taxi": "driving",
        "rental car": "driving",
        "personal vehicle": "driving",
        "driving": "driving"
    }
    mode = mode_map.get(str(travel_mode).lower().strip(), "driving")
    
    def format_stop(s):
        if isinstance(s, dict):
            if s.get("latitude") and s.get("longitude"):
                return f"{s['latitude']},{s['longitude']}"
            return s.get("name", "")
        return str(s)
        
    origin = urllib.parse.quote_plus(format_stop(stops[0]))
    destination = urllib.parse.quote_plus(format_stop(stops[-1]))
    
    waypoints = ""
    if len(stops) > 2:
        wp_list = [format_stop(s) for s in stops[1:-1]]
        waypoints = urllib.parse.quote_plus("|".join(wp_list))
        return f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&waypoints={waypoints}&travelmode={mode}"
        
    return f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&travelmode={mode}"
