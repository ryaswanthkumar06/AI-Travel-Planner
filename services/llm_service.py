import requests
import json
import os
import re

def polish_itinerary_with_llm(itinerary_data):
    """
    Polishes the candidate itinerary by calling Gemini.
    If no API key exists, or the call fails, returns the itinerary unchanged.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        itinerary_data["llm_polished"] = False
        itinerary_data["llm_warning"] = "API key required. Polished AI descriptions unavailable."
        return itinerary_data

    # Call Gemini REST API (gemini-1.5-flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # Strip coordinates and technical items to keep the token prompt footprint light
    prompt_data = {
        "destination": itinerary_data["destination"],
        "days": itinerary_data["days"],
        "travelers": itinerary_data["travelers"],
        "budget": itinerary_data["budget"],
        "interests": itinerary_data["interests"],
        "hotel": {
            "name": itinerary_data["selected_hotel"]["name"],
            "category": itinerary_data["selected_hotel"]["category"],
            "price": itinerary_data["selected_hotel"].get("price_per_night")
        },
        "itinerary": []
    }
    
    for day in itinerary_data["itinerary"]:
        day_events = []
        for e in day["events"]:
            if e["type"] in ["Attraction", "Restaurant"]:
                day_events.append({
                    "id": e.get("id"),
                    "time": e["time"],
                    "type": e["type"],
                    "name": e["name"],
                    "category": e.get("category"),
                    "description": e["description"]
                })
            else:
                day_events.append({
                    "time": e["time"],
                    "type": e["type"],
                    "name": e["name"],
                    "description": e["description"]
                })
        prompt_data["itinerary"].append({
            "day": day["day"],
            "theme": day["theme"],
            "events": day_events
        })
        
    prompt = f"""
You are a senior travel coordinator AI. You must polish the draft travel itinerary supplied below.

CRITICAL INSTRUCTIONS:
1. DO NOT invent or add any new attractions, hotels, or restaurants. Use ONLY the places and descriptions provided in the JSON.
2. Enhance the 'description' field for each Attraction and Restaurant by adding interesting historical context, travel tips, or local secrets, but DO NOT alter names, coordinates, prices, or IDs.
3. Add a new string field 'why_recommended' for each Attraction and Restaurant explaining how it matches the user interests: {prompt_data['interests']}.
4. Add a new string field 'travel_tip' under each Day (at the day level) providing regional advice (weather precautions, attire, etc.).
5. Return the modified itinerary in structured JSON format matching the original day-wise list.

Original JSON Itinerary:
{json.dumps(prompt_data, indent=2)}

Return ONLY a valid JSON block containing the key "itinerary" mapping to the list of days. Avoid any markdown code wrapper other than standard JSON block.
"""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                text_content = candidates[0]["content"]["parts"][0]["text"]
                # Clean up any potential markdown text wrapping
                text_content = re.sub(r'^```json\s*', '', text_content, flags=re.IGNORECASE)
                text_content = re.sub(r'\s*```$', '', text_content)
                
                parsed_llm = json.loads(text_content)
                llm_days = parsed_llm.get("itinerary", [])
                
                # Merge polished descriptions and why_recommended back into original data
                # to guarantee we don't drop coordinates, price tags, or transit segments
                for idx_day, orig_day in enumerate(itinerary_data["itinerary"]):
                    if idx_day < len(llm_days):
                        llm_day = llm_days[idx_day]
                        orig_day["travel_tip"] = llm_day.get("travel_tip", "Enjoy your day's exploration!")
                        
                        # Match events
                        llm_events = llm_day.get("events", [])
                        for orig_ev in orig_day["events"]:
                            if orig_ev["type"] in ["Attraction", "Restaurant"]:
                                # Match by name or ID
                                for llm_ev in llm_events:
                                    if llm_ev.get("name") == orig_ev["name"] or llm_ev.get("id") == orig_ev.get("id"):
                                        if llm_ev.get("description"):
                                            orig_ev["description"] = llm_ev["description"]
                                        orig_ev["why_recommended"] = llm_ev.get("why_recommended", "Fits your interests.")
                                        break
                                        
                itinerary_data["llm_polished"] = True
                return itinerary_data
    except Exception:
        # Fallback when Gemini is offline or fails to parse
        pass
        
    itinerary_data["llm_polished"] = False
    itinerary_data["llm_warning"] = "AI polishing failed or timed out. Showing verified database itinerary."
    return itinerary_data
