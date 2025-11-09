import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# ✅ Force load the .env file by specifying absolute path
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path)

# Check if the key is now found
print("DEBUG → API_KEY:", os.getenv("API_KEY"))
print("DEBUG → WEATHER_API_URL:", os.getenv("WEATHER_API_URL"))

app = Flask(__name__)
application = app  # for Vercel compatibility

# ✅ Load environment variables
WEATHER_API_KEY = os.getenv("API_KEY")
WEATHER_BASE_URL = os.getenv("WEATHER_API_URL") or "https://api.weatherapi.com/v1"

if not WEATHER_API_KEY:
    print("⚠️ ERROR: API_KEY not found. Please set it in your .env or environment variables.")
else:
    print("✅ API_KEY loaded successfully.")

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/weather')
def get_weather():
    try:
        city = request.args.get('city')
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        day_index = int(request.args.get('day', 0))  # support forecast offset

        # Determine query string
        if city:
            query = city
        elif lat and lon:
            query = f"{lat},{lon}"
        else:
            return jsonify({"success": False, "message": "City or coordinates required."}), 400

        # ✅ Call WeatherAPI
        forecast_url = f"{WEATHER_BASE_URL}/forecast.json"
        params = {
            "key": WEATHER_API_KEY,
            "q": query,
            "days": 5,
            "aqi": "yes",
            "alerts": "no"
        }

        response = requests.get(forecast_url, params=params)
        data = response.json()

        # Handle API errors cleanly
        if "error" in data:
            msg = data["error"].get("message", "Invalid API key or request.")
            return jsonify({"success": False, "message": msg}), 404

        current = data["current"]
        location = data["location"]
        forecast_days = data["forecast"]["forecastday"]

        # Use current weather or forecasted day
        selected_day = forecast_days[min(day_index, len(forecast_days)-1)]
        day_info = selected_day["day"]

        astronomy_url = f"{WEATHER_BASE_URL}/astronomy.json"
        astronomy_params = {"key": WEATHER_API_KEY, "q": query, "dt": selected_day["date"]}
        astronomy_resp = requests.get(astronomy_url, params=astronomy_params).json()
        astronomy = astronomy_resp.get("astronomy", {}).get("astro", {})

        air_quality = current.get("air_quality", {})
        aqi_us = air_quality.get("us-epa-index", 0)

        aqi_levels = {
            1: "Good 😊",
            2: "Moderate 😐",
            3: "Unhealthy for Sensitive Groups 😷",
            4: "Unhealthy 🤒",
            5: "Very Unhealthy 😨",
            6: "Hazardous ☠️"
        }

        return jsonify({
            "success": True,
            "city_name": location["name"],
            "country": location["country"],
            "localtime": location["localtime"],
            "temperature": round(day_info["avgtemp_c"]),
            "humidity": current["humidity"],
            "wind_speed": current["wind_kph"],
            "description": day_info["condition"]["text"],
            "lat": location["lat"],
            "lon": location["lon"],
            "sunrise": astronomy.get("sunrise"),
            "sunset": astronomy.get("sunset"),
            "aqi_index": aqi_us,
            "aqi_status": aqi_levels.get(aqi_us, "Unknown"),
            "forecast": [
                {
                    "date": day["date"],
                    "max_temp": day["day"]["maxtemp_c"],
                    "min_temp": day["day"]["mintemp_c"],
                    "condition": day["day"]["condition"]["text"],
                    "icon": day["day"]["condition"]["icon"]
                } for day in forecast_days
            ]
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {e}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
