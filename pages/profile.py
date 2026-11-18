import streamlit as st
import logging
import textwrap
from database.db_manager import get_user_preferences, save_user_preferences, get_user_trips

logger = logging.getLogger(__name__)

with open("assets/style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def normalize_interests(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(i).strip() for i in value if str(i).strip()]
    if isinstance(value, str):
        return [i.strip() for i in value.split(",") if i.strip()]
    return []

if "user" not in st.session_state or not st.session_state.get("user"):
    st.warning("⚠️ Please login to view your profile.")
    st.stop()

user    = st.session_state["user"]
user_id = user.get("id", 1)

try:
    prefs = get_user_preferences(user_id) or {}
except Exception as e:
    logger.error(f"Failed to load preferences for user {user_id}: {e}")
    prefs = {}

BUDGET_OPTS = [
    "Budget (₹500–₹2,000/day)",
    "Moderate (₹2,000–₹5,000/day)",
    "Premium (₹5,000–₹15,000/day)",
    "Luxury (₹15,000+/day)",
]
STYLE_OPTS  = ["Relaxed","Balanced","Adventure","Luxury","Backpacking","Family","Romantic","Cultural"]
FOOD_OPTS   = ["Any","Vegetarian","Non-Vegetarian","Vegan","Jain","South Indian","North Indian","Seafood","Street Food"]
STAY_OPTS   = ["Budget Hotels","Mid-range Hotels","Luxury Palaces","Resorts","Hostels","Homestays"]
TRANS_OPTS  = ["Walking","Public Transit","Bus","Train","Taxi","Rental Car","Personal Vehicle"]
INT_OPTS    = ["Historical Places","Nature","Adventure","Beaches","Shopping","Spiritual",
               "Photography","Wildlife","Nightlife","Food","Architecture","Museums"]

def safe_idx(opts, val, default=0):
    try:
        return opts.index(val) if val in opts else default
    except Exception:
        return default

# ── Header ────────────────────────────────────────────────────────────
st.markdown("<h2 style='color:#FFFFFF;'>👤 My Profile</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:rgba(255,255,255,0.60);'>Manage your account details and travel preferences.</p>", unsafe_allow_html=True)
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────────────────────────────
avatar_col, pref_col = st.columns([1, 2.5], gap="large")

with avatar_col:
    name_parts   = user.get("name", "Traveler").split()
    initials     = "".join(p[0].upper() for p in name_parts[:2])
    
    st.markdown(textwrap.dedent(f"""
    <div style="background:rgba(16,24,43,0.78);border:1px solid rgba(255,255,255,0.14);
                border-radius:18px;padding:28px 20px 22px;backdrop-filter:blur(16px);text-align:center;">
        <div style="width:80px;height:80px;
                    background:linear-gradient(135deg,#FF7A59 0%,#3F6F9F 100%);
                    border-radius:50%;display:flex;align-items:center;
                    justify-content:center;font-size:1.8rem;font-weight:900;
                    color:#FFFFFF;margin:0 auto 14px;letter-spacing:1px;">
            {initials}
        </div>
        <p style="font-family:Outfit,sans-serif;font-weight:900;font-size:1.15rem;
                   color:#FFFFFF;margin:0 0 4px;">{user.get('name','Traveler')}</p>
        <p style="font-size:0.82rem;color:rgba(255,255,255,0.52);margin:0 0 14px;">
            ✉️ {user.get('email','')}
        </p>
        <span style="background:rgba(255,122,89,0.18);border:1px solid rgba(255,122,89,0.35);
                     border-radius:999px;padding:4px 14px;font-size:0.74rem;
                     font-weight:700;color:#FF9A7A;">
            ✈️ Explorer
        </span>
    </div>
    """).strip(), unsafe_allow_html=True)

    st.write("")

    with st.container(border=True):
        st.markdown(textwrap.dedent("""
        <p style="color:rgba(255,255,255,0.50);font-size:0.72rem;font-weight:700;
                   text-transform:uppercase;letter-spacing:0.10em;margin:0 0 12px;">
            📊 Quick Stats
        </p>
        """).strip(), unsafe_allow_html=True)
        try:
            all_trips = get_user_trips(user_id)
            num_trips    = len(all_trips)
            unique_cities = len(set(t["destination"] for t in all_trips))
            total_budget  = sum(float(t["budget"]) for t in all_trips)
        except Exception as e:
            logger.error(f"Error loading trips: {e}")
            num_trips = unique_cities = 0
            total_budget = 0.0

        for val, lbl in [
            (num_trips,       "Trips Planned"),
            (unique_cities,   "Destinations"),
            (f"₹{total_budget:,.0f}", "Total Budget"),
        ]:
            st.markdown(textwrap.dedent(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                         padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.08);">
                <span style="font-size:0.80rem;color:rgba(255,255,255,0.55);">{lbl}</span>
                <span style="font-size:0.88rem;font-weight:800;color:#FFFFFF;">{val}</span>
            </div>
            """).strip(), unsafe_allow_html=True)

with pref_col:
    st.markdown("<h3 style='color:#FFFFFF;border-left:3px solid #FF7A59;padding-left:12px;'>🎒 Travel Preferences</h3>", unsafe_allow_html=True)
    st.write("")

    try:
        with st.form("profile_prefs_form"):
            fc1, fc2 = st.columns(2, gap="medium")

            with fc1:
                new_budget = st.selectbox(
                    "💰 Budget Level",
                    BUDGET_OPTS,
                    index=safe_idx(BUDGET_OPTS, prefs.get("budget_preference"), 1)
                )
                new_style = st.selectbox(
                    "⛰️ Travel Style",
                    STYLE_OPTS,
                    index=safe_idx(STYLE_OPTS, prefs.get("travel_style"), 1)
                )
                new_food = st.selectbox(
                    "🍽️ Food Preference",
                    FOOD_OPTS,
                    index=safe_idx(FOOD_OPTS, prefs.get("food_preference"), 0)
                )

            with fc2:
                new_stay = st.selectbox(
                    "🏨 Accommodation",
                    STAY_OPTS,
                    index=safe_idx(STAY_OPTS, prefs.get("accommodation_preference"), 1)
                )
                new_trans = st.selectbox(
                    "🚗 Transportation",
                    TRANS_OPTS,
                    index=safe_idx(TRANS_OPTS, prefs.get("transportation_preference"), 1)
                )

            cur_interests = normalize_interests(prefs.get("interests", ""))
            valid_interests = [i for i in cur_interests if i in INT_OPTS]
            if not valid_interests:
                valid_interests = ["Historical Places"]

            new_interests = st.multiselect(
                "❤️ Travel Interests",
                INT_OPTS,
                default=valid_interests
            )

            st.write("")
            save_btn = st.form_submit_button(
                "💾 Save Preferences", use_container_width=True, type="primary"
            )

        if save_btn:
            try:
                save_user_preferences(
                    user_id=user_id,
                    budget_preference=new_budget,
                    travel_style=new_style,
                    food_preference=new_food,
                    accommodation_preference=new_stay,
                    transportation_preference=new_trans,
                    interests=",".join(new_interests)
                )
                if "trip_inputs" in st.session_state:
                    st.session_state["trip_inputs"]["budget_level"]   = new_budget
                    st.session_state["trip_inputs"]["travel_style"]   = new_style
                    st.session_state["trip_inputs"]["styles"]         = [new_style]
                    st.session_state["trip_inputs"]["food_pref"]      = [new_food]
                    st.session_state["trip_inputs"]["accommodation"]  = new_stay
                    st.session_state["trip_inputs"]["transport"]      = new_trans
                    st.session_state["trip_inputs"]["interests"]      = new_interests
                st.success("✅ Preferences saved! Your next trip plan will use these settings.")
            except Exception as e:
                logger.error(f"Failed to save preferences for user {user_id}: {e}")
                st.error("⚠️ Your preferences could not be saved. Please try again.")

    except Exception as e:
        logger.error(f"Profile preferences form error: {e}")
        st.error("⚠️ Your travel preferences could not be loaded. Please refresh the page.")

    st.write("")
    st.markdown("<h3 style='color:#FFFFFF;border-left:3px solid #FF7A59;padding-left:12px;'>🔐 Security</h3>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(textwrap.dedent("""
        <p style="font-size:0.85rem;color:rgba(255,255,255,0.65);margin:0;">
            To change your password, please contact support or use the account recovery flow.
        </p>
        """).strip(), unsafe_allow_html=True)
        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("🌍 Explore Destinations", use_container_width=True):
                st.switch_page("pages/explore.py")
        with sc2:
            if st.button("🧭 Plan a Trip", use_container_width=True, type="primary"):
                st.switch_page("pages/plan_trip.py")
