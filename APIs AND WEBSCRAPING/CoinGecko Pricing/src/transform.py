import pandas as pd
from datetime import datetime
from src.extract_price import extract as exp

def transform_data(data):
    """ Converting Last Updated to time in min
    """
    data['last_updated(min)'] = pd.to_datetime(data['last_updated'], errors='coerce').dt.hour
    data = data.drop(columns=['last_updated'])
    data['total_volume_bil'] = data['total_volume']/(1000000000)
    data = data.drop(columns=['total_volume'])
    return data


# if __name__ == '__main__':
#     df = exp.extract()
#     data = transform_data(df)
#     print(data.shape)
#     print(data.head())

