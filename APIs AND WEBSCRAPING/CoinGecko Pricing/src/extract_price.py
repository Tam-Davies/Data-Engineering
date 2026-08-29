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
    cols_to_keep = ['symbol', 'name', 'current_price', 'market_cap',
                 'market_cap_rank', 'total_volume', 'last_updated']
    return df[cols_to_keep]
   

# if __name__ == '__main__':
#     df = extract()
#     print(df.shape)
#     print(df.head())
    