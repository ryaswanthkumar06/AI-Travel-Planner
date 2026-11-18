# SmartTravel AI - Data Sources and Verification Status

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
*   **Fields Used**: `id`, `name`, `city`, `state`, `country`, `category`, `description`, `latitude`, `longitude`, `rating`, `price`, `visit_duration_minutes`, `opening_time`, `closing_time`, `image_url`, `source`, `source_url` (the `rating` column is intentionally blank until provider verification)
*   **Date Accessed**: 2026-08-24
*   **License/Usage Notes**: Informational usage allowed by TSTDC; monuments details conform to official Archeological Survey of India (ASI) standards.
*   **Rating note**: The local `rating` values were removed because they were not independently verified. Display ratings only after a successful Google Places match.
*   **Status**: **CURATED DATA — ROW-LEVEL DETAILS REQUIRE VERIFICATION**

---

## 🍔 3. Restaurants Dataset (`restaurants.csv`)
*   **Source Name**: Synthetic demonstration catalogue
*   **Source URL**: None. The current rows do not have verified restaurant source pages.
*   **Data Type**: Illustrative restaurant names, cuisine labels, price bands, ratings, hours, and approximate coordinates.
*   **Coverage**: 30 destination labels with five templated sample rows per city.
*   **Status**: **DEMO DATA — NOT VERIFIED**

**Important:** Restaurant names, ratings, coordinates, prices, and opening hours must not be presented as verified businesses or live Google Maps information. Replace the sample rows with individually researched businesses and validated source details before production use.

---

## 🏨 4. Hotels Dataset (`hotels.csv`)
*   **Source Name**: Synthetic demonstration catalogue
*   **Source URL**: None. The current rows do not have verified hotel source pages.
*   **Data Type**: Illustrative hotel names, accommodation categories, price estimates, ratings, amenities, and approximate coordinates.
*   **Coverage**: 30 destination labels with five templated sample rows per city.
*   **Status**: **DEMO DATA — NOT VERIFIED**

**Important:** Hotel names, ratings, coordinates, rates, and amenities must not be presented as verified businesses, live Google Maps ratings, or current availability. Replace the sample rows with individually researched properties and validated source details before production use.

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
