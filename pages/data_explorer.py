import streamlit as st
import pandas as pd
from services.data_service import (
    get_validation_report, 
    get_attractions, 
    get_restaurants, 
    get_hotels, 
    get_accident_zones, 
    get_city,
    get_cities
)

# Ensure user is authenticated
if "user" not in st.session_state or not st.session_state["user"]:
    st.warning("Please login to view data explorer.")
    st.stop()

st.markdown("## 📊 Data Quality & Travel Explorer")
st.markdown("Inspect local travel datasets, verify geocoordinates, and check data validation audits.")

st.markdown("<hr style='margin-top: 10px; margin-bottom: 25px; border-border-color: #E2ECF5;'>", unsafe_allow_html=True)

# Define datasets to inspect
datasets = [
    ("cities.csv", "cities", "Cities Registry"),
    ("attractions.csv", "attractions", "Tourist Attractions"),
    ("restaurants.csv", "restaurants", "Dining & Restaurants"),
    ("hotels.csv", "hotels", "Accommodations / Hotels"),
    ("accident_zones.csv", "accident_zones", "Road Accident Blackspots")
]

st.markdown("### 🔍 1. Data Quality & Validation Report")
st.markdown("This report runs validation audits on the raw CSV sheets, checking coordinates, timing formats, and duplicate keys.")

# Run reports and compile stats table
report_rows = []
all_errors = {}

for filename, dtype, label in datasets:
    report = get_validation_report(filename, dtype)
    metrics = report["metrics"]
    
    report_rows.append({
        "Dataset": label,
        "Filename": filename,
        "Total Rows": metrics["total"],
        "Valid Rows": metrics["valid"],
        "Invalid Rows": metrics["invalid"],
        "Missing Coords": metrics["missing_coordinates"],
        "Missing Prices": metrics["missing_prices"],
        "Missing Timings": metrics["missing_hours"],
        "Missing Images": metrics["missing_images"],
        "Duplicates": metrics["duplicates"]
    })
    
    if report["errors"]:
        all_errors[label] = report["errors"]

# Display summary table
report_df = pd.DataFrame(report_rows)
st.dataframe(report_df, use_container_width=True, hide_index=True)

# Collapsible error logs
if all_errors:
    with st.expander("⚠️ View Validation Warning Logs"):
        for dataset_label, errors in all_errors.items():
            st.markdown(f"**{dataset_label} Issues:**")
            for err in errors:
                st.markdown(f"- `{err}`")
else:
    st.success("✅ Clean validation audit: No coordinate or datatype warnings detected in any active datasets!")

st.write("")
st.write("")

st.markdown("### 🗺️ 2. City Dataset Explorer")
st.markdown("Query verified landmarks and safety zones for supported destinations. No fabricated values are shown here.")

col1, col2 = st.columns([1, 2])

with col1:
    cities_df = get_cities()
    city_list = sorted(cities_df["city"].tolist()) if not cities_df.empty else ["Hyderabad"]
    city_select = st.selectbox(
        "Select Target City",
        city_list
    )
    
    category_select = st.selectbox(
        "Select Category",
        ["Attractions", "Restaurants", "Hotels", "Accident Zones"]
    )

with col2:
    # Display city meta coordinates
    city_meta = get_city(city_select)
    if city_meta:
        st.markdown(f"""
        <div class="travel-card" style="padding: 15px 20px; background: rgba(255,255,255,0.09);">
            <h4 style="margin: 0; color: #0F172A;">🌐 Destination Coordinates (REAL DATA)</h4>
            <div style="font-size: 0.92rem; color: #52667A; margin-top: 8px; line-height: 1.5;">
                <strong>City:</strong> {city_meta['city']}<br>
                <strong>State:</strong> {city_meta['state']} | <strong>Country:</strong> {city_meta['country']}<br>
                <strong>Latitude:</strong> {city_meta['latitude']} | <strong>Longitude:</strong> {city_meta['longitude']}<br>
                <strong>Timezone:</strong> {city_meta['timezone']}<br>
                <strong>Source:</strong> {city_meta['source']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert-card alert-warning" style="margin: 0;">
            <div class="alert-title">⚠️ Destination Registry Missing</div>
            <div style="font-size: 0.88rem;">
                No verified location coordinates or timezone settings exist for '{city_select}' in the cities database.
            </div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# Query data based on selections
if category_select == "Attractions":
    data_df = get_attractions(city_select)
    if not data_df.empty:
        st.markdown(f"#### Verified Attractions in {city_select} (REAL DATA)")
        # Filter columns to display
        display_df = data_df[[
            "name", "category", "rating", "price", "visit_duration_minutes",
            "opening_time", "closing_time", "latitude", "longitude", "source"
        ]].rename(columns={
            "name": "Name",
            "category": "Category",
            "rating": "Rating (0-5)",
            "price": "Entry Fee (INR)",
            "visit_duration_minutes": "Duration (mins)",
            "opening_time": "Opens",
            "closing_time": "Closes",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "source": "Source"
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No verified data available.")

elif category_select == "Restaurants":
    data_df = get_restaurants(city_select)
    if not data_df.empty:
        st.markdown(f"#### Verified Restaurants in {city_select} (REAL DATA)")
        display_df = data_df[[
            "name", "cuisine", "food_type", "price_range", "rating",
            "latitude", "longitude", "source"
        ]].rename(columns={
            "name": "Name",
            "cuisine": "Cuisine",
            "food_type": "Diet Type",
            "price_range": "Price Tier",
            "rating": "Rating",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "source": "Source"
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No verified data available.")

elif category_select == "Hotels":
    data_df = get_hotels(city_select)
    if not data_df.empty:
        st.markdown(f"#### Verified Hotels in {city_select} (REAL DATA)")
        display_df = data_df[[
            "name", "category", "price_per_night", "rating",
            "latitude", "longitude", "amenities", "source"
        ]].rename(columns={
            "name": "Hotel Name",
            "category": "Category",
            "price_per_night": "Price/Night (INR)",
            "rating": "Rating",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "amenities": "Amenities",
            "source": "Source"
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No verified data available.")

elif category_select == "Accident Zones":
    data_df = get_accident_zones(city_select)
    if not data_df.empty:
        st.markdown(f"#### Verified Highway Accident Blackspots in {city_select} (REAL DATA)")
        display_df = data_df[[
            "location_name", "road_name", "risk_level", "accident_count",
            "risk_type", "recommended_action", "latitude", "longitude", "source", "data_date"
        ]].rename(columns={
            "location_name": "Location Stretch",
            "road_name": "Highway / Road Name",
            "risk_level": "Risk Level",
            "accident_count": "Accidents logged",
            "risk_type": "Risk Factors",
            "recommended_action": "Safety Advice",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "source": "Audit Source",
            "data_date": "Audit Date"
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        # Output exactly the warning requested for safety data missing
        st.warning("No verified accident-zone dataset is currently available.")
