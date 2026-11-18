import streamlit as st
import json
import textwrap
from services.data_service import get_cities, get_attractions, get_restaurants, get_hotels, get_accident_zones
from services.weather_service import get_live_weather
from services.safety_service import get_safety_report

with open("assets/style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(textwrap.dedent("""
<style>
.orb-wrap {
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    padding:24px 12px 16px;
    background:rgba(16,24,43,0.65);
    border:1px solid rgba(255,122,89,0.22);
    border-radius:18px; backdrop-filter:blur(16px);
    margin-bottom:18px;
}
.orb-container { position:relative; width:110px; height:110px; margin-bottom:14px; animation:orb-float 3s ease-in-out infinite; }
.orb-core {
    width:72px; height:72px;
    background:linear-gradient(135deg,#3F6F9F 0%,#FF7A59 100%);
    border-radius:50%; position:absolute; top:50%; left:50%;
    transform:translate(-50%,-50%);
    animation:orb-glow 2.5s ease-in-out infinite;
    display:flex; align-items:center; justify-content:center;
    font-size:1.7rem; z-index:2;
}
.orb-ring1 { position:absolute; inset:0; border-radius:50%; border:2px solid rgba(63,111,159,0.45); border-top-color:rgba(63,111,159,0.90); animation:ring-spin 4s linear infinite; }
.orb-ring2 { position:absolute; inset:10px; border-radius:50%; border:2px dashed rgba(255,122,89,0.40); animation:ring-spin2 6s linear infinite; }
.orb-title { font-family:'Outfit',sans-serif; font-weight:800; font-size:1.1rem; color:#FFFFFF !important; text-align:center; margin:0 0 3px; }
.orb-sub   { font-size:0.78rem; color:rgba(255,255,255,0.50) !important; text-align:center; margin:0; }
.weather-result-card {
    background:rgba(16,24,43,0.75);
    border:1px solid rgba(63,111,159,0.40);
    border-radius:14px; padding:16px 18px;
    margin-top:10px; backdrop-filter:blur(14px);
}
</style>
""").strip(), unsafe_allow_html=True)

cities_df       = get_cities()
all_cities_list = list(cities_df["city"].unique())
active_trip     = st.session_state.get("active_trip")

st.markdown("<h2 style='color:#FFFFFF;'>💬 SmartTravel AI Assistant</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:rgba(255,255,255,0.60);'>Your intelligent travel advisor — destinations, weather, hotels, safety, dining, and personalised itineraries.</p>", unsafe_allow_html=True)
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

orb_col, chat_col = st.columns([1, 2.5], gap="large")

with orb_col:
    st.markdown(textwrap.dedent("""
    <div class="orb-wrap">
        <div class="orb-container">
            <div class="orb-ring1"></div>
            <div class="orb-ring2"></div>
            <div class="orb-core">🌍</div>
        </div>
        <p class="orb-title">SmartTravel AI</p>
        <p class="orb-sub">Travel assistant · Gemini when configured</p>
    </div>
    """).strip(), unsafe_allow_html=True)

    if active_trip:
        st.success(f"📍 Context: **{active_trip['destination']}**")
    else:
        st.info("💡 Ask about any Indian city.")

    st.markdown("<p style='color:rgba(255,255,255,0.70);font-weight:600;font-size:0.84rem;'>Quick Questions:</p>", unsafe_allow_html=True)
    quick_prompts = [
        "🌤️ Weather in Goa?",
        "🏨 Hotels in Jaipur?",
        "🍽️ Restaurants in Mumbai?",
        "🛡️ Safety in Hyderabad?",
        "💰 Budget for Manali?",
        "🏛️ Best places in Delhi?",
    ]
    for qp in quick_prompts:
        if st.button(qp, use_container_width=True, key=f"qp_{qp}"):
            st.session_state["chat_prefill"] = qp

with chat_col:
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [{"role": "assistant", "content":
            "👋 **Namaste!** I'm your **SmartTravel AI Assistant**.\n\n"
            "Ask me about 30+ Indian destinations — attractions, weather, hotels, dining, safety, budget, or your active trip. 🌍"}]

    prefill = st.session_state.pop("chat_prefill", None)
    if prefill:
        st.session_state["chat_history"].append({"role": "user", "content": prefill})

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask anything — e.g. 'Best places in Jaipur for 3 days?'") or prefill

    if user_input and (not prefill or user_input != prefill):
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state["chat_history"].append({"role": "user", "content": user_input})

    if user_input:
        q_low = user_input.lower()
        def find_city_in_text(text_value):
            lowered = str(text_value or "").lower()
            for city_name in sorted(all_cities_list, key=len, reverse=True):
                if city_name.lower() in lowered:
                    return city_name
            return None

        # Prefer the city named in this question, then active-trip context, then
        # the most recent city mentioned in the ongoing conversation.
        target_city = find_city_in_text(user_input)
        if not target_city and active_trip:
            target_city = active_trip.get("destination")
        if not target_city:
            for previous_message in reversed(st.session_state["chat_history"][:-1]):
                target_city = find_city_in_text(previous_message.get("content", ""))
                if target_city:
                    break

        # ── Try Gemini API first (uses configurable GEMINI_MODEL and secure header)
        from services.llm_service import query_gemini_assistant, is_gemini_configured

        city_attractions = [dict(r) for _, r in get_attractions(target_city).iterrows()] if target_city else []
        city_hotels      = [dict(r) for _, r in get_hotels(target_city).iterrows()] if target_city else []
        city_restaurants = [dict(r) for _, r in get_restaurants(target_city).iterrows()] if target_city else []
        city_zones       = [dict(r) for _, r in get_accident_zones(target_city).iterrows()] if target_city else []

        previous_messages = st.session_state["chat_history"][:-1][-8:]
        conversation_context = "\n".join(
            f"{'User' if item.get('role') == 'user' else 'Assistant'}: {item.get('content', '')}"
            for item in previous_messages
            if item.get("role") in ("user", "assistant")
        )
        resp_text = None
        gemini_state = "not_configured"
        if is_gemini_configured():
            with st.spinner("🌍 Asking Gemini…"):
                prompt = f"""You are SmartTravel AI, an accurate and conversational India travel assistant.
Use the supplied local catalogue as context, but distinguish catalogue estimates from live verified information.
Do not invent Google ratings, review counts, hotel availability, opening status, prices, or safety guarantees.
If the catalogue does not contain the requested information, say so and provide useful general guidance.
Continue the conversation naturally and resolve follow-up references using the conversation history.

Conversation so far:
{conversation_context or 'No earlier messages.'}

Destination context: {target_city or 'Not specified'}
Attractions in the local catalogue: {[a['name']+' ('+a['category']+')' for a in city_attractions[:8]]}
Hotels in the local catalogue: {[h['name']+' ('+h['category']+', estimated ₹'+str(h.get('price_per_night',''))+'/night)' for h in city_hotels[:5]]}
Restaurants in the local catalogue: {[r['name']+' ('+r['cuisine']+')' for r in city_restaurants[:5]]}
Safety catalogue entries: {[z['location_name']+' - '+z['risk_level'] for z in city_zones[:3]]}
Active trip context: {json.dumps(active_trip.get('itinerary', [])[:2], ensure_ascii=False) if active_trip else 'None'}

Latest user question: {user_input}

Respond helpfully with clear sections or bullets where useful. Ask a short clarification when essential details are missing."""
                resp_text = query_gemini_assistant(prompt)
                gemini_state = "success" if resp_text else "request_failed"

        # ── Local catalogue fallback (clearly identified; not a Gemini answer)
        if not resp_text:
            prefix = "🤖 **SmartTravel AI** *(Local catalogue fallback — not a Gemini response)*\n\n"

            if not target_city:
                resp_text = prefix + "Which Indian destination are you asking about? Mention a city so I can check the local travel catalogue."
            elif any(k in q_low for k in ["weather","temperature","rain","forecast","climate","hot","cold"]):
                city_row = cities_df[cities_df["city"].str.lower() == target_city.lower()]
                if not city_row.empty:
                    lat = float(city_row.iloc[0]["latitude"])
                    lng = float(city_row.iloc[0]["longitude"])
                    try:
                        w = get_live_weather(lat, lng)
                        resp_text = prefix + (
                            f"☀️ **Live Weather — {target_city}**\n\n"
                            f"| Metric | Value |\n|--------|-------|\n"
                            f"| 🌡️ Temperature | **{w.get('temp',26)}°C** (Feels like {w.get('feels_like',27)}°C) |\n"
                            f"| ☁️ Condition | {w.get('condition','Pleasant')} |\n"
                            f"| 💧 Humidity | {w.get('humidity',60)}% |\n"
                            f"| 💨 Wind | {w.get('wind',10)} km/h |\n"
                            f"| 📅 Best Season | {city_row.iloc[0].get('best_time','Oct–Mar')} |\n\n"
                            f"**💡 Travel Tip:** {('Great weather for outdoor sightseeing! ☀️' if w.get('temp',26) < 32 else 'Hot conditions — plan outdoor visits for early morning or evening. 🕐')}"
                        )
                    except Exception:
                        resp_text = prefix + f"Weather service temporarily unavailable for {target_city}. Please try again."
                else:
                    resp_text = prefix + f"I couldn't find weather data for {target_city}."

            elif any(k in q_low for k in ["hotel","stay","lodge","resort","accommodation"]):
                if city_hotels:
                    rows = "\n".join(f"- **{h['name']}** — *{h['category']}* · estimated ₹{h.get('price_per_night','N/A'):,}/night\n  > 📍 {h.get('address',target_city)}" for h in city_hotels[:5])
                    resp_text = prefix + f"🏨 **Catalogue hotel entries in {target_city}:**\n\n{rows}\n\nThese are local catalogue entries, not live availability or verified Google Maps ratings."
                else:
                    resp_text = prefix + f"No hotel data found for {target_city} in our database."

            elif any(k in q_low for k in ["restaurant","food","eat","dining","cuisine"]):
                if city_restaurants:
                    rows = "\n".join(f"- **{r['name']}** — *{r['cuisine']}* · {r.get('price_range','Budget')}" for r in city_restaurants[:5])
                    resp_text = prefix + f"🍽️ **Restaurant entries in the {target_city} catalogue:**\n\n{rows}\n\nThese are catalogue entries, not live Google Maps ratings or confirmed business availability."
                else:
                    resp_text = prefix + f"No restaurant data found for {target_city}."

            elif any(k in q_low for k in ["safety","accident","hazard","safe","risk","dangerous"]):
                s_rep = get_safety_report(target_city)
                alerts_txt = "\n".join(
                    f"- ⚠️ **{a['location_name']}** ({a['road_name']}) — *{a['risk_level']} Risk*\n  > 🛡️ {a['recommended_action']}"
                    for a in s_rep.get("alerts",[])[:4]
                ) or "✅ No active high-risk alerts on main tourist routes."
                resp_text = prefix + (
                    f"🛡️ **Safety Report — {target_city}**\n"
                    f"- **Status:** `{s_rep.get('status','Safe')}`\n"
                    f"- **Advisory:** {s_rep.get('message','Verified safe for travel.')}\n\n"
                    f"**⚠️ Monitored Corridors:**\n{alerts_txt}"
                )

            elif any(k in q_low for k in ["budget","cost","price","cheap","expensive","money"]):
                if active_trip and active_trip.get("destination","").lower() == target_city.lower():
                    b = active_trip.get("budget_breakdown",{})
                    resp_text = prefix + (
                        f"💰 **Budget Breakdown — {target_city} Trip:**\n\n"
                        f"| Category | Cost |\n|----------|------|\n"
                        f"| 🏨 Hotel | ₹{b.get('hotel_cost',0):,.0f} |\n"
                        f"| 🍽️ Food | ₹{b.get('food_cost',0):,.0f} |\n"
                        f"| 🚗 Transport | ₹{b.get('transport_cost',0):,.0f} |\n"
                        f"| 🎟️ Activities | ₹{b.get('attractions_cost',0):,.0f} |\n"
                        f"| **Total** | **₹{b.get('total_cost',0):,.0f}** |\n"
                        f"| Remaining | ₹{b.get('remaining',0):,.0f} |"
                    )
                else:
                    resp_text = prefix + (
                        f"💰 **Daily Budget Guide — {target_city}:**\n\n"
                        f"| Type | Per Day |\n|------|------|\n"
                        f"| 🎒 Budget | ₹1,500–₹2,500 |\n"
                        f"| ⚖️ Mid-Range | ₹3,000–₹6,000 |\n"
                        f"| 🏰 Luxury | ₹8,000–₹20,000+ |"
                    )

            else:
                if city_attractions:
                    rows = "\n".join(
                        f"- **{a['name']}** — *{a['category']}*\n"
                        f"  > ⏱️ {a.get('visit_duration_minutes',90)} min | 🎟️ Catalogue entry fee: ₹{a.get('price',0):,}"
                        for a in city_attractions[:6]
                    )
                    resp_text = prefix + (
                        f"🏛️ **Top Attractions in {target_city}:**\n\n{rows}\n\n"
                        "💡 *Ask me about: weather, hotels, dining, safety, budget, or use **Plan Trip** for a full itinerary.*"
                    )
                else:
                    resp_text = prefix + f"I have limited data for {target_city}. Try searching for a major Indian destination like Goa, Jaipur, or Delhi."

        with st.chat_message("assistant"):
            st.markdown(resp_text)
        if gemini_state == "not_configured":
            st.warning("Gemini API key is not configured. This answer came from the local catalogue, not the AI model.")
        elif gemini_state == "request_failed":
            st.warning("Gemini did not return a response. This answer came from the local catalogue. Check the server logs for the API error, key permissions, quota, model name, or network connection.")
        st.session_state["chat_history"].append({"role": "assistant", "content": resp_text})

    st.write("")
    if len(st.session_state.get("chat_history", [])) > 2:
        if st.button("🗑️ Clear Conversation", use_container_width=False):
            st.session_state["chat_history"] = [st.session_state["chat_history"][0]]
            st.rerun()
