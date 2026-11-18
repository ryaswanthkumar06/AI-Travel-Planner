import streamlit as st
import pandas as pd
import textwrap
from services.data_service import get_cities, get_attractions, get_hotels, get_restaurants, get_accident_zones
from services.destination_image_service import (
    get_destination_image,
    get_attraction_image,
    get_hotel_image,
    get_restaurant_image,
    get_destination_photo,
    get_attraction_photo,
    get_hotel_photo,
    get_restaurant_photo,
    get_place_photos,
    render_card_image_html,
    resolve_place_photo
)
from services.weather_service import get_live_weather
from services.safety_service import get_safety_report
from services.maps_service import get_google_maps_search_url, get_google_maps_directions_url

with open("assets/style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(textwrap.dedent("""
<style>
.exp-hero {
    position: relative; overflow: hidden;
    border-radius: 16px; margin-bottom: 18px;
    height: 220px;
}
.exp-hero img {
    width: 100%; height: 100%; object-fit: cover;
    display: block; filter: brightness(0.55);
}
.exp-hero-text {
    position: absolute; bottom: 0; left: 0; right: 0;
    padding: 20px 24px;
    background: linear-gradient(0deg, rgba(16,24,43,0.90) 0%, transparent 100%);
}
.exp-hero-city {
    font-family: 'Outfit', sans-serif; font-weight: 900;
    font-size: 1.8rem; color: #FFFFFF !important; margin: 0 0 2px;
}
.exp-hero-state { font-size: 0.88rem; color: rgba(255,255,255,0.65) !important; margin: 0; }
.gallery-thumb {
    width: 100%; height: 85px; object-fit: cover; border-radius: 8px;
    transition: transform 0.2s;
}
.gallery-thumb:hover { transform: scale(1.03); }
</style>
""").strip(), unsafe_allow_html=True)

active_city = st.session_state.get("explore_city", "")
cities_df   = get_cities()

# ─────────────────────────────────────────────────────────────────
# DESTINATION DETAIL VIEW
# ─────────────────────────────────────────────────────────────────
if active_city:
    matches   = cities_df[cities_df["city"].str.lower() == active_city.lower().strip()]
    city_data = dict(matches.iloc[0]) if not matches.empty else None

    if not city_data:
        st.error(f"Destination '{active_city}' not found in verified database.")
        if st.button("⬅️ Back to Explore"):
            st.session_state["explore_city"] = ""
            st.rerun()
    else:
        if st.button("⬅️ Back to Explore", key="exp_back"):
            st.session_state["explore_city"] = ""
            st.rerun()

        st.write("")
        hero_img = get_destination_photo(city_data["city"])
        
        # Hero banner
        st.markdown(textwrap.dedent(f"""
        <div class="exp-hero">
            <img src="{hero_img}" alt="{city_data['city']}"
                 onerror="this.style.background='linear-gradient(135deg,#17243D,#FF7A59)';this.style.display='block';">
            <div class="exp-hero-text">
                <p class="exp-hero-city">{city_data['city']}</p>
                <p class="exp-hero-state">📍 {city_data['state']}, India</p>
            </div>
        </div>
        """).strip(), unsafe_allow_html=True)

        # Photo Gallery Preview
        dest_photos = get_place_photos(city_data["city"], count=4)
        if len(dest_photos) > 1:
            g_cols = st.columns(len(dest_photos))
            for gi, g_url in enumerate(dest_photos):
                with g_cols[gi]:
                    st.markdown(textwrap.dedent(f"""
                    <img class="gallery-thumb" src="{g_url}" alt="Gallery photo {gi+1}"
                         onerror="this.style.display='none';" />
                    """).strip(), unsafe_allow_html=True)
            st.write("")

        # Action CTAs
        ac1, ac2, ac3 = st.columns(3, gap="medium")
        with ac1:
            if st.button(f"🧭 Plan Trip to {city_data['city']}", type="primary", use_container_width=True):
                st.session_state.setdefault("trip_inputs", {})["destination"] = city_data["city"]
                st.session_state["plan_step"] = 1
                st.switch_page("pages/plan_trip.py")
        with ac2:
            maps_url = get_google_maps_search_url(f"{city_data['city']}, {city_data['state']}, India",
                                                   city_data.get("latitude"), city_data.get("longitude"))
            st.link_button("📍 Open in Google Maps", maps_url, use_container_width=True)
        with ac3:
            if st.button("💬 Ask AI About This City", use_container_width=True):
                st.session_state["chat_prefill"] = f"Tell me about {city_data['city']}"
                st.switch_page("pages/assistant.py")

        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

        # Key metrics + weather
        w = {}
        try:
            w = get_live_weather(float(city_data["latitude"]), float(city_data["longitude"]))
        except Exception:
            pass

        m1, m2, m3, m4, m5 = st.columns(5, gap="medium")
        icon_map = {"Clear":"☀️","Sunny":"☀️","Cloudy":"☁️","Partly Cloudy":"⛅",
                    "Rain":"🌧️","Drizzle":"🌦️","Thunderstorm":"⛈️","Fog":"🌫️","Haze":"🌫️","Mist":"🌫️"}
        for col, val, lbl in [
            (m1, city_data.get("best_time", "Oct–Mar"), "📅 Best Time"),
            (m2, f"₹{city_data.get('average_daily_budget', 3500):,.0f}/day", "💰 Est. Budget"),
            (m3, f"☀️ {w.get('temp','—')}°C" if w else "☀️ 26°C", "🌡️ Temp"),
            (m4, w.get("condition","Pleasant") if w else "Pleasant", "☁️ Weather"),
            (m5, city_data.get("state","India"), "📍 State"),
        ]:
            with col:
                st.metric(lbl, val)

        st.write("")
        st.markdown(f"<p style='color:rgba(255,255,255,0.75);font-size:0.95rem;line-height:1.6;'>{city_data.get('description','')}</p>", unsafe_allow_html=True)

        # Tabs: Attractions, Hotels, Restaurants, Safety, Weather
        tab_attr, tab_hotels, tab_rest, tab_safety, tab_weather = st.tabs([
            "🏛️ Attractions", "🏨 Hotels", "🍽️ Restaurants", "🛡️ Safety", "🌤️ Weather"
        ])

        with tab_attr:
            st.markdown("<h3 style='color:#FFFFFF;'>🏛️ Top Attractions</h3>", unsafe_allow_html=True)
            try:
                attr_df = get_attractions(city_data["city"])
            except Exception:
                attr_df = pd.DataFrame()
            if attr_df.empty:
                st.info("No attraction data available for this destination.")
            else:
                attr_cols = st.columns(3, gap="medium")
                for i, (_, a) in enumerate(attr_df.iterrows()):
                    place_info = resolve_place_photo(
                        a.get("name", ""), city_name=city_data["city"], category=a.get("category", "attraction"),
                        latitude=a.get("latitude"), longitude=a.get("longitude")
                    )
                    img = place_info.get("photo_url") or get_attraction_photo(
                        a.get("name", ""), city_name=city_data["city"], category=a.get("category", ""),
                        latitude=a.get("latitude"), longitude=a.get("longitude")
                    )
                    rating_text = (f"⭐ {place_info['rating']} · Google Maps"
                                   if place_info.get("place_verified") and place_info.get("rating") is not None
                                   else "Google rating unavailable")
                    maps_url = get_google_maps_search_url(f"{a['name']}, {city_data['city']}", a.get("latitude"), a.get("longitude"))
                    img_html = render_card_image_html(img, a['name'], height_px=140, attribution=place_info.get("attribution"), category_icon="🏛️")
                    with attr_cols[i % 3]:
                        st.markdown(textwrap.dedent(f"""
                        <div class="dest-card" style="margin-bottom:12px;">
                            {img_html}
                            <div class="dest-card-body">
                                <p class="dest-card-city" style="font-size:0.90rem;">{a['name']}</p>
                                <p class="dest-card-state">{a.get('category','Attraction')}</p>
                                <div style="display:flex;gap:6px;align-items:center;margin-bottom:6px;">
                                    <span class="dest-rating">{rating_text}</span>
                                    <span style="font-size:0.72rem;color:rgba(255,255,255,0.45);">⏱️ {a.get('visit_duration_minutes',90)} min</span>
                                </div>
                                <p class="dest-card-meta">🎟️ Entry: ₹{a.get('price',0):,}</p>
                            </div>
                        </div>
                        """).strip(), unsafe_allow_html=True)
                        st.link_button("📍 Maps", maps_url, use_container_width=True)

        with tab_hotels:
            st.markdown("<h3 style='color:#FFFFFF;'>🏨 Hotel Catalogue</h3>", unsafe_allow_html=True)
            st.caption("These are sample catalogue records, not verified live hotel listings. Google ratings appear only after a confident place match.")
            try:
                hotels_df = get_hotels(city_data["city"])
            except Exception:
                hotels_df = pd.DataFrame()
            if hotels_df.empty:
                st.info("No hotel data available.")
            else:
                for _, h in hotels_df.iterrows():
                    place_info = resolve_place_photo(
                        h.get("name", ""), city_name=city_data["city"], category=f"hotel {h.get('category', '')}",
                        latitude=h.get("latitude"), longitude=h.get("longitude")
                    )
                    img = place_info.get("photo_url") or get_hotel_photo(
                        h.get("name", ""), city_name=city_data["city"], category=h.get("category", "Mid-range"),
                        latitude=h.get("latitude"), longitude=h.get("longitude")
                    )
                    rating_text = (f"⭐ {place_info['rating']} · Google Maps"
                                   if place_info.get("place_verified") and place_info.get("rating") is not None
                                   else "Google rating unavailable")
                    maps_url = get_google_maps_search_url(f"{h['name']}, {city_data['city']}", h.get("latitude"), h.get("longitude"))
                    img_html = render_card_image_html(img, h['name'], height_px=110, border_radius="10px",
                                                      attribution=place_info.get("attribution"), category_icon="🏨")
                    hc_l, hc_r = st.columns([3, 1], gap="medium")
                    with hc_l:
                        st.markdown(textwrap.dedent(f"""
                        <div class="place-card" style="margin-bottom:0;display:flex;gap:14px;align-items:center;">
                            <div style="width:130px;flex-shrink:0;">
                                {img_html}
                            </div>
                            <div class="place-card-body" style="padding:4px 0;">
                                <p class="place-card-name" style="margin:0 0 4px;">{h['name']}</p>
                                <p class="place-card-sub" style="margin:0 0 4px;">📍 {h.get('address', city_data['city'])} · <span class="dest-rating">{rating_text}</span></p>
                                <p class="place-card-meta" style="margin:0 0 4px;">🏷️ {h.get('category','Standard')} &nbsp;·&nbsp; 💰 ₹{h.get('price_per_night',3000):,.0f}/night</p>
                                <p class="place-card-meta" style="margin:0;">🛌 {str(h.get('amenities','')).replace(';',' · ')[:80]}</p>
                            </div>
                        </div>
                        """).strip(), unsafe_allow_html=True)
                    with hc_r:
                        st.write("")
                        st.link_button("📍 Maps", maps_url, use_container_width=True)
                        if st.button("Book", key=f"exp_book_{h['name']}", use_container_width=True):
                            st.session_state.setdefault("trip_inputs", {})["destination"] = city_data["city"]
                            st.switch_page("pages/plan_trip.py")
                    st.write("")

        with tab_rest:
            st.markdown("<h3 style='color:#FFFFFF;'>🍽️ Restaurant Catalogue</h3>", unsafe_allow_html=True)
            st.caption("These are sample catalogue records, not verified live restaurant listings. Google ratings appear only after a confident place match.")
            try:
                rest_df = get_restaurants(city_data["city"])
            except Exception:
                rest_df = pd.DataFrame()
            if rest_df.empty:
                st.info("No restaurant data available.")
            else:
                rc1, rc2 = st.columns(2, gap="medium")
                for i, (_, r) in enumerate(rest_df.iterrows()):
                    place_info = resolve_place_photo(
                        r.get("name", ""), city_name=city_data["city"], category=f"restaurant {r.get('cuisine', '')}",
                        latitude=r.get("latitude"), longitude=r.get("longitude")
                    )
                    img = place_info.get("photo_url") or get_restaurant_photo(
                        r.get("name", ""), city_name=city_data["city"], cuisine=r.get("cuisine", ""),
                        latitude=r.get("latitude"), longitude=r.get("longitude")
                    )
                    rating_text = (f"⭐ {place_info['rating']} · Google Maps"
                                   if place_info.get("place_verified") and place_info.get("rating") is not None
                                   else "Google rating unavailable")
                    maps_url = get_google_maps_search_url(f"{r['name']}, {city_data['city']}", r.get("latitude"), r.get("longitude"))
                    img_html = render_card_image_html(img, r['name'], height_px=100, border_radius="10px",
                                                      attribution=place_info.get("attribution"), category_icon="🍽️")
                    with (rc1 if i % 2 == 0 else rc2):
                        st.markdown(textwrap.dedent(f"""
                        <div class="place-card" style="margin-bottom:0;display:flex;gap:12px;align-items:center;">
                            <div style="width:110px;flex-shrink:0;">
                                {img_html}
                            </div>
                            <div class="place-card-body" style="padding:4px 0;">
                                <p class="place-card-name" style="margin:0 0 4px;">{r['name']}</p>
                                <p class="place-card-sub" style="margin:0 0 4px;">🍱 {r.get('cuisine','Multi')} · <span class="dest-rating">{rating_text}</span></p>
                                <p class="place-card-meta" style="margin:0;">{r.get('price_range','Budget')} · {r.get('food_type','Multi')}</p>
                            </div>
                        </div>
                        """).strip(), unsafe_allow_html=True)
                        st.link_button("📍 Maps", maps_url, use_container_width=True)
                        st.write("")

        with tab_safety:
            st.markdown("<h3 style='color:#FFFFFF;'>🛡️ Safety Overview</h3>", unsafe_allow_html=True)
            s_rep = get_safety_report(city_data["city"])
            status = s_rep.get("status","Safe")
            if status == "High Risk":
                st.error(f"🚨 **{status}** — {s_rep.get('message','')}")
            elif status == "Caution":
                st.warning(f"⚠️ **{status}** — {s_rep.get('message','')}")
            else:
                st.success(f"✅ **{status}** — {s_rep.get('message','No active blackspots on tourist routes.')}")

            if s_rep.get("alerts"):
                st.write("")
                for a in s_rep["alerts"][:5]:
                    risk_cls = "risk-high" if "high" in a["risk_level"].lower() else "risk-medium" if "medium" in a["risk_level"].lower() else "risk-low"
                    zone_url = get_google_maps_search_url(f"{a['location_name']}, {city_data['city']}", a.get("latitude"), a.get("longitude"))
                    col_l, col_r = st.columns([4, 1])
                    with col_l:
                        st.markdown(textwrap.dedent(f"""
                        <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);
                                    border-radius:12px;padding:12px 16px;margin-bottom:4px;backdrop-filter:blur(8px);">
                            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                                <span class="{risk_cls}">{'🚨 High' if 'high' in a['risk_level'].lower() else '⚠️ Medium' if 'medium' in a['risk_level'].lower() else '✅ Low'}</span>
                                <strong style="color:#FFFFFF;font-size:0.90rem;">{a['location_name']}</strong>
                            </div>
                            <p style="font-size:0.78rem;color:rgba(255,255,255,0.58);margin:0 0 3px;">🛣️ {a['road_name']} &nbsp;|&nbsp; ⚠️ {a['risk_type']}</p>
                            <p style="font-size:0.78rem;color:rgba(255,255,255,0.58);margin:0;">🛡️ {a['recommended_action']}</p>
                        </div>
                        """).strip(), unsafe_allow_html=True)
                    with col_r:
                        st.write("")
                        st.link_button("📍 Map", zone_url, use_container_width=True)
                    st.write("")

        with tab_weather:
            st.markdown("<h3 style='color:#FFFFFF;'>🌤️ Weather Conditions</h3>", unsafe_allow_html=True)
            if w:
                icon_w = icon_map.get(w.get("condition",""), "🌤️")
                ww1, ww2, ww3, ww4, ww5 = st.columns(5, gap="medium")
                for col, val, lbl in [
                    (ww1, f"{icon_w} {w.get('temp','—')}°C", "Temperature"),
                    (ww2, f"{w.get('feels_like','—')}°C", "Feels Like"),
                    (ww3, w.get("condition","—"), "Condition"),
                    (ww4, f"{w.get('humidity','—')}%", "Humidity"),
                    (ww5, f"{w.get('wind','—')} km/h", "Wind"),
                ]:
                    with col:
                        st.metric(lbl, val)

                if w.get("forecast"):
                    st.write("")
                    st.markdown("<p style='color:rgba(255,255,255,0.65);font-weight:600;margin-bottom:10px;'>📅 3-Day Forecast:</p>", unsafe_allow_html=True)
                    fc_cols = st.columns(min(3, len(w["forecast"])))
                    months_abbr = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                    for fi, fc in enumerate(w["forecast"][:3]):
                        parts = fc.get("date","").split("-")
                        try:
                            date_str = f"{months_abbr[int(parts[1])]} {parts[2]}"
                        except Exception:
                            date_str = fc.get("date","")
                        with fc_cols[fi]:
                            with st.container(border=True):
                                st.markdown(textwrap.dedent(f"""
                                <div style="text-align:center;">
                                    <p style="font-size:0.80rem;color:rgba(255,255,255,0.55);margin:0;">{date_str}</p>
                                    <p style="font-size:2rem;margin:4px 0;">{fc.get('icon','🌤️')}</p>
                                    <p style="font-weight:700;color:#FFFFFF;margin:0;">{fc.get('max_temp','?')}° / {fc.get('min_temp','?')}°</p>
                                    <p style="font-size:0.75rem;color:rgba(100,180,240,0.80);margin:2px 0 0;">💧 {fc.get('rain_probability',0)}%</p>
                                </div>
                                """).strip(), unsafe_allow_html=True)
            else:
                st.info("Weather data unavailable.")

# ─────────────────────────────────────────────────────────────────
# EXPLORE LIST VIEW (30+ Destinations)
# ─────────────────────────────────────────────────────────────────
else:
    st.markdown("<h2 style='color:#FFFFFF;'>🌍 Explore India</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.60);'>Discover verified destinations, attractions, dining, and safe routes tailored to you.</p>", unsafe_allow_html=True)
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # Filters
    f1, f2, f3, f4 = st.columns([3, 2, 2, 2], gap="medium")
    with f1:
        search_q = st.text_input(" ", placeholder="🔍  Search destinations…", label_visibility="collapsed", key="exp_search")
    with f2:
        states_list = ["All States"] + sorted(list(cities_df["state"].unique()))
        sel_state = st.selectbox(" ", states_list, label_visibility="collapsed", key="exp_state")
    with f3:
        styles_list = ["All Styles","Historical","Cultural","Nature","Beach","Spiritual","Adventure","Food"]
        sel_style = st.selectbox(" ", styles_list, label_visibility="collapsed", key="exp_style")
    with f4:
        sort_by = st.selectbox(" ", ["Popularity","Budget ↑","Budget ↓","Name A–Z"], label_visibility="collapsed", key="exp_sort")

    # Filter + sort
    filtered = cities_df.copy()
    if search_q:
        q = search_q.lower()
        filtered = filtered[
            filtered["city"].str.lower().str.contains(q, na=False) |
            filtered["state"].str.lower().str.contains(q, na=False) |
            filtered["description"].str.lower().str.contains(q, na=False)
        ]
    if sel_state != "All States":
        filtered = filtered[filtered["state"] == sel_state]
    if sel_style != "All Styles":
        filtered = filtered[filtered["travel_styles"].str.contains(sel_style, case=False, na=False)]
    if sort_by == "Budget ↑":
        filtered = filtered.sort_values("average_daily_budget", ascending=True)
    elif sort_by == "Budget ↓":
        filtered = filtered.sort_values("average_daily_budget", ascending=False)
    elif sort_by == "Name A–Z":
        filtered = filtered.sort_values("city", ascending=True)

    st.markdown(f"<p style='color:rgba(255,255,255,0.45);font-size:0.82rem;margin-bottom:14px;'>Showing <strong style='color:rgba(255,255,255,0.80);'>{len(filtered)}</strong> destinations</p>", unsafe_allow_html=True)

    if filtered.empty:
        st.warning("No destinations matching your criteria.")
    else:
        grid_cols = st.columns(3, gap="medium")
        for idx, (_, row) in enumerate(filtered.iterrows()):
            col = grid_cols[idx % 3]
            img = get_destination_photo(row["city"])
            maps_url = get_google_maps_search_url(f"{row['city']}, {row['state']}, India",
                                                  row.get("latitude"), row.get("longitude"))
            img_html = render_card_image_html(img, row["city"], height_px=160, category_icon="🌍")
            with col:
                st.markdown(textwrap.dedent(f"""
                <div class="dest-card">
                    {img_html}
                    <div class="dest-card-body">
                        <p class="dest-card-city">{row['city']}</p>
                        <p class="dest-card-state">{row['state']}, India</p>
                        <p class="dest-card-meta">Explore travel highlights</p>
                        <p class="dest-card-desc">{str(row.get('description',''))[:90]}…</p>
                        <p class="dest-card-meta">📅 Best: {row.get('best_time','Oct–Mar')}</p>
                        <p class="dest-card-meta">💰 ₹{row.get('average_daily_budget',3500.0):,.0f}/day</p>
                    </div>
                </div>
                """).strip(), unsafe_allow_html=True)
                btn_c1, btn_c2 = st.columns(2, gap="small")
                with btn_c1:
                    if st.button("View Details", key=f"exp_view_{row['city']}_{idx}", use_container_width=True):
                        st.session_state["explore_city"] = row["city"]
                        st.rerun()
                with btn_c2:
                    st.link_button("📍 Maps", maps_url, use_container_width=True)
