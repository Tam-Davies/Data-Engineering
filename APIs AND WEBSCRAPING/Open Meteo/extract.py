import requests
import pandas as pd

# url = "https://api.open-meteo.com/v1/forecast"
url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
 

def extract():
    params = {
            "latitude": 52.52,
            "longitude": 13.41,
            "daily": ["sunrise", "rain_sum"],
            "hourly": ["temperature_2m", "rain", "showers", "precipitation"],
            "current": ["temperature_2m", "is_day", "rain"],
            "timezone": "America/New_York",
            "past_days": 92,
        }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    lat = data['latitude']
    lon = data['longitude']

    df_hourly = pd.DataFrame(data['hourly'])
    df_hourly['latitude'] = lat
    df_hourly['longitude'] = lon

    df_daily = pd.DataFrame(data['daily'])
    df_daily['latitude'] = lat
    df_daily['longitude'] = lon

    df_current = pd.DataFrame([data['current']])
    df_current['latitude'] = lat
    df_current['longitude'] = lon

    return df_hourly, df_daily, df_current

if __name__ == '__main__':
    hourly, daily, current = extract()
    print(hourly)
    print(daily)
    print(current)