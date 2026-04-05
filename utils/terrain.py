MOUNTAIN_ZONES = [
    (7.5,  14.5, 74.0, 78.5, 5.5, "Western Ghats"),
    (26.0, 38.0, 70.0, 82.0, 4.0, "Hindu Kush / Pakistan"),
    (27.0, 36.0, 80.0, 97.0, 6.5, "Himalayas"),
    (25.0, 30.0, 88.0, 95.0, 4.5, "Assam hills"),
    (44.0, 48.5, 5.0,  16.0, 5.0, "Alps"),
    (36.0, 44.0, -9.0, 4.0,  4.0, "Pyrenees"),
    (40.0, 45.0, 20.0, 28.0, 4.0, "Balkans"),
    (38.0, 44.0, 39.0, 50.0, 4.5, "Caucasus Mountains"),
    (28.0, 37.0, 34.0, 42.0, 3.5, "Zagros Mountains"),
    (35.0, 55.0, -125.0, -100.0, 5.5, "Rocky Mountains"),
    (35.0, 44.0, -85.0,  -70.0,  3.0, "Appalachians"),
    (25.0, 40.0, 96.0,  110.0, 4.5, "Yunnan / Sichuan"),
    (31.0, 36.0, -6.0, 3.0, 3.5, "Atlas Mountains"),
    (-55.0, -15.0, -75.0, -65.0, 5.0, "Andes"),
]

def get_terrain_factor(lat, lon):
    max_score = 0.0
    for zone in MOUNTAIN_ZONES:
        min_lat, max_lat, min_lon, max_lon, score, name = zone
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            max_score = max(max_score, score)
    return max_score
