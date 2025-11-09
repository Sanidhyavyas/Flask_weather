import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
application = app

print("DEBUG → API_KEY:", os.getenv("API_KEY"))

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

if not WEATHER_API_KEY:
    print("⚠️ WARNING: WEATHER_API_KEY not found! Please set it in environment variables.")

WEATHER_BASE_URL = "https://api.weatherapi.com/v1"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/weather')
def get_weather():
    try:
        city = request.args.get('city')
        lat = request.args.get('lat')
        lon = request.args.get('lon')

        if city:
            query = city
        elif lat and lon:
            query = f"{lat},{lon}"
        else:
            return jsonify({"success": False, "message": "City or coordinates required."}), 400

        # Build the forecast URL
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

        if "error" in data:
            return jsonify({"success": False, "message": data["error"]["message"]}), 404

        # Astronomy data
        astronomy_url = f"{WEATHER_BASE_URL}/astronomy.json"
        astronomy_params = {"key": WEATHER_API_KEY, "q": query}
        astronomy_resp = requests.get(astronomy_url, params=astronomy_params).json()
        astronomy = astronomy_resp.get("astronomy", {}).get("astro", {})

        current = data["current"]
        location = data["location"]
        forecast_days = data["forecast"]["forecastday"]

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
            "temperature": round(current["temp_c"]),
            "humidity": current["humidity"],
            "wind_speed": current["wind_kph"],
            "description": current["condition"]["text"],
            "lat": location["lat"],
            "lon": location["lon"],
            "sunrise": astronomy.get("sunrise"),
            "sunset": astronomy.get("sunset"),
            "aqi_index": aqi_us,
            "aqi_status": aqi_levels.get(aqi_us, "Unknown"),
            "pollutants": {
                "co": round(air_quality.get("co", 0), 2),
                "no2": round(air_quality.get("no2", 0), 2),
                "o3": round(air_quality.get("o3", 0), 2),
                "pm2_5": round(air_quality.get("pm2_5", 0), 2),
                "pm10": round(air_quality.get("pm10", 0), 2),
                "so2": round(air_quality.get("so2", 0), 2)
            },
            "forecast": [
                {
                    "date": day["date"],
                    "max_temp": day["day"]["maxtemp_c"],
                    "min_temp": day["day"]["mintemp_c"],
                    "condition": day["day"]["condition"]["text"],
                    "icon": day["day"]["condition"]["icon"],
                    "hourly": [
                        {
                            "time": hour["time"].split(" ")[1],
                            "temp": hour["temp_c"],
                            "condition": hour["condition"]["text"],
                            "icon": hour["condition"]["icon"]
                        }
                        for hour in day["hour"][::3]
                    ]
                } for day in forecast_days
            ]
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {e}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
