import streamlit as st
import os
import requests
import json
from services.data_service import get_cities, get_attractions, get_hotels, get_restaurants
from services.weather_service import get_live_weather
from services.safety_service import get_safety_report

def render_floating_assistant():
    """
    Renders a floating AI Assistant widget with an animated glowing 3D orb
    accessible at the bottom right corner of all main pages.
    """
    # Container for floating assistant session state
    if "floating_chat_open" not in st.session_state:
        st.session_state["floating_chat_open"] = False
        
    if "floating_messages" not in st.session_state:
        st.session_state["floating_messages"] = [
            {"role": "assistant", "content": "👋 Hi! I am your **SmartTravel AI Companion**. Ask me about weather, top spots, or route safety for 30+ destinations!"}
        ]
        
    # CSS for 3D animated glowing orb and chat modal window
    st.markdown("""
    <style>
    .floating-assistant-btn {
        position: fixed;
        bottom: 25px;
        right: 25px;
        z-index: 99999;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 10px;
        background: linear-gradient(135deg, #10243E 0%, #28658F 100%);
        color: white;
        padding: 10px 18px;
        border-radius: 30px;
        box-shadow: 0 10px 25px rgba(40, 101, 143, 0.4);
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .floating-assistant-btn:hover {
        transform: translateY(-3px) scale(1.03);
        box-shadow: 0 14px 30px rgba(40, 101, 143, 0.6);
    }
    .ai-orb-sphere {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #38BDF8, #28658F, #0F172A);
        box-shadow: 0 0 12px #38BDF8, inset 0 0 8px #E0F2FE;
        animation: orbPulse 2.5s infinite ease-in-out;
    }
    @keyframes orbPulse {
        0% { transform: scale(0.95); box-shadow: 0 0 8px #38BDF8; }
        50% { transform: scale(1.15); box-shadow: 0 0 18px #38BDF8, 0 0 25px #0EA5E9; }
        100% { transform: scale(0.95); box-shadow: 0 0 8px #38BDF8; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar quick trigger or expander helper
    with st.sidebar:
        st.markdown("<hr style='margin: 15px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        with st.expander("🤖 Ask SmartTravel Assistant", expanded=False):
            q_input = st.text_input("Ask a question:", placeholder="e.g. Weather in Munnar?", key="sb_ai_q")
            if st.button("Ask Assistant", key="sb_ai_btn", use_container_width=True):
                if q_input:
                    # Quick answer
                    target_city = "Hyderabad"
                    for c in ["Goa", "Munnar", "Jaipur", "Delhi", "Mumbai", "Varanasi", "Kochi", "Bangalore"]:
                        if c.lower() in q_input.lower():
                            target_city = c
                            break
                    if "weather" in q_input.lower():
                        w = get_live_weather(17.385, 78.486)
                        st.info(f"🌤️ **Weather in {target_city}:** {w.get('temp', 26)}°C, {w.get('condition', 'Pleasant')}")
                    elif "safe" in q_input.lower() or "safety" in q_input.lower():
                        s = get_safety_report(target_city)
                        st.info(f"🛡️ **Safety Status:** {s.get('status', 'Safe')} — {s.get('message', '')}")
                    else:
                        att_df = get_attractions(target_city)
                        top_spots = ", ".join(att_df["name"].tolist()[:3]) if not att_df.empty else "Charminar, Golconda Fort"
                        st.success(f"🏛️ **Top Spots in {target_city}:** {top_spots}")
