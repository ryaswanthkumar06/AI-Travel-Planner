import streamlit as st
import datetime
import time

with open("assets/style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("<h2 style='color:#FFFFFF;'>🌦️ Weather Forecast</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:rgba(255,255,255,0.60);'>Live meteorological summaries using the Open-Meteo API.</p>", unsafe_allow_html=True)
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

ICON_MAP = {
    "Clear":"☀️","Sunny":"☀️","Cloudy":"☁️","Partly Cloudy":"⛅",
    "Rain":"🌧️","Drizzle":"🌦️","Thunderstorm":"⛈️","Fog":"🌫️",
    "Haze":"🌫️","Mist":"🌫️","Snow":"❄️"
}

if not st.session_state.get("active_trip"):
    with st.container(border=True):
        st.markdown("""
        <div style="text-align:center;padding:36px 20px;">
            <p style="font-size:3rem;margin-bottom:10px;">🌤️</p>
            <p style="font-family:Outfit,sans-serif;font-weight:800;font-size:1.15rem;color:#FFFFFF;margin-bottom:8px;">
                No Active Trip
            </p>
            <p style="color:rgba(255,255,255,0.55);font-size:0.88rem;max-width:380px;margin:0 auto;">
                Destination weather forecasts and dynamic itinerary adjustments will appear here
                after generating a trip via <strong style="color:#FF9A7A;">Plan Trip</strong>
                or loading a saved trip from <strong style="color:#FF9A7A;">My Trips</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)
    st.write("")
    if st.button("🧭 Plan a Trip Now", type="primary"):
        st.switch_page("pages/plan_trip.py")
else:
    trip        = st.session_state["active_trip"]
    destination = trip["destination"]
    hotel       = trip.get("selected_hotel", {})
    curr        = trip.get("weather_summary", {})

    # Destination header
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;">
        <span style="font-size:1.6rem;">{ICON_MAP.get(curr.get('condition',''),'🌤️')}</span>
        <div>
            <p style="font-family:Outfit,sans-serif;font-weight:800;font-size:1.2rem;color:#FFFFFF;margin:0;">{destination}</p>
            <p style="font-size:0.80rem;color:rgba(255,255,255,0.50);margin:0;">
                📍 {hotel.get('latitude','—')}, {hotel.get('longitude','—')}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Current conditions
    st.markdown("<h3 style='color:#FFFFFF;'>🌡️ Current Conditions</h3>", unsafe_allow_html=True)
    cw1, cw2, cw3, cw4, cw5 = st.columns(5, gap="medium")
    for col, val, lbl in [
        (cw1, f"{ICON_MAP.get(curr.get('condition',''),'🌤️')} {curr.get('temp','—')}°C", "Temperature"),
        (cw2, f"{curr.get('feels_like','—')}°C", "Feels Like"),
        (cw3, curr.get("condition","—"), "Condition"),
        (cw4, f"{curr.get('humidity','—')}%", "Humidity"),
        (cw5, f"{curr.get('wind','—')} km/h", "Wind Speed"),
    ]:
        with col:
            st.metric(lbl, val)

    # Safety overlay
    st.write("")
    safety_text = "Route Clear ✅" if trip.get("safety_status","Safe") == "Safe" else f"⚠️ {trip.get('safety_status','')}"
    with st.container(border=True):
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
            <div style="flex:1;min-width:0;">
                <p style="color:rgba(255,255,255,0.55);font-size:0.75rem;text-transform:uppercase;letter-spacing:0.07em;margin:0 0 2px;">Route Safety</p>
                <p style="font-weight:700;color:#FFFFFF;font-size:1rem;margin:0;">{safety_text}</p>
            </div>
            <div style="flex:1;min-width:0;">
                <p style="color:rgba(255,255,255,0.55);font-size:0.75rem;text-transform:uppercase;letter-spacing:0.07em;margin:0 0 2px;">Data Source</p>
                <p style="font-weight:700;color:#FFFFFF;font-size:0.88rem;margin:0;">Open-Meteo API</p>
            </div>
            <div style="flex:1;min-width:0;">
                <p style="color:rgba(255,255,255,0.55);font-size:0.75rem;text-transform:uppercase;letter-spacing:0.07em;margin:0 0 2px;">Fetched At</p>
                <p style="font-weight:700;color:#FFFFFF;font-size:0.88rem;margin:0;">{datetime.datetime.fromtimestamp(curr.get('fetched_time', time.time())).strftime('%H:%M, %d %b %Y')} {'(Cached)' if curr.get('cached') else '(Live)'}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 7-day forecast
    if trip.get("weather_forecast"):
        st.write("")
        st.markdown("<h3 style='color:#FFFFFF;'>📅 Forecast Timeline</h3>", unsafe_allow_html=True)
        months_abbr = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        fc_list     = trip["weather_forecast"]
        fc_cols     = st.columns(min(7, len(fc_list)), gap="small")

        for idx, fc in enumerate(fc_list[:7]):
            if idx >= len(fc_cols):
                break
            parts = fc.get("date","").split("-")
            try:
                date_str = f"{months_abbr[int(parts[1])]} {parts[2]}"
            except Exception:
                date_str = fc.get("date", f"Day {idx+1}")

            with fc_cols[idx]:
                with st.container(border=True):
                    st.markdown(f"""
                    <div style="text-align:center;">
                        <p style="font-size:0.72rem;font-weight:800;color:rgba(255,255,255,0.55);margin:0;">{date_str}</p>
                        <p style="font-size:2rem;margin:5px 0;">{fc.get('icon','🌤️')}</p>
                        <p style="font-size:0.90rem;font-weight:700;color:#FFFFFF;margin:0;">{fc.get('max_temp','?')}° / {fc.get('min_temp','?')}°</p>
                        <p style="font-size:0.72rem;color:rgba(100,180,240,0.80);margin:2px 0 0;">💧 {fc.get('rain_probability',0)}%</p>
                        <p style="font-size:0.70rem;color:rgba(255,255,255,0.42);margin:2px 0 0;">{fc.get('condition','')[:12]}</p>
                    </div>
                    """, unsafe_allow_html=True)

    st.write("")
    st.markdown("""
    <div style="background:rgba(63,111,159,0.14);border:1px solid rgba(63,111,159,0.30);
                border-radius:12px;padding:12px 16px;margin-top:8px;">
        <p style="font-size:0.82rem;color:rgba(255,255,255,0.68);margin:0;">
            ℹ️ <strong style="color:#FFFFFF;">Open-Meteo Integration:</strong>
            Conditions fetched live from the latitude/longitude center of your destination.
            Weather-aware planning automatically swaps outdoor events with indoor attractions
            when precipitation probability exceeds 50%.
        </p>
    </div>
    """, unsafe_allow_html=True)
