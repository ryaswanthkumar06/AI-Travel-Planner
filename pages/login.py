import streamlit as st
import textwrap
from services.auth_service import authenticate_user, register_user

# Load stylesheet
with open("assets/style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Page-scoped styles (dedented to prevent markdown code-block parsing)
st.markdown(textwrap.dedent("""
<style>
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }

.login-hero-box {
    background: linear-gradient(145deg, #101828 0%, #1A3350 45%, #2F6690 80%, #4A88B8 100%);
    border-radius: 18px;
    padding: 42px 36px;
    min-height: 580px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
}
.login-hero-box::before {
    content: '';
    position: absolute; inset: 0;
    background:
      radial-gradient(ellipse at 80% 10%, rgba(255,138,101,0.25) 0%, transparent 55%),
      radial-gradient(ellipse at 10% 90%, rgba(63,124,172,0.30) 0%, transparent 55%);
    pointer-events: none;
}
.hero-brand-name {
    font-family: 'Outfit', sans-serif;
    font-size: 2rem; font-weight: 900;
    color: #FFFFFF !important;
    margin: 0 0 4px 0; position: relative; z-index: 1;
}
.hero-brand-tag {
    color: rgba(255,255,255,0.60) !important;
    font-size: 0.88rem; margin: 0 0 36px 0;
    position: relative; z-index: 1;
}
.hero-h2 {
    font-family: 'Outfit', sans-serif !important;
    font-size: 2.35rem !important; font-weight: 900 !important;
    color: #FFFFFF !important;
    line-height: 1.15 !important;
    margin: 0 0 14px 0;
    position: relative; z-index: 1;
}
.hero-accent { color: #FF8A65 !important; }
.hero-desc {
    color: rgba(255,255,255,0.72) !important;
    font-size: 0.95rem; line-height: 1.6;
    max-width: 360px; margin: 0 0 28px 0;
    position: relative; z-index: 1;
}
.feat-row {
    display: flex; align-items: center; gap: 12px;
    padding: 9px 0;
    border-top: 1px solid rgba(255,255,255,0.10);
    position: relative; z-index: 1;
}
.feat-row:first-child { border-top: none; }
.feat-icon {
    width: 34px; height: 34px; flex-shrink: 0;
    background: rgba(255,138,101,0.22);
    border-radius: 8px;
    display: flex; align-items: center;
    justify-content: center; font-size: 0.95rem;
}
.feat-title {
    display: block;
    color: #FFFFFF !important;
    font-size: 0.85rem; font-weight: 700;
}
.feat-sub {
    color: rgba(255,255,255,0.55) !important;
    font-size: 0.76rem;
}
.login-card-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.55rem; font-weight: 800;
    color: #17243D !important; margin: 0 0 4px 0;
}
.login-card-sub {
    color: #52667A !important;
    font-size: 0.88rem; margin: 0 0 20px 0;
}
</style>
"""), unsafe_allow_html=True)

# ── Two-column layout ─────────────────────────────────────────────
col_hero, col_form = st.columns([1.05, 1], gap="medium")

with col_hero:
    # Dedented HTML string to prevent markdown indented code-block parser
    hero_html = textwrap.dedent("""
    <div class="login-hero-box">
    <div>
    <p class="hero-brand-name">🌍 SmartTravel AI</p>
    <p class="hero-brand-tag">Your intelligent Indian travel companion</p>
    <h2 class="hero-h2">
    Plan Smarter.<br>
    <span class="hero-accent">Travel Safer.</span><br>
    Explore Better.
    </h2>
    <p class="hero-desc">
    AI-powered itineraries, real-time weather, verified safety data,
    and Google Maps navigation for 30+ iconic Indian destinations.
    </p>
    </div>
    <div>
    <div class="feat-row">
    <div class="feat-icon">🧭</div>
    <div>
    <span class="feat-title">AI Itinerary Builder</span>
    <span class="feat-sub">Personalised day-by-day trip plans</span>
    </div>
    </div>
    <div class="feat-row">
    <div class="feat-icon">🛡️</div>
    <div>
    <span class="feat-title">Highway Safety Intelligence</span>
    <span class="feat-sub">Blackspot &amp; risk zone alerts</span>
    </div>
    </div>
    <div class="feat-row">
    <div class="feat-icon">🌤️</div>
    <div>
    <span class="feat-title">Live Weather Forecasts</span>
    <span class="feat-sub">Real-time conditions at your destination</span>
    </div>
    </div>
    <div class="feat-row">
    <div class="feat-icon">📍</div>
    <div>
    <span class="feat-title">Google Maps Integration</span>
    <span class="feat-sub">Navigate every stop on your itinerary</span>
    </div>
    </div>
    </div>
    </div>
    """)
    st.markdown(hero_html, unsafe_allow_html=True)

with col_form:
    with st.container(border=True):
        tab_in, tab_up = st.tabs(["🔑 Sign In", "📝 Create Account"])

        # ── SIGN IN ───────────────────────────────────────────
        with tab_in:
            st.markdown(textwrap.dedent("""
            <p class="login-card-title">Welcome back 👋</p>
            <p class="login-card-sub">Sign in to access your itineraries and saved trips.</p>
            """), unsafe_allow_html=True)

            with st.form("signin_form", clear_on_submit=False):
                email_in = st.text_input(
                    "Email Address", placeholder="you@example.com", key="signin_email"
                )
                pass_in = st.text_input(
                    "Password", type="password", placeholder="Your password", key="signin_pass"
                )
                st.write("")
                submit_in = st.form_submit_button(
                    "🚀 Sign In", use_container_width=True, type="primary"
                )

            if submit_in:
                if not email_in or not pass_in:
                    st.error("⚠️ Please enter both email and password.")
                else:
                    user = authenticate_user(email_in.strip(), pass_in)
                    if user:
                        st.session_state["authenticated"] = True
                        st.session_state["user"] = user
                        st.success(f"✅ Welcome back, **{user['name']}**!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid email or password. Please try again.")

            st.markdown(textwrap.dedent("""
            <div style="text-align:center;margin-top:14px;">
                <span style="font-size:0.82rem;color:#52667A;">
                    No account? Switch to the <strong>Create Account</strong> tab above →
                </span>
            </div>
            """), unsafe_allow_html=True)

        # ── CREATE ACCOUNT ────────────────────────────────────
        with tab_up:
            st.markdown(textwrap.dedent("""
            <p class="login-card-title">Join SmartTravel AI 🌍</p>
            <p class="login-card-sub">Create a free account to start planning your dream trips.</p>
            """), unsafe_allow_html=True)

            with st.form("signup_form", clear_on_submit=False):
                name_up  = st.text_input("Full Name", placeholder="Your full name", key="signup_name")
                email_up = st.text_input(
                    "Email Address", placeholder="you@example.com", key="signup_email"
                )
                pass_up  = st.text_input(
                    "Password (min. 6 chars)", type="password",
                    placeholder="Choose a strong password", key="signup_pass"
                )
                pass_up2 = st.text_input(
                    "Confirm Password", type="password",
                    placeholder="Repeat your password", key="signup_pass2"
                )
                st.write("")
                submit_up = st.form_submit_button(
                    "🎉 Create Account", use_container_width=True, type="primary"
                )

            if submit_up:
                if not name_up or not email_up or not pass_up or not pass_up2:
                    st.error("⚠️ Please fill in all fields.")
                elif pass_up != pass_up2:
                    st.error("❌ Passwords do not match.")
                elif len(pass_up) < 6:
                    st.error("❌ Password must be at least 6 characters.")
                else:
                    try:
                        register_user(name_up.strip(), email_up.strip(), pass_up)
                        user = authenticate_user(email_up.strip(), pass_up)
                        if user:
                            st.session_state["authenticated"] = True
                            st.session_state["user"] = user
                            st.success(f"🎉 Account created! Welcome, **{name_up}**!")
                            st.rerun()
                        else:
                            st.success("✅ Account created! Please sign in.")
                    except ValueError as ve:
                        st.error(f"❌ {ve}")
                    except Exception as e:
                        st.error(f"❌ Registration error: {e}")
