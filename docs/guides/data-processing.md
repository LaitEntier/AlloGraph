# Modifying the data pipeline

All loading, cleaning, and derived-variable logic lives in `modules/data_processing.py`.

## Entry points

- `load_data(file_path)` — reads CSV/Excel, auto-detects the CSV separator, normalizes column names
- `normalize_column_names(df)` — case-insensitive matching against `EXPECTED_COLUMNS`, plus known synonyms
- `process_data(df)` — the main entry point called after upload; chains all enrichment steps

## Adding a derived variable

1. Write a `create_my_variable(df)` function in `data_processing.py` following the existing style: French Google-style docstring, defensive handling of missing columns, returns the modified DataFrame.
2. Call it from `process_data()`, in a sensible position relative to its dependencies (e.g. `Year` is created early because other derivations use it).
3. Decide which **slim stores** need the new column (`data-store-survival`, `data-store-gvh`, `data-store-viz`) and update the store-population logic in `app.py` accordingly.
4. Verify with the test sample: the new column should appear and pages that use it should render.

## Rules of thumb

- **Backward compatibility first**: never rename or drop a column in `EXPECTED_COLUMNS` without auditing every page — columns are referenced by name throughout `pages/` and `visualizations/`.
- **Missing data**: input files are messy. Existing transformations tolerate missing columns/values (they check membership before transforming). Match that behavior; do not assume a column exists.
- **Dates** are parsed flexibly; reuse the existing parsing helpers rather than adding new `pd.to_datetime` calls with hard-coded formats.
- **Column names with spaces** are the norm here (`Treatment Date`). Keep new derived names consistent in style.

## Testing your change

There is no automated test suite. The manual check is:

1. Restart the app, load `data/test_sample.csv`.
2. Open the pages affected by your variable and confirm the figures/tables look right.
3. Upload a file with a **missing** related column and confirm nothing crashes.
