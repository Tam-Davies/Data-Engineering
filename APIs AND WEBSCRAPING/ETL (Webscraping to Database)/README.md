# Largest Banks ETL Pipeline

An end-to-end ETL (Extract, Transform, Load) pipeline that scrapes a "List of largest banks" table from a Wikipedia snapshot, converts market cap into multiple currencies, and loads the result into both a CSV file and a SQLite database for querying.

## Pipeline overview

**Source:** Wayback Machine snapshot of `en.wikipedia.org/wiki/List_of_largest_banks` (2023-09-08)
**Output:** `Largest_banks_data.csv` and a `Largest_banks` table inside `Banks.db`

```
Extract (BeautifulSoup)  →  Transform (currency conversion)  →  Load (CSV + SQLite)  →  Query
```

### 1. Extract — `extract(url, table_attribs)`
- Fetches the archived Wikipedia page with `requests` and parses it with `BeautifulSoup`
- Grabs the **3rd `<tbody>`** on the page (`tables[2]`) and reads each `<tr>` row
- Keeps only rows where the first cell is a link (`col[0].find('a')`) and the market cap cell isn't an em-dash placeholder (`'—' not in col[1]`)
- Builds a `Name` / `MC_USD_Billion` DataFrame from the bank name and market cap columns

### 2. Transform — `transform(df)`
- Loads `exchange_rate.csv` to get GBP/EUR/INR conversion rates against USD
- Cleans `MC_USD_Billion` (strips commas, coerces to numeric)
- Adds `MC_GBP_Billion`, `MC_EUR_Billion`, and `MC_INR_Billion` columns, each rounded to 2 decimal places

### 3. Load — `load_to_csv` / `load_to_db`
- `load_to_csv(df, csv_path)` writes the transformed table to `Largest_banks_data.csv`
- `load_to_db(df, sql_connection, table_name)` writes it into a SQLite table (`if_exists='replace'`)

### 4. Query — `run_query(query_statement, sql_connection)`
- Runs a SQL statement against the SQLite table via `pd.read_sql` and prints the result
- Example queries used: filter by `MC_USD_Billion >= 100`, average market cap in GBP, top banks by USD market cap

### Logging — `log_progress(message)`
Every stage of the pipeline (preliminaries, extraction, transformation, load, query, completion) is timestamped and appended to `etl_project_log.txt`, giving a simple audit trail of each run.

## ⚠️ Known issue: extraction is pulling the wrong table

The most recent run's output doesn't look like bank data — it lists **countries** (France, Canada, South Korea, Brazil, etc.) with small whole-number market caps (1–6), not the large real-world bank market caps (hundreds of billions of USD) the pipeline is designed to produce. The `WHERE MC_USD_Billion >= 100` query in the log correctly returns an **empty result**, confirming the extracted values are far too small to be genuine bank market caps.

Likely cause: `tables[2]` (the 3rd `<tbody>` on the archived page) no longer points to the "largest banks" table — Wikipedia page layouts can shift over time (added infoboxes, new sections, etc.), so a fixed table index is fragile. Worth re-checking which `<tbody>` index actually holds the banks table on the current archived snapshot, or better, selecting the table by a more specific identifier (e.g. its preceding heading or a `class`/`caption` match) instead of a hardcoded position.

## Run history

`etl_project_log.txt` shows the pipeline has been run **15 times** across two days (Apr 11–12, plus one run in Aug), with most runs completing the full extract → transform → load → query cycle in well under 10 minutes. A few early runs stop after "Preliminaries complete" with no further log lines — those runs likely errored out or were interrupted before extraction finished.

## Requirements

```
requests
beautifulsoup4
pandas
```

Also expects an `exchange_rate.csv` file (with `Currency` and `Rate` columns) in the working directory — referenced by `transform()` but not included in this upload.

## Usage

Run the notebook top to bottom. It will:
1. Scrape and parse the source page
2. Convert currencies
3. Write `Largest_banks_data.csv` and populate `Banks.db`
4. Run and print a few example SQL queries
5. Append progress timestamps to `etl_project_log.txt`
