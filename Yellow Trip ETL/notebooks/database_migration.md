# Database Migration Guide

This guide covers the PostgreSQL migration workflow for the processed NYC Yellow Taxi dataset.

## Objective

The project creates a cleaned and feature-enriched Parquet dataset in `output/nyc_taxi_processed`, then moves that result into PostgreSQL using Spark's JDBC connector.

## Files involved

- `notebooks/database_migration.ipynb` — Spark session setup and database write/load validation
- `output/nyc_taxi_processed` — processed Parquet output produced by the exploratory ETL notebook

## Prerequisites

- Java installed and configured
- PostgreSQL installed and running locally
- PostgreSQL JDBC driver available at `C:\spark_jar\postgresql-42.7.13.jar`
- A database named `nysc_taxi_trips_spark`
- A PostgreSQL user with write permissions

## Migration flow

1. Start a Spark session with the PostgreSQL JDBC driver configured.
2. Read the processed dataset from the Parquet output folder.
3. Write the DataFrame to PostgreSQL using JDBC mode `overwrite`.
4. Confirm the destination table was loaded by reading the table back with Spark.
5. Compare row counts between the Parquet source and PostgreSQL destination.

## Example configuration

```python
spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("PostgreSQL_Test")
    .config("spark.jars", r"C:\spark_jar\postgresql-42.7.13.jar")
    .getOrCreate()
)
```

```python
df_final.write \
    .format("jdbc") \
    .option("url", "jdbc:postgresql://localhost:5432/nysc_taxi_trips_spark") \
    .option("dbtable", "consolidated_table") \
    .option("user", "postgres") \
    .option("password", "your_password") \
    .option("driver", "org.postgresql.Driver") \
    .mode("overwrite") \
    .save()
```

## Notes

- The notebook sets `JAVA_HOME` explicitly in the environment.
- `consolidated_table` is the PostgreSQL table used for the migrated dataset.
- If the table name or database credentials differ, update the JDBC options accordingly.
- For large datasets, ensure the Spark driver and PostgreSQL instance have enough memory and connection limits.
