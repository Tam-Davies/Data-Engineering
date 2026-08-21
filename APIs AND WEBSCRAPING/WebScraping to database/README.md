# Top 50 Highest-Ranked Films — Scrape & Load

Scrapes the top 50 entries from a "100 Most Highly-Ranked Films" list (archived snapshot), saves them to CSV, and loads them into a SQLite database for querying.

## Pipeline overview

```
Extract (BeautifulSoup, first 50 rows)  →  Save to CSV  →  Reload CSV  →  Load to SQLite
```

1. Fetches an archived EverybodyWiki page (`web.archive.org` snapshot from 2023-09-02) with `requests` and parses it with `BeautifulSoup`
2. Reads the **first `<tbody>`** on the page (`tables[0]`), walks its `<tr>` rows, and stops once **50 films** have been collected — pulling `Average Rank`, `Film`, and `Year` from each row's `<td>` cells
3. Writes the result to `top_50_films.csv`
4. Re-reads that CSV back into a DataFrame and loads it into `Movies.db` as a table via `to_sql(..., if_exists='replace')`

## ⚠️ Known issue: three tables in `Movies.db`, not one

`db_name`/`table_name` are set up front as `Movies.db` / `Top_50`, but the actual `to_sql()` call at the end uses a **hardcoded string** (`'top_50_films'`) instead of the `table_name` variable — and it uses the DataFrame re-read from CSV, not the original `df`. As a result, `Movies.db` currently contains **three different tables**, only one of which has real data:

| Table | Rows | Notes |
|---|---|---|
| `Top_50` | 0 | Empty — created by `table_name` presumably in an earlier/different run, but never populated since the final `to_sql()` call doesn't reference it |
| `top_50_films.csv` | 50 | Has data — looks like an earlier run accidentally passed the filename itself as the table name |
| `top_50_films` | 50 | The "real" table from the current code, includes a stray `Unnamed: 0` index column carried over from `pd.read_csv` re-reading the CSV that was saved with `df.to_csv()` (no `index=False`) |

Worth cleaning up: use `table_name` consistently instead of a hardcoded string, drop the leftover `Top_50` and `top_50_films.csv` tables, and add `index=False` to the `to_csv()` call to avoid the extra unnamed index column showing up downstream.

## What the data shows

- **The list skews toward mid-20th-century cinema.** Median release year is **1976.5**, and **21 of the 50 films (42%)** were made before 1970 — despite film production volume being far higher in recent decades, meaning older films are punching well above their weight in this ranking.
- **The 1950s is the best-represented decade** (9 films), followed by the 1990s (8) and 1970s (7). The 2000s decade is comparatively underrepresented, with only 4 films — fewer than the 1930s and 1940s combined output despite being contemporary(ish) to the list's 2023 snapshot date.
- **Only 9 films (18%) are from 2000 onward** — this "greatest of all time" style ranking clearly favors legacy/classic status over recency; recent blockbusters like *Avengers: Endgame* (2019) and *Parasite* (2019) do make the cut, but are heavily outnumbered by pre-1980 films.
- Full year range: **1931** (*City Lights*) to **2019** (*Parasite*, *Avengers: Endgame*) — an 88-year span.

## Requirements

```
requests
beautifulsoup4
pandas
```

## Usage

Run the notebook top to bottom. It scrapes the source page, writes `top_50_films.csv`, and loads the data into `Movies.db`.
