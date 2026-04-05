from flask import Flask, jsonify, request
from flask_cors import CORS
import os

from services.flight_lookup import get_flight_info
from services.weather import get_route_weather
from services.turbulence_engine import score_route
from services.translator import translate_forecast

app = Flask(__name__)
CORS(app)

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})

@app.route("/api/flight/<flight_number>")
def get_forecast(flight_number):
    flight_number = flight_number.upper().strip()
    date = request.args.get("date", None)
    flight = get_flight_info(flight_number, date)
    if not flight:
        return jsonify({"error": "Flight not found", "code": "FLIGHT_NOT_FOUND"}), 404
    weather = get_route_weather(
        waypoints=flight["waypoints"],
        altitude_ft=flight["cruise_altitude_ft"],
        departure_time=flight["departure_time"]
    )
    segments = score_route(
        waypoints=flight["waypoints"],
        weather=weather,
        aircraft_type=flight["aircraft_type"]
    )
    forecast = translate_forecast(flight=flight, segments=segments)
    return jsonify(forecast)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
