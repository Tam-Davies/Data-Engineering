git# Salaries Dataset - Data Cleaning and EDA with PySpark

This project analyzes the salary dataset using PySpark, with a focus on cleaning messy values, validating salary and date fields, and creating derived features for exploratory analysis.

## Project Goal

The notebook was designed to:

- inspect the dataset structure
- identify missing or malformed values
- clean salary columns (`montobruto` and `montoneto`)
- normalize date fields (`periodoreportainicio` and `periodoreportafin`)
- engineer simple features such as reporting period length and estimated deductions
- run exploratory data analysis

---

## Dataset Context

The dataset contains salary information and reporting periods for employees or public official records, including:

- `entidadfederativa`
- `montobruto`
- `montoneto`
- `periodoreportainicio`
- `periodoreportafin`

The main challenge in this project was not the analysis itself, but cleaning inconsistent values in the source CSV.

---

## Main Problems Encountered and How They Were Troubleshot

### 1) Null and missing values in critical columns

Problem:
- The dataset contained rows where `montobruto` or `montoneto` were missing or invalid.
- These rows could distort calculations and feature engineering.

Troubleshooting:
- Counted rows with missing values using:
  - `raw_df.count() - raw_df.na.drop().count()`
- Checked the percentage of missing values:
  - `null_count_pct = (null_count / raw_df.count()) * 100`
- Narrowed focus to rows with usable salary figures using:
  - `raw_df.na.drop(subset=['montobruto', 'montoneto']).count()`
- Identified where the missing records were concentrated by state:
  - `dropped_rows.groupBy('entidadfederativa').count().orderBy('count', ascending=False).show()`

Outcome:
- The project recognized that the salary columns were the core data quality issue and decided to filter or sanitize them before analysis.

---

### 2) Salary columns were not cleanly typed as numeric

Problem:
- `montobruto` and `montoneto` did not reliably parse as numeric values.
- Values included commas, spaces, negative signs, blank strings, or irregular tokens.
- A naive cast to `double` would fail or produce nulls.

Troubleshooting approach:
- Read the dataset with `inferSchema = false` first to avoid Spark trying to infer the wrong schema too early.
- Inspect actual raw values before converting.
- Use regex validation to only convert strings that were numeric-like.

Example logic used:

```python
F.when(
    F.trim(F.col("montobruto").cast("string")).rlike(r"^[0-9,\.\s-]+$"),
    F.regexp_replace(F.trim(F.col("montobruto").cast("string")), r",", "").cast("double")
).otherwise(None)
```

This was used for both salary columns.

Why this worked:
- It preserved only values that looked like numbers.
- It removed thousands separators such as commas.
- It rejected text values such as `NULL`, `NA`, `USET`, and dates.

---

### 3) Values like `NULL`, `NA`, `USET`, and empty strings were contaminating numeric fields

Problem:
- Some cells contained placeholder values instead of numeric salary values.
- These values could not be cast directly to double.

Troubleshooting:
- Built a validation filter that flagged rows containing alphabetic text or known placeholders:

```python
bad_salary_rows = raw_df.filter(
    F.trim(F.col("montobruto").cast("string")).rlike(r".*[A-Za-z].*")
    |
    F.trim(F.col("montoneto").cast("string")).rlike(r".*[A-Za-z].*")
    |
    F.trim(F.col("montobruto").cast("string")).isin("USET", "NULL", "NA", "")
    |
    F.trim(F.col("montoneto").cast("string")).isin("USET", "NULL", "NA", "")
)
```

- Then removed those rows from the cleaned dataset.

Outcome:
- This created a `clean_df` where salary values were valid doubles and ready for modeling or analysis.

---

### 4) Date formats were inconsistent

Problem:
- The date columns used different formats across rows, such as:
  - `dd/MM/yyyy`
  - `yyyy-MM-dd`
- Passing them directly into `to_date()` caused failures and inconsistent parsing.

Troubleshooting:
- Avoided strict conversion before checking format.
- Sanitized date strings as strings first.
- Kept only rows matching valid patterns before converting:

```python
F.when(
    F.trim(F.col("periodoreportainicio")).rlike(r"^\d{2}/\d{2}/\d{4}$|^\d{4}-\d{2}-\d{2}$"),
    F.trim(F.col("periodoreportainicio"))
).otherwise(None)
```

Then later converted valid values with both supported formats:

```python
F.coalesce(
  F.to_date("periodoreportainicio", "dd/MM/yyyy"),
  F.to_date("periodoreportainicio", "yyyy-MM-dd")
)
```

Outcome:
- Only rows with valid dates were kept for subsequent feature engineering.

---

### 5) The first conversion attempt was too aggressive

Problem:
- In the earlier version, the notebook tried to convert the full dataset directly:

```python
raw_df = raw_df.withColumn(
    "periodoreportainicio",
    to_date("periodoreportainicio", "dd/MM/yyyy")
)
```

This caused issues because the source had inconsistent or invalid formats.

Troubleshooting:
- The notebook was revised to follow a safer pipeline:
  1. read raw CSV as text
  2. validate values with `rlike()`
  3. clean numeric fields
  4. clean date strings
  5. filter invalid rows
  6. convert to proper types only after validation

This was a key lesson: do not cast before validating the raw strings.

---

### 6) CSV reading assumptions were wrong

Problem:
- The dataset may have had formatting issues or unexpected field delimiters.
- A quick read without checking how the CSV was structured can lead to misaligned columns.

Troubleshooting:
- Read the file with `inferSchema = false` to inspect raw text instead of inferred types.
- Check the schema and the top rows with:

```python
raw_df.show(10, truncate=False)
raw_df.printSchema()
```

- if needed, review whether delimiter or quoting config should be adjusted.

This helped confirm that the main problem was not total file corruption, but malformed field values and inconsistent formatting.

---

### 7) Schema confusion between temporary and final dataframes

Problem:
- The notebook changed `raw_df`, `spark_df`, and `clean_df` several times across different tries.
- This created confusion about which dataframe was the cleaned one and which was still a raw or partially processed version.

Troubleshooting:
- The project settled on a clearer pipeline structure:
  - `raw_df` = raw CSV read as text
  - `clean_df` = validated and cleaned data
  - `spark_df` = a later processed version for analysis
- This separation made the notebook easier to debug and reduce accidental reprocessing.

---

## Final Working Approach

The notebook eventually converged on this robust pattern:

1. Read the CSV with `inferSchema = false`
2. Inspect raw values and schema
3. Validate and sanitize `montobruto` and `montoneto`
4. Remove non-numeric or placeholder values
5. Validate date formats
6. Keep only rows with valid salary and date values
7. Convert to proper types
8. Compute derived features
9. Run EDA

### Missing-Value Strategy

Use the strategy that matches the field:

- Drop rows missing required salary or reporting-period values because those rows cannot support the main analysis.
- Fill optional text fields with a label when retaining the record is more useful than dropping it:

```python
clean_df = clean_df.na.fill({"cargo": "Unknown", "area": "Unknown"})
```

- For optional numeric columns, use `pyspark.ml.feature.Imputer` only when a documented statistic such as the median is appropriate. Do not impute the core salary fields without checking how that changes the analysis.

The final feature engineering section included:

```python
clean_df = clean_df.withColumn(
    "period_dias",
    F.datediff("periodoreportafin", "periodoreportainicio")
).withColumn(
    "deducciones_estimadas",
    F.col("montobruto") - F.col("montoneto")
)
```

This created:
- `period_dias`: difference between report start and end dates
- `deducciones_estimadas`: estimated deduction amount

---

## Key Lessons Learned

- Always inspect raw values before casting.
- Use regex to validate suspicious numeric fields.
- Do not trust schema inference on dirty CSVs.
- Sanitize dates before converting them to Spark date types.
- Keep a clear separation between raw, cleaned, and analyzed dataframes.
- Filter invalid rows early to avoid downstream failures.
- Choose `na.drop`, `na.fill`, or `Imputer` according to the meaning of the missing field.

---

## Recommended Next Steps

- Save the cleaned dataframe to a parquet file for reuse.
- Build summary statistics by `entidadfederativa`.
- Compare gross vs net salary distributions.
- Plot deductions and period lengths.
- Create notebook sections for final business insights and visualization.

---

## Quick Summary

The biggest issue in this notebook was not a single bug, but a chain of data quality problems:

- inconsistent salary formatting
- invalid placeholder values
- mixed date formats
- rows with missing important fields

The workflow was fixed by validating the raw strings before casting, filtering bad records, and building a cleaner, more reliable dataset for analysis.
