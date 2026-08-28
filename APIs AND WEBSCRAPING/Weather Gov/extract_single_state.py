import requests
import pandas as pd

url = 'https://api.weather.gov/alerts/active/area/'

headers = {'accept': 'application/geo+json',
           'User-Agent': '(yourapp.com, your.email@example.com)'}

def extract(region):

     response = requests.get(f'{url}{region}', headers=headers)
     response.raise_for_status()
     data = response.json()
    #  print(data.keys())
     print(len(data['features']))   # how many alerts, if any
     df = pd.json_normalize(data['features'])
     return df


if __name__ == '__main__':
     extracts = extract('NY')
     print(extracts)