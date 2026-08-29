import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from transform import transform_data as td
from extract import extract_data as ex 
import pandas as pd

load_dotenv()

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

def load_to_db(df, table_name, engine):
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    return df


if __name__ == '__main__':
    sql_connection = engine.connect()
    raw_data = ex()
    df = td(raw_data)
    load_to_db(df, db_name, sql_connection)
    query_output_1 = pd.read_sql(f'SELECT * FROM {db_name}', sql_connection)
    print(query_output_1)