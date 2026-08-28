# 🌍 SmartTravel AI — AI-Powered Travel Planner for India

**SmartTravel AI** is an intelligent, data-driven travel recommendation and itinerary planning system for India. Built on top of verified datasets (30 destinations, 300 attractions, 150 hotels, 150 restaurants, and 60 monitored highway safety corridors), it combines real-time weather forecasts, Google Places metadata, budget auto-optimization, and route safety audits to create complete day-wise travel itineraries.

---

## 🌟 Key Features

1. **30 Verified Indian Destinations**:
   - Goa, Hyderabad, Munnar, Varanasi, Delhi, Mumbai, Bengaluru, Jaipur, Udaipur, Agra, Mysuru, Ooty, Manali, Shimla, Rishikesh, Kochi, Alleppey, Chennai, Madurai, Pondicherry, Darjeeling, Gangtok, Amritsar, Kolkata, Wayanad, Jodhpur, Kodaikanal, Coorg, Ahmedabad, Srinagar.

2. **Google Places & Google Maps Integration**:
   - `📍 Open in Google Maps` and `🚗 Get Directions` links beside every landmark, hotel, restaurant, and itinerary activity.
   - Point-to-Point routing and multi-stop day route URLs.

3. **9-Step Planning Wizard**:
   - Stepper workflow collecting Destination, Dates, Travelers, Budget, Travel Style, Interests, Food Preferences, Lodging Tier, and Transport Mode.
   - 7 Result Tabs: *Day-Wise Timeline, Interactive Route Map, Budget Calculation & Auto-Optimizer, Weather Forecast, Safety Advisor, Recommended Hotels, and Recommended Dining.*

4. **Real-Time Weather & Forecasts**:
   - Integrates OpenWeather API and Open-Meteo REST API for live temperatures, humidity, wind speeds, and multi-day trip forecasts.

5. **Travel Safety Dashboard**:
   - Monitored highway blackspots, pedestrian hazard junctions, and route proximity warnings based on MoRTH audit data.

6. **Dual-Mode AI Travel Assistant**:
   - Interactive chatbot answering questions on 30+ destinations, packing advice, weather, stays, dining, and active itineraries.

7. **PDF Report Exports**:
   - Generates formatted PDF trip itineraries for offline download.

---

## 🛠️ Project Architecture

```
AI-Travel-Anti/
├── app.py                          # Main entry point & dynamic page router
├── assets/style.css                # High-contrast SaaS design system
├── components/
│   └── floating_assistant.py       # Floating AI chatbot component
├── data/
│   ├── db_seeder.py                # 30-city database generator
│   ├── cities.csv                  # 30 destinations
│   ├── attractions.csv             # 300 verified landmarks
│   ├── hotels.csv                  # 150 hotel selections
│   ├── restaurants.csv             # 150 dining options
│   └── accident_zones.csv          # 60 safety blackspots
├── database/
│   └── db_manager.py               # SQLite CRUD operations
├── pages/
│   ├── home.py                     # Hero section & 30-destination grid
│   ├── dashboard.py                # User travel stats & catalog coverage
│   ├── explore.py                  # Search, multi-filters, & Detail tabs
│   ├── plan_trip.py                # 9-step wizard & 7 result tabs
│   ├── my_trips.py                 # Saved itineraries & PDF downloads
│   ├── safety.py                   # Travel Safety Dashboard & blackspots
│   ├── assistant.py                # AI Assistant chatbot console
│   ├── profile.py                  # Travel preferences form
│   ├── login.py                    # Split-layout Sign In / Register
│   └── logout.py                   # Session clear
└── services/
    ├── google_places_service.py    # Google Places API (New) integration
    ├── maps_service.py             # Google Maps & Directions URL generator
    ├── image_service.py            # Landmark photo URL mappings
    ├── weather_service.py          # OpenWeather & Open-Meteo forecast engine
    ├── safety_service.py           # Route safety proximity auditor
    ├── itinerary_service.py        # Unified itinerary generator
    ├── data_service.py             # Data loader helpers
    ├── budget_service.py           # Budget calculation engine
    └── routing_service.py          # Haversine distance calculator
```

---

## 🚀 Setup & Installation Instructions

### 1. Prerequisites
- Python 3.10+
- Virtual environment (`venv`)

### 2. Installation
```powershell
# Clone or navigate to the workspace
cd C:\PROJECTS\AI-Travel-Anti

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### 3. Environment Variables (`.env`)
Copy `.env.example` to `.env` and fill in optional API keys:
```env
GOOGLE_MAPS_API_KEY=your_key_here
GOOGLE_PLACES_API_KEY=your_key_here
OPENWEATHER_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```
*Note: If any key is left unconfigured, the system automatically uses verified local databases and free open APIs (Open-Meteo) with zero crashes.*

### 4. Seed Database
```powershell
python data/db_seeder.py
```

### 5. Run Application
```powershell
streamlit run app.py --server.port 8515
```

---

## 🔑 Test Account Credentials

- **Email:** `test@example.com`
- **Password:** `password123`
*(Or click "Create Account" on the Sign In page to register any new account.)*
