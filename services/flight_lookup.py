import os
import requests
from datetime import datetime, timezone
from utils.geo import interpolate_waypoints
from utils.aircraft import get_aircraft_profile

AVIATIONSTACK_KEY = os.environ.get("AVIATIONSTACK_KEY", "")
BASE_URL = "http://api.aviationstack.com/v1"

AIRPORT_COORDS = {
    "DEL": {"lat": 28.5562, "lon": 77.1000, "name": "New Delhi"},
    "BOM": {"lat": 19.0896, "lon": 72.8656, "name": "Mumbai"},
    "BLR": {"lat": 13.1979, "lon": 77.7063, "name": "Bangalore"},
    "CCU": {"lat": 22.6520, "lon": 88.4463, "name": "Kolkata"},
    "MAA": {"lat": 12.9941, "lon": 80.1709, "name": "Chennai"},
    "HYD": {"lat": 17.2403, "lon": 78.4294, "name": "Hyderabad"},
    "DXB": {"lat": 25.2532, "lon": 55.3657, "name": "Dubai"},
    "LHR": {"lat": 51.4775, "lon": -0.4614, "name": "London"},
    "SIN": {"lat": 1.3644,  "lon": 103.9915, "name": "Singapore"},
    "BKK": {"lat": 13.6811, "lon": 100.7472, "name": "Bangkok"},
    "CDG": {"lat": 49.0097, "lon": 2.5479, "name": "Paris"},
    "JFK": {"lat": 40.6413, "lon": -73.7781, "name": "New York"},
    "NRT": {"lat": 35.7720, "lon": 140.3929, "name": "Tokyo"},
}

MOCK_FLIGHTS = {
    "6E204":  ("DEL", "BOM", "07:30", "A20N", "IndiGo"),
    "AI302":  ("BOM", "BLR", "06:15", "A320", "Air India"),
    "EK509":  ("DEL", "DXB", "14:20", "B77W", "Emirates"),
    "SG8169": ("DEL", "CCU", "11:10", "B738", "SpiceJet"),
    "BA140":  ("DEL", "LHR", "20:45", "B789", "British Airways"),
}

def get_flight_info(flight_number, date=None):
    if not AVIATIONSTACK_KEY:
        return _mock_flight(flight_number)
    params = {"access_key": AVIATIONSTACK_KEY, "flight_iata": flight_number, "limit": 1}
    if date:
        params["flight_date"] = date
    try:
        resp = requests.get(f"{BASE_URL}/flights", params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("data"):
            return _mock_flight(flight_number)
        return _normalize(data["data"][0])
    except Exception as e:
        print(f"[flight_lookup] error: {e}")
        return _mock_flight(flight_number)

def _normalize(raw):
    dep_iata = raw["departure"]["iata"]
    arr_iata = raw["arrival"]["iata"]
    dep_airport = AIRPORT_COORDS.get(dep_iata, {"lat": 0, "lon": 0, "name": dep_iata})
    arr_airport = AIRPORT_COORDS.get(arr_iata, {"lat": 0, "lon": 0, "name": arr_iata})
    aircraft_iata = raw.get("aircraft", {}).get("iata", "A320")
    profile = get_aircraft_profile(aircraft_iata)
    dep_time_str = raw["departure"].get("scheduled", "") or ""
    dep_time = _parse_time(dep_time_str)
    waypoints = interpolate_waypoints(
        origin=(dep_airport["lat"], dep_airport["lon"]),
        destination=(arr_airport["lat"], arr_airport["lon"]),
        n_points=8
    )
    return {
        "flight_number": raw["flight"]["iata"],
        "airline": raw["airline"]["name"],
        "from_iata": dep_iata,
        "from_city": dep_airport.get("name", dep_iata),
        "to_iata": arr_iata,
        "to_city": arr_airport.get("name", arr_iata),
        "departure_time": dep_time,
        "aircraft_iata": aircraft_iata,
        "aircraft_type": profile["type"],
        "aircraft_name": profile["name"],
        "cruise_altitude_ft": profile["cruise_altitude_ft"],
        "waypoints": waypoints,
        "duration_minutes": _estimate_duration(waypoints),
        "status": raw.get("flight_status", "scheduled")
    }

def _parse_time(time_str):
    if not time_str:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(time_str)
    except:
        return datetime.now(timezone.utc)

def _estimate_duration(waypoints):
    from utils.geo import haversine_km
    total_km = sum(haversine_km(waypoints[i], waypoints[i+1]) for i in range(len(waypoints)-1))
    return int((total_km / 850) * 60) + 30

def _mock_flight(flight_number):
    if flight_number not in MOCK_FLIGHTS:
        return None
    dep, arr, dep_time_str, ac, airline = MOCK_FLIGHTS[flight_number]
    dep_airport = AIRPORT_COORDS[dep]
    arr_airport = AIRPORT_COORDS[arr]
    profile = get_aircraft_profile(ac)
    waypoints = interpolate_waypoints(
        origin=(dep_airport["lat"], dep_airport["lon"]),
        destination=(arr_airport["lat"], arr_airport["lon"]),
        n_points=8
    )
    now = datetime.now(timezone.utc)
    dep_time = now.replace(
        hour=int(dep_time_str.split(":")[0]),
        minute=int(dep_time_str.split(":")[1]),
        second=0, microsecond=0
    )
    return {
        "flight_number": flight_number,
        "airline": airline,
        "from_iata": dep,
        "from_city": dep_airport["name"],
        "to_iata": arr,
        "to_city": arr_airport["name"],
        "departure_time": dep_time,
        "aircraft_iata": ac,
        "aircraft_type": profile["type"],
        "aircraft_name": profile["name"],
        "cruise_altitude_ft": profile["cruise_altitude_ft"],
        "waypoints": waypoints,
        "duration_minutes": _estimate_duration(waypoints),
        "status": "scheduled"
    }
