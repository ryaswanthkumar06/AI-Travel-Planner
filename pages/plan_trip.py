import streamlit as st
import os
import json
import time
import datetime
import textwrap
import plotly.express as px
from services.data_service import get_cities, get_attractions, get_hotels, get_restaurants
from services.destination_image_service import (
    get_destination_image,
    get_attraction_image,
    get_hotel_image,
    get_restaurant_image,
    get_destination_photo,
    get_attraction_photo,
    get_hotel_photo,
    get_restaurant_photo,
    render_card_image_html,
    resolve_place_photo
)
from services.itinerary_service import generate_itinerary
from services.weather_service import get_live_weather
from services.safety_service import get_safety_report
from services.maps_service import get_google_maps_search_url, get_google_maps_directions_url, get_google_maps_route_url
from database.db_manager import save_trip, get_user_preferences

# Load stylesheet
with open("assets/style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Fetch user defaults from database if available
user = st.session_state.get("user", {"id": 1})
user_id = user.get("id", 1)
user_prefs = get_user_preferences(user_id) if user_id else {}

# Initialize Stepper States
if "plan_step" not in st.session_state:
    st.session_state["plan_step"] = 1
    
if "trip_inputs" not in st.session_state:
    st.session_state["trip_inputs"] = {}

trip_inputs = st.session_state["trip_inputs"]

# Setup defaults for all parameters
today = datetime.date.today()
defaults = {
    "destination": "Goa",
    "start_date": today + datetime.timedelta(days=7),
    "end_date": today + datetime.timedelta(days=9),
    "adults": 2,
    "children": 0,
    "seniors": 0,
    "traveler_type": "Couple",
    "budget_level": "Medium (Standard)",
    "custom_budget": 35000.0,
    "styles": ["Balanced"],
    "interests": ["Historical Places", "Beaches"],
    "food_pref": ["Any"],
    "accommodation": "Mid-range Hotels",
    "transport": "Public Transit"
}

# Apply database preferences if they exist
if user_prefs:
    if "budget_preference" in user_prefs and user_prefs["budget_preference"]:
        defaults["budget_level"] = user_prefs["budget_preference"]
    if "travel_style" in user_prefs and user_prefs["travel_style"]:
        defaults["styles"] = [user_prefs["travel_style"]]
    if "interests" in user_prefs and user_prefs["interests"]:
        if isinstance(user_prefs["interests"], str):
            defaults["interests"] = [i.strip() for i in user_prefs["interests"].split(",") if i.strip()]
        elif isinstance(user_prefs["interests"], list):
            defaults["interests"] = user_prefs["interests"]
    if "food_preference" in user_prefs and user_prefs["food_preference"]:
        defaults["food_pref"] = [user_prefs["food_preference"]]
    if "accommodation_preference" in user_prefs and user_prefs["accommodation_preference"]:
        defaults["accommodation"] = user_prefs["accommodation_preference"]
    if "transportation_preference" in user_prefs and user_prefs["transportation_preference"]:
        defaults["transport"] = user_prefs["transportation_preference"]

# Ensure every field is initialized safely
for key, val in defaults.items():
    if key not in trip_inputs or trip_inputs[key] is None:
        trip_inputs[key] = val

# Standardize date types and bounds
for key in ["start_date", "end_date"]:
    val = trip_inputs[key]
    if isinstance(val, str):
        try:
            trip_inputs[key] = datetime.datetime.strptime(val, "%Y-%m-%d").date()
        except Exception:
            trip_inputs[key] = defaults[key]

if trip_inputs["start_date"] < today:
    trip_inputs["start_date"] = today

if trip_inputs["end_date"] < trip_inputs["start_date"]:
    trip_inputs["end_date"] = trip_inputs["start_date"] + datetime.timedelta(days=2)

# ----------------------------------------------------
# 1. WIZARD STEPPER VIEW
# ----------------------------------------------------
if not st.session_state.get("active_trip"):
    st.markdown("<h2 style='color:#FFFFFF;'>🧭 Plan Your Trip</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.60);'>Customize your journey step-by-step and let AI create your verified day-wise itinerary.</p>", unsafe_allow_html=True)
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    
    # 9-Step Stepper Progress Bar — Sunset Travel Theme
    steps_titles = ["Destination", "Dates", "Travelers", "Budget", "Style", "Interests", "Food", "Stay", "Transport"]
    active_step = st.session_state["plan_step"]

    stepper_html = textwrap.dedent("""
    <style>
    .stepper-wrap { display:flex; justify-content:space-between; align-items:center;
                    margin-bottom:24px; overflow-x:auto; padding:12px 0; gap:0; }
    .step-item { text-align:center; flex:1; min-width:72px; }
    .step-circle { width:30px; height:30px; border-radius:50%; display:flex;
                   align-items:center; justify-content:center; margin:0 auto 5px auto;
                   font-size:0.82rem; font-weight:700; color:#FFFFFF !important; }
    .step-label  { font-size:0.73rem; font-weight:600; display:block; }
    .step-connector { flex:1; height:3px; min-width:12px; border-radius:99px;
                      margin-bottom:18px; }
    </style>
    <div class='stepper-wrap'>""").strip()

    for idx, title in enumerate(steps_titles):
        s_num = idx + 1
        if s_num < active_step:
            bg    = "#2D9D6E"
            lbl_c = "rgba(255,255,255,0.80)"
            symbol = "✓"
        elif s_num == active_step:
            bg    = "#FF7A59"
            lbl_c = "#FFFFFF"
            symbol = str(s_num)
        else:
            bg    = "rgba(255,255,255,0.15)"
            lbl_c = "rgba(255,255,255,0.45)"
            symbol = str(s_num)

        stepper_html += f"<div class='step-item'><div class='step-circle' style='background:{bg};'>{symbol}</div><span class='step-label' style='color:{lbl_c};'>{title}</span></div>"
        if idx < len(steps_titles) - 1:
            conn_c = "#2D9D6E" if s_num < active_step else ("#FF7A59" if s_num == active_step else "rgba(255,255,255,0.12)")
            stepper_html += f"<div class='step-connector' style='background:{conn_c};'></div>"

    stepper_html += "</div>"
    st.markdown(stepper_html, unsafe_allow_html=True)
    
    # Step Forms Container
    with st.container(border=True):
        if active_step == 1:
            st.markdown("### 🗺️ Step 1: Where do you want to go?")
            cities_df = get_cities()
            city_list = sorted(list(cities_df["city"].unique()))
            
            selected_city = st.selectbox(
                "Select destination from 30 verified Indian cities:", 
                city_list, 
                index=city_list.index(trip_inputs["destination"]) if trip_inputs["destination"] in city_list else 0
            )
            trip_inputs["destination"] = selected_city
            
            st.markdown("#### Popular Choices:")
            p_cols = st.columns(4)
            popular_picks = ["Goa", "Hyderabad", "Munnar", "Jaipur"]
            for i, p_name in enumerate(popular_picks):
                with p_cols[i]:
                    st.image(get_destination_image(p_name), use_container_width=True)
                    if st.button(f"Choose {p_name}", key=f"quick_step_{p_name}", use_container_width=True):
                        trip_inputs["destination"] = p_name
                        st.session_state["plan_step"] = 2
                        st.rerun()
                        
        elif active_step == 2:
            st.markdown("### 📅 Step 2: When are you traveling?")

            # Render start_date with minimum boundary set to today
            start_date = st.date_input("Start Date", value=trip_inputs["start_date"], min_value=datetime.date.today())

            # Dynamically adjust end_date value if start_date exceeds it
            min_end_date = start_date
            current_end = trip_inputs["end_date"]
            if current_end < start_date:
                current_end = start_date

            end_date = st.date_input("End Date", value=current_end, min_value=min_end_date)
            
            trip_inputs["start_date"] = start_date
            trip_inputs["end_date"] = end_date
            
            days_diff = (end_date - start_date).days + 1
            nights_diff = max(0, days_diff - 1)
            st.info(f"✨ Scheduled Duration: **{days_diff} Days / {nights_diff} Nights**")
            
        elif active_step == 3:
            st.markdown("### 👥 Step 3: Who is traveling?")
            traveler_type = st.radio(
                "Traveler Type:", 
                ["Solo", "Couple", "Family with Kids", "Friends Group"],
                index=["Solo", "Couple", "Family with Kids", "Friends Group"].index(trip_inputs.get("traveler_type", "Couple"))
            )
            trip_inputs["traveler_type"] = traveler_type
            
            tc1, tc2, tc3 = st.columns(3)
            with tc1:
                trip_inputs["adults"] = st.number_input("Adults (18+)", min_value=1, max_value=20, value=trip_inputs["adults"])
            with tc2:
                trip_inputs["children"] = st.number_input("Children (2-12)", min_value=0, max_value=10, value=trip_inputs["children"])
            with tc3:
                trip_inputs["seniors"] = st.number_input("Seniors (60+)", min_value=0, max_value=10, value=trip_inputs["seniors"])
                
        elif active_step == 4:
            st.markdown("### 💰 Step 4: Budget Preference")
            budget_opts = ["Budget (Backpacker)", "Medium (Standard)", "Luxury (Premium)", "Custom Exact Amount"]
            cur_b_level = trip_inputs.get("budget_level", "Medium (Standard)")
            b_level = st.selectbox("Select Spending Style:", budget_opts, index=budget_opts.index(cur_b_level) if cur_b_level in budget_opts else 1)
            trip_inputs["budget_level"] = b_level
            
            if b_level == "Custom Exact Amount":
                trip_inputs["custom_budget"] = st.number_input("Total Budget Cap (₹ INR):", min_value=5000.0, max_value=1000000.0, value=float(trip_inputs["custom_budget"]), step=5000.0)
            else:
                rates = {"Budget (Backpacker)": 2000.0, "Medium (Standard)": 4500.0, "Luxury (Premium)": 12000.0}
                days = (trip_inputs["end_date"] - trip_inputs["start_date"]).days + 1
                total_p = trip_inputs["adults"] + trip_inputs["children"] + trip_inputs["seniors"]
                est = rates.get(b_level, 4500.0) * days * total_p
                trip_inputs["custom_budget"] = est
                st.info(f"💡 Estimated Budget Calculation: **₹{est:,.0f}** for {days} days across {total_p} traveler(s).")
                
        elif active_step == 5:
            st.markdown("### 🎨 Step 5: Travel Pace & Style")
            styles_pool = ["Relaxed & Leisure", "Balanced & Moderate", "Fast-Paced Explorer", "Adventure & Trekking", "Culture & Heritage", "Foodie & Culinary"]
            cur_styles = trip_inputs.get("styles", ["Balanced & Moderate"])
            selected_styles = st.multiselect("Select Primary Styles:", styles_pool, default=[s for s in cur_styles if s in styles_pool] or ["Balanced & Moderate"])
            trip_inputs["styles"] = selected_styles if selected_styles else ["Balanced & Moderate"]
            
        elif active_step == 6:
            st.markdown("### 🏛️ Step 6: Places & Interests")
            interests_pool = ["Historical Places", "Museums", "Religious Places", "Nature & Scenery", "Beaches", "Wildlife & Safaris", "Shopping & Bazaars", "Nightlife & Pubs", "Adventure & Sports", "Local Food & Street Food"]
            cur_interests = trip_inputs.get("interests", ["Historical Places", "Nature & Scenery"])
            selected_interests = st.multiselect("Select Activities to Prioritize:", interests_pool, default=[i for i in cur_interests if i in interests_pool] or ["Historical Places"])
            trip_inputs["interests"] = selected_interests if selected_interests else ["Historical Places"]
            
        elif active_step == 7:
            st.markdown("### 🍽️ Step 7: Food & Dietary Preferences")
            food_opts = ["Vegetarian", "Non-Vegetarian", "Vegan", "Jain", "South Indian", "North Indian", "Seafood", "Street Food", "Any"]
            cur_food = trip_inputs.get("food_pref", ["Any"])
            selected_food = st.multiselect("Select Dietary Types:", food_opts, default=[f for f in cur_food if f in food_opts] or ["Any"])
            trip_inputs["food_pref"] = selected_food if selected_food else ["Any"]
            
        elif active_step == 8:
            st.markdown("### 🏨 Step 8: Accommodation Preference")
            stay_opts = ["Budget Hotels", "Mid-range Hotels", "Luxury Palaces", "Resorts", "Hostels", "Homestays"]
            cur_stay = trip_inputs.get("accommodation", "Mid-range Hotels")
            selected_stay = st.selectbox("Preferred Lodging Tier:", stay_opts, index=stay_opts.index(cur_stay) if cur_stay in stay_opts else 1)
            trip_inputs["accommodation"] = selected_stay
            
        elif active_step == 9:
            st.markdown("### 🚗 Step 9: Transportation Preference")
            trans_opts = ["Walking", "Public Transit", "Bus", "Train", "Taxi", "Rental Car", "Personal Vehicle"]
            cur_trans = trip_inputs.get("transport", "Public Transit")
            selected_trans = st.selectbox("Preferred Mode of Travel:", trans_opts, index=trans_opts.index(cur_trans) if cur_trans in trans_opts else 1)
            trip_inputs["transport"] = selected_trans
            
    # Stepper Navigation Buttons
    st.write("")
    nav_col1, nav_col2, nav_col3 = st.columns([2, 8, 3])
    with nav_col1:
        if active_step > 1:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state["plan_step"] -= 1
                st.rerun()
    with nav_col3:
        if active_step < 9:
            if st.button("Next Step ➡️", use_container_width=True, type="primary"):
                st.session_state["plan_step"] += 1
                st.rerun()
        else:
            if st.button("🚀 Generate Itinerary", use_container_width=True, type="primary"):
                progress_placeholder = st.empty()
                with progress_placeholder.container():
                    st.write("")
                    p_text = st.empty()
                    p_bar = st.progress(0)
                    loading_steps = [
                        "Analyzing your preferences...",
                        "Finding verified attractions...",
                        "Finding restaurants...",
                        "Checking hotels...",
                        "Checking weather forecasts...",
                        "Checking safety information...",
                        "Building your day-wise itinerary...",
                        "Optimizing route..."
                    ]
                    for idx, msg in enumerate(loading_steps):
                        p_text.markdown(f"⚙️ **SmartTravel Engine:** {msg}")
                        p_bar.progress((idx + 1) / len(loading_steps))
                        time.sleep(0.2)
                progress_placeholder.empty()
                
                days_count = (trip_inputs["end_date"] - trip_inputs["start_date"]).days + 1
                total_travelers = trip_inputs["adults"] + trip_inputs["children"] + trip_inputs["seniors"]
                
                try:
                    generated_trip = generate_itinerary(
                        destination=trip_inputs["destination"],
                        start_date=trip_inputs["start_date"],
                        end_date=trip_inputs["end_date"],
                        days=days_count,
                        travelers=total_travelers,
                        budget=trip_inputs["custom_budget"],
                        travel_style=trip_inputs["styles"][0] if trip_inputs["styles"] else "Balanced",
                        interests=trip_inputs["interests"],
                        food_preferences=trip_inputs["food_pref"],
                        accommodation=trip_inputs["accommodation"],
                        transportation=trip_inputs["transport"]
                    )
                    st.session_state["active_trip"] = generated_trip
                    st.session_state["active_trip_name"] = f"{trip_inputs['destination']} {days_count}-Day Adventure"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating itinerary: {str(e)}")

# ----------------------------------------------------
# 2. GENERATED ITINERARY VIEW
# ----------------------------------------------------
else:
    trip = st.session_state["active_trip"]
    destination = trip.get("destination", "Destination")
    trip_name = st.session_state.get("active_trip_name", f"{destination} Getaway")
    
    # Top Action Bar
    top_c1, top_c2, top_c3, top_c4, top_c5 = st.columns([3.2, 1.8, 1.8, 1.6, 1.6])
    with top_c1:
        st.markdown(f"<h2 style='color:#FFFFFF;margin:0;'>🎒 {trip_name}</h2>", unsafe_allow_html=True)
        meta_txt = f"{trip.get('days', 3)} Days · {trip.get('travelers', 2)} Travelers · ₹{trip.get('budget', 30000):,.0f} Budget"
        if trip.get("llm_polished"):
            meta_txt += " · ✨ AI Polished"
        st.markdown(f"<p style='color:rgba(255,255,255,0.60);margin:0;'>{meta_txt}</p>", unsafe_allow_html=True)
    
    is_saved = st.session_state.get("is_trip_saved", False) or bool(trip.get("id"))
    with top_c2:
        if is_saved:
            st.button("✅ Saved", disabled=True, use_container_width=True)
        else:
            if st.button("💾 Save Trip", type="primary", use_container_width=True):
                user_id = user.get("id", 1)
                try:
                    t_id = save_trip(
                        user_id=user_id,
                        name=trip_name,
                        destination=destination,
                        start_date=str(trip_inputs.get("start_date", "")),
                        end_date=str(trip_inputs.get("end_date", "")),
                        duration_days=int(trip.get("days", 3)),
                        travelers=int(trip.get("travelers", 2)),
                        budget=float(trip.get("budget", 30000)),
                        interests=trip_inputs.get("interests", []),
                        itinerary_json=json.dumps(trip.get("itinerary", [])),
                        hotel_json=json.dumps(trip.get("selected_hotel", {})),
                        restaurants_json=json.dumps(trip.get("selected_restaurants", [])),
                        travel_style=trip_inputs.get("styles", ["Balanced"])[0] if trip_inputs.get("styles") else "Balanced",
                        food_preferences=trip_inputs.get("food_pref", ["Any"]),
                        accommodation=trip_inputs.get("accommodation", "Mid-range Hotels"),
                        transportation=trip_inputs.get("transport", "Public Transit")
                    )
                    st.session_state["saved_trip_id"] = t_id
                    st.session_state["is_trip_saved"] = True
                    trip["id"] = t_id
                    st.success("✓ Trip saved successfully to My Trips!")
                    time.sleep(0.8)
                    st.rerun()
                except Exception as e:
                    st.error("Unable to save this trip right now. Please try again.")

    with top_c3:
        try:
            from services.pdf_service import generate_trip_pdf_bytes
            pdf_bytes = generate_trip_pdf_bytes(trip)
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=f"{destination}_SmartTravel_Itinerary.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception:
            if st.button("📥 Export PDF", use_container_width=True):
                st.info("PDF generation ready.")

    with top_c4:
        if st.button("🔄 Re-Plan", use_container_width=True):
            st.session_state["active_trip"] = None
            st.session_state["is_trip_saved"] = False
            st.rerun()

    with top_c5:
        if st.button("💬 Ask AI", use_container_width=True):
            st.session_state["chat_prefill"] = f"Tell me tips for my {destination} trip"
            st.switch_page("pages/assistant.py")
            
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    
    # 7-Tab Detail Display
    tab_itinerary, tab_map, tab_budget, tab_weather, tab_safety, tab_hotels, tab_restaurants = st.tabs([
        "📅 Day-by-Day Plan",
        "🗺️ Route Map",
        "💰 Budget Breakdown",
        "🌤️ Weather Forecast",
        "🛡️ Safety Advisor",
        "🏨 Recommended Hotels",
        "🍽️ Recommended Restaurants"
    ])
    
    # TAB 1: DAY-WISE ITINERARY
    with tab_itinerary:
        st.markdown("<h3 style='color:#FFFFFF;'>📅 Day-by-Day Timeline Schedule</h3>", unsafe_allow_html=True)
        
        # Selected Hotel Banner
        sh = trip.get("selected_hotel", {})
        if sh:
            with st.container(border=True):
                h_c1, h_c2 = st.columns([1.2, 3.8])
                with h_c1:
                    h_img = sh.get("photo_url") or get_hotel_photo(
                        sh.get("name", ""), city_name=destination, category=sh.get("category", "hotel"),
                        latitude=sh.get("latitude"), longitude=sh.get("longitude")
                    )
                    st.markdown(render_card_image_html(h_img, sh.get("name", "Hotel"), height_px=115,
                                                        border_radius="10px", category_icon="🏨"),
                                unsafe_allow_html=True)
                with h_c2:
                    st.markdown(f"🏨 **Primary Accommodation:** **{sh.get('name', 'Selected Lodging')}**")
                    hotel_rating = sh.get("rating")
                    hotel_reviews = sh.get("review_count")
                    if hotel_rating is not None:
                        review_label = f" ({hotel_reviews:,} reviews)" if hotel_reviews else ""
                        rating_label = f"⭐ {hotel_rating}{review_label} · Google Maps"
                    else:
                        rating_label = "Google rating unavailable"
                    st.markdown(f"{rating_label} | Class: {sh.get('category', 'Standard')} | ₹{sh.get('price_per_night', 3000):,.0f} / night")
                    st.markdown(f"🛌 Amenities: {str(sh.get('amenities', '')).replace(';', ', ')}")
                    h_map_url = get_google_maps_search_url(f"{sh.get('name')}, {destination}", sh.get("latitude"), sh.get("longitude"))
                    st.link_button("📍 Open Hotel in Maps", h_map_url)
                    
        # Loop Day Plans
        for day in trip["itinerary"]:
            day_num = day["day"]
            with st.expander(f"📅 **Day {day_num} — {day.get('theme', 'Explore')}** ({day.get('weather', 'Clear')})", expanded=True):
                if day.get("travel_tip"):
                    st.markdown(f"<div style='background:rgba(56,189,248,0.10);border:1px solid rgba(56,189,248,0.28);border-radius:8px;padding:8px 12px;margin-bottom:10px;'><span style='color:#38BDF8;font-size:0.82rem;font-weight:700;'>💡 Day {day_num} Tip:</span> <span style='color:rgba(255,255,255,0.85);font-size:0.82rem;'>{day['travel_tip']}</span></div>", unsafe_allow_html=True)
                if day.get("day_route_url"):
                    st.link_button(f"🚗 Open Day {day_num} Route in Google Maps", day["day_route_url"])
                    st.write("")
                    
                for ev in day.get("events", []):
                    with st.container(border=True):
                        col_ev_time, col_ev_body, col_ev_map = st.columns([2.4, 5.6, 2])
                        with col_ev_time:
                            st.markdown(f"**🕐 {ev.get('time', '10:00 AM')}**")
                            cat_badge = ev.get('category', 'Activity')
                            st.markdown(f"<span style='background:rgba(255,122,89,0.25);border:1px solid rgba(255,122,89,0.45);border-radius:999px;padding:2px 10px;font-size:0.72rem;font-weight:700;color:#FF9A7A;'>{cat_badge}</span>", unsafe_allow_html=True)
                            
                            ev_img = ev.get("photo_url") or ev.get("image_url")
                            if not ev_img:
                                if ev.get("type") == "Restaurant" or "dining" in cat_badge.lower():
                                    ev_img = get_restaurant_photo(ev.get("name", ""), city_name=destination)
                                elif ev.get("type") == "Meal":
                                    ev_img = trip.get("selected_hotel", {}).get("photo_url") or get_hotel_photo(
                                        trip.get("selected_hotel", {}).get("name", ""),
                                        city_name=destination,
                                        category=trip.get("selected_hotel", {}).get("category", "hotel")
                                    )
                                elif "hotel" in cat_badge.lower() or "stay" in cat_badge.lower():
                                    ev_img = get_hotel_photo(ev.get("name", ""), city_name=destination)
                                else:
                                    ev_img = get_attraction_photo(ev.get("name", ""), city_name=destination, category=cat_badge)
                                    
                            c_icon = "🍽️" if (ev.get("type") in ["Restaurant", "Meal"] or "dining" in cat_badge.lower()) else "🏛️"
                            st.markdown(render_card_image_html(ev_img, ev.get("name", "Place"), height_px=80, border_radius="8px", category_icon=c_icon), unsafe_allow_html=True)
                            
                            if ev.get("duration"):
                                st.markdown(f"<span style='font-size:0.78rem;color:rgba(255,255,255,0.55);'>⏱️ {ev['duration']} mins</span>", unsafe_allow_html=True)
                            if ev.get("distance_from_prev", 0) > 0:
                                st.markdown(f"<span style='font-size:0.74rem;color:rgba(255,255,255,0.50);'>🚗 +{ev['distance_from_prev']} km ({ev.get('travel_time_mins', 5)}m)</span>", unsafe_allow_html=True)
                        with col_ev_body:
                            st.markdown(f"<p style='font-family:Outfit,sans-serif;font-weight:800;font-size:1.05rem;color:#FFFFFF;margin:0 0 4px;'>{ev.get('name', 'Place')}</p>", unsafe_allow_html=True)
                            
                            rating_val = ev.get('rating') if ev.get("rating_source") == "Google Places" else None
                            rev_cnt = ev.get('review_count')
                            if rating_val is not None:
                                rev_txt = f" ({rev_cnt:,.0f} reviews)" if rev_cnt else ""
                                st.markdown(f"<span style='color:#FFD166;font-weight:700;font-size:0.82rem;'>⭐ {rating_val}{rev_txt} · Google Maps</span>", unsafe_allow_html=True)
                                
                            st.markdown(f"<p style='font-size:0.84rem;color:rgba(255,255,255,0.72);margin:4px 0 6px;'>{ev.get('description', '')}</p>", unsafe_allow_html=True)
                            if ev.get("why_recommended"):
                                st.markdown(f"<p style='font-size:0.78rem;color:#A7F3D0;margin:0 0 6px;'>✨ <em>Why: {ev['why_recommended']}</em></p>", unsafe_allow_html=True)
                            
                            if ev.get("address"):
                                st.markdown(f"<p style='font-size:0.76rem;color:rgba(255,255,255,0.50);margin:0 0 4px;'>📍 {ev['address']}</p>", unsafe_allow_html=True)
                            if ev.get("opening_hours"):
                                st.markdown(f"<p style='font-size:0.76rem;color:rgba(255,255,255,0.50);margin:0 0 4px;'>🕐 Hours: {ev['opening_hours']}</p>", unsafe_allow_html=True)
                                
                            if ev.get("cost", 0) > 0:
                                st.markdown(f"<span style='font-size:0.80rem;color:#FFD166;font-weight:700;'>💵 Est. Cost: ₹{ev['cost']:,.0f}</span>", unsafe_allow_html=True)
                            if ev.get("safety"):
                                st.warning(ev["safety"])
                            if ev.get("weather_note"):
                                st.info(ev["weather_note"])
                            if ev.get("interests") or ev.get("category"):
                                cat = ev.get('category', 'Activity')
                                st.markdown(f"<p style='font-size:0.74rem;color:rgba(255,255,255,0.42);margin:4px 0 0;'>Recommended for: {cat}</p>", unsafe_allow_html=True)
                        with col_ev_map:
                            if ev.get("maps_url"):
                                st.link_button("📍 Maps", ev["maps_url"], use_container_width=True)
                            if ev.get("directions_url"):
                                st.link_button("🚗 Route", ev["directions_url"], use_container_width=True)
                                
                # Day Summary Box
                day_evs = day.get("events", [])
                day_cost = sum(e.get("cost", 0) for e in day_evs)
                st.markdown(textwrap.dedent(f"""
                <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:10px;padding:12px 16px;margin-top:10px;">
                    <p style="font-weight:700;color:#FF9A7A;font-size:0.85rem;margin:0 0 6px;">📊 DAY {day_num} SUMMARY</p>
                    <div style="display:flex;flex-wrap:wrap;gap:16px;font-size:0.80rem;color:rgba(255,255,255,0.70);">
                        <span>🏛️ <strong>{len([e for e in day_evs if e.get('type')=='Attraction'])}</strong> Places</span>
                        <span>🍽️ <strong>{len([e for e in day_evs if e.get('type') in ['Restaurant','Meal']])}</strong> Dining Stops</span>
                        <span>🚗 <strong>{day.get('distance_km', 0):.1f} km</strong> Travel</span>
                        <span>⏱️ <strong>~{day.get('travel_time_mins', 0)} mins</strong> Transit</span>
                        <span>💰 <strong>₹{day_cost:,.0f}</strong> Day Expenses</span>
                    </div>
                </div>
                """).strip(), unsafe_allow_html=True)

        # OVERALL TRIP SUMMARY SECTION
        st.write("")
        st.markdown("<h3 style='color:#FFFFFF;border-left:3px solid #FF7A59;padding-left:12px;'>📋 Overall Trip Summary</h3>", unsafe_allow_html=True)
        b_summary = trip.get("budget_breakdown", {})
        total_dist = sum(d.get("distance_km", 0) for d in trip.get("itinerary", []))
        total_transit_time = sum(d.get("travel_time_mins", 0) for d in trip.get("itinerary", []))
        
        with st.container(border=True):
            sum_c1, sum_c2 = st.columns(2, gap="medium")
            with sum_c1:
                st.markdown(textwrap.dedent(f"""
                <p style="font-weight:700;color:#FF9A7A;margin-bottom:8px;">💰 Expense Breakdown</p>
                <div style="font-size:0.85rem;line-height:1.8;">
                    <div style="display:flex;justify-content:space-between;"><span>🏨 Accommodation</span><strong>₹{b_summary.get('hotel_cost', 0):,.0f}</strong></div>
                    <div style="display:flex;justify-content:space-between;"><span>🍽️ Food & Dining</span><strong>₹{b_summary.get('food_cost', 0):,.0f}</strong></div>
                    <div style="display:flex;justify-content:space-between;"><span>🎟️ Activities & Entry</span><strong>₹{b_summary.get('attractions_cost', 0):,.0f}</strong></div>
                    <div style="display:flex;justify-content:space-between;"><span>🚗 Transportation</span><strong>₹{b_summary.get('transport_cost', 0):,.0f}</strong></div>
                    <hr style="border-color:rgba(255,255,255,0.15);margin:6px 0;"/>
                    <div style="display:flex;justify-content:space-between;color:#FFD166;font-size:0.95rem;"><span>Total Estimated Cost</span><strong>₹{b_summary.get('total_cost', 0):,.0f}</strong></div>
                </div>
                """).strip(), unsafe_allow_html=True)
            with sum_c2:
                st.markdown(textwrap.dedent(f"""
                <p style="font-weight:700;color:#FF9A7A;margin-bottom:8px;">🚗 Logistics & Route Details</p>
                <div style="font-size:0.85rem;line-height:1.8;">
                    <div style="display:flex;justify-content:space-between;"><span>📍 Destination</span><strong>{trip.get('destination')}</strong></div>
                    <div style="display:flex;justify-content:space-between;"><span>📅 Duration</span><strong>{trip.get('days')} Days</strong></div>
                    <div style="display:flex;justify-content:space-between;"><span>👥 Travelers</span><strong>{trip.get('travelers')} Person(s)</strong></div>
                    <div style="display:flex;justify-content:space-between;"><span>🛣️ Total Distance</span><strong>~{total_dist:.1f} km</strong></div>
                    <div style="display:flex;justify-content:space-between;"><span>⏱️ Total Travel Time</span><strong>~{total_transit_time} mins</strong></div>
                    <div style="display:flex;justify-content:space-between;"><span>🚗 Travel Mode</span><strong>{trip.get('travel_style', 'Balanced')}</strong></div>
                </div>
                """).strip(), unsafe_allow_html=True)

    # TAB 2: INTERACTIVE ROUTE MAP
    with tab_map:
        st.markdown("### Route & Landmark Leaflet Map")
        
        map_points = []
        if sh.get("latitude") and sh.get("longitude"):
            map_points.append({"name": sh["name"], "type": "Hotel", "lat": sh["latitude"], "lng": sh["longitude"], "color": "purple"})
            
        for day in trip["itinerary"]:
            for ev in day["events"]:
                if ev.get("latitude") and ev.get("longitude"):
                    p_type = ev.get("type", "Attraction")
                    color = "blue"
                    if p_type == "Restaurant" or ev.get("category") == "Dining":
                        color = "green"
                    elif p_type == "Meal":
                        color = "purple"
                    map_points.append({"name": ev["name"], "type": p_type, "lat": ev["latitude"], "lng": ev["longitude"], "color": color})
                    
        for a in trip.get("safety_alerts", []):
            if a.get("latitude") and a.get("longitude"):
                map_points.append({"name": a["location_name"], "type": "Safety Hazard", "lat": a["latitude"], "lng": a["longitude"], "color": "red"})
                
        if not map_points:
            st.info("No coordinates available to plot map.")
        else:
            import streamlit.components.v1 as components
            markers_js = ""
            for p in map_points:
                popup_txt = f"<b>{p['name']}</b><br/>Type: {p['type']}"
                markers_js += f"L.marker([{p['lat']}, {p['lng']}]).addTo(map).bindPopup('{popup_txt}');\n"
                
            coords_poly = ", ".join(f"[{p['lat']}, {p['lng']}]" for p in map_points if p['type'] != 'Safety Hazard')
            
            map_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
                <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
                <style>#map {{ height: 420px; width: 100%; border-radius: 8px; }}</style>
            </head>
            <body>
                <div id="map"></div>
                <script>
                    var map = L.map('map').setView([{map_points[0]['lat']}, {map_points[0]['lng']}], 12);
                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                        attribution: '&copy; OpenStreetMap contributors'
                    }}).addTo(map);
                    {markers_js}
                    var route = L.polyline([{coords_poly}], {{color: '#28658F', weight: 4}}).addTo(map);
                    map.fitBounds(route.getBounds());
                </script>
            </body>
            </html>
            """
            components.html(map_html, height=440)
            
            st.markdown("""
            **Legend:** 🔵 Attractions | 🟣 Hotels & Accommodations | 🟢 Restaurants & Dining | 🔴 Highway Safety Zones
            """)
            
            all_stops_url = get_google_maps_route_url([{"latitude": p["lat"], "longitude": p["lng"], "name": p["name"]} for p in map_points if p["type"] != "Safety Hazard"], travel_mode=trip_inputs.get("transport", "driving"))
            st.link_button("🌐 View Complete Itinerary Route in Google Maps", all_stops_url, use_container_width=True)

    # TAB 3: BUDGET BREAKDOWN
    with tab_budget:
        st.markdown("### Itemized Budget Calculation")
        b = trip.get("budget_breakdown", {})
        total_b = b.get("total_budget", trip["budget"])
        est_cost = b.get("total_cost", 0.0)
        rem = b.get("remaining", total_b - est_cost)
        
        b_c1, b_c2, b_c3 = st.columns(3)
        with b_c1:
            st.metric("Total Budget Cap", f"₹{total_b:,.2f}")
        with b_c2:
            st.metric("Estimated Trip Cost", f"₹{est_cost:,.2f}")
        with b_c3:
            st.metric("Remaining Balance", f"₹{rem:,.2f}")
            
        if rem < 0:
            st.warning(f"⚠️ **Budget Warning:** This itinerary is approximately ₹{abs(rem):,.0f} above your selected budget cap.")
            if st.button("⚡ Optimize Budget (Auto-adjust Lodging)", type="primary"):
                st.session_state["trip_inputs"]["accommodation"] = "Budget Hotels"
                st.session_state["active_trip"] = None
                st.rerun()
                
        b_vals = [b.get("hotel_cost",0), b.get("food_cost",0), b.get("transport_cost",0), b.get("attractions_cost",0)]
        b_names = ["🏨 Accommodation", "🍽️ Food", "🚗 Transport", "🎟️ Activities"]
        b_colors = ["#3F6F9F", "#FF7A59", "#FFB07C", "#2D9D6E"]

        if sum(b_vals) > 0:
            fig = px.pie(
                names=b_names, values=b_vals,
                color_discrete_sequence=b_colors,
                hole=0.42
            )
            fig.update_traces(
                textposition="none",
                hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>"
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white", family="Inter"),
                showlegend=True,
                legend=dict(
                    orientation="v", x=1.02, y=0.5,
                    font=dict(color="white", size=13),
                    bgcolor="rgba(0,0,0,0)",
                    bordercolor="rgba(255,255,255,0.15)",
                    borderwidth=1,
                ),
                margin=dict(t=20, b=20, l=20, r=160),
                height=320,
                title=dict(
                    text="Budget Distribution",
                    font=dict(color="white", size=15),
                    x=0.5
                )
            )
            st.plotly_chart(fig, use_container_width=True, key="plan_trip_budget_pie")
        else:
            st.info("Budget breakdown not available for this itinerary.")

        st.write("")
        it1, it2 = st.columns(2, gap="large")
        with it1:
            for name, val in zip(b_names, b_vals):
                st.markdown(f"<div style='display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.72);font-size:0.86rem;'>{name}</span><span style='color:#FFFFFF;font-weight:700;font-size:0.86rem;'>₹{val:,.0f}</span></div>", unsafe_allow_html=True)
        with it2:
            st.markdown(f"<div style='background:rgba(255,122,89,0.12);border:1px solid rgba(255,122,89,0.30);border-radius:12px;padding:16px;text-align:center;'><p style='color:rgba(255,255,255,0.60);font-size:0.78rem;margin:0 0 4px;text-transform:uppercase;letter-spacing:0.07em;'>Total Planned Cost</p><p style='font-family:Outfit,sans-serif;font-size:2rem;font-weight:900;color:#FFFFFF;margin:0;'>₹{est_cost:,.0f}</p><p style='color:rgba(255,255,255,0.50);font-size:0.80rem;margin:6px 0 0;'>of ₹{total_b:,.0f} budget</p></div>", unsafe_allow_html=True)

    # TAB 4: WEATHER FORECAST
    with tab_weather:
        st.markdown(f"### Live Weather for {destination}")
        w_curr = trip.get("weather_summary", {})
        
        with st.container(border=True):
            wc1, wc2, wc3, wc4 = st.columns(4)
            with wc1:
                st.metric("Temperature", f"{w_curr.get('temp', 26)}°C")
            with wc2:
                st.metric("Condition", f"{w_curr.get('condition', 'Clear')}")
            with wc3:
                st.metric("Humidity", f"{w_curr.get('humidity', 60)}%")
            with wc4:
                st.metric("Wind Speed", f"{w_curr.get('wind', 10)} km/h")
                
        if trip.get("weather_forecast"):
            st.markdown("#### Multi-Day Forecast:")
            f_cols = st.columns(len(trip["weather_forecast"][:trip["days"]]))
            for idx, fc in enumerate(trip["weather_forecast"][:trip["days"]]):
                with f_cols[idx]:
                    with st.container(border=True):
                        st.markdown(f"**Day {idx+1}** ({fc.get('date', '')})")
                        st.markdown(f"{fc.get('icon', '🌤️')} **{fc.get('condition', 'Clear')}**")
                        st.markdown(f"Max: {fc.get('max_temp', 28)}°C | Min: {fc.get('min_temp', 20)}°C")
                        st.markdown(f"🌧️ Rain Chance: {fc.get('rain_probability', 0)}%")

    # TAB 5: SAFETY ADVISOR
    with tab_safety:
        st.markdown(f"### Highway Safety Status for {destination}")
        s_status = trip.get("safety_status", "Safe")
        if s_status == "High Risk":
            st.error(f"🚨 **Route Safety Threat Status: HIGH RISK**\n\n{trip.get('safety_message', '')}")
        elif s_status == "Caution":
            st.warning(f"⚠️ **Route Safety Threat Status: CAUTION**\n\n{trip.get('safety_message', '')}")
        else:
            st.success(f"✅ **Route Safety Threat Status: SAFE**\n\n{trip.get('safety_message', 'No highway accident blackspots on immediate path.')}")
            
        alerts = trip.get("safety_alerts", [])
        if alerts:
            st.markdown("#### Documented Hazard Corridors Along Route:")
            for a in alerts:
                with st.container(border=True):
                    st.markdown(f"⚠️ **{a['location_name']}** ({a['road_name']})")
                    st.markdown(f"Risk Level: **{a['risk_level']}** | Hazard: **{a['risk_type']}**")
                    st.markdown(f"🛡️ **Precaution:** *{a['recommended_action']}*")
                    zone_url = get_google_maps_search_url(f"{a['location_name']}, {destination}", a.get("latitude"), a.get("longitude"))
                    st.link_button("📍 View Hazard Spot on Map", zone_url)
        else:
            st.info("No recorded accident blackspots detected within 1.5 km of this itinerary's coordinates.")

    # TAB 6: RECOMMENDED HOTELS
    with tab_hotels:
        st.markdown(f"### Hotel Accommodations in {destination}")
        hotels_df = get_hotels(destination)
        for idx, row in hotels_df.iterrows():
            place_info = resolve_place_photo(
                row.get("name", ""), city_name=destination, category=row.get("category", "hotel"),
                latitude=row.get("latitude"), longitude=row.get("longitude")
            )
            hotel_img = place_info.get("photo_url") or get_hotel_image(
                row["category"], hotel_name=row.get("name", ""), city_name=destination,
                latitude=row.get("latitude"), longitude=row.get("longitude")
            )
            rating_text = (f"⭐ {place_info['rating']} · Google Maps"
                           if place_info.get("place_verified") and place_info.get("rating") is not None
                           else "Google rating unavailable")
            with st.container(border=True):
                h_c1, h_c2 = st.columns([1, 3])
                with h_c1:
                    st.markdown(render_card_image_html(hotel_img, row["name"], height_px=130,
                                                       attribution=place_info.get("attribution"),
                                                       category_icon="🏨"), unsafe_allow_html=True)
                with h_c2:
                    st.markdown(f"#### {row['name']}")
                    st.markdown(f"<span class='travel-badge badge-success'>{row['category']}</span> {rating_text}", unsafe_allow_html=True)
                    st.markdown(f"💰 **Nightly Rate:** ₹{row.get('price_per_night', 3000):,.0f}")
                    st.markdown(f"🛌 **Amenities:** {str(row.get('amenities', '')).replace(';', ', ')}")
                    h_url = get_google_maps_search_url(f"{row['name']}, {destination}", row.get("latitude"), row.get("longitude"))
                    st.link_button("📍 Open in Google Maps", h_url)

    # TAB 7: RECOMMENDED RESTAURANTS
    with tab_restaurants:
        st.markdown(f"### Dining & Eateries in {destination}")
        restaurants_df = get_restaurants(destination)
        for idx, row in restaurants_df.iterrows():
            place_info = resolve_place_photo(
                row.get("name", ""), city_name=destination, category=row.get("cuisine", "restaurant"),
                latitude=row.get("latitude"), longitude=row.get("longitude")
            )
            restaurant_img = place_info.get("photo_url") or get_restaurant_image(
                row["cuisine"], restaurant_name=row.get("name", ""), city_name=destination,
                latitude=row.get("latitude"), longitude=row.get("longitude")
            )
            rating_text = (f"⭐ {place_info['rating']} · Google Maps"
                           if place_info.get("place_verified") and place_info.get("rating") is not None
                           else "Google rating unavailable")
            with st.container(border=True):
                r_c1, r_c2 = st.columns([1, 3])
                with r_c1:
                    st.markdown(render_card_image_html(restaurant_img, row["name"], height_px=130,
                                                       attribution=place_info.get("attribution"),
                                                       category_icon="🍽️"), unsafe_allow_html=True)
                with r_c2:
                    st.markdown(f"#### {row['name']}")
                    st.markdown(f"🍱 **Cuisine:** {row['cuisine']} &nbsp;|&nbsp; 🥬 **Diet:** {row.get('food_type', 'Multi')}")
                    st.markdown(f"{rating_text} &nbsp;|&nbsp; 🕒 **Hours:** {row.get('opening_time', '10:00')} - {row.get('closing_time', '22:30')}")
                    r_url = get_google_maps_search_url(f"{row['name']}, {destination}", row.get("latitude"), row.get("longitude"))
                    st.link_button("📍 Open in Google Maps", r_url)
