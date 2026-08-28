import urllib.request

candidates = [
    # General India / Architecture / Nature / Palaces / Lakes / Forts
    "https://images.unsplash.com/photo-1524492412937-b28074a5d7da",
    "https://images.unsplash.com/photo-1548013146-72479768bada",
    "https://images.unsplash.com/photo-1599661046289-e31897846e41",
    "https://images.unsplash.com/photo-1570168007204-dfb528c6958f",
    "https://images.unsplash.com/photo-1506461883276-594a12b11cf3",
    "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2",
    "https://images.unsplash.com/photo-1567157577867-05ccb1388e66",
    "https://images.unsplash.com/photo-1587474260584-136574528ed5",
    "https://images.unsplash.com/photo-1564507592333-c60657eea523",
    "https://images.unsplash.com/photo-1596176530529-78163a4f7af2",
    "https://images.unsplash.com/photo-1558431382-27e303142255",
    "https://images.unsplash.com/photo-1477584305850-38c5f18c88bb",
    "https://images.unsplash.com/photo-1514222134-b57cbb8ce073",
    "https://images.unsplash.com/photo-1582510003544-4d00b7f74220",
    "https://images.unsplash.com/photo-1569470451072-68314f596aec",
    "https://images.unsplash.com/photo-1605649487212-47bdab064df7",
    "https://images.unsplash.com/photo-1589308078059-be1415eab4c3",
    "https://images.unsplash.com/photo-1593693397690-362cb9666fc2",
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e",
    "https://images.unsplash.com/photo-1566073771259-6a8506099945",
    "https://images.unsplash.com/photo-1582719508461-905c673771fd",
    "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa",
    "https://images.unsplash.com/photo-1540555700478-4be289fbecef",
    "https://images.unsplash.com/photo-1555854877-bab0e564b8d5",
    "https://images.unsplash.com/photo-1589301760014-d929f3979dbc",
    "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46",
    "https://images.unsplash.com/photo-1504674900247-0877df9cc836",
    "https://images.unsplash.com/photo-1554118811-1e0d58224f24",
    "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae",
    "https://images.unsplash.com/photo-1604514636960-2e1f5b118575",
    "https://images.unsplash.com/photo-1549488344-1f9b8d2bd1f3",
    "https://images.unsplash.com/photo-1566121318599-51cf4a04a39b",
    "https://images.unsplash.com/photo-1501555088652-021faa106b9b",
    "https://images.unsplash.com/photo-1483985988355-763728e1935b"
]

for base in candidates:
    url = f"{base}?auto=format&fit=crop&w=800&q=80"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"200 OK: {base}")
    except Exception as e:
        print(f"FAIL: {base} -> {e}")
