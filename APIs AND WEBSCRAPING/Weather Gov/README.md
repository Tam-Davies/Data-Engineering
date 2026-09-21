# Weather Gov ETL

This project extracts active weather alerts from the [National Weather Service API](https://api.weather.gov/), transforms the response into a smaller pandas dataframe, and loads the result into Google BigQuery. It is an alert-ingestion pipeline, not a forecast-generation service.

## Project Structure

- `main.py` - Runs the complete extraction, transformation, and load pipeline.
- `src/extract_multiple_states.py` - Fetches active alerts for multiple state codes.
- `src/extract_single_state.py` - Fetches active alerts for one state code.
- `src/transform.py` - Selects and renames the fields sent to BigQuery.
- `src/load_to_GCP.py` - Creates/checks the BigQuery dataset and loads the dataframe.
- `src/log.py` - Configures logging to `logs/process.log`.
- `logs/process.log` - Pipeline execution log.
- `data/` - Reserved for local data files; the current pipeline loads directly into BigQuery.

## Requirements

- Python 3.9 or newer
- Internet access to `api.weather.gov`
- A Google Cloud project with BigQuery enabled
- Google Cloud credentials configured for Application Default Credentials

Install the Python packages from the project directory:

```bash
python -m pip install requests pandas google-cloud-bigquery pyarrow
```

`pyarrow` is required by the BigQuery dataframe loader.

## Google Cloud Authentication

Authenticate locally with the Google Cloud CLI:

```bash
gcloud auth application-default login
gcloud config set project first-cloud-sql-project-507007
```

Alternatively, set `GOOGLE_APPLICATION_CREDENTIALS` to the path of a service-account JSON key that has permission to create datasets and load BigQuery tables. Do not commit credential files to this repository.

## API User-Agent

The National Weather Service asks clients to identify themselves. Before running the pipeline, replace the placeholder value in `src/extract_multiple_states.py` and `src/extract_single_state.py`:

```python
headers = {
    "accept": "application/geo+json",
    "User-Agent": "your-app-name, your.email@example.com",
}
```

## Run the Pipeline

Run from the `Weather Gov` directory so the `src` imports resolve correctly:

```bash
cd "APIs AND WEBSCRAPING/Weather Gov"
python main.py
```

The default pipeline requests active alerts for `NY,CA,TX`. It logs each stage and prints the number of rows sent to BigQuery:

```text
Loading <row-count> rows...
Load complete.
```

## Pipeline Flow

1. `extract('NY,CA,TX')` requests active alerts from `https://api.weather.gov/alerts/active`.
2. The JSON `features` response is normalized into a pandas dataframe.
3. The transformation keeps the alert ID, type, geometry, severity, affected zones, category, and SAME geocode fields, then renames the nested columns.
4. BigQuery loads the transformed dataframe into `weather_data`.
5. Progress messages are written to `logs/process.log`.

## BigQuery Destination

The current loader is configured for project `first-cloud-sql-project-507007` and table `Weather_Gov.weather_data`. The authenticated Google Cloud identity needs permission to create datasets and load data, or the destination dataset must already exist.

There is an existing naming inconsistency in `src/load_to_GCP.py`: the dataset existence check and creation use `Waether_Gov`, while the table destination uses `Weather_Gov`. Make these names consistent before relying on automatic dataset creation; otherwise create the intended `Weather_Gov` dataset manually.

## Troubleshooting

- `ModuleNotFoundError`: install the packages listed above in the active Python environment.
- `DefaultCredentialsError`: configure Application Default Credentials or set `GOOGLE_APPLICATION_CREDENTIALS`.
- `403 Forbidden` from BigQuery: grant the authenticated identity access to the project and BigQuery dataset/table.
- API request errors: verify internet access and use a descriptive `User-Agent` value.
- Empty-alert response: the current transformation expects the alert columns to exist, so a response with no active alerts may fail during transformation.
- Import errors when running from another directory: change into `Weather Gov` before running `python main.py`.