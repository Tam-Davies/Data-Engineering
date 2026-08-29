import pyodbc
from sqlalchemy import create_engine
import urllib
from src.extract_price import extract as exp
from src.transform import transform_data as td
import pandas as pd

params = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=crypto_coin_prices;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

def load_to_db(df, table_name):
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    return df


# if __name__ == '__main__':
#     sql_connection = engine.connect()
#     raw_data = exp.extract()
#     df = td(raw_data)
#     table_name = "crypto_prices"
#     load_to_db(df, table_name, sql_connection)
#     query_output_1 = pd.read_sql(f'SELECT * FROM {table_name}', sql_connection)
#     print(query_output_1)