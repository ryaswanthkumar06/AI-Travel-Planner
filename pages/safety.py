import streamlit as st
import pandas as pd
import textwrap
from services.data_service import get_accident_zones
from services.destination_image_service import (
    get_destination_image,
    get_destination_photo,
    render_card_image_html
)
from services.maps_service import get_google_maps_search_url

with open("assets/style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("<h2 style='color:#FFFFFF;'>🛡️ Travel Safety Dashboard</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:rgba(255,255,255,0.60);'>Verified highway blackspot, accident corridor, and risk zone data for Indian travel routes.</p>", unsafe_allow_html=True)
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

st.markdown(textwrap.dedent("""
<div style="background:rgba(63,111,159,0.18);border:1px solid rgba(63,111,159,0.35);
            border-radius:12px;padding:12px 16px;margin-bottom:20px;display:flex;gap:10px;align-items:flex-start;">
    <span style="font-size:1.1rem;flex-shrink:0;">ℹ️</span>
    <p style="margin:0;font-size:0.84rem;color:rgba(255,255,255,0.80);">
        <strong style="color:#FFFFFF;">Reference Safety Data:</strong>
        Based on published road audits and accident blackspot studies. Always verify local authority guidance and exercise caution while travelling.
    </p>
</div>
""").strip(), unsafe_allow_html=True)

try:
    safety_df = pd.read_csv("data/accident_zones.csv")
except Exception:
    safety_df = pd.DataFrame(columns=["id","location_name","road_name","city","state",
                                       "latitude","longitude","risk_level","accident_count",
                                       "risk_type","recommended_action","source","data_date"])

total_zones = len(safety_df)
high_risk   = len(safety_df[safety_df["risk_level"].str.lower() == "high"])   if not safety_df.empty else 0
med_risk    = len(safety_df[safety_df["risk_level"].str.lower() == "medium"]) if not safety_df.empty else 0
low_risk    = len(safety_df[safety_df["risk_level"].str.lower() == "low"])    if not safety_df.empty else 0

# Stats
s1, s2, s3, s4 = st.columns(4, gap="medium")
for col, val, lbl in [
    (s1, total_zones, "Total Zones"),
    (s2, high_risk,   "🚨 High Risk"),
    (s3, med_risk,    "⚠️ Medium Risk"),
    (s4, low_risk,    "✅ Low Risk"),
]:
    with col:
        st.metric(lbl, val)

st.write("")

# Filter
fc1, fc2 = st.columns([3, 1])
with fc1:
    search_q = st.text_input(" ", placeholder="🔍  Search corridors, roads, cities…", label_visibility="collapsed", key="safety_search")
with fc2:
    risk_filter = st.selectbox(" ", ["All Levels", "High", "Medium", "Low"], label_visibility="collapsed", key="safety_risk")

filtered = safety_df.copy()
if search_q:
    q = search_q.lower()
    filtered = filtered[
        filtered["location_name"].str.lower().str.contains(q, na=False) |
        filtered["road_name"].str.lower().str.contains(q, na=False) |
        filtered["city"].str.lower().str.contains(q, na=False)
    ]
if risk_filter != "All Levels":
    filtered = filtered[filtered["risk_level"].str.lower() == risk_filter.lower()]

st.markdown(f"<p style='color:rgba(255,255,255,0.55);font-size:0.82rem;margin-bottom:12px;'>Showing {len(filtered)} of {total_zones} monitored corridors</p>", unsafe_allow_html=True)

for idx, row in filtered.iterrows():
    risk_lv  = str(row["risk_level"]).strip().lower()
    risk_cls = "risk-high" if risk_lv == "high" else "risk-medium" if risk_lv == "medium" else "risk-low"
    risk_lbl = ("🚨 High Risk" if risk_lv == "high" else
                "⚠️ Medium Risk" if risk_lv == "medium" else "✅ Low Risk")

    col_l, col_r = st.columns([3, 1], gap="medium")
    with col_l:
        st.markdown(textwrap.dedent(f"""
        <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.12);
                    border-radius:14px;padding:16px 18px;backdrop-filter:blur(12px);margin-bottom:4px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                <p style="font-family:Outfit,sans-serif;font-weight:800;font-size:0.98rem;
                           color:#FFFFFF;margin:0;">⚠️ {row['location_name']}</p>
                <span class="{risk_cls}">{risk_lbl}</span>
            </div>
            <p style="font-size:0.82rem;color:rgba(255,255,255,0.65);margin:0 0 4px;">
                🛣️ <strong style="color:#FFFFFF;">{row['road_name']}</strong> &nbsp;|&nbsp;
                📍 {row['city']}, {row.get('state','India')}
            </p>
            <p style="font-size:0.82rem;color:rgba(255,255,255,0.65);margin:0 0 4px;">
                💥 <strong style="color:#FFFFFF;">Hazard:</strong> {row['risk_type']} &nbsp;|&nbsp;
                📈 <strong style="color:#FFFFFF;">Incidents:</strong> {row['accident_count']}
            </p>
            <p style="font-size:0.82rem;color:rgba(255,255,255,0.65);margin:0 0 8px;">
                🛡️ <strong style="color:#FFFFFF;">Action:</strong> <em style="color:rgba(255,255,255,0.80);">{row['recommended_action']}</em>
            </p>
            <p style="font-size:0.72rem;color:rgba(255,255,255,0.35);margin:0;">
                📅 {row.get('data_date','2024-Q3')} &nbsp;|&nbsp; 🔗 {row['source']}
            </p>
        </div>
        """).strip(), unsafe_allow_html=True)
    with col_r:
        img = get_destination_photo(row["city"])
        st.markdown(render_card_image_html(img, row["city"], height_px=95, border_radius="10px", category_icon="🛡️"), unsafe_allow_html=True)
        map_url = get_google_maps_search_url(
            f"{row['location_name']}, {row['city']}",
            row.get("latitude"), row.get("longitude")
        )
        st.link_button("📍 Google Maps", map_url, use_container_width=True)
    st.write("")

if filtered.empty:
    st.info("No safety zones matching your search.")
