import os
import sys
import math
import requests
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

AVIATIONSTACK_KEY = os.environ.get("AVIATIONSTACK_KEY", "")

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

AIRCRAFT_DB = {
    "A320": {"name": "Airbus A320", "type": "narrow_body", "alt": 35000},
    "A20N": {"name": "Airbus A320neo", "type": "narrow_body", "alt": 36000},
    "A321": {"name": "Airbus A321", "type": "narrow_body", "alt": 35000},
    "B737": {"name": "Boeing 737", "type": "narrow_body", "alt": 35000},
    "B738": {"name": "Boeing 737-800", "type": "narrow_body", "alt": 35000},
    "B77W": {"name": "Boeing 777-300ER", "type": "wide_body", "alt": 40000},
    "B789": {"name": "Boeing 787-9 Dreamliner", "type": "wide_body", "alt": 40000},
    "B788": {"name": "Boeing 787-8", "type": "wide_body", "alt": 40000},
    "A333": {"name": "Airbus A330-300", "type": "wide_body", "alt": 39000},
    "A359": {"name": "Airbus A350-900", "type": "wide_body", "alt": 41000},
    "A380": {"name": "Airbus A380", "type": "wide_body", "alt": 40000},
}

MOCK_FLIGHTS = {
    "6E204":  ("DEL", "BOM", "07:30", "A20N", "IndiGo"),
    "AI302":  ("BOM", "BLR", "06:15", "A320", "Air India"),
    "EK509":  ("DEL", "DXB", "14:20", "B77W", "Emirates"),
    "SG8169": ("DEL", "CCU", "11:10", "B738", "SpiceJet"),
    "BA140":  ("DEL", "LHR", "20:45", "B789", "British Airways"),
}

MOUNTAIN_ZONES = [
    (7.5, 14.5, 74.0, 78.5, 5.5, "Western Ghats"),
    (27.0, 36.0, 80.0, 97.0, 6.5, "Himalayas"),
    (26.0, 38.0, 70.0, 82.0, 4.0, "Hindu Kush"),
    (44.0, 48.5, 5.0, 16.0, 5.0, "Alps"),
    (35.0, 55.0, -125.0, -100.0, 5.5, "Rocky Mountains"),
    (38.0, 44.0, 39.0, 50.0, 4.5, "Caucasus"),
    (-55.0, -15.0, -75.0, -65.0, 5.0, "Andes"),
]

SCORE_LABELS = [
    (0, 1.5, "Glass Smooth", "smooth", "#3dd68c"),
    (1.5, 3, "Very Smooth", "smooth", "#3dd68c"),
    (3, 4.5, "Mostly Smooth", "smooth", "#3dd68c"),
    (4.5, 6, "Light Chop", "light", "#f0c060"),
    (6, 7.5, "Moderate", "moderate", "#f07060"),
    (7.5, 9, "Significant", "significant", "#e03030"),
    (9, 11, "Severe", "severe", "#b00000"),
]

ANALOGIES = {
    "smooth": "Like sitting in a parked car.",
    "light": "Like driving on a slightly uneven road.",
    "moderate": "Like driving on a cobblestone street — uncomfortable but manageable.",
    "significant": "Drinks will slide. Crew will be seated.",
    "severe": "Extremely rare. Less than 0.01% of flights.",
}

TIPS = {
    "smooth": [
        {"icon": "😴", "text": "Great flight for sleeping. Noise-cancelling headphones and a neck pillow."},
        {"icon": "🎯", "text": "Even on smooth flights, keeping your seatbelt loosely fastened is always smart."},
    ],
    "light": [
        {"icon": "⏱️", "text": "Any rough patches are brief and predictable. Knowing they're coming is the best preparation."},
        {"icon": "🫁", "text": "Box breathing works: 4 counts in, hold 4, out 4, hold 4."},
        {"icon": "🎧", "text": "Set up your playlist before takeoff so you never need to reach up during bumpy sections."},
    ],
    "moderate": [
        {"icon": "💺", "text": "Seatbelt on and snug from the moment you sit. Don't wait for the sign."},
        {"icon": "📊", "text": "Moderate turbulence is uncomfortable but poses no structural risk. Crews fly routes like this daily."},
        {"icon": "🎧", "text": "Choose your longest podcast before boarding — distraction is the most effective tool."},
        {"icon": "📋", "text": "Watch the crew. If they're calm, you can be too."},
    ],
    "significant": [
        {"icon": "💺", "text": "Stay seated and belted throughout."},
        {"icon": "🫁", "text": "Focus on breathing. Long exhales reduce anxiety significantly."},
    ],
    "severe": [
        {"icon": "💺", "text": "Severe turbulence is extremely rare — below 0.01% of flights."},
        {"icon": "🫁", "text": "Focus only on your breathing. Long, slow exhales."},
    ],
}

def haversine_km(p1, p2):
    R = 6371.0
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def interpolate_waypoints(origin, destination, n=8):
    waypoints = []
    for i in range(n):
        t = i / (n - 1)
        lat = origin[0] + t * (destination[0] - origin[0])
        lon = origin[1] + t * (destination[1] - origin[1])
        waypoints.append((round(lat, 4), round(lon, 4)))
    return waypoints

def get_terrain(lat, lon):
    for zone in MOUNTAIN_ZONES:
        if zone[0] <= lat <= zone[1] and zone[2] <= lon <= zone[3]:
            return zone[4]
    return 0.0

def get_aircraft(code):
    return AIRCRAFT_DB.get(code.upper(), {"name": "Commercial Aircraft", "type": "narrow_body", "alt": 35000})

def get_label(score):
    for lo, hi, label, cls, color in SCORE_LABELS:
        if lo <= score < hi:
            return label, cls, color
    return "Severe", "severe", "#b00000"

def get_weather(lat, lon, alt_ft, dep_time):
    level = 200 if alt_ft >= 36000 else (250 if alt_ft >= 30000 else 300)
    try:
        params = {
            "latitude": round(lat, 3),
            "longitude": round(lon, 3),
            "hourly": [f"wind_speed_{level}hPa", "cape", "lifted_index"],
            "forecast_days": 2,
            "timezone": "UTC"
        }
        r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=6)
        r.raise_for_status()
        data = r.json()
        times = data["hourly"]["time"]
        target = dep_time.strftime("%Y-%m-%dT%H:00")
        idx = next((i for i, t in enumerate(times) if t == target), 0)
        wind_ms = data["hourly"].get(f"wind_speed_{level}hPa", [15])[idx] or 15
        return {
            "wind_kts": round(wind_ms * 1.94384, 1),
            "cape": data["hourly"].get("cape", [0])[idx] or 0,
            "li": data["hourly"].get("lifted_index", [2])[idx] or 2,
        }
    except:
        return {"wind_kts": 30, "cape": 0, "li": 2}

def score_segment(w1, w2, terrain):
    shear = abs(w1["wind_kts"] - w2["wind_kts"])
    shear_s = 0 if shear < 10 else (2 if shear < 20 else (4 if shear < 30 else (6 if shear < 45 else 8)))
    wind = w1["wind_kts"]
    jet_s = 0 if wind < 30 else (1.5 if wind < 50 else (3.5 if wind < 70 else (5.5 if wind < 90 else (7.5 if wind < 110 else 9))))
    cape = w1["cape"]
    cape_s = 0 if cape < 100 else (1.5 if cape < 300 else (3.5 if cape < 600 else (5.5 if cape < 1000 else (7.5 if cape < 2000 else 9))))
    li = w1["li"]
    li_s = 0 if li > 2 else (1 if li > 0 else (3 if li > -2 else (5 if li > -4 else 7.5)))
    raw = shear_s*0.30 + jet_s*0.30 + cape_s*0.20 + li_s*0.10 + terrain*0.10
    return round(min(10.0, raw), 1)

def get_flight(flight_number):
    if AVIATIONSTACK_KEY:
        try:
            r = requests.get(
                "http://api.aviationstack.com/v1/flights",
                params={"access_key": AVIATIONSTACK_KEY, "flight_iata": flight_number, "limit": 1},
                timeout=8
            )
            data = r.json()
            if data.get("data"):
                raw = data["data"][0]
                dep = raw["departure"]["iata"]
                arr = raw["arrival"]["iata"]
                if dep in AIRPORT_COORDS and arr in AIRPORT_COORDS:
                    ac_code = raw.get("aircraft", {}).get("iata", "A320") or "A320"
                    ac = get_aircraft(ac_code)
                    dep_a = AIRPORT_COORDS[dep]
                    arr_a = AIRPORT_COORDS[arr]
                    wps = interpolate_waypoints((dep_a["lat"], dep_a["lon"]), (arr_a["lat"], arr_a["lon"]))
                    dep_time_str = raw["departure"].get("scheduled", "") or ""
                    try:
                        dep_time = datetime.fromisoformat(dep_time_str)
                    except:
                        dep_time = datetime.now(timezone.utc)
                    total_km = sum(haversine_km(wps[i], wps[i+1]) for i in range(len(wps)-1))
                    dur = int((total_km / 850) * 60) + 30
                    return {
                        "number": raw["flight"]["iata"],
                        "airline": raw["airline"]["name"],
                        "from_iata": dep, "from_city": dep_a["name"],
                        "to_iata": arr, "to_city": arr_a["name"],
                        "dep_time": dep_time,
                        "dep_time_str": dep_time.strftime("%H:%M"),
                        "aircraft_name": ac["name"],
                        "aircraft_type": ac["type"],
                        "altitude": ac["alt"],
                        "waypoints": wps,
                        "duration": dur,
                        "status": raw.get("flight_status", "scheduled"),
                    }
        except Exception as e:
            print(f"AviationStack error: {e}")

    if flight_number not in MOCK_FLIGHTS:
        return None
    dep, arr, dep_time_str, ac_code, airline = MOCK_FLIGHTS[flight_number]
    dep_a = AIRPORT_COORDS[dep]
    arr_a = AIRPORT_COORDS[arr]
    ac = get_aircraft(ac_code)
    wps = interpolate_waypoints((dep_a["lat"], dep_a["lon"]), (arr_a["lat"], arr_a["lon"]))
    total_km = sum(haversine_km(wps[i], wps[i+1]) for i in range(len(wps)-1))
    dur = int((total_km / 850) * 60) + 30
    now = datetime.now(timezone.utc)
    dep_time = now.replace(hour=int(dep_time_str.split(":")[0]), minute=int(dep_time_str.split(":")[1]), second=0, microsecond=0)
    return {
        "number": flight_number,
        "airline": airline,
        "from_iata": dep, "from_city": dep_a["name"],
        "to_iata": arr, "to_city": arr_a["name"],
        "dep_time": dep_time,
        "dep_time_str": dep_time_str,
        "aircraft_name": ac["name"],
        "aircraft_type": ac["type"],
        "altitude": ac["alt"],
        "waypoints": wps,
        "duration": dur,
        "status": "scheduled",
    }

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})

@app.route("/api/flight/<flight_number>")
def forecast(flight_number):
    flight_number = flight_number.upper().strip()
    f = get_flight(flight_number)
    if not f:
        return jsonify({"error": "Flight not found"}), 404

    wps = f["waypoints"]
    alt = f["altitude"]
    dep_time = f["dep_time"]
    dampening = 0.78 if f["aircraft_type"] == "wide_body" else (1.12 if f["aircraft_type"] == "regional" else 1.0)

    weather = [get_weather(lat, lon, alt, dep_time) for lat, lon in wps]

    segments = []
    total_km = sum(haversine_km(wps[i], wps[i+1]) for i in range(len(wps)-1))

    for i in range(len(wps)-1):
        w1 = weather[i]
        w2 = weather[i+1] if i+1 < len(weather) else w1
        mid_lat = (wps[i][0] + wps[i+1][0]) / 2
        mid_lon = (wps[i][1] + wps[i+1][1]) / 2
        dist = haversine_km(wps[i], wps[i+1])
        if i == 0:
    dur = 20
elif i == len(wps)-2:
    dur = 20
else:
    cruise_minutes = max(10, f["duration"] - 40)
    cruise_segments = max(1, len(wps) - 3)
    dur = max(8, int(cruise_minutes / cruise_segments))
        terrain = get_terrain(mid_lat, mid_lon)
        raw = score_segment(w1, w2, terrain)
        score = round(min(10.0, raw * dampening), 1)
        phase = "departure" if i == 0 else ("arrival" if i == len(wps)-2 else "cruise")
        label, cls, color = get_label(score)

        if phase == "departure":
            name = f"Departure from {f['from_city']}"
        elif phase == "arrival":
            name = f"Descent into {f['to_city']}"
        else:
            if terrain > 0:
                name = "⚡ Mountain wave region" if score >= 4.5 else "Mountain region"
            elif score >= 4.5:
                name = "⚡ Jet stream corridor"
            else:
                name = "En route cruise"

        segments.append({
            "index": i, "name": name,
            "detail": f"{'Smooth, stable air' if score < 2 else ('Jet stream winds' if w1['wind_kts'] > 60 else ('Mountain wave turbulence' if terrain > 0 else 'Mixed atmospheric factors'))} · {dur} min",
            "score": score, "label": label, "class": cls, "color": color,
            "duration_min": dur, "phase": phase,
        })

    scores = [s["score"] for s in segments]
    weights = [0.5 if s["phase"] in ("departure","arrival") else 1.0 for s in segments]
    avg = sum(s*w for s,w in zip(scores,weights)) / sum(weights)
    overall = round(avg, 1)
    max_score = max(scores)
    o_label, o_cls, o_color = get_label(overall)

    rough = [s for s in segments if s["score"] >= 4.5]
    if not rough:
        desc = f"Expect a comfortable ride from {f['from_city']} to {f['to_city']}. Weather conditions are calm with no significant disruptions forecast. You can relax."
    else:
        total_rough = sum(s["duration_min"] for s in rough)
        m_label, _, _ = get_label(max_score)
        desc = f"Mostly smooth with {len(rough)} patch{'es' if len(rough)>1 else ''} of {m_label.lower()} turbulence — approximately {total_rough} minutes total. {ANALOGIES[o_cls]}"

    tips = TIPS.get(o_cls, TIPS["light"])[:]
    if f["aircraft_type"] == "wide_body":
        tips.insert(0, {"icon": "✈️", "text": f"You're on a {f['aircraft_name']}. Wide-body aircraft absorb turbulence significantly better than narrow-body jets."})
    tips = tips[:4]

    factors_raw = {}
    for i, seg_w in enumerate(weather[:-1]):
        factors_raw["jet_stream"] = max(factors_raw.get("jet_stream",0), min(10, seg_w["wind_kts"]/13))
        factors_raw["convective"] = max(factors_raw.get("convective",0), min(10, seg_w["cape"]/300))
        factors_raw["instability"] = max(factors_raw.get("instability",0), max(0, min(10, (2-seg_w["li"])*2)))
    for seg in segments:
        if "Mountain" in seg["name"] or "mountain" in seg["detail"]:
            factors_raw["terrain"] = max(factors_raw.get("terrain",0), 5.5)

    factor_meta = {
        "jet_stream": {"icon":"🌬️","name":"Jet Stream"},
        "convective": {"icon":"⛈️","name":"Convective Activity"},
        "instability": {"icon":"📊","name":"Atmospheric Instability"},
        "terrain": {"icon":"🏔️","name":"Mountain Waves"},
    }
    factors = []
    for k, v in sorted(factors_raw.items(), key=lambda x: -x[1]):
        fl, fc, fcol = get_label(v)
        factors.append({"icon": factor_meta[k]["icon"], "name": factor_meta[k]["name"], "value": round(v,1), "pct": round(v*10), "label": fl, "color": fcol})
    factors = factors[:4]

    phases = []
    elapsed = 0
    for seg in segments:
        pct = int((elapsed / f["duration"]) * 100) if f["duration"] else 0
        ni = seg["index"] + 1
        if ni < len(segments):
            ns = segments[ni]
            next_text = f"⚡ {ns['name']} in ~{ns['duration_min']} min — stay seated" if ns["score"] >= 4.5 else f"Smooth air ahead for ~{ns['duration_min']} min"
            show_cd = ns["score"] >= 4.5
        else:
            next_text = "Approaching destination — final descent"
            show_cd = False
        phase = {"pct": pct, "phase": seg["name"], "next": next_text, "score": seg["score"], "countdown": show_cd}
        if show_cd:
            ns = segments[ni]
            fl2, _, _ = get_label(ns["score"])
            phase.update({"cb_title": f"{fl2} ahead", "cb_sub": f"{ns['name']} · seatbelt on", "cb_mins": seg["duration_min"]})
        phases.append(phase)
        elapsed += seg["duration_min"]

    h = f["duration"] // 60
    m = f["duration"] % 60
    dur_str = f"{h}h {m}m" if h and m else (f"{h}h" if h else f"{m}m")

    return jsonify({
        "flight": {
            "number": f["number"], "airline": f["airline"],
            "from_iata": f["from_iata"], "from_city": f["from_city"],
            "to_iata": f["to_iata"], "to_city": f["to_city"],
            "departure_time": f["dep_time_str"],
            "aircraft": f["aircraft_name"],
            "altitude": f"{f['altitude']:,} ft",
            "duration": dur_str, "status": f["status"],
        },
        "forecast": {
            "score": overall, "max_score": max_score,
            "verdict": o_label, "verdict_class": o_cls, "color": o_color,
            "description": desc, "analogy": ANALOGIES[o_cls],
        },
        "segments": segments,
        "factors": factors,
        "tips": tips,
        "phases": phases,
        "data_sources": ["NOAA Aviation Weather", "Open-Meteo", "AviationStack"],
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
