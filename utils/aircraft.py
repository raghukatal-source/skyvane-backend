AIRCRAFT_DB = {
    "A319": {"name": "Airbus A319",          "type": "narrow_body", "cruise_altitude_ft": 35000},
    "A320": {"name": "Airbus A320",          "type": "narrow_body", "cruise_altitude_ft": 35000},
    "A321": {"name": "Airbus A321",          "type": "narrow_body", "cruise_altitude_ft": 35000},
    "A20N": {"name": "Airbus A320neo",       "type": "narrow_body", "cruise_altitude_ft": 36000},
    "A21N": {"name": "Airbus A321neo",       "type": "narrow_body", "cruise_altitude_ft": 36000},
    "B737": {"name": "Boeing 737",           "type": "narrow_body", "cruise_altitude_ft": 35000},
    "B738": {"name": "Boeing 737-800",       "type": "narrow_body", "cruise_altitude_ft": 35000},
    "B739": {"name": "Boeing 737-900",       "type": "narrow_body", "cruise_altitude_ft": 35000},
    "B38M": {"name": "Boeing 737 MAX 8",     "type": "narrow_body", "cruise_altitude_ft": 36000},
    "A332": {"name": "Airbus A330-200",      "type": "wide_body",   "cruise_altitude_ft": 39000},
    "A333": {"name": "Airbus A330-300",      "type": "wide_body",   "cruise_altitude_ft": 39000},
    "A350": {"name": "Airbus A350",          "type": "wide_body",   "cruise_altitude_ft": 41000},
    "A359": {"name": "Airbus A350-900",      "type": "wide_body",   "cruise_altitude_ft": 41000},
    "A380": {"name": "Airbus A380",          "type": "wide_body",   "cruise_altitude_ft": 40000},
    "B763": {"name": "Boeing 767-300",       "type": "wide_body",   "cruise_altitude_ft": 39000},
    "B772": {"name": "Boeing 777-200",       "type": "wide_body",   "cruise_altitude_ft": 40000},
    "B773": {"name": "Boeing 777-300",       "type": "wide_body",   "cruise_altitude_ft": 40000},
    "B77W": {"name": "Boeing 777-300ER",     "type": "wide_body",   "cruise_altitude_ft": 40000},
    "B787": {"name": "Boeing 787",           "type": "wide_body",   "cruise_altitude_ft": 40000},
    "B788": {"name": "Boeing 787-8",         "type": "wide_body",   "cruise_altitude_ft": 40000},
    "B789": {"name": "Boeing 787-9 Dreamliner","type": "wide_body", "cruise_altitude_ft": 40000},
    "ATR7": {"name": "ATR 72",               "type": "regional",    "cruise_altitude_ft": 25000},
    "AT75": {"name": "ATR 72-500",           "type": "regional",    "cruise_altitude_ft": 25000},
    "CRJ2": {"name": "Bombardier CRJ200",    "type": "regional",    "cruise_altitude_ft": 35000},
    "E190": {"name": "Embraer E190",         "type": "narrow_body", "cruise_altitude_ft": 35000},
    "E195": {"name": "Embraer E195",         "type": "narrow_body", "cruise_altitude_ft": 35000},
}

DEFAULT_PROFILE = {"name": "Commercial Aircraft", "type": "narrow_body", "cruise_altitude_ft": 35000}

def get_aircraft_profile(iata_code):
    return AIRCRAFT_DB.get(iata_code.upper(), DEFAULT_PROFILE)
