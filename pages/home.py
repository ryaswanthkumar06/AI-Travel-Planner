import streamlit as st
import pandas as pd
import textwrap
from services.data_service import get_cities, get_hotels, get_restaurants
from services.destination_image_service import (
    get_destination_image,
    get_hotel_image,
    get_restaurant_image,
    get_destination_photo,
    get_hotel_photo,
    get_restaurant_photo,
    render_card_image_html,
    resolve_place_photo,
    is_places_api_configured
)
from services.maps_service import get_google_maps_search_url
from services.weather_service import get_live_weather
from services.google_places_service import search_place_details
from database.db_manager import get_user_trips

with open("assets/style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

user    = st.session_state.get("user", {"name": "Traveler", "id": 1})
user_id = user.get("id", 1)

# ── Page-scoped styles ────────────────────────────────────────────
st.markdown(textwrap.dedent("""
<style>
/* Home page hero */
.hero-wrap {
    background: linear-gradient(135deg, rgba(16,24,43,0.72) 0%, rgba(16,24,43,0.55) 100%);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 20px;
    padding: 46px 42px;
    backdrop-filter: blur(8px);
    position: relative; overflow: hidden;
}
.hero-wrap::before {
    content: '';
    position: absolute; top: -60px; right: -60px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(255,122,89,0.22) 0%, transparent 70%);
    border-radius: 50%; pointer-events: none;
}
.hero-headline {
    font-family: 'Outfit', sans-serif !important;
    font-size: clamp(2rem, 4vw, 3rem) !important;
    font-weight: 900 !important; color: #FFFFFF !important;
    line-height: 1.1 !important; margin: 0 0 12px 0;
    text-shadow: 0 3px 16px rgba(0,0,0,0.40) !important;
}
.hero-accent { color: #FF7A59 !important; }
.hero-sub {
    color: rgba(255,255,255,0.75) !important;
    font-size: 0.98rem; line-height: 1.65; max-width: 480px; margin-bottom: 0;
}
.weather-chip {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.22);
    border-radius: 999px; padding: 6px 16px;
    color: #FFFFFF !important; font-size: 0.88rem; font-weight: 600;
    backdrop-filter: blur(8px); margin-bottom: 14px;
}
.user-chip {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(255,122,89,0.18); border: 1px solid rgba(255,122,89,0.35);
    border-radius: 999px; padding: 5px 14px;
    color: #FFFFFF !important; font-size: 0.83rem; font-weight: 600;
}
.why-item {
    display: flex; align-items: flex-start; gap: 14px;
    background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px; padding: 16px 18px; margin-bottom: 10px;
    backdrop-filter: blur(8px); transition: background 0.2s;
}
.why-item:hover { background: rgba(255,255,255,0.10); }
.why-icon-wrap {
    width: 40px; height: 40px; border-radius: 10px;
    background: rgba(255,122,89,0.20); border: 1px solid rgba(255,122,89,0.35);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; flex-shrink: 0;
}
.why-title { font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 0.95rem; color: #FFFFFF !important; margin: 0 0 2px; }
.why-sub   { font-size: 0.80rem; color: rgba(255,255,255,0.55) !important; margin: 0; }
.section-hdr {
    font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 1.15rem;
    color: #FFFFFF !important; margin: 0 0 14px;
}
</style>
""").strip(), unsafe_allow_html=True)

# ── Fetch Data ───────────────────────────────────────────────────
cities_df   = get_cities()
user_trips  = get_user_trips(user_id)
active_trip = st.session_state.get("active_trip")

# Active context city for weather and highlights
ctx_city = "Goa"
if active_trip:
    ctx_city = active_trip.get("destination", "Goa")
elif user_trips:
    ctx_city = user_trips[0].get("destination", "Goa")

# Weather for context city
weather_info = None
try:
    c_row = cities_df[cities_df["city"].str.lower() == ctx_city.lower()]
    if not c_row.empty:
        weather_info = get_live_weather(float(c_row.iloc[0]["latitude"]), float(c_row.iloc[0]["longitude"]))
except Exception:
    pass

# ── Layout ────────────────────────────────────────────────────────
left_col, right_col = st.columns([2.6, 1.4], gap="large")

with left_col:
    # ── HERO SECTION ─────────────────────────────────────────────
    w_badge_html = ""
    if weather_info:
        w_badge_html = f'<div class="weather-chip"><span>{weather_info.get("icon","☀️")}</span><span>{ctx_city} {weather_info.get("temp","—")}°C · {weather_info.get("condition","Pleasant")}</span></div>'

    st.markdown(textwrap.dedent(f"""
    <div class="hero-wrap">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap;">
            <div class="user-chip">👋 Welcome back, <strong>{user.get('name','Traveler')}</strong></div>
            {w_badge_html}
        </div>
        <h1 class="hero-headline">
            Plan Smarter.<br>
            <span class="hero-accent">Travel Safer.</span><br>
            Explore India.
        </h1>
        <p class="hero-sub">
            AI-driven itineraries with verified attractions, live weather forecasts,
            integrated route safety alerts, and curated culinary experiences.
        </p>
    </div>
    """).strip(), unsafe_allow_html=True)

    st.write("")

    # ── QUICK SEARCH BAR ─────────────────────────────────────────
    s_col1, s_col2 = st.columns([3, 1], gap="small")
    with s_col1:
        search_q = st.text_input(
            " ",
            placeholder="🔍  Search 30+ destinations (e.g., Goa, Jaipur, Munnar, Varanasi…)",
            label_visibility="collapsed",
            key="home_dest_search"
        )
    with s_col2:
        if st.button("Explore All", type="primary", use_container_width=True):
            st.switch_page("pages/explore.py")

    st.write("")

    # ── POPULAR DESTINATIONS ──────────────────────────────────────
    sec1, sec2 = st.columns([1, 1])
    with sec1:
        st.markdown("<p class='section-hdr'>🔥 Popular Destinations</p>", unsafe_allow_html=True)
    with sec2:
        if st.button("View All →", key="home_viewall_dest", use_container_width=False):
            st.switch_page("pages/explore.py")

    # Filter by search
    display_cities = cities_df.copy()
    if search_q:
        q = search_q.lower().strip()
        display_cities = display_cities[
            display_cities["city"].str.lower().str.contains(q, na=False) |
            display_cities["state"].str.lower().str.contains(q, na=False) |
            display_cities["description"].str.lower().str.contains(q, na=False)
        ]

    dest_cols = st.columns(5, gap="small")
    for idx, (_, row) in enumerate(display_cities.head(5).iterrows()):
        img = get_destination_photo(row["city"])
        img_html = render_card_image_html(img, row["city"], height_px=110, category_icon="🌍")
        with dest_cols[idx % 5]:
            st.markdown(textwrap.dedent(f"""
            <div class="dest-card">
                {img_html}
                <div class="dest-card-body">
                    <p class="dest-card-city">{row['city']}</p>
                    <p class="dest-card-state">{row['state']}, India</p>
                    <p class="dest-card-meta">Explore destination highlights</p>
                    <p class="dest-card-meta">📅 Best: {row.get('best_time','Oct–Mar')}</p>
                    <p class="dest-card-meta">💰 ₹{row.get('average_daily_budget',3500.0):,.0f}/day</p>
                </div>
            </div>
            """).strip(), unsafe_allow_html=True)
            if st.button("Explore", key=f"home_exp_{row['city']}_{idx}", use_container_width=True):
                st.session_state["explore_city"] = row["city"]
                st.switch_page("pages/explore.py")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ── HOTELS + RESTAURANTS IN CONTEXT CITY ─────────────────────
    hotels_col, rest_col = st.columns(2, gap="large")

    with hotels_col:
        st.markdown(f"<p class='section-hdr'>🏨 Top Hotels in {ctx_city}</p>", unsafe_allow_html=True)
        try:
            hotels_df = get_hotels(ctx_city)
        except Exception:
            hotels_df = pd.DataFrame()

        if hotels_df.empty:
            st.markdown("<p style='color:rgba(255,255,255,0.50);font-size:0.85rem;'>No hotels found for this destination.</p>", unsafe_allow_html=True)
        else:
            for _, h in hotels_df.head(3).iterrows():
                place_info = resolve_place_photo(
                    h.get("name", ""), city_name=ctx_city, category=f"hotel {h.get('category', '')}",
                    latitude=h.get("latitude"), longitude=h.get("longitude")
                )
                img = place_info.get("photo_url") or get_hotel_photo(
                    h.get("name", ""), city_name=ctx_city, category=h.get("category", "hotel"),
                    latitude=h.get("latitude"), longitude=h.get("longitude")
                )
                google_rating = place_info.get("rating") if place_info.get("place_verified") else None
                rating_text = f"⭐ {google_rating} · Google Maps" if google_rating is not None else "Google rating unavailable"
                maps_url = get_google_maps_search_url(f"{h['name']}, {ctx_city}", h.get("latitude"), h.get("longitude"))
                img_html = render_card_image_html(img, h['name'], height_px=95, border_radius="10px",
                                                  attribution=place_info.get("attribution"), category_icon="🏨")
                st.markdown(textwrap.dedent(f"""
                <div class="place-card" style="display:flex;gap:12px;align-items:center;">
                    <div style="width:110px;flex-shrink:0;">
                        {img_html}
                    </div>
                    <div class="place-card-body" style="padding:4px 0;">
                        <p class="place-card-name" style="margin:0 0 4px;">{h['name']}</p>
                        <p class="place-card-sub" style="margin:0 0 4px;">📍 {h.get('address', ctx_city)} · {h.get('category','Mid-range')}</p>
                        <p class="place-card-meta" style="margin:0;">{rating_text} &nbsp;·&nbsp; ₹{h.get('price_per_night',3000):,.0f}/night</p>
                    </div>
                </div>
                """).strip(), unsafe_allow_html=True)
                hc1, hc2 = st.columns(2, gap="small")
                with hc1:
                    if st.button("View", key=f"home_hv_{h['name']}_{_}", use_container_width=True):
                        st.session_state["explore_city"] = ctx_city
                        st.switch_page("pages/explore.py")
                with hc2:
                    st.link_button("📍 Maps", maps_url, use_container_width=True)

    with rest_col:
        st.markdown(f"<p class='section-hdr'>🍽️ Popular Restaurants in {ctx_city}</p>", unsafe_allow_html=True)
        try:
            rest_df = get_restaurants(ctx_city)
        except Exception:
            rest_df = pd.DataFrame()

        if rest_df.empty:
            st.markdown("<p style='color:rgba(255,255,255,0.50);font-size:0.85rem;'>No restaurants found for this destination.</p>", unsafe_allow_html=True)
        else:
            for _, r in rest_df.head(3).iterrows():
                place_info = resolve_place_photo(
                    r.get("name", ""), city_name=ctx_city, category=f"restaurant {r.get('cuisine', '')}",
                    latitude=r.get("latitude"), longitude=r.get("longitude")
                )
                img = place_info.get("photo_url") or get_restaurant_photo(
                    r.get("name", ""), city_name=ctx_city, cuisine=r.get("cuisine", ""),
                    latitude=r.get("latitude"), longitude=r.get("longitude")
                )
                google_rating = place_info.get("rating") if place_info.get("place_verified") else None
                rating_text = f"⭐ {google_rating} · Google Maps" if google_rating is not None else "Google rating unavailable"
                maps_url = get_google_maps_search_url(f"{r['name']}, {ctx_city}", r.get("latitude"), r.get("longitude"))
                img_html = render_card_image_html(img, r['name'], height_px=95, border_radius="10px",
                                                  attribution=place_info.get("attribution"), category_icon="🍽️")
                st.markdown(textwrap.dedent(f"""
                <div class="place-card" style="display:flex;gap:12px;align-items:center;">
                    <div style="width:110px;flex-shrink:0;">
                        {img_html}
                    </div>
                    <div class="place-card-body" style="padding:4px 0;">
                        <p class="place-card-name" style="margin:0 0 4px;">{r['name']}</p>
                        <p class="place-card-sub" style="margin:0 0 4px;">🍱 {r.get('cuisine','Multi')} · {r.get('food_type','Multi')}</p>
                        <p class="place-card-meta" style="margin:0;">{rating_text} &nbsp;·&nbsp; {r.get('price_range','Budget')}</p>
                    </div>
                </div>
                """).strip(), unsafe_allow_html=True)
                rc1, rc2 = st.columns(2, gap="small")
                with rc1:
                    if st.button("View", key=f"home_rv_{r['name']}_{_}", use_container_width=True):
                        st.session_state["explore_city"] = ctx_city
                        st.switch_page("pages/explore.py")
                with rc2:
                    st.link_button("📍 Maps", maps_url, use_container_width=True)

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ── WHY SMARTTRAVEL AI ────────────────────────────────────────
    st.markdown("<p class='section-hdr'>✨ Why SmartTravel AI?</p>", unsafe_allow_html=True)
    st.write("")
    why_c1, why_c2 = st.columns(2, gap="medium")
    whys = [
        ("🧠", "AI-Powered Itineraries", "Personalised day-by-day plans"),
        ("🌤️", "Real-Time Weather", "Live forecasts & travel alerts"),
        ("📍", "Google Maps Integration", "Directions, routes & navigation"),
        ("✅", "Verified Data", "Real places, reviews & photos"),
        ("🛡️", "Safety First", "Highway blackspot & zone alerts"),
        ("💰", "Smart Budgeting", "Cost breakdowns & optimisation"),
    ]
    for i, (icon, title, sub) in enumerate(whys):
        col = why_c1 if i % 2 == 0 else why_c2
        with col:
            st.markdown(textwrap.dedent(f"""
            <div class="why-item">
                <div class="why-icon-wrap">{icon}</div>
                <div>
                    <p class="why-title">{title}</p>
                    <p class="why-sub">{sub}</p>
                </div>
            </div>
            """).strip(), unsafe_allow_html=True)

# ── RIGHT PANEL ───────────────────────────────────────────────────
with right_col:
    st.markdown("""<p class="rp-title" style="color:rgba(255,255,255,0.60);font-size:0.80rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">📅 Upcoming Trip</p>""", unsafe_allow_html=True)
    with st.container(border=True):
        if active_trip:
            trip_img = get_destination_image(active_trip["destination"])
            st.image(trip_img, use_container_width=True)
            st.markdown(textwrap.dedent(f"""
            <p style="font-family:Outfit,sans-serif;font-weight:800;font-size:0.95rem;color:#FFFFFF;margin:6px 0 2px;">{active_trip['destination']} Getaway</p>
            <p style="font-size:0.78rem;color:rgba(255,255,255,0.55);margin:0;">{active_trip.get('days',3)} Days Trip</p>
            """).strip(), unsafe_allow_html=True)
            if st.button("📅 Upcoming", key="home_rp_trip", use_container_width=True, type="primary"):
                st.switch_page("pages/plan_trip.py")
        elif user_trips:
            t = user_trips[0]
            trip_img = get_destination_image(t["destination"])
            st.image(trip_img, use_container_width=True)
            st.markdown(textwrap.dedent(f"""
            <p style="font-family:Outfit,sans-serif;font-weight:800;font-size:0.95rem;color:#FFFFFF;margin:6px 0 2px;">{t['name']}</p>
            <p style="font-size:0.78rem;color:rgba(255,255,255,0.55);margin:0;">{t['duration_days']} Days · {t['destination']}</p>
            """).strip(), unsafe_allow_html=True)
            if st.button("📅 View Trip", key="home_rp_mytrip", use_container_width=True, type="primary"):
                st.switch_page("pages/my_trips.py")
        else:
            st.markdown(textwrap.dedent("""
            <div style="text-align:center;padding:20px 0;">
                <span style="font-size:2rem;">✈️</span>
                <p style="color:rgba(255,255,255,0.55);font-size:0.82rem;margin-top:8px;">No trips planned yet.</p>
            </div>
            """).strip(), unsafe_allow_html=True)
            if st.button("🧭 Plan Your First Trip", key="home_rp_plan", use_container_width=True, type="primary"):
                st.switch_page("pages/plan_trip.py")

    st.write("")

    # Quick Actions
    st.markdown("""<p class="rp-title" style="color:rgba(255,255,255,0.60);font-size:0.80rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">⚡ Quick Actions</p>""", unsafe_allow_html=True)
    with st.container(border=True):
        if st.button("🧭 Plan a New Trip", use_container_width=True, type="primary", key="home_qa_plan"):
            st.switch_page("pages/plan_trip.py")
        if st.button("🌍 Explore Destinations", use_container_width=True, key="home_qa_exp"):
            st.switch_page("pages/explore.py")
        if st.button("🎒 My Saved Trips", use_container_width=True, key="home_qa_mytrips"):
            st.switch_page("pages/my_trips.py")
        if st.button("💬 Ask AI Assistant", use_container_width=True, key="home_qa_ai"):
            st.switch_page("pages/assistant.py")
        if st.button("🛡️ Safety Advisor", use_container_width=True, key="home_qa_safety"):
            st.switch_page("pages/safety.py")

    st.write("")

    # Travel Tip
    st.markdown("""<p class="rp-title" style="color:rgba(255,255,255,0.60);font-size:0.80rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">💡 Travel Tip of the Day</p>""", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(textwrap.dedent("""
        <p style="font-size:0.85rem;color:rgba(255,255,255,0.80);margin:0 0 6px;font-weight:600;">Early Bird Advantage</p>
        <p style="font-size:0.78rem;color:rgba(255,255,255,0.55);line-height:1.5;margin:0;">
            Visit popular attractions between 8:30 AM and 10:00 AM to avoid crowds and enjoy the best lighting for photos.
        </p>
        """).strip(), unsafe_allow_html=True)
