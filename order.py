import requests
import schedule
import time
import folium
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timezone, timedelta

API_KEY = "d81e366ffb7ff5b0f8f9f7eaf7989c1c"

IST = timezone(timedelta(hours=5, minutes=30))

def convert_to_ist(utc_timestamp):
    utc_time = datetime.fromtimestamp(utc_timestamp, timezone.utc)  
    return utc_time.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")

def get_weather_emoji(description):
    description = description.lower()
    if "cloud" in description:
        return "☁️"
    elif "rain" in description:
        return "🌧️"
    elif "clear" in description:
        return "☀️"
    elif "snow" in description:
        return "❄️"
    elif "storm" in description or "thunder" in description:
        return "⛈️"
    elif "mist" in description or "fog" in description:
        return "🌫️"
    else:
        return "🌡️"

def calculate_wind_chill(temp_c, wind_speed_kmh):
    if temp_c <= 10 and wind_speed_kmh > 4.8:
        return round(13.12 + 0.6215 * temp_c - 11.37 * (wind_speed_kmh ** 0.16) + 0.3965 * temp_c * (wind_speed_kmh ** 0.16), 2)
    return "N/A"

def sunlight_duration(sunrise_str, sunset_str):
    sunrise = datetime.strptime(sunrise_str, "%Y-%m-%d %H:%M:%S")
    sunset = datetime.strptime(sunset_str, "%Y-%m-%d %H:%M:%S")
    return str(sunset - sunrise)

def temp_status(temp):
    if temp < 10:
        return "❄️ Cold"
    elif 10 <= temp <= 25:
        return "😊 Pleasant"
    else:
        return "🔥 Hot"

def log_to_file(data):
    with open("weather_log.txt", "a") as f:
        f.write(f"{datetime.now()}: {data['city']} | {data['temperature']}°C | {data['weather']} | Humidity: {data['humidity']}%\n")

def get_uv_index(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/uvi?appid={API_KEY}&lat={lat}&lon={lon}"
    response = requests.get(url)
    if response.ok:
        data = response.json()
        return data.get("value", "N/A")
    return "N/A"

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    
    if response.status_code == 200:
        return {
            "city": city,
            "temperature": data["main"]["temp"],
            "feels_like": data["main"].get("feels_like"),
            "temp_min": data["main"].get("temp_min"),
            "temp_max": data["main"].get("temp_max"),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "sea_level": data["main"].get("sea_level"),
            "grnd_level": data["main"].get("grnd_level"),
            "weather": data["weather"][0]["description"],
            "wind_speed": data["wind"].get("speed"),
            "wind_deg": data["wind"].get("deg"),
            "gust": data["wind"].get("gust"),
            "rain_1h": data.get("rain", {}).get("1h", 0),
            "clouds": data["clouds"].get("all"),
            "lat": data["coord"]["lat"],
            "lon": data["coord"]["lon"],
            "sunrise": convert_to_ist(data["sys"].get("sunrise")),
            "sunset": convert_to_ist(data["sys"].get("sunset")),
            "visibility": data.get("visibility"),
            "country": data["sys"].get("country"),
        }
    else:
        print(f"Error fetching weather for {city}: {data['message']}")
        return None

def create_map(cities_data):
    avg_lat = sum([data["lat"] for data in cities_data if data]) / len(cities_data)
    avg_lon = sum([data["lon"] for data in cities_data if data]) / len(cities_data)
    weather_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=3)
    
    for data in cities_data:
        if data:
            emoji = get_weather_emoji(data['weather'])
            uv_index = get_uv_index(data['lat'], data['lon'])
            duration = sunlight_duration(data['sunrise'], data['sunset'])
            popup_html = f"""
            <b>City:</b> {data['city']} ({data['country']})<br>
            <b>{emoji} Weather:</b> {data['weather'].capitalize()}, Clouds: {data['clouds']}%<br>
            <b>🌡️ Temperature:</b> {data['temperature']}°C (Feels like: {data['feels_like']}°C)<br>
            <b>🔻 Min / 🔺 Max Temp:</b> {data['temp_min']}°C / {data['temp_max']}°C<br>
            <b>💧 Humidity:</b> {data['humidity']}%<br>
            <b>🧭 Wind:</b> {data['wind_speed']} m/s at {data['wind_deg']}°<br>
            <b>🌧️ Rain (last 1h):</b> {data['rain_1h']} mm<br>
            <b>🎯 Pressure:</b> {data['pressure']} hPa<br>
            <b>☀️ UV Index:</b> {uv_index}<br>
            <b>⏰ Daylight:</b> {duration}<br>
            <b>👀 Visibility:</b> {data.get('visibility', 'N/A')} meters<br>
            <b>🌅 Sunrise:</b> {data['sunrise']} | <b>🌇 Sunset:</b> {data['sunset']}
            """
            folium.Marker(
                location=[data["lat"], data["lon"]],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{emoji} {data['city']}"
            ).add_to(weather_map)
    
    weather_map.save("weather_map.html")
    print("Map saved as weather_map.html. Open it in a browser.")

def plot_weather_trends(cities_data): 
    fig = go.Figure()
    
    for data in cities_data:
        if data:
            fig.add_trace(go.Bar(
                x=[data["city"]],
                y=[data["temperature"]],
                name=f"{data['city']} ({data['weather']})"
            ))
    
    fig.update_layout(title="Temperature Comparison", xaxis_title="City", yaxis_title="Temperature (°C)")
    fig.show()

def plot_humidity(cities_data):
    fig = go.Figure()

    for data in cities_data:
        if data:
            fig.add_trace(go.Bar(
                x=[data["city"]],
                y=[data["humidity"]],
                name=f"{data['city']} ({data['humidity']}%)"
            ))

    fig.update_layout(title="Humidity Comparison", xaxis_title="City", yaxis_title="Humidity (%)")
    fig.show()

def get_forecast(city):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.ok:
        data = response.json()
        return [{
            "datetime": convert_to_ist(entry["dt"]),
            "temperature": entry["main"]["temp"],
            "humidity": entry["main"]["humidity"],
            "rain": entry.get("rain", {}).get("3h", 0),
            "wind_speed": entry["wind"]["speed"]
        } for entry in data["list"]]
    return None

def plot_forecast(city):
    forecast_data = get_forecast(city)
    if not forecast_data:
        return

    dates = [entry["datetime"] for entry in forecast_data]  
    temps = [entry["temperature"] for entry in forecast_data]
    humidity = [entry["humidity"] for entry in forecast_data]

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))  

    sns.lineplot(x=dates, y=temps, marker='o', color='red', ax=axes[0])
    axes[0].set_title(f"Temperature Forecast for {city}")
    axes[0].set_ylabel("Temperature (°C)")
    axes[0].tick_params(axis='x', rotation=45)

    sns.lineplot(x=dates, y=humidity, marker='o', color='blue', ax=axes[1])
    axes[1].set_title(f"Humidity Forecast for {city}")
    axes[1].set_ylabel("Humidity (%)")
    axes[1].tick_params(axis='x', rotation=45)

    fig.tight_layout()  
    plt.show()

def schedule_weather_updates(cities):
    schedule.every(10).minutes.do(live_weather_update, cities=cities)
    while True:
        schedule.run_pending()
        time.sleep(10)

def live_weather_update(cities):
    cities_data = []
    for city in cities:
        data = get_weather(city)
        if data:
            wind_speed_kmh = data['wind_speed'] * 3.6  
            wind_chill = calculate_wind_chill(data['temperature'], wind_speed_kmh)
            status = temp_status(data['temperature'])
            duration = sunlight_duration(data['sunrise'], data['sunset'])
            print(f"{data['city']}: {data['temperature']}°C, {data['weather']} {get_weather_emoji(data['weather'])}, Wind Chill: {wind_chill}°C, {status}, Daylight: {duration}")
            log_to_file(data)
            cities_data.append(data)
    
    create_map(cities_data)
    plot_weather_trends(cities_data)
    plot_humidity(cities_data)

if __name__ == "__main__":
    cities = ["Hyderabad", "Nuzvid", "Delhi", "Vijayawada", "Antarctica", "New York", "London", "Tokyo"]
    city_for_forecast = input("Enter city name for forecast: ")
    if city_for_forecast not in cities:
        cities.append(city_for_forecast)
    live_weather_update(cities)
    plot_forecast(city_for_forecast)
    schedule_weather_updates(cities)