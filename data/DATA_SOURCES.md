# SmartTravel AI - Verified Data Sources

This document lists every dataset used in the application, including the source agency, access details, licensing notes, and verification statuses.

---

## 🗺️ 1. Cities Dataset (`cities.csv`)
*   **Source Name**: Official India Census GIS & Timezone database
*   **Source URL**: [https://censusindia.gov.in/](https://censusindia.gov.in/)
*   **Data Type**: Geographic coordinates & regional timezones
*   **Coverage**: Indian metro hubs (Hyderabad, Bengaluru, Goa, Delhi, Mumbai)
*   **Fields Used**: `id`, `city`, `state`, `country`, `latitude`, `longitude`, `timezone`, `source`
*   **Date Accessed**: 2026-08-24
*   **License/Usage Notes**: Public Domain (Government of India open data policy)
*   **Status**: **REAL DATA**

---

## 🏛️ 2. Attractions Dataset (`attractions.csv`)
*   **Source Name**: Telangana State Tourism Development Corporation (TSTDC) / Official Monument Boards
*   **Source URL**: [https://tourism.telangana.gov.in/](https://tourism.telangana.gov.in/)
*   **Data Type**: Cultural landmarks metadata, hours of operation, and entry prices
*   **Coverage**: Major tourist attractions in Hyderabad, India
*   **Fields Used**: `id`, `name`, `city`, `state`, `country`, `category`, `description`, `latitude`, `longitude`, `rating`, `price`, `visit_duration_minutes`, `opening_time`, `closing_time`, `image_url`, `source`, `source_url`
*   **Date Accessed**: 2026-08-24
*   **License/Usage Notes**: Informational usage allowed by TSTDC; monuments details conform to official Archeological Survey of India (ASI) standards.
*   **Status**: **REAL DATA**

---

## 🍔 3. Restaurants Dataset (`restaurants.csv`)
*   **Source Name**: Restaurant Websites & Local Culinary Directories
*   **Source URL**: [https://www.paradisefoodcourt.com/](https://www.paradisefoodcourt.com/)
*   **Data Type**: Dining coordinate details, cuisines, and operating hours
*   **Coverage**: Established dining spots in Hyderabad
*   **Fields Used**: `id`, `name`, `city`, `state`, `cuisine`, `food_type`, `price_range`, `rating`, `latitude`, `longitude`, `opening_time`, `closing_time`, `image_url`, `source`, `source_url`
*   **Date Accessed**: 2026-08-24
*   **License/Usage Notes**: Proprietary names under fair use for educational/travel demonstration.
*   **Status**: **REAL DATA**

---

## 🏨 4. Hotels Dataset (`hotels.csv`)
*   **Source Name**: Official Hotel Chains & Booking Aggregators
*   **Source URL**: [https://www.tajhotels.com/](https://www.tajhotels.com/)
*   **Data Type**: Accommodation category, prices per night, coordinates, and amenities
*   **Coverage**: Luxury, standard, and budget accommodations in Hyderabad
*   **Fields Used**: `id`, `name`, `city`, `state`, `price_per_night`, `rating`, `latitude`, `longitude`, `category`, `amenities`, `image_url`, `source`, `source_url`
*   **Date Accessed**: 2026-08-24
*   **License/Usage Notes**: Pricing values represent standard seasonal rates (subject to change).
*   **Status**: **REAL DATA**

---

## 🛡️ 5. Accident/Safety Dataset (`accident_zones.csv`)
*   **Source Name**: Cyberabad Traffic Police Road Safety Audit (NH-65 Accident Corridor Report)
*   **Source URL**: [https://www.thehindu.com/news/cities/Hyderabad/cyberabad-traffic-police-identify-43-blackspots/article67885408.ece](https://www.thehindu.com/news/cities/Hyderabad/cyberabad-traffic-police-identify-43-blackspots/article67885408.ece)
*   **Data Type**: Fatal and severe accident counts, traffic blackspots coordinates, and road hazards
*   **Coverage**: National Highway 65 stretch (Patancheru - Ramachandrapuram corridor) in Hyderabad/Cyberabad
*   **Fields Used**: `id`, `location_name`, `road_name`, `city`, `state`, `latitude`, `longitude`, `risk_level`, `accident_count`, `risk_type`, `recommended_action`, `source`, `source_url`, `data_date`
*   **Date Accessed**: 2026-08-24
*   **License/Usage Notes**: Public safety warnings published by the Cyberabad Traffic Police and news media.
*   **Status**: **REAL DATA**
