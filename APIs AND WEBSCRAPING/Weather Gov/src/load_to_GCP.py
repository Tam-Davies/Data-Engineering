from google.cloud import bigquery
from src.transform import transform_data as td

def load_to_BigQuery(data):
    client = bigquery.Client(project="first-cloud-sql-project-507007")

    dataset_id = "first-cloud-sql-project-507007.Waether_Gov"
    try:
        client.get_dataset(dataset_id)  # check if it exists
    except Exception:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        client.create_dataset(dataset)

    table_id = "first-cloud-sql-project-507007.Weather_Gov.weather_data"
    job = client.load_table_from_dataframe(data, table_id)
    job.result()

# print("Data loaded successfully!")
# client = bigquery.Client(
#     project="first-cloud-sql-project-507007"
# )

# print(client.project)