import pandas as pd
import re

def validate_time_format(time_str):
    """Validates time format (HH:MM or HH:MM:SS or HH:MM AM/PM)."""
    if pd.isna(time_str) or not isinstance(time_str, str):
        return False
    # Check HH:MM or HH:MM:SS
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$'
    # Check HH:MM AM/PM
    pattern_ampm = r'^(0?[1-9]|1[0-2]):[0-5][0-9]\s*(AM|PM|am|pm)$'
    return bool(re.match(pattern, time_str) or re.match(pattern_ampm, time_str))

def validate_dataframe(df, dataset_type):
    """
    Validates a pandas DataFrame based on the dataset type.
    dataset_type: 'cities', 'attractions', 'restaurants', 'hotels', 'accident_zones'
    
    Returns a dict with:
        - 'valid_df': DataFrame with valid rows only
        - 'invalid_df': DataFrame with invalid rows
        - 'metrics': dict of count metrics
        - 'errors': list of strings detailing errors
    """
    errors = []
    metrics = {
        "total": len(df),
        "valid": 0,
        "invalid": 0,
        "missing_coordinates": 0,
        "missing_prices": 0,
        "missing_images": 0,
        "missing_hours": 0,
        "duplicates": 0
    }
    
    if df is None or df.empty:
        return {"valid_df": pd.DataFrame(), "invalid_df": pd.DataFrame(), "metrics": metrics, "errors": ["DataFrame is empty or None"]}
        
    # Check required columns
    required_cols = {
        "cities": ["id", "city", "latitude", "longitude"],
        "attractions": ["id", "name", "city", "latitude", "longitude", "rating", "price", "opening_time", "closing_time"],
        "restaurants": ["id", "name", "city", "latitude", "longitude", "rating", "opening_time", "closing_time"],
        "hotels": ["id", "name", "city", "latitude", "longitude", "price_per_night", "rating"],
        "accident_zones": ["id", "location_name", "city", "latitude", "longitude", "risk_level"]
    }
    
    cols = required_cols.get(dataset_type, [])
    missing_cols = [c for c in cols if c not in df.columns]
    if missing_cols:
        msg = f"Missing required columns for {dataset_type}: {missing_cols}"
        errors.append(msg)
        return {"valid_df": pd.DataFrame(columns=df.columns), "invalid_df": df, "metrics": metrics, "errors": errors}
        
    # Check duplicate IDs
    if "id" in df.columns:
        duplicate_ids = df[df["id"].duplicated()]
        if not duplicate_ids.empty:
            metrics["duplicates"] += len(duplicate_ids)
            errors.append(f"Duplicate IDs detected in {dataset_type}: {duplicate_ids['id'].tolist()}")

    valid_rows = []
    invalid_rows = []
    
    for idx, row in df.iterrows():
        row_errors = []
        row_id = row.get("id", idx)
        
        # 1. Normalize and check city name
        if "city" in row:
            if pd.isna(row["city"]) or str(row["city"]).strip() == "":
                row_errors.append("City name is empty or missing")
                
        # 2. Coordinates validation
        lat = row.get("latitude")
        lng = row.get("longitude")
        
        if pd.isna(lat) or pd.isna(lng):
            metrics["missing_coordinates"] += 1
            row_errors.append("Missing latitude or longitude coordinates")
        else:
            try:
                lat_val = float(lat)
                lng_val = float(lng)
                if not (-90.0 <= lat_val <= 90.0):
                    row_errors.append(f"Latitude out of bounds: {lat_val}")
                if not (-180.0 <= lng_val <= 180.0):
                    row_errors.append(f"Longitude out of bounds: {lng_val}")
            except ValueError:
                row_errors.append(f"Non-numeric coordinates: lat={lat}, lng={lng}")

        # 3. Rating validation
        if "rating" in row:
            rating = row.get("rating")
            if not pd.isna(rating):
                try:
                    rating_val = float(rating)
                    if not (0.0 <= rating_val <= 5.0):
                        row_errors.append(f"Rating out of bounds (0-5): {rating_val}")
                except ValueError:
                    row_errors.append(f"Non-numeric rating: {rating}")
            else:
                row_errors.append("Missing rating value")

        # 4. Price validation
        price_fields = ["price", "price_per_night"]
        for pf in price_fields:
            if pf in row:
                price = row.get(pf)
                if pd.isna(price):
                    metrics["missing_prices"] += 1
                else:
                    try:
                        price_val = float(price)
                        if price_val < 0:
                            row_errors.append(f"Negative price detected: {price_val}")
                    except ValueError:
                        row_errors.append(f"Non-numeric price for {pf}: {price}")

        # 5. Image URL validation
        if "image_url" in row:
            img = row.get("image_url")
            if pd.isna(img) or str(img).strip() == "":
                metrics["missing_images"] += 1

        # 6. Opening hours validation
        if "opening_time" in row and "closing_time" in row:
            open_t = row.get("opening_time")
            close_t = row.get("closing_time")
            if pd.isna(open_t) or pd.isna(close_t) or str(open_t).strip() == "" or str(close_t).strip() == "":
                metrics["missing_hours"] += 1
                row_errors.append("Missing timing columns: opening_time/closing_time")
            else:
                if not validate_time_format(str(open_t)):
                    row_errors.append(f"Invalid format for opening_time: {open_t}")
                if not validate_time_format(str(close_t)):
                    row_errors.append(f"Invalid format for closing_time: {close_t}")

        if row_errors:
            metrics["invalid"] += 1
            for err in row_errors:
                errors.append(f"Row ID {row_id} error: {err}")
            invalid_rows.append(row)
        else:
            metrics["valid"] += 1
            valid_rows.append(row)
            
    valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=df.columns)
    invalid_df = pd.DataFrame(invalid_rows) if invalid_rows else pd.DataFrame(columns=df.columns)
    
    return {
        "valid_df": valid_df,
        "invalid_df": invalid_df,
        "metrics": metrics,
        "errors": errors
    }
