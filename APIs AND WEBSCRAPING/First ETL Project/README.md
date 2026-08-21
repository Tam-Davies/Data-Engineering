# Multi-Source ETL Pipeline (CSV / JSON / XML → Unified CSV)

A generic ETL pipeline that extracts person records (`name`, `height`, `weight`) from any CSV, JSON, or XML files sitting in the working directory, converts imperial units to metric, and loads the combined result into a single output CSV — with every stage timestamped to a log file.

## Pipeline overview

```
Extract (CSV + JSON + XML)  →  Transform (inches→meters, lbs→kg)  →  Load (transformed_data.csv)
```

### 1. Extract
- `extract_from_csv(file)` — reads a CSV straight into a DataFrame with `pd.read_csv`
- `extract_from_json(file)` — reads line-delimited JSON with `pd.read_json(file, lines=True)`
- `extract_from_xml(file)` — parses XML with `ElementTree`, walking each `<person>` element and pulling out `name`/`height`/`weight`
- `extract()` — orchestrates all three: globs `*.csv`, `*.json`, and `*.xml` in the working directory (skipping the target output file if it happens to match `*.csv`) and concatenates everything into one DataFrame

### 2. Transform — `transform(data)`
- Height: inches → meters (`× 0.0254`, rounded to 2 dp)
- Weight: pounds → kilograms (`× 0.45359237`, rounded to 2 dp)

### 3. Load — `load_data(target_file, transformed_data)`
Writes the transformed DataFrame to `transformed_data.csv`.

### Logging — `log_progress(message)`
Each phase boundary (`ETL Job Started`, `Extract phase Started/Ended`, `Transform phase Started/Ended`, `Load phase Started/Ended`, `ETL Job Ended`) is timestamped and appended to `log_file.txt`.

## Source files

| File | Rows | Content |
|---|---|---|
| `source1.csv`, `source2.csv`, `source3.csv` | 5 each | Identical: alex, ajay, alice, ravi, joe |
| `source1.json`, `source2.json`, `source3.json` | 4 each | Identical: jack, tom, tracy, john |
| `source1.xml`, `source2.xml`, `source3.xml` | 4 each | Identical: simon, jacob, cindy, ivan |

## ⚠️ Known issue: triplicated data in the output

`transformed_data.csv` contains **39 rows**, but there are only **13 unique people** (5 + 4 + 4) across the source files. Every person appears **exactly 3 times** — because `source1`, `source2`, and `source3` hold identical content per format, and `extract()` loops over *every* matching file with `glob.glob("*.csv")` / `*.json` / `*.xml` rather than deduplicating. This is expected behavior for the code as written (it's treating `source1/2/3` as three separate data drops to ingest, not copies of one file) — but if these three files were meant to represent the *same* batch of people rather than three distinct batches, the pipeline needs a `drop_duplicates()` step before `load_data()`, or the redundant source files should be removed before running extract.

Also worth checking: `extract()` filters out `target_file` from the CSV glob, but only compares the bare filename (`target_file = "transformed_data.csv"`) — if the notebook is ever run from a different working directory than where `transformed_data.csv` lives, this comparison could fail to exclude it, causing the output file to be re-ingested as a source on a second run.

## Run history

`log_file.txt` shows the pipeline has run twice — once on Apr 6 and once on Aug 21 — both completing all phases in well under 2 seconds (the Aug 21 run took ~1 second end-to-end).

## Requirements

```
pandas
```
(`xml.etree.ElementTree`, `glob`, and `datetime` are part of the Python standard library.)

## Usage

Place any number of CSV/JSON/XML files with `name`/`height`/`weight` fields in the working directory alongside the notebook, then run all cells. Output lands in `transformed_data.csv`; progress is logged to `log_file.txt`.
