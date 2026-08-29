from src.extract_multiple_states import extract
from src.transform import transform_data
from src.load_to_GCP import load_to_BigQuery
from src.log import logger



if __name__ == "__main__":
    logger.info("Starting ETL pipeline")

    logger.info("Starting data extraction")
    raw_data = extract('NY,CA,TX')

    logger.info("Starting data transformation")
    transformed_df = transform_data(raw_data)

    print(f"Loading {len(transformed_df)} rows...")

    logger.info("Starting BigQuery load")
    load_to_BigQuery(transformed_df)
    print("Load complete.")