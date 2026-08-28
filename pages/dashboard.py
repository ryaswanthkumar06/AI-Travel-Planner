import streamlit as st
import pandas as pd
import json
import textwrap
from database.db_manager import get_user_trips, delete_trip
from services.destination_image_service import (
    get_destination_image,
    get_destination_photo,
    render_card_image_html
)
from services.maps_service import get_google_maps_search_url
from services.weather_service import get_live_weather
from services.data_service import get_cities

with open("assets/style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

user    = st.session_state.get("user", {"name": "Traveler", "id": 1})
user_id = user.get("id", 1)
trips   = get_user_trips(user_id)
cities_df = get_cities()

try:
    attractions_count = len(pd.read_csv("data/attractions.csv"))
    hotels_count      = len(pd.read_csv("data/hotels.csv"))
    restaurants_count = len(pd.read_csv("data/restaurants.csv"))
    safety_count      = len(pd.read_csv("data/accident_zones.csv"))
except Exception:
    attractions_count = hotels_count = restaurants_count = safety_count = 0

num_trips          = len(trips)
unique_cities      = len(set(t["destination"] for t in trips))
total_budget_spent = sum(float(t["budget"]) for t in trips)
active_trip        = st.session_state.get("active_trip")
ctx_city           = active_trip["destination"] if active_trip else (trips[0]["destination"] if trips else "Goa")

# Header
st.markdown("<h2 style='color:#FFFFFF;'>📈 Travel Dashboard</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='color:rgba(255,255,255,0.60);'>Welcome back, <strong style='color:#FF9A7A;'>{user.get('name','Traveler')}</strong>. Here's your SmartTravel AI overview.</p>", unsafe_allow_html=True)
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# Stats row
s1, s2, s3, s4 = st.columns(4, gap="medium")
for col, val, lbl in [
    (s1, num_trips,           "Trips Planned"),
    (s2, unique_cities,       "Cities Visited"),
    (s3, f"₹{total_budget_spent:,.0f}", "Total Budget"),
    (s4, len(cities_df),      "Database Cities"),
]:
    with col:
        st.metric(lbl, val)

st.write("")

left_col, right_col = st.columns([2, 1], gap="large")

with left_col:
    st.markdown("<h3 style='color:#FFFFFF;border-left:3px solid #FF7A59;padding-left:12px;'>🎒 Saved Itineraries</h3>", unsafe_allow_html=True)
    if not trips:
        st.info("💡 No saved trips yet.")
        if st.button("🧭 Plan a New Trip Now", type="primary"):
            st.switch_page("pages/plan_trip.py")
    else:
        for t in trips[:5]:
            img = get_destination_photo(t["destination"])
            maps_url = get_google_maps_search_url(f"{t['destination']}, India")
            img_html = render_card_image_html(img, t["destination"], height_px=65, border_radius="10px", category_icon="🌍")
            st.markdown(textwrap.dedent(f"""
            <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.12);
                        border-radius:14px;display:flex;align-items:center;gap:14px;
                        padding:12px 16px;margin-bottom:10px;backdrop-filter:blur(12px);">
                <div style="width:78px;flex-shrink:0;">
                    {img_html}
                </div>
                <div style="flex:1;min-width:0;">
                    <p style="font-family:Outfit,sans-serif;font-weight:800;font-size:0.96rem;
                               color:#FFFFFF;margin:0 0 4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                        {t['name']}
                    </p>
                    <p style="font-size:0.78rem;color:rgba(255,255,255,0.52);margin:0;">
                        📍 {t['destination']} &nbsp;·&nbsp; 📅 {t['duration_days']}d &nbsp;·&nbsp;
                        👥 {t['travelers']} &nbsp;·&nbsp; 💰 ₹{float(t['budget']):,.0f}
                    </p>
                </div>
            </div>
            """).strip(), unsafe_allow_html=True)
            dc1, dc2, dc3 = st.columns(3, gap="small")
            with dc1:
                if st.button("👁️ View", key=f"dash_v_{t['id']}", use_container_width=True):
                    st.session_state["active_trip"] = {
                        "id": t["id"], "destination": t["destination"],
                        "days": t["duration_days"], "travelers": t["travelers"],
                        "budget": t["budget"],
                        "itinerary": json.loads(t["itinerary_json"]) if t.get("itinerary_json") else [],
                        "selected_hotel": json.loads(t["hotel_json"]) if t.get("hotel_json") else {},
                        "selected_restaurants": json.loads(t["restaurants_json"]) if t.get("restaurants_json") else [],
                        "budget_breakdown": {"total_budget": t["budget"], "hotel_cost": 0, "food_cost": 0,
                                             "transport_cost": 0, "attractions_cost": 0, "total_cost": 0, "remaining": t["budget"]},
                        "safety_status": "Safe", "safety_message": "Verified.",
                        "safety_alerts": [], "weather_summary": {"temp": 26, "condition": "Pleasant",
                        "icon": "⛅", "wind": 10, "humidity": 65, "feels_like": 28, "fetched_time": 0, "cached": True},
                        "weather_forecast": [],
                    }
                    st.session_state["active_trip_name"] = t["name"]
                    st.switch_page("pages/plan_trip.py")
            with dc2:
                st.link_button("📍 Maps", maps_url, use_container_width=True)
            with dc3:
                if st.button("🗑️ Del", key=f"dash_d_{t['id']}", use_container_width=True):
                    delete_trip(t["id"])
                    st.rerun()
            st.write("")

        if len(trips) > 5:
            if st.button(f"→ View all {len(trips)} trips", use_container_width=False):
                st.switch_page("pages/my_trips.py")

with right_col:
    st.markdown("<h3 style='color:#FFFFFF;border-left:3px solid #FF7A59;padding-left:12px;'>⚡ Quick Actions</h3>", unsafe_allow_html=True)
    for label, page in [
        ("🧭 Plan a Trip", "pages/plan_trip.py"),
        ("🌍 Explore India", "pages/explore.py"),
        ("🎒 My Trips", "pages/my_trips.py"),
        ("💬 AI Assistant", "pages/assistant.py"),
        ("🛡️ Safety Check", "pages/safety.py"),
    ]:
        if st.button(label, use_container_width=True, key=f"dash_qa_{page}"):
            st.switch_page(page)

    st.write("")
    st.markdown("<h3 style='color:#FFFFFF;border-left:3px solid #FF7A59;padding-left:12px;'>📊 Data Coverage</h3>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(textwrap.dedent(f"""
        <div style="font-size:0.88rem;line-height:2;color:rgba(255,255,255,0.75);">
            🗺️ <strong style="color:#FFFFFF;">Cities:</strong> {len(cities_df)}<br>
            🏛️ <strong style="color:#FFFFFF;">Attractions:</strong> {attractions_count}<br>
            🏨 <strong style="color:#FFFFFF;">Hotels:</strong> {hotels_count}<br>
            🍽️ <strong style="color:#FFFFFF;">Restaurants:</strong> {restaurants_count}<br>
            🛡️ <strong style="color:#FFFFFF;">Safety Zones:</strong> {safety_count}
        </div>
        """).strip(), unsafe_allow_html=True)
        st.write("")
        if st.button("🔍 Explore Full Database", use_container_width=True):
            st.switch_page("pages/explore.py")
