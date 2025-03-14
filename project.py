import requests
import json
import schedule
import time
import folium
import plotly.graph_objects as go
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource
import matplotlib.pyplot as plt
import seaborn as sns
API_KEY = "22ba1a51558faee7656eb9a1c55f176a"
# Function to fetch current weather data
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    
    if response.status_code == 200:
        return {
            "city": city,
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "weather": data["weather"][0]["description"],
            "lat": data["coord"]["lat"],
            "lon": data["coord"]["lon"]
        }
    else:
        print(f"Error fetching weather for {city}: {data['message']}")
        return None

# Function to fetch weather forecast
def get_forecast(city):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200:
        forecast_data = []
        for entry in data["list"]:
            forecast_data.append({
                "datetime": entry["dt_txt"],
                "temperature": entry["main"]["temp"],
                "humidity": entry["main"]["humidity"]
            })
        return forecast_data
    else:
        print(f"Error fetching forecast for {city}: {data['message']}")
        return None

# Function to display weather data using Matplotlib and Seaborn
def plot_forecast(city):
    forecast_data = get_forecast(city)
    if not forecast_data:
        return
    
    dates = [entry["datetime"] for entry in forecast_data]
    temps = [entry["temperature"] for entry in forecast_data]
    
    plt.figure(figsize=(10, 5))
    sns.lineplot(x=dates, y=temps, marker='o')
    plt.xticks(rotation=45)
    plt.xlabel("Date and Time")
    plt.ylabel("Temperature (°C)")
    plt.title(f"Temperature Forecast for {city}")
    plt.grid()
    plt.show()

# Function to display weather data on an interactive map
def create_map(cities_data):
    weather_map = folium.Map(location=[0, 0], zoom_start=2)
    
    for data in cities_data:
        if data:
            folium.Marker(
                location=[data["lat"], data["lon"]],
                popup=f"{data['city']}: {data['temperature']}°C, {data['weather']}",
                tooltip=data['city']
            ).add_to(weather_map)
    
    weather_map.save("weather_map.html")
    print("Map saved as weather_map.html. Open it in a browser.")

# Function to visualize weather trends using Plotly
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

# Function to visualize humidity levels using Bokeh
def plot_humidity_bokeh(cities_data):
    cities = [data["city"] for data in cities_data if data]
    humidities = [data["humidity"] for data in cities_data if data]
    
    source = ColumnDataSource(data=dict(cities=cities, humidities=humidities))
    
    p = figure(x_range=cities, height=400, title="Humidity Levels",
               toolbar_location=None, tools="")

    p.vbar(x='cities', top='humidities', width=0.5, source=source, legend_field="cities")
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.legend.title = "Cities"
    
    show(p)

# Function to update and display live weather
def live_weather_update(cities):
    cities_data = [get_weather(city) for city in cities]
    
    print("\nLive Weather Updates:")
    for data in cities_data:
        if data:
            print(f"{data['city']}: {data['temperature']}°C, {data['weather']}, Humidity: {data['humidity']}%")
    
    create_map(cities_data)
    plot_weather_trends(cities_data)
    plot_humidity_bokeh(cities_data)

# Scheduling live updates every 10 minutes
def schedule_weather_updates(cities):
    schedule.every(10).minutes.do(live_weather_update, cities=cities)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

# Main function
if __name__ == "__main__":
    cities = ["New York", "London", "Tokyo", "Delhi"]
    
    # Initial weather update
    live_weather_update(cities)
    
    # Fetch and plot forecast for a specific city
    city_for_forecast = "New York"
    plot_forecast(city_for_forecast)
    
    # Start live updates
    schedule_weather_updates(cities)
