# Yellow Trip ETL - Quick README

## Project summary

This project processes NYC Yellow Taxi trip data with PySpark, performs exploratory analysis, and now includes a PostgreSQL migration workflow to move the cleaned output into a database.

## Main files

- `notebooks/exploratory data analysis.ipynb` — ETL pipeline and EDA
- `notebooks/database_migration.ipynb` — Spark-to-PostgreSQL migration notebook
- `notebooks/database_migration.md` — migration guide and setup notes
- `output/nyc_taxi_processed` — cleaned Parquet output
- `README.md` — full project documentation

## Quick workflow

1. Load raw Yellow Taxi CSV files.
2. Clean, validate, and transform the data.
3. Engineer features such as trip duration, speed, and fare metrics.
4. Save the final processed dataset as Parquet.
5. Load the Parquet output into PostgreSQL with the migration notebook.

## Database migration

The migration notebook connects Spark to PostgreSQL using the JDBC driver, writes the consolidated table, and verifies the uploaded row count after the write completes.

## Environment

- Python 3.9+
- Java 8/11+
- Apache Spark / PySpark
- PostgreSQL database server
- PostgreSQL JDBC driver for Spark

## References

- Full project notes: `README.md`
- Migration walkthrough: `notebooks/database_migration.md`
- Migration notebook: `notebooks/database_migration.ipynb`
