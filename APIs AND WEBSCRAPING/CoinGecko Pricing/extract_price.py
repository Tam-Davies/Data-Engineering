import os
from dotenv import load_dotenv
import pandas as pd
import requests

load_dotenv()
api_key = os.getenv('API_KEY_ACCESS')
# base_url = 'https://api.coingecko.com/api/v3/simple'

headers = {'x-cg-demo-api-key': api_key,
           "accept": "application/json"}


def extract(per_page=100, page=1):
    params = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": per_page,
    "page": page,
    "sparkline": "false"
     }
    response = requests.get('https://api.coingecko.com/api/v3/coins/markets',
                                headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)
    return df
   

if __name__ == '__main__':
    df = extract()
    print(df.shape)
    print(df.head())
    df.to_csv('CoinGecko Pricing/coin_prices.csv', index=False)