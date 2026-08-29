import pandas as pd
import src.extract_multiple_states as ems

def transform_data(data):
    """
    Selecting only Important features and renaming each column before loading it
    """
    data  = data[['id', 'type', 'geometry', 'properties.severity', 'properties.affectedZones', 'properties.category', 'properties.geocode.SAME']]
    data = data.rename(columns={'properties.severity':'severity',
                                'properties.affectedZones': 'affected_zones',
                                'properties.category': 'category',
                                'properties.geocode.SAME': 'geocode'})
    return data


if __name__ == '__main__':
    df = ems.extract('NY,CA,TX')
    data = transform_data(df)
    print(data.head())