# Yellow Taxi Trip ETL

A PySpark-based ETL and exploratory data analysis project for NYC Yellow Taxi trip data.

## Overview

The notebook performs the following tasks:

1. Loads CSV taxi data into a Spark DataFrame.
2. Profiles the dataset and checks for nulls and duplicates.
3. Cleans and casts columns to appropriate data types.
4. Removes invalid trips.
5. Creates analytical features.
6. Performs exploratory analysis using PySpark aggregations and window functions.
7. Validates processed records.
8. Saves the cleaned dataset as Parquet.

## Project Structure

```text
Yellow Trip ETL/
├── data/                     # Raw source files removed from GitHub due to file-size limits
├── notebooks/
│   ├── exploratory data analysis.ipynb
│   ├── database_migration.ipynb
│   └── database_migration.md
├── output/                   # Processed Parquet output removed from GitHub due to size limits
│   └── nyc_taxi_processed/
├── QREADME.md
├── README.md
└── .gitignore               # Excludes large datasets from version control
```

> Note: The raw CSV files and processed Parquet output were intentionally deleted from this repository because they were too large to push to GitHub. The ETL notebooks remain in place so the project can be rerun locally with the dataset restored.

## Database Migration

The project now includes a PostgreSQL migration workflow in `notebooks/database_migration.ipynb`.

This notebook:

- loads the processed Parquet dataset from `output/nyc_taxi_processed`
- configures a Spark session with the PostgreSQL JDBC driver
- writes the consolidated dataset to a PostgreSQL table
- validates the migrated row count after the load

Use the companion note in `notebooks/database_migration.md` for the step-by-step migration process and environment assumptions.

## Requirements

- Python 3.9+
- Java 8 or 11
- Apache Spark
- PySpark
- Visual Studio Code with the Jupyter extension

Install PySpark with:

```powershell
pip install pyspark
```

## Running the Notebook

1. Place the Yellow Taxi CSV files in the `data` directory.
2. Open `notebooks/exploratory data analysis.ipynb` in Visual Studio Code.
3. Select a Python kernel with PySpark installed.
4. Run the notebook cells sequentially.

The notebook reads files from:

```text
C:/Users/user/Desktop/Data Engineering/Yellow Trip ETL/data/*.csv
```

Update this path if the project is moved.

## Data Processing

The notebook converts timestamps and numeric columns to appropriate data types, including:

- Pickup and drop-off timestamps
- Passenger count
- Trip distance
- Fare and tax amounts
- Geographic coordinates

Invalid records are removed when they contain:

- Non-positive trip distance
- Non-positive fare amount
- Non-positive passenger count
- Drop-off time earlier than or equal to pickup time

## Feature Engineering

The following features are created:

- `trip_duration_min`
- `pickup_hour`
- `day_of_week`
- `fare_per_mile`
- `tip_pct`
- `average_speed_mph`

## Exploratory Analysis

The notebook analyzes:

- Trips by pickup hour
- Revenue by hour
- Vendor performance
- Payment type usage and revenue
- Average tips and tip percentages
- Distance quantiles
- Top fares using window functions
- Daily revenue and trip counts

## Output

The processed data is written to:

```text
output/nyc_taxi_processed
```

The output uses Apache Parquet format and can be loaded with:

```python
parquet_taxi_df = spark.read.parquet("output/nyc_taxi_processed")
```

## Validation

The notebook compares the original processed row count with the Parquet row count and checks for invalid calculated values such as:

- Non-positive trip durations
- Non-positive average speeds
- Non-positive fare per mile

## Notes

- The raw CSV files and processed Parquet output were removed from GitHub because they exceeded repository size limits.
- The output path is relative to the notebook's current working directory.
- The notebook may require additional driver memory for large datasets.
- Spark must be configured with a compatible Java installation.
- To reproduce the project locally, restore the `data/` CSV files and run the ETL notebook to regenerate `output/nyc_taxi_processed`.