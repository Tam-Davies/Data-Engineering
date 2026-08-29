import requests
import pandas as pd


headers = {'accept': 'application/geo+json',
           'User-Agent': '(yourapp.com, your.email@example.com)'}

def extract(regions):
    params = {"area": regions} 
    response = requests.get('https://api.weather.gov/alerts/active', headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    df = pd.json_normalize(data['features'])
    return df

if __name__ == '__main__':
    extracts = extract("NY,CA,TX")
    print(extracts.info())