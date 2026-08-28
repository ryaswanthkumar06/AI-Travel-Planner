import urllib.request

more_candidates = [
    "https://images.unsplash.com/photo-1590766940554-634a7ed41450",
    "https://images.unsplash.com/photo-1609766857041-ed402ea8069a",
    "https://images.unsplash.com/photo-1598890777032-bde835ba27c2",
    "https://images.unsplash.com/photo-1565008447742-97f6f38c985c",
    "https://images.unsplash.com/photo-1588416936097-41850ab3d86d",
    "https://images.unsplash.com/photo-1567157577867-05ccb1388e66",
    "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2", # Goa
    "https://images.unsplash.com/photo-1570168007204-dfb528c6958f", # Hyderabad
    "https://images.unsplash.com/photo-1506461883276-594a12b11cf3", # Kerala/Munnar
    "https://images.unsplash.com/photo-1561361513-2d000a50f0dc", # Varanasi
    "https://images.unsplash.com/photo-1599661046289-e31897846e41", # Jaipur
    "https://images.unsplash.com/photo-1548013146-72479768bada", # Taj Mahal
    "https://images.unsplash.com/photo-1524492412937-b28074a5d7da", # India monument
    "https://images.unsplash.com/photo-1598373182133-52452f7691ef", # Kashmir
    "https://images.unsplash.com/photo-1617868186608-87ae5c6f6bf0", # Himachal / Manali
    "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23", # Mountains / Shimla
    "https://images.unsplash.com/photo-1578632767115-351597cf2477", # Ooty
    "https://images.unsplash.com/photo-1616035003073-a80d4632057e", # South temple
    "https://images.unsplash.com/photo-1627894006066-b4578853b0e3", # Palace / Udaipur
    "https://images.unsplash.com/photo-1590050752117-238cb0612b1b"
]

for base in more_candidates:
    url = f"{base}?auto=format&fit=crop&w=800&q=80"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"200 OK: {base}")
    except Exception as e:
        print(f"FAIL: {base} -> {e}")
