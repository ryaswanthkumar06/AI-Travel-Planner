import streamlit as st
import os
import textwrap
from dotenv import load_dotenv

load_dotenv()

# 1. Page Config (MUST be called first)
st.set_page_config(
    page_title="SmartTravel AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject CSS System Stylesheet globally
def load_custom_css(css_filepath):
    if os.path.exists(css_filepath):
        with open(css_filepath, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Styling file '{css_filepath}' not found.")

load_custom_css("assets/style.css")

# 3. Sidebar Branding — Dark sunset theme
st.sidebar.markdown(textwrap.dedent("""
<style>
/* Extra sidebar polish */
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}
.brand-wrap {
    padding: 22px 16px 18px;
    border-bottom: 1px solid rgba(255,122,89,0.14);
    margin-bottom: 8px;
}
.brand-logo {
    font-size: 2.4rem;
    display: block;
    text-align: center;
    margin-bottom: 6px;
    animation: orb-float 3s ease-in-out infinite;
}
.brand-name {
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.28rem !important;
    font-weight: 900 !important;
    color: #FFFFFF !important;
    text-align: center;
    margin: 0 0 3px;
    letter-spacing: 0.3px;
}
.brand-tag {
    font-size: 0.72rem !important;
    color: rgba(255,255,255,0.42) !important;
    text-align: center;
    margin: 0;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.sidebar-section-label {
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    color: rgba(255,122,89,0.70) !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    padding: 14px 16px 5px;
    margin: 0;
}
</style>
<div class="brand-wrap">
    <span class="brand-logo">🌍</span>
    <p class="brand-name">SmartTravel AI</p>
    <p class="brand-tag">Plan Smarter · Travel Safer</p>
</div>
""").strip(), unsafe_allow_html=True)

# Additional CSS to hide Material icon text in sidebar
st.markdown(textwrap.dedent("""
<style>
/* Hide Material icon text nodes that appear as raw strings in Streamlit sidebar */
section[data-testid="stSidebar"] span[class*="material"],
section[data-testid="stSidebar"] .material-icons,
section[data-testid="stSidebar"] .material-symbols-outlined,
section[data-testid="stSidebar"] .material-symbols-rounded,
[data-testid="collapsedControl"] span.material-symbols-rounded,
[data-testid="collapsedControl"] span.material-icons {
    font-size: 0 !important;
    visibility: hidden !important;
    line-height: 0 !important;
    overflow: hidden !important;
    width: 0 !important;
    height: 0 !important;
}
/* Fix sidebar collapse toggle button */
[data-testid="collapsedControl"] {
    background: rgba(15,22,35,0.95) !important;
    border: 1px solid rgba(255,122,89,0.25) !important;
}
/* Sidebar nav section labels (TRAVEL PLANNER, TOOLS, ACCOUNT) */
section[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"],
section[data-testid="stSidebar"] [data-testid="stSidebarNavSectionLabel"] p,
section[data-testid="stSidebar"] [data-testid="stSidebarNavSectionLabel"] span {
    color: rgba(255,122,89,0.72) !important;
    font-size: 0.68rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
}
/* Nav item hover */
section[data-testid="stSidebar"] a:hover {
    background: rgba(255,122,89,0.14) !important;
    border-radius: 8px !important;
}
/* Active page highlight */
section[data-testid="stSidebar"] a[aria-current="page"] {
    background: linear-gradient(90deg, rgba(255,122,89,0.28), rgba(255,107,107,0.12)) !important;
    border-left: 3px solid #FF7A59 !important;
    border-radius: 0 8px 8px 0 !important;
    font-weight: 700 !important;
}
</style>
""").strip(), unsafe_allow_html=True)

# 4. Check Authentication & Define Page Lists
is_auth = st.session_state.get("authenticated", False)

if not is_auth:
    login_page = st.Page("pages/login.py", title="Sign In / Register", icon="🔑", default=True)
    pg = st.navigation([login_page])
else:
    home_page       = st.Page("pages/home.py",        title="Home",         icon="🏠", default=True)
    dashboard_page  = st.Page("pages/dashboard.py",   title="Dashboard",    icon="📈")
    explore_page    = st.Page("pages/explore.py",     title="Explore",      icon="🌍")
    plan_page       = st.Page("pages/plan_trip.py",   title="Plan Trip",    icon="🧭")
    my_trips_page   = st.Page("pages/my_trips.py",    title="My Trips",     icon="🎒")
    safety_page     = st.Page("pages/safety.py",      title="Safety",       icon="🛡️")
    assistant_page  = st.Page("pages/assistant.py",   title="AI Assistant", icon="💬")
    profile_page    = st.Page("pages/profile.py",     title="Profile",      icon="👤")
    logout_page     = st.Page("pages/logout.py",      title="Logout",       icon="🚪")

    pg = st.navigation({
        "TRAVEL PLANNER": [home_page, dashboard_page, explore_page, plan_page, my_trips_page],
        "INTELLIGENT TOOLS": [safety_page, assistant_page],
        "ACCOUNT": [profile_page, logout_page]
    })

pg.run()
