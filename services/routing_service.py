import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points in kilometers.
    """
    R = 6371.0  # Earth radius in kilometers
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    return R * c

def estimate_travel_time(distance_km, speed_kmh=25.0):
    """
    Estimates travel time in minutes based on distance and average speed.
    Adds a baseline 5 minutes for traffic buffer.
    """
    if distance_km <= 0.0:
        return 0
    time_hours = distance_km / speed_kmh
    time_minutes = time_hours * 60.0
    return int(time_minutes + 5)  # add 5 minutes buffer

def cluster_and_route_locations(locations, hotel_lat, hotel_lng, days):
    """
    Partitions attractions into 'days' clusters and orders each day's route.
    Uses a greedy clustering and Nearest Neighbor route optimizer.
    
    locations: list of dicts with 'latitude' and 'longitude'
    days: int
    """
    if not locations:
        return {}
        
    days = int(days)
    unassigned = list(locations)
    clusters = {i: [] for i in range(1, days + 1)}
    
    # 1. Cluster attractions to days
    for day in range(1, days + 1):
        if not unassigned:
            break
            
        # Target number of attractions for this day
        target_count = math.ceil(len(unassigned) / (days - day + 1))
        
        # Start cluster with the furthest unassigned item from the hotel (anchors the day's region)
        furthest_item = None
        max_dist = -1.0
        
        for item in unassigned:
            dist = haversine_distance(hotel_lat, hotel_lng, item["latitude"], item["longitude"])
            if dist > max_dist:
                max_dist = dist
                furthest_item = item
                
        unassigned.remove(furthest_item)
        day_cluster = [furthest_item]
        
        # Fill the day's cluster with closest unassigned items to this anchor
        while len(day_cluster) < target_count and unassigned:
            anchor = day_cluster[-1]
            closest_item = min(
                unassigned,
                key=lambda x: haversine_distance(anchor["latitude"], anchor["longitude"], x["latitude"], x["longitude"])
            )
            unassigned.remove(closest_item)
            day_cluster.append(closest_item)
            
        clusters[day] = day_cluster

    # 2. Optimize routes for each day (Nearest Neighbor sequence)
    routes = {}
    for day, cluster in clusters.items():
        if not cluster:
            routes[day] = []
            continue
            
        # Route starting from hotel -> nearest attraction -> next nearest -> ...
        route = []
        current_lat, current_lng = hotel_lat, hotel_lng
        remaining = list(cluster)
        
        while remaining:
            next_spot = min(
                remaining,
                key=lambda x: haversine_distance(current_lat, current_lng, x["latitude"], x["longitude"])
            )
            remaining.remove(next_spot)
            route.append(next_spot)
            current_lat, current_lng = next_spot["latitude"], next_spot["longitude"]
            
        routes[day] = route
        
    return routes
