import streamlit as st
import streamlit.components.v1 as components
import json

# Load stylesheet
with open("assets/style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("<h2 style='color:#FFFFFF;'>📍 Route Map Viewer</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:rgba(255,255,255,0.60);'>Interactive routing, coordinates, and highway safety accident-zone overlays.</p>", unsafe_allow_html=True)
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

if not st.session_state.get("active_trip"):
    with st.container(border=True):
        st.markdown("""
        <div style="text-align:center;padding:36px 20px;">
            <p style="font-size:3rem;margin-bottom:10px;">🗺️</p>
            <p style="font-family:Outfit,sans-serif;font-weight:800;font-size:1.15rem;color:#FFFFFF;margin-bottom:8px;">No Active Trip</p>
            <p style="color:rgba(255,255,255,0.55);font-size:0.88rem;">Generate a trip via <strong style="color:#FF9A7A;">Plan Trip</strong> to view your interactive route map.</p>
        </div>
        """, unsafe_allow_html=True)
    if st.button("🧭 Plan a Trip Now", type="primary"):
        st.switch_page("pages/plan_trip.py")
else:
    trip = st.session_state["active_trip"]
    destination = trip["destination"]
    st.success(f"📍 Displaying active route map for **{st.session_state.get('active_trip_name', destination)}**")
    
    # 1. Compile coordinates lists and marker lists for Leaflet
    hotel = trip["selected_hotel"]
    hotel_lat = float(hotel["latitude"])
    hotel_lng = float(hotel["longitude"])
    hotel_name = hotel["name"].replace("'", "\\'")
    
    # Day colors dictionary
    day_colors = {
        1: "#0284C7",  # Blue
        2: "#7C3AED",  # Purple
        3: "#10B981",  # Green
        4: "#F59E0B",  # Orange
        5: "#EC4899",  # Pink
        6: "#14B8A6",  # Teal
        7: "#6366F1"   # Indigo
    }
    
    marker_js = []
    routes_js = []
    
    # Hotel Marker
    marker_js.append(f"""
    L.circleMarker([{hotel_lat}, {hotel_lng}], {{
        color: '#0F172A',
        fillColor: '#334155',
        fillOpacity: 0.8,
        radius: 10,
        weight: 3
    }}).addTo(map).bindPopup("<b>🏠 Lodging: {hotel_name}</b><br/>{hotel['category']} Accommodation");
    """)
    
    # Add attractions and restaurants
    has_missing_coords = False
    
    for day in trip["itinerary"]:
        d_num = day["day"]
        color = day_colors.get(d_num, "#0284C7")
        day_coords = [(hotel_lat, hotel_lng)] # start day route from hotel
        
        for ev in day["events"]:
            if ev["type"] in ["Attraction", "Restaurant"]:
                lat_val = ev.get("lat") or ev.get("latitude")
                lng_val = ev.get("lng") or ev.get("longitude")
                
                if lat_val is not None and lng_val is not None:
                    lat = float(lat_val)
                    lng = float(lng_val)
                    name = ev["name"].replace("'", "\\'")
                    desc = ev.get("category", "").replace("'", "\\'")
                    time = ev["time"]
                    
                    day_coords.append((lat, lng))
                    
                    icon = "🏛️" if ev["type"] == "Attraction" else "🍽️"
                    m_color = "#0284C7" if ev["type"] == "Attraction" else "#10B981"
                    
                    marker_js.append(f"""
                    L.circleMarker([{lat}, {lng}], {{
                        color: '{color}',
                        fillColor: '{m_color}',
                        fillOpacity: 0.9,
                        radius: 8,
                        weight: 2
                    }}).addTo(map).bindPopup("<b>{icon} {name}</b><br/>Day {d_num} - {time}<br/>{desc}");
                    """)
                else:
                    has_missing_coords = True
                
        # Return to hotel at night
        day_coords.append((hotel_lat, hotel_lng))
        
        # Add Polyline for this day
        coords_str = ", ".join(f"[{lat}, {lng}]" for lat, lng in day_coords)
        dash_style = "'5, 10'" if d_num % 2 == 0 else "''"
        routes_js.append(f"""
        L.polyline([{coords_str}], {{
            color: '{color}',
            weight: 4,
            opacity: 0.8,
            dashArray: {dash_style}
        }}).addTo(map);
        """)
        
    if has_missing_coords:
        st.warning("⚠️ Some itinerary locations do not have verified coordinates and could not be mapped.")
        
    # Add Safety / Accident Zones (RED markers with 1.5 km radius circle)
    for zone in trip.get("safety_alerts", []):
        z_lat_val = zone.get("latitude") or zone.get("lat")
        z_lng_val = zone.get("longitude") or zone.get("lng")
        if z_lat_val is None or z_lng_val is None:
            continue
            
        z_lat = float(z_lat_val)
        z_lng = float(z_lng_val)
        z_name = zone["location_name"].replace("'", "\\'")
        z_road = zone["road_name"].replace("'", "\\'")
        z_risk = zone["risk_level"]
        z_advice = zone["recommended_action"].replace("'", "\\'")
        
        marker_js.append(f"""
        // Safety Zone Center Marker
        L.circleMarker([{z_lat}, {z_lng}], {{
            color: '#DC2626',
            fillColor: '#EF4444',
            fillOpacity: 1.0,
            radius: 8,
            weight: 2
        }}).addTo(map).bindPopup("<b>⚠️ HIGH RISK ZONE: {z_name}</b><br/>Road: {z_road}<br/>Advice: {z_advice}");
        
        // 1.5 km Safety Warning Circle Radius
        L.circle([{z_lat}, {z_lng}], {{
            color: '#EF4444',
            fillColor: '#FCA5A5',
            fillOpacity: 0.15,
            radius: 1500
        }}).addTo(map);
        """)
        
    # Generate complete HTML code block for Leaflet
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SmartTravel AI Leaflet Map</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            html, body, #map {{
                height: 100%;
                width: 100%;
                margin: 0;
                padding: 0;
            }}
            .legend {{
                padding: 6px 8px;
                font: 12px/14px Arial, Helvetica, sans-serif;
                background: white;
                background: rgba(255,255,255,0.9);
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
                border-radius: 5px;
                line-height: 18px;
                color: #555;
            }}
            .legend i {{
                width: 18px;
                height: 18px;
                float: left;
                margin-right: 8px;
                opacity: 0.7;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            // Initialize map centered at the hotel
            var map = L.map('map').setView([{hotel_lat}, {hotel_lng}], 13);
            
            // Add standard OpenStreetMap tiles
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}).addTo(map);
            
            // Render route lines
            {"".join(routes_js)}
            
            // Render markers
            {"".join(marker_js)}
            
            // Add Legend
            var legend = L.control({{position: 'bottomright'}});
            legend.onAdd = function (map) {{
                var div = L.DomUtil.create('div', 'legend');
                div.innerHTML += '<b>Route Key</b><br/>';
                div.innerHTML += '<i style="background: #334155; border-radius: 50%;"></i> Lodging Hotel<br/>';
                div.innerHTML += '<i style="background: #0284C7; border-radius: 50%;"></i> Sightseeing Monument<br/>';
                div.innerHTML += '<i style="background: #10B981; border-radius: 50%;"></i> Local Restaurant<br/>';
                div.innerHTML += '<i style="background: #DC2626; border-radius: 50%;"></i> Traffic Hazard Zone<br/>';
                div.innerHTML += '<i style="background: rgba(239,68,68,0.2); border: 1px solid #EF4444;"></i> Caution Boundary (1.5 km)<br/>';
                return div;
            }};
            legend.addTo(map);
        </script>
    </body>
    </html>
    """
    
    # Render Leaflet html container
    components.html(map_html, height=600, scrolling=False)
    
    st.markdown("""
    💡 **Map Controls**:
    - Use mouse scroll or touch gesture to zoom in/out.
    - Click on any marker node (Hotel, Attraction, Diner, or Hazard) to read descriptions, scheduled timings, and safety warnings.
    - Lines represent route legs connecting your day stops chronologically.
    """)
