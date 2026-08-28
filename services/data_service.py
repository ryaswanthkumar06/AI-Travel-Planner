import pandas as pd
import os
from utils.data_validator import validate_dataframe

DATA_DIR = "data"

def load_dataset_raw(filename):
    """Loads a CSV file from data folder. Returns DataFrame or empty DataFrame if not found."""
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def get_verified_data(filename, dataset_type):
    """Loads a CSV file, runs validation, and returns the valid DataFrame only."""
    df = load_dataset_raw(filename)
    validation = validate_dataframe(df, dataset_type)
    return validation["valid_df"]

def get_validation_report(filename, dataset_type):
    """Loads a CSV file and returns the full validation dictionary."""
    df = load_dataset_raw(filename)
    return validate_dataframe(df, dataset_type)

CITY_ALIASES = {
    # Bengaluru / Bangalore variants — CSV stores as "Bengaluru"
    "bangalore":    "Bengaluru",
    "bengaluru":    "Bengaluru",
    "bengalooru":   "Bengaluru",
    "banglore":     "Bengaluru",
    # Mysuru / Mysore variants — CSV stores as "Mysuru"
    "mysore":       "Mysuru",
    "mysuru":       "Mysuru",
    # Delhi variants — CSV stores as "Delhi"
    "new delhi":    "Delhi",
    "new_delhi":    "Delhi",
    # Mumbai variants — CSV stores as "Mumbai"
    "bombay":       "Mumbai",
    # Chennai variants — CSV stores as "Chennai"
    "madras":       "Chennai",
    # Kolkata variants — CSV stores as "Kolkata"
    "calcutta":     "Kolkata",
    # Alleppey — CSV stores as "Alleppey"
    "alappuzha":    "Alleppey",
    # Pondicherry — CSV stores as "Pondicherry"
    "puducherry":   "Pondicherry",
    "pondy":        "Pondicherry",
    # Coorg — CSV stores as "Coorg"
    "kodagu":       "Coorg",
    # Varanasi — CSV stores as "Varanasi"
    "banaras":      "Varanasi",
    "benares":      "Varanasi",
    "kashi":        "Varanasi",
    # Kochi
    "cochin":       "Kochi",
    # Srinagar
    "kashmir":      "Srinagar",
    # Wayanad
    "wynad":        "Wayanad",
    # Agra
    "agra":         "Agra",
    # Darjeeling
    "darjiling":    "Darjeeling",
    # Manali
    "manaly":       "Manali",
    # Gangtok
    "gangtok":      "Gangtok",
    # Amritsar
    "amritsar":     "Amritsar",
}

def resolve_canonical_city_name(city_name):
    """Maps common alternate names (e.g. Bengaluru -> Bangalore) to database canonical names."""
    if not city_name:
        return ""
    name_lower = str(city_name).lower().strip()
    return CITY_ALIASES.get(name_lower, str(city_name).strip())

def get_city(city_name):
    """Returns details of a specific city. Returns dict or None."""
    city_name = resolve_canonical_city_name(city_name)
    df = get_verified_data("cities.csv", "cities")
    if df.empty:
        return None
    # Case-insensitive filter
    matches = df[df["city"].str.lower() == city_name.lower().strip()]
    if not matches.empty:
        return dict(matches.iloc[0])
    return None

def get_attractions(city_name):
    """Returns valid attractions for a city."""
    city_name = resolve_canonical_city_name(city_name)
    df = get_verified_data("attractions.csv", "attractions")
    if df.empty:
        return pd.DataFrame()
    return df[df["city"].str.lower() == city_name.lower().strip()]

def get_restaurants(city_name):
    """Returns valid restaurants for a city."""
    city_name = resolve_canonical_city_name(city_name)
    df = get_verified_data("restaurants.csv", "restaurants")
    if df.empty:
        return pd.DataFrame()
    return df[df["city"].str.lower() == city_name.lower().strip()]

def get_hotels(city_name):
    """Returns valid hotels for a city."""
    city_name = resolve_canonical_city_name(city_name)
    df = get_verified_data("hotels.csv", "hotels")
    if df.empty:
        return pd.DataFrame()
    return df[df["city"].str.lower() == city_name.lower().strip()]

def get_accident_zones(city_name):
    """Returns valid accident zones for a city."""
    city_name = resolve_canonical_city_name(city_name)
    df = get_verified_data("accident_zones.csv", "accident_zones")
    if df.empty:
        return pd.DataFrame()
    return df[df["city"].str.lower() == city_name.lower().strip()]

def get_cities():
    """Returns all verified cities."""
    return get_verified_data("cities.csv", "cities")

