# Architecture

## Overview

AlloGraph follows the classic **Dash multi-page pattern**, but pages are *hand-wired* in `app.py` (not `dash.register_page`). Each page module exposes two functions:

- `get_layout()` — returns the page layout (a `dbc.Container`)
- `register_callbacks(app)` — registers the page's callbacks on the app

`app.py` initializes the Dash app, imports every page module, calls their `register_callbacks`, and owns the **global callbacks**: navigation (routing between pages) and data upload/purge.

## Project layout

```
AlloGraph/
├── app.py                  # Entry point: app init, navigation, data upload callbacks
├── wsgi.py                 # WSGI entry point (production)
├── config.py               # Configuration (currently empty)
├── modules/                # Core logic, page-independent
│   ├── data_processing.py    # Data loading, cleaning, derived variables
│   ├── dashboard_layout.py   # Shared UI components (sidebar builders, filters)
│   ├── competing_risks.py    # Competing risks statistical analysis
│   ├── cache_utils.py        # In-memory caching for expensive computations
│   ├── validation.py         # Data validation (placeholder)
│   └── callbacks.py          # Shared callbacks (placeholder)
├── pages/                  # One module per analysis page
│   ├── home.py               # Landing page, data upload, overview graph
│   ├── patients.py           # Demographics
│   ├── hemopathies.py        # Disease analysis
│   ├── procedures.py         # Donor/stem cell source, conditioning, prophylaxis
│   ├── gvh.py                # GvHD (competing risks)
│   ├── relapse.py            # Relapse vs death (competing risks)
│   ├── survival.py           # Kaplan–Meier curves, long-term follow-up
│   ├── toxicity.py           # Toxicity analysis
│   ├── indics.py             # Clinical indicators dashboard (KPIs)
│   └── legal.py / privacy.py / cookies.py   # Static legal pages
├── visualizations/
│   └── allogreffes/
│       ├── graphs.py         # Plotly figure factory functions
│       └── upsetjs_embed.py  # Pure-SVG interactive UpSet plot
├── utils/                  # plotting_helpers.py, redcap_helpers.py (placeholders)
├── assets/                 # CSS, images, Lottie config (served by Dash)
└── data/                   # Sample data (de-identified)
```

## Data flow

```
CSV/Excel upload (Home sidebar)
        │
        ▼
data_processing.process_data(df)      # cleaning + derived variables
        │
        ▼
dcc.Store components (client-side)    # data-store + slim stores
        │
        ▼
page callbacks read the store,
apply page-specific sidebar filters,
call visualizations/allogreffes/graphs.py
        │
        ▼
Plotly figures rendered in the page
```

1. Data is uploaded from the Home page sidebar (CSV or Excel — separator auto-detected).
2. `process_data()` cleans and enriches the dataframe (see below).
3. The processed dataframe is serialized into `dcc.Store` components in the browser. **Nothing is persisted server-side** — this matters for GDPR (see [Deployment](../deployment.md#security-gdpr)).
4. Each page reads the store, applies its own sidebar filters, and renders figures.

### Slim data stores

To reduce client↔server transfer (important on VM deployments), the dataset is split into specialized stores, populated on load and cleared on purge:

| Store | Content |
|---|---|
| `data-store` | Full dataset (use sparingly) |
| `data-store-survival` | Only columns needed for survival analysis |
| `data-store-gvh` | Only columns needed for GvH analysis |
| `data-store-viz` | Visualization columns (most common operations) |

When you add a derived column, check which slim stores need it.

## Key data transformations

`modules/data_processing.py` enriches the raw registry data:

- `Year` — extracted from `Treatment Date`
- `Age At Diagnosis` — from `Date Of Birth` and `Date Diagnosis`
- `Age Groups` — `18-`, `18-39`, `40-64`, `65-74`, `75+`
- `Greffes` — combines `Donor Type` + `Source Stem Cells`
- `Blood + Rh` — combines `Blood Group` + `Rhesus Factor`
- `Compatibilité HLA` — HLA compatibility from match/donor fields
- Conditioning regimen and prophylaxis drug columns → binary treatment indicators
- Chronic GvHD scores remapped: `Limited → Mild`, `Extensive → Severe`
- `Main Diagnosis Category` — grouped diagnosis categories

Column names are normalized case-insensitively against `EXPECTED_COLUMNS` (see [Data format](../data-format.md)).

## Caching

Expensive computations (lifelines survival fits, competing risks) are wrapped with the decorator from `modules/cache_utils.py`:

```python
from modules.cache_utils import cache_survival_result

@cache_survival_result
def expensive_calculation(data, params):
    ...
```

Characteristics: **in-memory only** (no disk persistence), cleared on restart, cache keys use content hashes (no PHI), session-scoped.

## Styling conventions

Figures from `visualizations/allogreffes/graphs.py` share a consistent look:

- Primary `#0D3182` (dark blue), secondary `#2E86AB`, accent `#c0392b` (AlloGraph red)
- Background `#f8f9fa`
- Palette `px.colors.qualitative.Safe`

Reuse these constants for any new figure.

## Code conventions

- Comments and docstrings: **French** (Google-style docstrings); user-facing text: **English**
- `snake_case` functions/variables, `UPPER_CASE` constants, `PascalCase` classes
- Heavy callbacks use `prevent_initial_call=True` to avoid running on page load
