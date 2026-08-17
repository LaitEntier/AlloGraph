# AlloGraph — Developer Documentation

AlloGraph is a web application for the analysis of **allogeneic hematopoietic stem cell transplantation (allo-HSCT)** data. It is built with **Dash** and **Plotly** and gives clinicians and researchers reproducible analytical tools compatible with common HSCT registry structures, including the **EBMT Registry** format.

Analyses covered: patient demographics, disease distributions, transplant procedures, GvHD, relapse, toxicity, survival (Kaplan–Meier), competing risks, and a clinical indicators dashboard.

## Quickstart

```bash
pip install -r requirements.txt
python app.py
# Server starts at http://127.0.0.1:8000
```

Then open the app, click **Load test sample** on the Home page (or upload `data/test_sample.csv`), and navigate through the pages.

## Where to go next

- **New to the project?** Start with [Installation](getting-started/installation.md), then [Architecture](getting-started/architecture.md).
- **Adding a feature?** See the [how-to guides](guides/add-page.md) (new page, new visualization, data pipeline changes).
- **Working with the data?** Check the [expected data format](data-format.md).
- **Deploying or tuning performance?** See [Deployment & performance](deployment.md).
- **Looking up a function?** Browse the [API reference](reference/index.md), generated from the source docstrings.

## Documentation conventions

- This site is built with [MkDocs](https://www.mkdocs.org/) + [mkdocstrings](https://mkdocstrings.github.io/) (API reference generated automatically from docstrings).
- The API reference reflects the docstrings in the source — **keep docstrings up to date when you change a function signature**. Docstrings use Google style and are written in French (project convention).
- To preview this site locally:

```bash
pip install -r requirements-docs.txt
mkdocs serve   # http://127.0.0.1:8000... (default 8000, use -a if the app runs too)
```
