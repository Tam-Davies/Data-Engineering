from  src.extract_price import extract as ext
from  src.transform import transform_data as td
from src.load import load_to_db as ltd, engine
import pandas as pd
from src.log import logs 

if __name__ == "__main__":
    logs("Starting Data Extraction")
    df = ext()
    logs('Starting Data Transformation')
    transformed_df = td(df)
    table_name = "crypto_prices"
    logs('Loading Data')
    ltd(transformed_df, table_name)
    # query_output_1 = pd.read_sql(f'SELECT * FROM {table_name}', engine)
    # print(query_output_1)
    print('Data Loaded Succesffully')