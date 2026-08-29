import pandas as pd
from datetime import datetime
from extract import extract_data as ex

def transform_data(data):
    """
      I will convert period to datetime 
    """
    data['period'] = pd.to_datetime(data['period'], errors='coerce').dt.year
    data = data.rename(columns={
    'area-name': 'area_name',
    'product-name': 'product_name',
    'process-name': 'process_name',
    'series-description': 'series_description'
})


    return data


if __name__ == '__main__':
    data = ex()
    df = transform_data(data)
    print(df.info())