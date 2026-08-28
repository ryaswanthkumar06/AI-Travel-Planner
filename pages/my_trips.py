import streamlit as st
import json
import textwrap
from database.db_manager import get_user_trips, delete_trip
from services.destination_image_service import (
    get_destination_image,
    get_destination_photo,
    render_card_image_html
)
from services.maps_service import get_google_maps_search_url

with open("assets/style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(textwrap.dedent("""
<style>
.trip-row {
    background: rgba(255,255,255,0.09);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 14px;
    display: flex; align-items: center; gap: 14px;
    padding: 14px 16px; margin-bottom: 10px;
    backdrop-filter: blur(12px);
    transition: background 0.2s;
}
.trip-row:hover { background: rgba(255,255,255,0.14); }
.trip-info { flex: 1; min-width: 0; }
.trip-name {
    font-family: 'Outfit', sans-serif; font-weight: 800;
    font-size: 0.96rem; color: #FFFFFF !important;
    margin: 0 0 4px; overflow: hidden;
    text-overflow: ellipsis; white-space: nowrap;
}
.trip-meta { font-size: 0.78rem; color: rgba(255,255,255,0.55) !important; margin: 0; }
.trip-badge {
    background: rgba(255,122,89,0.18); border: 1px solid rgba(255,122,89,0.32);
    border-radius: 999px; padding: 3px 10px;
    font-size: 0.72rem; font-weight: 700; color: #FF9A7A !important;
    white-space: nowrap; flex-shrink: 0;
}
</style>
""").strip(), unsafe_allow_html=True)

user    = st.session_state.get("user", {"name": "Traveler", "id": 1})
user_id = user.get("id", 1)
trips   = get_user_trips(user_id)

# Header
st.markdown("<h2 style='color:#FFFFFF;'>🎒 My Trips</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:rgba(255,255,255,0.60);'>All your saved itineraries in one place.</p>", unsafe_allow_html=True)
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# Filter
fc1, fc2 = st.columns([3, 1], gap="medium")
with fc1:
    trip_search = st.text_input(" ", placeholder="🔍  Search trips…", label_visibility="collapsed", key="mytrips_search")
with fc2:
    sort_opt = st.selectbox(" ", ["Newest First", "Oldest First", "By Destination"], label_visibility="collapsed", key="mytrips_sort")

filtered_trips = trips
if trip_search:
    q = trip_search.lower()
    filtered_trips = [t for t in trips if q in t["name"].lower() or q in t["destination"].lower()]
if sort_opt == "Oldest First":
    filtered_trips = list(reversed(filtered_trips))
elif sort_opt == "By Destination":
    filtered_trips = sorted(filtered_trips, key=lambda t: t["destination"])

# Summary stats
if trips:
    sc1, sc2, sc3, sc4 = st.columns(4, gap="medium")
    for col, val, lbl in [
        (sc1, len(trips),                "Saved Trips"),
        (sc2, len(set(t["destination"] for t in trips)), "Destinations"),
        (sc3, sum(t["duration_days"] for t in trips),    "Total Days"),
        (sc4, f"₹{sum(float(t['budget']) for t in trips):,.0f}", "Total Budget"),
    ]:
        with col:
            st.metric(lbl, val)
    st.write("")

if not filtered_trips:
    st.info("💡 No saved trips yet — plan your first adventure!" if not trip_search else "No trips match your search.")
    if st.button("🧭 Plan a New Trip", type="primary", use_container_width=False):
        st.switch_page("pages/plan_trip.py")
else:
    for t in filtered_trips:
        img = get_destination_photo(t["destination"])
        img_html = render_card_image_html(img, t["destination"], height_px=65, border_radius="10px", category_icon="🌍")
        
        date_display = f"{t.get('start_date')} to {t.get('end_date')} ({t['duration_days']}d)" if (t.get("start_date") and t.get("end_date")) else f"{t['duration_days']} days"
        
        st.markdown(textwrap.dedent(f"""
        <div class="trip-row">
            <div style="width:80px;flex-shrink:0;">
                {img_html}
            </div>
            <div class="trip-info">
                <p class="trip-name">{t['name']}</p>
                <p class="trip-meta">
                    📍 {t['destination']} &nbsp;·&nbsp;
                    📅 {date_display} &nbsp;·&nbsp;
                    👥 {t['travelers']} travelers &nbsp;·&nbsp;
                    💰 ₹{float(t['budget']):,.0f}
                </p>
            </div>
            <span class="trip-badge">{t['destination']}</span>
        </div>
        """).strip(), unsafe_allow_html=True)

        bc1, bc2, bc3, bc4 = st.columns([1, 1, 1.2, 1], gap="small")
        with bc1:
            if st.button("👁️ View", key=f"mt_view_{t['id']}", use_container_width=True):
                st.session_state["active_trip"] = {
                    "id": t["id"], "destination": t["destination"],
                    "days": t["duration_days"], "travelers": t["travelers"],
                    "budget": t["budget"],
                    "start_date": t.get("start_date", ""),
                    "end_date": t.get("end_date", ""),
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
                st.session_state["is_trip_saved"] = True
                st.switch_page("pages/plan_trip.py")
        with bc2:
            maps_url = get_google_maps_search_url(f"{t['destination']}, India")
            st.link_button("📍 Maps", maps_url, use_container_width=True)
        with bc3:
            try:
                from services.pdf_service import generate_trip_pdf_bytes
                t_obj = {
                    "destination": t["destination"],
                    "days": t["duration_days"],
                    "travelers": t["travelers"],
                    "budget": t["budget"],
                    "itinerary": json.loads(t["itinerary_json"]) if t.get("itinerary_json") else [],
                    "selected_hotel": json.loads(t["hotel_json"]) if t.get("hotel_json") else {},
                    "selected_restaurants": json.loads(t["restaurants_json"]) if t.get("restaurants_json") else [],
                    "safety_status": "Safe",
                    "safety_message": "Verified Safe",
                    "safety_alerts": []
                }
                pdf_bytes = generate_trip_pdf_bytes(t_obj)
                st.download_button(
                    label="📥 PDF",
                    data=pdf_bytes,
                    file_name=f"{t['destination']}_Itinerary.pdf",
                    mime="application/pdf",
                    key=f"mt_pdf_{t['id']}",
                    use_container_width=True
                )
            except Exception:
                st.button("📥 PDF", key=f"mt_pdf_dis_{t['id']}", disabled=True, use_container_width=True)
        with bc4:
            if st.button("🗑️ Del", key=f"mt_del_{t['id']}", use_container_width=True):
                delete_trip(t["id"])
                st.rerun()
        st.write("")
