# Adding a new visualization

## 1. Write the figure factory

Add a function in `visualizations/allogreffes/graphs.py`. Conventions:

- Take a pandas DataFrame (+ explicit parameters) and return a `plotly.graph_objects.Figure`
- Handle the empty-data case gracefully (return an empty figure with a message rather than raising)
- Reuse the shared styling constants defined at the top of the module:

| Constant | Value | Use |
|---|---|---|
| Primary color | `#0D3182` | main series |
| Secondary color | `#2E86AB` | secondary series |
| Accent color | `#c0392b` | highlights, warnings |
| Background | `#f8f9fa` | plot/paper background |
| Palette | `px.colors.qualitative.Safe` | categorical series |

## 2. Wire it into a page

In the page module (`pages/…`):

1. Add a container in `get_layout()` — typically `dcc.Graph(id='my-graph')` inside a `dbc.Card`.
2. Add a callback in `register_callbacks(app)` that reads the appropriate store (usually `data-store-viz`), applies the page filters, calls your figure factory, and returns the figure.

```python
@app.callback(
    Output('my-graph', 'figure'),
    Input('data-store-viz', 'data'),
    Input('my-filter-dropdown', 'value'),
    prevent_initial_call=True,
)
def update_my_graph(data, filter_value):
    df = pd.DataFrame(data)
    return gr.my_new_figure(df, filter_value)
```

## 3. If it is a reusable filter, not a figure

Sidebar controls and cross-page filters belong in `modules/dashboard_layout.py`, not in a page module. Existing helpers (`apply_age_filter`, `apply_malignancy_filter`, `register_age_toggle_callback`) are the pattern to follow.

## Special case: UpSet plots

`visualizations/allogreffes/upsetjs_embed.py` renders a **pure-SVG interactive UpSet plot** (no external JS dependency, no CORB issues) used for conditioning/prophylaxis combination analysis on the Procedures page. If you need an UpSet for another set of binary indicators, reuse that module rather than adding a JS dependency.
