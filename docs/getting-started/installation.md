# Installation

## Requirements

- **Python 3.10** (see `.python-version`)
- All runtime dependencies are pinned in `requirements.txt`

## Local setup

```bash
# Create and activate a virtual environment
python -m venv .venv
# Windows (Git Bash)
source .venv/Scripts/activate
# Linux/macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
python app.py
# -> http://127.0.0.1:8000
```

### Key dependencies

| Area | Packages |
|---|---|
| Web framework | Dash 2.18.2, dash-bootstrap-components 1.5.0, dash_extensions 1.0.20 |
| Visualizations | Plotly 5.17.0 |
| Data | pandas 2.1.4, numpy 1.24.3, openpyxl 3.1.2, xlrd 2.0.1 |
| Statistics | scipy 1.11.4, lifelines 0.27.7 (optional but recommended) |
| Production | gunicorn 21.2.0 |

!!! note "Optional dependencies"
    - `lifelines` — required for survival curves (Kaplan–Meier). The app starts without it but survival analyses are disabled (a warning is printed).
    - `flask-compress` — enables gzip compression of responses. Optional, recommended for VM deployments (see [Deployment & performance](../deployment.md)).

## DevContainer

The project ships a `.devcontainer/devcontainer.json` for GitHub Codespaces or the VS Code Dev Containers extension. It uses a Python 3.11 image, installs `requirements.txt`, and configures the Python extension. Opening the project in a container gives you a ready-to-run environment.

## Sample data

`data/test_sample.csv` is a de-identified dataset you can use to exercise every page without real patient data. The Home page has a **Load test sample** button that loads it directly. `data/import_template_allograph.xlsx` is the import template showing the expected columns.

## Verifying your setup

1. Start the app and load the test sample.
2. Navigate through all analysis pages (Patients, Hémopathies, Procedures, GvH, Relapse, Survival, Toxicity, Indicators).
3. Check that visualizations render and that sidebar filters update them.

There is currently no automated test suite for the application logic; verification is manual as described above.
