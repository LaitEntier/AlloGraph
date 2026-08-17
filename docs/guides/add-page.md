# Adding a new analysis page

Pages are hand-wired in `app.py`. Adding one takes five steps.

## 1. Create the page module

Create `pages/my_analysis.py` with the two conventional entry points:

```python
# pages/my_analysis.py
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

import modules.dashboard_layout as layouts
import visualizations.allogreffes.graphs as gr


def get_layout():
    """Retourne le layout de la page."""
    return dbc.Container([
        # sidebar controls + graph containers
    ])


def register_callbacks(app):
    """Enregistre les callbacks de la page."""

    @app.callback(
        Output('my-graph', 'figure'),
        Input('data-store-viz', 'data'),
        prevent_initial_call=True,
    )
    def update_graph(data):
        ...
```

Look at an existing page close to your need (`pages/patients.py` for distributions, `pages/procedures.py` for tabs) and copy its structure — sidebar builders and filters already exist in `modules/dashboard_layout.py` (`apply_malignancy_filter`, `apply_age_filter`, `register_age_toggle_callback`, …).

## 2. Import and register in `app.py`

```python
import pages.my_analysis as my_analysis_page
```

Then, where the other pages are registered:

```python
my_analysis_page.register_callbacks(app)
```

## 3. Route the page in the navigation callback

`app.py` contains the global navigation callback that maps the current URL (or nav button clicks) to a page layout. Add your page there so `my_analysis_page.get_layout()` is returned for its route.

## 4. Add the navigation button

Add a sidebar button in `modules/dashboard_layout.py`, where the other nav buttons are built.

## 5. Checklist before committing

- [ ] Page renders with the test sample loaded (`data/test_sample.csv`)
- [ ] Page behaves sanely with **no data loaded** (empty-state message, no traceback)
- [ ] Sidebar filters update the figures
- [ ] Heavy callbacks use `prevent_initial_call=True`
- [ ] New derived columns, if any, are added to the relevant slim stores (see [Architecture](../getting-started/architecture.md#slim-data-stores))
