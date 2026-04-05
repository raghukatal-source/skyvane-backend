from datetime import datetime
from services.turbulence_engine import get_overall_score

SCORE_LABELS = [
    (0,   1.5, "Glass Smooth",    "smooth"),
    (1.5, 3,   "Very Smooth",     "smooth"),
    (3,   4.5, "Mostly Smooth",   "smooth"),
    (4.5, 6,   "Light Chop",      "light"),
    (6,   7.5, "Moderate",        "moderate"),
    (7.5, 9,   "Significant",     "significant"),
    (9,   10,  "Severe",          "severe"),
]

SCORE_COLORS = {
    "smooth":      "#3dd68c",
    "light":       "#f0c060",
    "moderate":    "#f07060",
    "significant": "#e03030",
    "severe":      "#b00000",
}

SCORE_ANALOGIES = {
    "smooth":      "Like sitting in a parked car.",
    "light":       "Like driving on a slightly uneven road.",
    "moderate":    "Like driving on a cobblestone street — uncomfortable but manageable.",
    "significant": "Drinks will slide. Crew will be seated. This is rare.",
    "severe":      "Extremely rare. Less than 0.01% of flights.",
}

TIPS_LIBRARY = {
    "smooth": [
        {"icon": "😴", "text": "Great flight for sleeping. Noise-cancelling headphones and a neck pillow."},
        {"icon": "🎯", "text": "Even on smooth flights, keeping your seatbelt loosely fastened is always smart."},
        {"icon": "📱", "text": "Save this forecast and come back to it mid-flight if you need reassurance."},
    ],
    "light": [
        {"icon": "⏱️", "text": "Any rough patches are brief and predictable. Knowing they're coming is the best preparation."},
        {"icon": "🫁", "text": "Box breathing works: 4 counts in, hold 4, out 4, hold 4. Try it before boarding."},
        {"icon": "🎧", "text": "Set up your playlist before takeoff so you never need to reach up during bumpy sections."},
    ],
    "moderate": [
        {"icon": "💺", "text": "Seatbelt on and snug from the moment you sit. Don't wait for the sign."},
        {"icon": "📊", "text": "Moderate turbulence is uncomfortable but poses no structural risk. Crews fly routes like this daily."},
        {"icon": "🎧", "text": "Choose your longest podcast before boarding — distraction is the most effective tool."},
        {"icon": "📋", "text": "Watch the crew. If they're calm, you can be too. They've done this hundreds of times."},
    ],
    "significant": [
        {"icon": "💺", "text": "Stay seated and belted throughout. This is serious advice, not precaution."},
        {"icon": "📊", "text": "Significant turbulence is rare. The aircraft is designed to handle far worse than this."},
        {"icon": "🫁", "text": "Focus on breathing. Long exhales activate the parasympathetic nervous system and reduce anxiety."},
    ],
    "severe": [
        {"icon": "💺", "text": "Severe turbulence is extremely rare — below 0.01% of flights."},
        {"icon": "🫁", "text": "Focus only on your breathing. Nothing else. Long, slow exhales."},
    ]
}

def translate_forecast(flight, segments):
    overall  = get_overall_score(segments)
    score    = overall["score"]
    max_sc   = overall["max_score"]
    verdict_label, verdict_class = _get_label(score)
    analogy  = SCORE_ANALOGIES[verdict_class]
    translated_segments = [_translate_segment(seg, flight) for seg in segments]
    factors  = _build_factors(segments)
    tips     = _build_tips(score, flight["aircraft_type"], flight["aircraft_name"])
    phases   = _build_inflight_phases(translated_segments, flight["duration_minutes"])
    desc     = _build_description(score, max_sc, translated_segments, flight)
    return {
        "flight": {
            "number":         flight["flight_number"],
            "airline":        flight["airline"],
            "from_iata":      flight["from_iata"],
            "from_city":      flight["from_city"],
            "to_iata":        flight["to_iata"],
            "to_city":        flight["to_city"],
            "departure_time": flight["departure_time"].strftime("%H:%M"),
            "aircraft":       flight["aircraft_name"],
            "altitude":       f"{flight['cruise_altitude_ft']:,} ft",
            "duration":       _fmt_duration(flight["duration_minutes"]),
            "status":         flight["status"],
        },
        "forecast": {
            "score":          score,
            "max_score":      max_sc,
            "verdict":        verdict_label,
            "verdict_class":  verdict_class,
            "color":          SCORE_COLORS[verdict_class],
            "description":    desc,
            "analogy":        analogy,
        },
        "segments":     translated_segments,
        "factors":      factors,
        "tips":         tips,
        "phases":       phases,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "data_sources": ["NOAA Aviation Weather (PIREPs)", "Open-Meteo (Wind/CAPE)", "AviationStack (Flight data)"]
    }

def _translate_segment(seg, flight):
    score = seg["score"]
    label, cls = _get_label(score)
    name  = _segment_name(seg, flight)
    cause = _segment_cause(seg)
    return {
        "index":        seg["index"],
        "name":         name,
        "detail":       f"{cause} · {seg['duration_min']} min",
        "score":        score,
        "label":        label,
        "class":        cls,
        "color":        SCORE_COLORS[cls],
        "duration_min": seg["duration_min"],
        "phase":        seg["phase"],
        "lat":          seg["mid_lat"],
        "lon":          seg["mid_lon"],
    }

def _segment_name(seg, flight):
    phase = seg["phase"]
    score = seg["score"]
    if phase == "departure":
        prefix = "⚡ " if score >= 4.5 else ""
        return f"{prefix}Departure from {flight['from_city']}"
    if phase == "arrival":
        prefix = "⚡ " if score >= 4.5 else ""
        return f"{prefix}Descent into {flight['to_city']}"
    factors  = seg["factors"]
    dominant = max(factors, key=factors.get)
    prefix   = "⚡ " if score >= 4.5 else ""
    factor_names = {
        "jet_stream":  "Jet stream corridor",
        "convective":  "Convective zone",
        "terrain":     "Mountain wave region",
        "wind_shear":  "Wind shear zone",
        "pirep":       "Reported turbulence zone",
        "instability": "Atmospheric instability",
    }
    return f"{prefix}{factor_names.get(dominant, 'En route cruise')}"

def _segment_cause(seg):
    factors  = seg["factors"]
    score    = seg["score"]
    if score < 2:
        return "Smooth, stable air"
    dominant = max(factors, key=factors.get)
    causes = {
        "jet_stream":  "Jet stream winds",
        "convective":  "Convective activity",
        "terrain":     "Mountain wave turbulence",
        "wind_shear":  "Wind shear gradient",
        "pirep":       "Pilot-reported turbulence",
        "instability": "Unstable atmosphere",
    }
    return causes.get(dominant, "Mixed factors")

def _build_factors(segments):
    factor_totals = {}
    for seg in segments:
        for k, v in seg["factors"].items():
            factor_totals[k] = max(factor_totals.get(k, 0), v)
    factor_meta = {
        "jet_stream":  {"icon": "🌬️", "name": "Jet Stream"},
        "convective":  {"icon": "⛈️", "name": "Convective Activity"},
        "terrain":     {"icon": "🏔️", "name": "Mountain Waves"},
        "wind_shear":  {"icon": "💨", "name": "Wind Shear"},
        "pirep":       {"icon": "✈️", "name": "Pilot Reports"},
        "instability": {"icon": "📊", "name": "Atmospheric Instability"},
    }
    result = []
    for k, val in sorted(factor_totals.items(), key=lambda x: -x[1]):
        meta  = factor_meta.get(k, {"icon": "❓", "name": k})
        label, cls = _get_label(val)
        result.append({
            "key":   k,
            "icon":  meta["icon"],
            "name":  meta["name"],
            "value": round(val, 1),
            "pct":   round(val * 10),
            "label": label,
            "color": SCORE_COLORS[cls],
        })
    return result[:4]

def _build_tips(score, aircraft_type, aircraft_name):
    _, cls = _get_label(score)
    tips   = TIPS_LIBRARY.get(cls, TIPS_LIBRARY["light"])[:]
    if aircraft_type == "wide_body":
        tips.insert(0, {
            "icon": "✈️",
            "text": f"You're on a {aircraft_name}. Wide-body aircraft physically absorb turbulence better — the ride will feel smoother than the score suggests."
        })
    return tips[:4]

def _build_inflight_phases(segments, total_minutes):
    if not segments:
        return []
    phases  = []
    elapsed = 0
    for seg in segments:
        pct   = int((elapsed / total_minutes) * 100) if total_minutes else 0
        score = seg["score"]
        next_idx = seg["index"] + 1
        if next_idx < len(segments):
            next_seg   = segments[next_idx]
            next_score = next_seg["score"]
            if next_score >= 4.5:
                next_text = f"⚡ {next_seg['name']} in ~{next_seg['duration_min']} min — stay seated"
            else:
                next_text = f"Smooth air ahead for ~{next_seg['duration_min']} min"
        else:
            next_text = "Approaching destination — final descent"
        show_countdown = next_idx < len(segments) and segments[next_idx]["score"] >= 4.5
        phase = {
            "pct":       pct,
            "phase":     seg["name"],
            "next":      next_text,
            "score":     score,
            "countdown": show_countdown,
        }
        if show_countdown:
            next_seg = segments[next_idx]
            phase["cb_title"] = f"{next_seg['label']} ahead"
            phase["cb_sub"]   = f"{next_seg['name']} · seatbelt on"
            phase["cb_mins"]  = seg["duration_min"]
        phases.append(phase)
        elapsed += seg["duration_min"]
    return phases

def _build_description(score, max_score, segments, flight):
    _, cls     = _get_label(score)
    rough_segs = [s for s in segments if s["score"] >= 4.5]
    if not rough_segs:
        return (
            f"Expect a comfortable ride from {flight['from_city']} to {flight['to_city']}. "
            f"Weather conditions along the route are calm with no significant disruptions forecast. "
            f"You can relax."
        )
    rough_names     = [s["name"].replace("⚡ ", "") for s in rough_segs]
    rough_label, _  = _get_label(max_score)
    total_rough_min = sum(s["duration_min"] for s in rough_segs)
    desc = (
        f"Mostly smooth with {len(rough_segs)} patch{'es' if len(rough_segs)>1 else ''} "
        f"of {rough_label.lower()} turbulence — approximately {total_rough_min} minutes total. "
    )
    if len(rough_names) == 1:
        desc += f"The bumpy section is over {rough_names[0]}. "
    else:
        desc += f"Rough sections: {', '.join(rough_names)}. "
    desc += SCORE_ANALOGIES[_get_label(max_score)[1]]
    return desc

def _get_label(score):
    for lo, hi, label, cls in SCORE_LABELS:
        if lo <= score < hi:
            return label, cls
    return "Severe", "severe"

def _fmt_duration(minutes):
    h = minutes // 60
    m = minutes % 60
    if h == 0:   return f"{m}m"
    if m == 0:   return f"{h}h"
    return f"{h}h {m}m"
