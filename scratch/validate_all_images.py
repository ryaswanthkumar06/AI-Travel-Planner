import os
import sys
import pandas as pd
import urllib.request
import urllib.error
import concurrent.futures

sys.path.insert(0, os.path.abspath("."))
from services.image_service import (
    CITY_IMAGES,
    ATTRACTION_SPECIFIC_IMAGES,
    CATEGORY_FALLBACKS,
    HOTEL_FALLBACKS,
    RESTAURANT_FALLBACKS,
    GENERAL_FALLBACK
)

def check_url(url_tuple):
    label, url = url_tuple
    if not url or not url.startswith("http"):
        return False, label, url, "Invalid URL scheme"
    if "photo-15000000" in url or "photo-16000000" in url:
        return False, label, url, "Dummy placeholder detected"
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            code = resp.getcode()
            if code == 200:
                return True, label, url, f"HTTP {code}"
            else:
                return False, label, url, f"HTTP {code}"
    except Exception as e:
        return False, label, url, str(e)

def main():
    urls_to_test = []
    
    # 1. Image service mappings
    for city, url in CITY_IMAGES.items():
        urls_to_test.append((f"CITY_IMAGES[{city}]", url))
    for att, url in ATTRACTION_SPECIFIC_IMAGES.items():
        urls_to_test.append((f"ATTRACTION_SPECIFIC[{att}]", url))
    for cat, url in CATEGORY_FALLBACKS.items():
        urls_to_test.append((f"CATEGORY_FALLBACKS[{cat}]", url))
    for h, url in HOTEL_FALLBACKS.items():
        urls_to_test.append((f"HOTEL_FALLBACKS[{h}]", url))
    for r, url in RESTAURANT_FALLBACKS.items():
        urls_to_test.append((f"RESTAURANT_FALLBACKS[{r}]", url))
    urls_to_test.append(("GENERAL_FALLBACK", GENERAL_FALLBACK))
    
    # 2. CSVs
    cities_df = pd.read_csv("data/cities.csv")
    for _, row in cities_df.iterrows():
        urls_to_test.append((f"cities.csv -> {row['city']}", row['image_url']))
        
    attr_df = pd.read_csv("data/attractions.csv")
    for _, row in attr_df.iterrows():
        urls_to_test.append((f"attractions.csv -> {row['name']} ({row['city']})", row['image_url']))
        
    hotels_df = pd.read_csv("data/hotels.csv")
    for _, row in hotels_df.iterrows():
        urls_to_test.append((f"hotels.csv -> {row['name']}", row['image_url']))
        
    rest_df = pd.read_csv("data/restaurants.csv")
    for _, row in rest_df.iterrows():
        urls_to_test.append((f"restaurants.csv -> {row['name']}", row['image_url']))

    # Deduplicate URLs to test
    unique_urls = {}
    for label, u in urls_to_test:
        if u not in unique_urls:
            unique_urls[u] = label

    print(f"Total entries across codebase & CSVs: {len(urls_to_test)}")
    print(f"Unique distinct image URLs: {len(unique_urls)}")
    print("Validating all image URLs concurrently via HTTP GET...")

    passed = 0
    failed = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_url, (lbl, u)) for u, lbl in unique_urls.items()]
        for f in concurrent.futures.as_completed(futures):
            ok, lbl, u, status = f.result()
            if ok:
                passed += 1
            else:
                failed.append((lbl, u, status))

    print(f"\n--- Validation Results ---")
    print(f"Passed: {passed}/{len(unique_urls)} ({passed/len(unique_urls)*100:.1f}%)")
    if failed:
        print(f"Failed ({len(failed)}):")
        for lbl, u, status in failed[:10]:
            print(f"  [FAIL] {lbl}: {u[:60]}... ({status})")
    else:
        print("ALL unique image URLs returned HTTP 200 successfully without broken links or placeholders!")

if __name__ == "__main__":
    main()
