# pages/sandbox.py
import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Import des modules communs
import modules.dashboard_layout as layouts


def get_layout():
    """Retourne le layout de la page Sandbox pour créer des visualisations personnalisées"""
    return dbc.Container([
        dbc.Tabs([
            dbc.Tab(
                label="Visualization",
                tab_id="tab-viz",
                children=[
                    dcc.Loading(
                        id="loading-sandbox-viz",
                        type="circle",
                        children=html.Div(
                            id='sandbox-chart-container',
                            style={'minHeight': '700px', 'paddingTop': '10px'}
                        )
                    )
                ]
            ),
            dbc.Tab(
                label="Data Summary",
                tab_id="tab-data",
                children=[
                    html.Div([
                        dbc.Button(
                            [html.I(className="bi bi-download me-2"), "Export Data"],
                            id="sandbox-export-btn",
                            color="secondary",
                            size="sm",
                            className="mb-2 mt-2"
                        ),
                        html.Div(
                            id='sandbox-summary-table',
                            style={'maxHeight': '500px', 'overflow': 'auto'}
                        ),
                    ])
                ]
            )
        ], id="sandbox-tabs", active_tab="tab-viz"),
        dcc.Download(id="sandbox-download-data")
    ], fluid=True)


def create_sandbox_sidebar_content(data):
    """
    Crée le contenu de la sidebar spécifique à la page Sandbox.
    Inspiré du flexdashboard shiny-ggplot2-diamonds.
    """
    if data is None or len(data) == 0:
        return html.Div([
            html.P('No data available', className='text-warning')
        ])
    
    df = pd.DataFrame(data)
    n_rows = len(df)
    
    # Variables
    numeric_cols = sorted(df.select_dtypes(include=['number']).columns.tolist())
    datetime_cols = sorted(df.select_dtypes(include=['datetime64']).columns.tolist())
    categorical_cols = sorted([c for c in df.columns if c not in numeric_cols and c not in datetime_cols])
    factor_cols = sorted([c for c in df.columns if df[c].dtype.name in ['object', 'category', 'bool']])
    
    variable_options = []
    if numeric_cols:
        variable_options.append({'label': '── Numeric ──', 'value': '', 'disabled': True})
        variable_options.extend([{'label': col, 'value': col} for col in numeric_cols])
    if datetime_cols:
        variable_options.append({'label': '── Date ──', 'value': '', 'disabled': True})
        variable_options.extend([{'label': col, 'value': col} for col in datetime_cols])
    if categorical_cols:
        variable_options.append({'label': '── Categorical ──', 'value': '', 'disabled': True})
        variable_options.extend([{'label': col, 'value': col} for col in categorical_cols])
    
    optional_variable_options = [{'label': 'None', 'value': ''}] + variable_options
    facet_options = [{'label': 'None', 'value': ''}] + [{'label': col, 'value': col} for col in factor_cols]
    
    # Années
    years_options = []
    if 'Year' in df.columns:
        years_options = [{'label': str(y), 'value': y} for y in sorted(df['Year'].unique().tolist())]
    
    default_sample = min(1000, n_rows)
    
    return html.Div([
        # ========== CHART CONFIGURATION ==========
        html.H6("Chart", className="mb-2", style={'color': '#021F59', 'fontWeight': '700'}),
        
        html.Label('Plot Type:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
        dcc.Dropdown(
            id='sandbox-plot-type',
            options=[
                {'label': 'Scatter', 'value': 'scatter'},
                {'label': 'Bar', 'value': 'bar'},
                {'label': 'Line', 'value': 'line'},
            ],
            value='scatter',
            clearable=False,
            className='mb-2',
            style={'fontSize': '12px'}
        ),
        
        html.Label('X Variable:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
        dcc.Dropdown(
            id='sandbox-x-variable',
            options=variable_options,
            placeholder='Select X...',
            clearable=True,
            className='mb-2',
            style={'fontSize': '12px'}
        ),
        
        html.Label('Y Variable:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
        dcc.Dropdown(
            id='sandbox-y-variable',
            options=optional_variable_options,
            placeholder='Select Y (optional)...',
            clearable=True,
            className='mb-2',
            style={'fontSize': '12px'}
        ),
        
        html.Label('Color/Group:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
        dcc.Dropdown(
            id='sandbox-color-variable',
            options=optional_variable_options,
            placeholder='Color by (optional)...',
            clearable=True,
            className='mb-2',
            style={'fontSize': '12px'}
        ),
        
        html.Label('Facet Row:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
        dcc.Dropdown(
            id='sandbox-facet-row',
            options=facet_options,
            placeholder='Row facet (optional)...',
            clearable=True,
            className='mb-2',
            style={'fontSize': '12px'}
        ),
        
        html.Label('Facet Column:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
        dcc.Dropdown(
            id='sandbox-facet-col',
            options=facet_options,
            placeholder='Column facet (optional)...',
            clearable=True,
            className='mb-2',
            style={'fontSize': '12px'}
        ),
        
        # Options contextuelles
        html.Div(
            id='sandbox-scatter-options',
            children=[
                dbc.Checklist(
                    options=[
                        {'label': ' Jitter', 'value': 'jitter'},
                        {'label': ' Trendline', 'value': 'trendline'},
                    ],
                    value=['jitter'],
                    id='sandbox-scatter-checklist',
                    inline=False,
                    className='mb-2',
                    style={'fontSize': '12px'}
                ),
            ],
            style={'display': 'block'}
        ),
        
        html.Div(
            id='sandbox-aggregation-option',
            children=[
                html.Label('Aggregation:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
                dcc.Dropdown(
                    id='sandbox-aggregation',
                    options=[
                        {'label': 'Count', 'value': 'count'},
                        {'label': 'Mean', 'value': 'mean'},
                        {'label': 'Median', 'value': 'median'},
                        {'label': 'Sum', 'value': 'sum'},
                        {'label': 'Min', 'value': 'min'},
                        {'label': 'Max', 'value': 'max'},
                        {'label': 'Std', 'value': 'std'},
                    ],
                    value='count',
                    clearable=False,
                    className='mb-2',
                    style={'fontSize': '12px'}
                ),
            ],
            style={'display': 'none'}
        ),
        
        html.Hr(style={'margin': '10px 0'}),
        
        # ========== DATA ==========
        html.H6("Data", className="mb-2", style={'color': '#021F59', 'fontWeight': '700'}),
        
        # Filtres médicaux compacts
        html.Div([
            html.Label('Filter by Year:', className='mb-1', style={'fontSize': '12px'}),
            dcc.Checklist(
                id='sandbox-year-filter',
                options=years_options,
                value=[y['value'] for y in years_options],
                inline=False,
                className='mb-2',
                style={'fontSize': '11px'}
            ),
            html.Hr(style={'margin': '8px 0'}),
            layouts.create_age_filter_component(component_id='sandbox-age-filter', title='Age groups'),
            html.Hr(style={'margin': '8px 0'}),
            layouts.create_malignancy_filter_component(component_id='sandbox-malignancy-filter', title='Diagnosis type'),
        ], style={'backgroundColor': '#f8f9fa', 'padding': '8px', 'borderRadius': '4px'}),
        
        html.Hr(style={'margin': '10px 0'}),
        
        # Mini info
        html.Div([
            html.P(["Obs: ", html.Strong(f"{n_rows:,}")], className="mb-0", style={'fontSize': '11px'}),
            html.P(["Vars: ", html.Strong(f"{len(df.columns)}")], className="mb-0", style={'fontSize': '11px'}),
        ])
    ])


def register_callbacks(app):
    """Enregistre tous les callbacks spécifiques à la page Sandbox"""
    
    @app.callback(
        [Output('sandbox-scatter-options', 'style'),
         Output('sandbox-aggregation-option', 'style')],
        [Input('sandbox-plot-type', 'value')]
    )
    def update_contextual_options(plot_type):
        if plot_type == 'scatter':
            return {'display': 'block'}, {'display': 'none'}
        elif plot_type in ['bar', 'line']:
            return {'display': 'none'}, {'display': 'block'}
        return {'display': 'none'}, {'display': 'none'}
    
    @app.callback(
        [Output('sandbox-scatter-checklist', 'options'),
         Output('sandbox-scatter-checklist', 'value')],
        [Input('sandbox-x-variable', 'value'),
         Input('sandbox-y-variable', 'value'),
         Input('sandbox-plot-type', 'value')],
        [State('data-store', 'data'),
         State('sandbox-scatter-checklist', 'value')]
    )
    def update_scatter_checklist(x_var, y_var, plot_type, data, current_value):
        if plot_type != 'scatter' or data is None:
            return dash.no_update, dash.no_update
        
        df = pd.DataFrame(data)
        
        def is_continuous(col):
            if not col or col not in df.columns:
                return False
            return pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_datetime64_any_dtype(df[col])
        
        trendline_disabled = not (is_continuous(x_var) and is_continuous(y_var) and y_var)
        
        options = [
            {'label': ' Jitter', 'value': 'jitter'},
            {'label': ' Trendline', 'value': 'trendline', 'disabled': trendline_disabled},
        ]
        
        new_value = list(current_value or [])
        if trendline_disabled and 'trendline' in new_value:
            new_value.remove('trendline')
        
        return options, new_value
    
    @app.callback(
        [Output('sandbox-chart-container', 'children'),
         Output('sandbox-summary-table', 'children')],
        [Input('sandbox-plot-type', 'value'),
         Input('sandbox-x-variable', 'value'),
         Input('sandbox-y-variable', 'value'),
         Input('sandbox-color-variable', 'value'),
         Input('sandbox-facet-row', 'value'),
         Input('sandbox-facet-col', 'value'),
         Input('sandbox-aggregation', 'value'),
         Input('sandbox-scatter-checklist', 'value'),
         Input('sandbox-year-filter', 'value'),
         Input('sandbox-age-filter', 'value'),
         Input('sandbox-malignancy-filter', 'value'),
         Input('data-store', 'data'),
         Input('current-page', 'data')]
    )
    def render_sandbox(plot_type, x_var, y_var, color_var, facet_row, facet_col,
                       aggregation, scatter_opts, selected_years,
                       selected_age_groups, malignancy_filter, data, current_page):
        """Génère le graphique et le résumé des données"""
        
        if current_page != 'Sandbox' or data is None:
            return dbc.Alert("Please load data first", color="warning"), html.Div()
        
        if not plot_type:
            return dbc.Alert("Please select a plot type", color="info"), html.Div()
        
        if not x_var:
            return dbc.Alert("Please select an X variable", color="info"), html.Div()
        
        df = pd.DataFrame(data)
        
        # Filtres
        if selected_years and 'Year' in df.columns:
            df = df[df['Year'].isin(selected_years)]
        
        if selected_age_groups and 'Age Group Detailed' in df.columns:
            df = df[df['Age Group Detailed'].isin(selected_age_groups)]
        
        df = layouts.apply_malignancy_filter(df, malignancy_filter)
        
        if df.empty:
            return dbc.Alert("No data available with the selected filters", color="warning"), html.Div()
        
        if x_var not in df.columns:
            return dbc.Alert(f"Column '{x_var}' not found", color="warning"), html.Div()
        
        if y_var and y_var not in df.columns:
            y_var = None
        if color_var and color_var not in df.columns:
            color_var = None
        if facet_row and facet_row not in df.columns:
            facet_row = None
        if facet_col and facet_col not in df.columns:
            facet_col = None
        
        jitter = 'jitter' in (scatter_opts or [])
        trendline = 'trendline' in (scatter_opts or [])
        
        try:
            fig = create_plot(
                data=df,
                x_var=x_var,
                y_var=y_var,
                color_var=color_var,
                facet_row=facet_row,
                facet_col=facet_col,
                plot_type=plot_type,
                aggregation=aggregation,
                jitter=jitter,
                trendline=trendline
            )
            
            summary = create_data_summary(df, x_var, y_var, color_var)
            
            graph = dcc.Graph(
                figure=fig,
                style={'height': '700px'},
                config={'responsive': True, 'displayModeBar': True}
            )
            
            return graph, summary
            
        except Exception as e:
            return dbc.Alert(f"Error generating chart: {str(e)}", color="danger"), html.Div()
    
    @app.callback(
        Output("sandbox-download-data", "data"),
        [Input("sandbox-export-btn", "n_clicks")],
        [State('data-store', 'data'),
         State('sandbox-x-variable', 'value'),
         State('sandbox-y-variable', 'value'),
         State('sandbox-color-variable', 'value'),
         State('sandbox-facet-row', 'value'),
         State('sandbox-facet-col', 'value'),
         State('sandbox-year-filter', 'value'),
         State('sandbox-age-filter', 'value'),
         State('sandbox-malignancy-filter', 'value')],
        prevent_initial_call=True
    )
    def export_chart_data(n_clicks, data, x_var, y_var, color_var, facet_row, facet_col,
                          selected_years, selected_age_groups, malignancy_filter):
        """Exporte les données utilisées pour le graphique"""
        if n_clicks is None or data is None:
            return dash.no_update
        
        try:
            df = pd.DataFrame(data)
            
            if selected_years and 'Year' in df.columns:
                df = df[df['Year'].isin(selected_years)]
            
            if selected_age_groups and 'Age Group Detailed' in df.columns:
                df = df[df['Age Group Detailed'].isin(selected_age_groups)]
            
            df = layouts.apply_malignancy_filter(df, malignancy_filter)
            
            cols = [c for c in [x_var, y_var, color_var, facet_row, facet_col] if c and c in df.columns]
            export_df = df[cols].copy() if cols else df.head(1000).copy()
            
            from datetime import datetime
            filename = f"sandbox_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return dcc.send_data_frame(export_df.to_csv, filename=filename, index=False)
            
        except Exception as e:
            print(f"Error during export: {e}")
            return dash.no_update


def _is_continuous(data, col):
    """Vérifie si une colonne est continue (numérique ou datetime)."""
    if not col or col not in data.columns:
        return False
    return pd.api.types.is_numeric_dtype(data[col]) or pd.api.types.is_datetime64_any_dtype(data[col])


def create_plot(data, x_var, y_var, color_var, facet_row, facet_col,
                plot_type, aggregation, jitter=False, trendline=False):
    """Crée un graphique Plotly selon les paramètres spécifiés."""
    
    color_param = color_var if color_var else None
    x_is_numeric = pd.api.types.is_numeric_dtype(data[x_var])
    x_is_datetime = pd.api.types.is_datetime64_any_dtype(data[x_var])
    y_is_numeric = y_var and pd.api.types.is_numeric_dtype(data[y_var])
    y_is_categorical = y_var and (pd.api.types.is_categorical_dtype(data[y_var]) or pd.api.types.is_object_dtype(data[y_var]))
    
    facet_kwargs = {}
    if facet_col:
        facet_kwargs['facet_col'] = facet_col
    if facet_row:
        facet_kwargs['facet_row'] = facet_row
    
    if plot_type == 'scatter':
        y_to_use = y_var if y_var else x_var
        
        # Jitter : si X est catégoriel et jitter=True, utiliser strip plot
        use_strip = jitter and not x_is_numeric
        
        if use_strip:
            fig = px.strip(
                data,
                x=x_var,
                y=y_to_use,
                color=color_param,
                title=f"Scatter: {y_to_use} vs {x_var}",
                height=700,
                **facet_kwargs
            )
        else:
            plot_data = data.copy()
            if jitter and x_is_numeric:
                # Jitter numérique : ajouter un peu de bruit
                x_range = plot_data[x_var].max() - plot_data[x_var].min()
                jitter_amount = x_range * 0.01 if x_range > 0 else 0.1
                plot_data[x_var] = plot_data[x_var] + np.random.normal(0, jitter_amount, len(plot_data))
                title = f"Scatter: {y_to_use} vs {x_var} (jittered)"
            else:
                title = f"Scatter: {y_to_use} vs {x_var}"
            
            fig = px.scatter(
                plot_data,
                x=x_var,
                y=y_to_use,
                color=color_param,
                title=title,
                height=700,
                opacity=0.6,
                **facet_kwargs
            )
            
            # Trendline manuelle (sans statsmodels)
            if trendline and y_var and _is_continuous(data, x_var) and _is_continuous(data, y_var):
                mask = data[[x_var, y_var]].notna().all(axis=1)
                x_clean = data.loc[mask, x_var]
                y_clean = data.loc[mask, y_var]
                if len(x_clean) > 1:
                    try:
                        # Conversion datetime -> timestamp numérique pour np.polyfit
                        x_fit = x_clean.astype('int64') / 1e9 if pd.api.types.is_datetime64_any_dtype(x_clean) else x_clean
                        y_fit = y_clean.astype('int64') / 1e9 if pd.api.types.is_datetime64_any_dtype(y_clean) else y_clean
                        
                        coeffs = np.polyfit(x_fit, y_fit, 1)
                        x_line = np.linspace(x_fit.min(), x_fit.max(), 100)
                        y_line = coeffs[0] * x_line + coeffs[1]
                        
                        # Reconversion pour l'affichage si besoin
                        if pd.api.types.is_datetime64_any_dtype(x_clean):
                            x_line = pd.to_datetime(x_line * 1e9)
                        if pd.api.types.is_datetime64_any_dtype(y_clean):
                            y_line = pd.to_datetime(y_line * 1e9)
                        
                        fig.add_trace(go.Scatter(
                            x=x_line,
                            y=y_line,
                            mode='lines',
                            name='Trendline',
                            line=dict(color='red', dash='dash'),
                            showlegend=True
                        ))
                    except Exception:
                        pass
    
    elif plot_type == 'bar':
        if y_var and y_is_categorical:
            # Stacked bar
            group_cols = [x_var, y_var]
            if facet_row and facet_row in data.columns:
                group_cols.append(facet_row)
            if facet_col and facet_col in data.columns:
                group_cols.append(facet_col)
            count_data = data.groupby(group_cols).size().reset_index(name='count')
            fig = px.bar(
                count_data,
                x=x_var,
                y='count',
                color=y_var,
                title=f"Bar: Distribution of {y_var} by {x_var}",
                height=700,
                barmode='stack',
                **facet_kwargs
            )
        elif y_var and y_is_numeric:
            agg_data = aggregate_data(data, x_var, y_var, color_param, aggregation, facet_row, facet_col)
            fig = px.bar(
                agg_data,
                x=x_var,
                y='value',
                color=color_param,
                title=f"Bar: {aggregation} of {y_var} by {x_var}",
                height=700,
                **facet_kwargs
            )
        else:
            group_cols = [x_var]
            if facet_row and facet_row in data.columns:
                group_cols.append(facet_row)
            if facet_col and facet_col in data.columns:
                group_cols.append(facet_col)
            if color_param and color_param in data.columns:
                group_cols.append(color_param)
            count_data = data.groupby(group_cols).size().reset_index(name='count')
            fig = px.bar(
                count_data,
                x=x_var,
                y='count',
                color=color_param if color_param else None,
                title=f"Bar: Count by {x_var}",
                height=700,
                **facet_kwargs
            )
    
    elif plot_type == 'line':
        if y_var and y_is_numeric:
            agg_data = aggregate_data(data, x_var, y_var, color_param, aggregation, facet_row, facet_col)
            fig = px.line(
                agg_data,
                x=x_var,
                y='value',
                color=color_param,
                title=f"Line: {aggregation} of {y_var} by {x_var}",
                height=700,
                markers=True,
                **facet_kwargs
            )
        else:
            group_cols = [x_var]
            if facet_row and facet_row in data.columns:
                group_cols.append(facet_row)
            if facet_col and facet_col in data.columns:
                group_cols.append(facet_col)
            if color_param and color_param in data.columns:
                group_cols.append(color_param)
            count_data = data.groupby(group_cols).size().reset_index(name='count')
            fig = px.line(
                count_data,
                x=x_var,
                y='count',
                color=color_param,
                title=f"Line: Count by {x_var}",
                height=700,
                markers=True,
                **facet_kwargs
            )
    else:
        fig = px.scatter(data, x=x_var, y=y_var or x_var, color=color_param, height=700)
    
    # Style
    fig.update_layout(
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=80, r=20, b=50, l=60)
    )
    
    if not x_is_numeric and len(data[x_var].unique()) > 5:
        fig.update_xaxes(tickangle=45)
    
    return fig


def aggregate_data(data, x_var, y_var, color_var, aggregation, facet_row=None, facet_col=None):
    """Agrège les données pour les graphiques de type bar/line."""
    group_cols = [x_var]
    if facet_row and facet_row in data.columns:
        group_cols.append(facet_row)
    if facet_col and facet_col in data.columns:
        group_cols.append(facet_col)
    if color_var and color_var in data.columns:
        group_cols.append(color_var)
    
    agg_func = {
        'count': 'count',
        'sum': 'sum',
        'mean': 'mean',
        'median': 'median',
        'min': 'min',
        'max': 'max',
        'std': 'std'
    }.get(aggregation, 'count')
    
    agg_data = data.groupby(group_cols)[y_var].agg(agg_func).reset_index()
    agg_data.columns = group_cols + ['value']
    return agg_data


def create_data_summary(data, x_var, y_var, color_var):
    """Crée un tableau résumé compact des données."""
    summary_rows = []
    
    for var, label in [(x_var, 'X'), (y_var, 'Y'), (color_var, 'Color')]:
        if not var or var not in data.columns:
            continue
        if pd.api.types.is_numeric_dtype(data[var]):
            stats = data[var].describe()
            summary_rows.append({
                'Role': label,
                'Variable': var,
                'Type': 'Numeric',
                'Count': f"{int(stats['count']):,}",
                'Mean': f"{stats['mean']:.2f}",
                'Std': f"{stats['std']:.2f}",
                'Min': f"{stats['min']:.2f}",
                'Max': f"{stats['max']:.2f}",
                'Missing': f"{data[var].isna().sum():,}"
            })
        else:
            summary_rows.append({
                'Role': label,
                'Variable': var,
                'Type': 'Categorical',
                'Count': f"{len(data):,}",
                'Mean': '-',
                'Std': '-',
                'Min': '-',
                'Max': '-',
                'Missing': f"{data[var].isna().sum():,}"
            })
    
    if not summary_rows:
        return html.P("No variables selected.")
    
    columns = [
        {"name": "Role", "id": "Role"},
        {"name": "Variable", "id": "Variable"},
        {"name": "Type", "id": "Type"},
        {"name": "Count", "id": "Count"},
        {"name": "Mean", "id": "Mean"},
        {"name": "Std", "id": "Std"},
        {"name": "Min", "id": "Min"},
        {"name": "Max", "id": "Max"},
        {"name": "Missing", "id": "Missing"},
    ]
    
    return dash_table.DataTable(
        data=summary_rows,
        columns=columns,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'center',
            'padding': '8px',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '12px'
        },
        style_header={
            'backgroundColor': '#021F59',
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'}
        ]
    )
