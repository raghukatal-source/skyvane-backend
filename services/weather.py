OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

def get_wind_data(lat, lon, altitude_ft, dep_time):
    if altitude_ft >= 36000:
        pressure_level = 200
    elif altitude_ft >= 30000:
        pressure_level = 250
    else:
        pressure_level = 300

    params = {
        "latitude": round(lat, 3),
        "longitude": round(lon, 3),
        "hourly": [
            f"wind_speed_{pressure_level}hPa",
            f"wind_direction_{pressure_level}hPa",
            f"temperature_{pressure_level}hPa",
            "cape",
            "lifted_index",
        ],
        "forecast_days": 2,
        "timezone": "UTC"
    }
    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=6)
        resp.raise_for_status()
        data = resp.json()
        return _extract_hourly(data, dep_time, pressure_level)
    except Exception as e:
        print(f"[weather] error at ({lat},{lon}): {e}")
        return _default_weather()

def _extract_hourly(data, target_time, pressure_level):
    times = data["hourly"]["time"]
    target_str = target_time.strftime("%Y-%m-%dT%H:00")
    idx = 0
    for i, t in enumerate(times):
        if t == target_str:
            idx = i
            break
    spd_key = f"wind_speed_{pressure_level}hPa"
    dir_key = f"wind_direction_{pressure_level}hPa"
    tmp_key = f"temperature_{pressure_level}hPa"
    hourly = data["hourly"]
    return {
        "wind_speed_kts": _ms_to_kts(hourly.get(spd_key, [0])[idx] or 0),
        "wind_direction": hourly.get(dir_key, [0])[idx] or 0,
        "temperature_c": hourly.get(tmp_key, [0])[idx] or -50,
        "cape": hourly.get("cape", [0])[idx] or 0,
        "lifted_index": hourly.get("lifted_index", [0])[idx] or 0,
    }

def get_pireps_along_route(waypoints):
    if not waypoints:
        return []
    lats = [w[0] for w in waypoints]
    lons = [w[1] for w in waypoints]
    bbox = f"{min(lons)-1},{min(lats)-1},{max(lons)+1},{max(lats)+1}"
    params = {"format": "json", "age": 3, "bbox": bbox, "type": "airep"}
    try:
        resp = requests.get("https://aviationweather.gov/api/data/pirep", params=params, timeout=6)
        resp.raise_for_status()
        return _parse_pireps(resp.json())
    except Exception as e:
        print(f"[weather] PIREP error: {e}")
        return []

def _parse_pireps(raw):
    pireps = []
    intensity_map = {
        "NEG": 0, "SMOOTH": 0, "LGT": 2, "LGT-MOD": 3,
        "MOD": 5, "MOD-SEV": 7, "SEV": 8, "EXTRM": 10
    }
    for p in raw:
        turb = p.get("turbulence", {})
        intensity_str = turb.get("intensity", "NEG").upper().replace(" ", "-")
        intensity = intensity_map.get(intensity_str, 0)
        if intensity == 0:
            continue
        pireps.append({
            "lat": p.get("latitude", 0),
            "lon": p.get("longitude", 0),
            "altitude_ft": p.get("altitudeFt") or 0,
            "intensity": intensity,
            "age_hours": p.get("ageHours", 1),
        })
    return pireps

def get_route_weather(waypoints, altitude_ft, departure_time):
    waypoint_weather = []
    for lat, lon in waypoints:
        w = get_wind_data(lat, lon, altitude_ft, departure_time)
        waypoint_weather.append({"lat": lat, "lon": lon, **w})
    pireps = get_pireps_along_route(waypoints)
    return {
        "waypoints": waypoint_weather,
        "pireps": pireps,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }

def _ms_to_kts(ms):
    return round(ms * 1.94384, 1)

def _default_weather():
    return {
        "wind_speed_kts": 30,
        "wind_direction": 270,
        "temperature_c": -50,
        "cape": 0,
        "lifted_index": 2,
    }
