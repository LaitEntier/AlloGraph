# pages/sandbox.py
import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import des modules communs
import modules.dashboard_layout as layouts
import visualizations.allogreffes.graphs as gr


def get_layout():
    """Retourne le layout de la page Sandbox pour créer des visualisations personnalisées"""
    return dbc.Container([
        # Zone du graphique
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5('Visualization', className='mb-0'),
                        html.Small(id='sandbox-chart-description', style={'color': '#ffffff'})
                    ]),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-sandbox",
                            type="circle",
                            children=html.Div(
                                id='sandbox-chart-container',
                                style={'minHeight': '500px'}
                            )
                        )
                    ])
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Data Summary Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5('Data Summary', className='mb-0'),
                        dbc.Button(
                            [html.I(className="bi bi-download me-2"), "Export Data"],
                            id="sandbox-export-btn",
                            color="secondary",
                            size="sm",
                            className="float-end"
                        ),
                    ]),
                    dbc.CardBody([
                        html.Div(
                            id='sandbox-summary-table',
                            style={'maxHeight': '400px', 'overflow': 'auto'}
                        ),
                        dcc.Download(id="sandbox-download-data")
                    ])
                ])
            ], width=12)
        ]),
        
    ], fluid=True)


def create_sandbox_sidebar_content(data):
    """
    Crée le contenu de la sidebar spécifique à la page Sandbox avec les contrôles de configuration.
    
    Args:
        data (list): Liste de dictionnaires (format store Dash) avec les données
        
    Returns:
        html.Div: Contenu de la sidebar
    """
    if data is None or len(data) == 0:
        return html.Div([
            html.P('No data available', className='text-warning')
        ])
    
    df = pd.DataFrame(data)
    
    # Obtenir les années disponibles pour les filtres
    years_options = []
    if 'Year' in df.columns:
        available_years = sorted(df['Year'].unique().tolist())
        years_options = [{'label': f'{year}', 'value': year} for year in available_years]
    
    # Préparer les options de variables
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    all_cols = sorted(numeric_cols + categorical_cols)
    
    variable_options = []
    if numeric_cols:
        variable_options.append({'label': '── Numeric ──', 'value': '', 'disabled': True})
        variable_options.extend([{'label': col, 'value': col} for col in sorted(numeric_cols)])
    if categorical_cols:
        variable_options.append({'label': '── Categorical ──', 'value': '', 'disabled': True})
        variable_options.extend([{'label': col, 'value': col} for col in sorted(categorical_cols)])
    
    # Options avec "None" pour les variables optionnelles
    optional_variable_options = [{'label': 'None', 'value': ''}] + variable_options
    
    return html.Div([
        # Section Configuration
        html.H6("Chart Configuration", className="mb-3", style={'color': '#021F59', 'fontWeight': '700'}),
        
        # X Variable
        html.Label('X Variable:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
        dcc.Dropdown(
            id='sandbox-x-variable',
            options=variable_options,
            placeholder='Select X...',
            clearable=True,
            className='mb-3',
            style={'fontSize': '12px'}
        ),
        
        # Y Variable
        html.Label('Y Variable:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
        dcc.Dropdown(
            id='sandbox-y-variable',
            options=optional_variable_options,
            placeholder='Select Y (optional)...',
            clearable=True,
            className='mb-3',
            style={'fontSize': '12px'}
        ),
        
        # Color Variable
        html.Label('Color/Group:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
        dcc.Dropdown(
            id='sandbox-color-variable',
            options=optional_variable_options,
            placeholder='Color by (optional)...',
            clearable=True,
            className='mb-3',
            style={'fontSize': '12px'}
        ),
        
        # Facet Variable
        html.Label('Subdivide by:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
        dcc.Dropdown(
            id='sandbox-facet-variable',
            options=optional_variable_options,
            placeholder='Facet by (optional)...',
            clearable=True,
            className='mb-3',
            style={'fontSize': '12px'}
        ),
        
        html.Hr(style={'margin': '15px 0'}),
        
        # Plot Type
        html.Label('Plot Type:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
        dcc.Dropdown(
            id='sandbox-plot-type',
            options=[
                {'label': 'Scatter Plot', 'value': 'scatter'},
                {'label': 'Line Chart', 'value': 'line'},
                {'label': 'Bar Chart', 'value': 'bar'},
                {'label': 'Box Plot', 'value': 'box'},
                {'label': 'Histogram', 'value': 'histogram'},
                {'label': 'Violin Plot', 'value': 'violin'},
                {'label': 'Density Plot', 'value': 'density'},
                {'label': 'Strip Plot', 'value': 'strip'},
            ],
            value='scatter',
            clearable=False,
            className='mb-3',
            style={'fontSize': '12px'}
        ),
        
        # Aggregation
        html.Label('Aggregation:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
        dcc.Dropdown(
            id='sandbox-aggregation',
            options=[
                {'label': 'Count', 'value': 'count'},
                {'label': 'Sum', 'value': 'sum'},
                {'label': 'Mean', 'value': 'mean'},
                {'label': 'Median', 'value': 'median'},
                {'label': 'Min', 'value': 'min'},
                {'label': 'Max', 'value': 'max'},
                {'label': 'Std', 'value': 'std'},
            ],
            value='count',
            clearable=False,
            className='mb-3',
            style={'fontSize': '12px'}
        ),
        
        # Orientation
        html.Label('Orientation:', className='mb-1', style={'fontSize': '12px', 'fontWeight': '600'}),
        dcc.Dropdown(
            id='sandbox-orientation',
            options=[
                {'label': 'Vertical', 'value': 'v'},
                {'label': 'Horizontal', 'value': 'h'},
            ],
            value='v',
            clearable=False,
            className='mb-3',
            style={'fontSize': '12px'}
        ),
        
        html.Hr(style={'margin': '15px 0'}),
        
        # Section Filtres
        html.H6("Data Filters", className="mb-3", style={'color': '#021F59', 'fontWeight': '700'}),
        
        # Filtres par année
        html.Label('Filter by Year:', className='mb-1', style={'fontSize': '12px'}),
        dcc.Checklist(
            id='sandbox-year-filter',
            options=years_options,
            value=[year['value'] for year in years_options],
            inline=False,
            className='mb-3',
            style={'fontSize': '11px'}
        ),
        
        html.Hr(style={'margin': '10px 0'}),
        
        # Filtres par tranche d'âge
        layouts.create_age_filter_component(component_id='sandbox-age-filter', title='Age groups'),
        
        html.Hr(style={'margin': '10px 0'}),
        
        # Filtres par type de diagnostic
        layouts.create_malignancy_filter_component(component_id='sandbox-malignancy-filter', title='Diagnosis type'),
        
        html.Hr(style={'margin': '10px 0'}),
        
        # Informations sur les données
        html.Div([
            html.H6("📊 Data Info", className="mb-2", style={'fontSize': '12px'}),
            html.P([
                "Patients: ", html.Strong(f"{len(df):,}")
            ], className="mb-1", style={'fontSize': '11px'}),
            html.P([
                "Variables: ", html.Strong(f"{len(df.columns):,}")
            ], className="mb-1", style={'fontSize': '11px'}),
            html.P([
                "Years: ", html.Strong(f"{len(df['Year'].unique()) if 'Year' in df.columns else 0}")
            ], className="mb-0", style={'fontSize': '11px'})
        ])
    ])


def register_callbacks(app):
    """Enregistre tous les callbacks spécifiques à la page Sandbox"""
    
    @app.callback(
        [Output('sandbox-y-variable', 'disabled'),
         Output('sandbox-aggregation', 'disabled')],
        [Input('sandbox-plot-type', 'value')]
    )
    def update_controls_state(plot_type):
        """Active/désactive certains contrôles selon le type de graphique"""
        if plot_type in ['histogram']:
            return True, False  # Y désactivé, agrégation activée
        elif plot_type in ['box', 'violin', 'strip']:
            return False, True  # Y activé, agrégation désactivée
        else:
            return False, False  # Tous activés
    
    @app.callback(
        [Output('sandbox-chart-container', 'children'),
         Output('sandbox-chart-description', 'children'),
         Output('sandbox-summary-table', 'children')],
        [Input('sandbox-x-variable', 'value'),
         Input('sandbox-y-variable', 'value'),
         Input('sandbox-color-variable', 'value'),
         Input('sandbox-facet-variable', 'value'),
         Input('sandbox-plot-type', 'value'),
         Input('sandbox-aggregation', 'value'),
         Input('sandbox-orientation', 'value'),
         Input('sandbox-year-filter', 'value'),
         Input('sandbox-age-filter', 'value'),
         Input('sandbox-malignancy-filter', 'value'),
         Input('data-store', 'data'),
         Input('current-page', 'data')]
    )
    def render_chart(x_var, y_var, color_var, facet_var, plot_type, aggregation, orientation,
                     selected_years, selected_age_groups, malignancy_filter, data, current_page):
        """Génère le graphique en temps réel selon les paramètres sélectionnés"""
        
        if current_page != 'Sandbox' or data is None:
            return (
                dbc.Alert("Please load data first", color="warning"),
                "",
                html.Div()
            )
        
        if not x_var:
            return (
                dbc.Alert("Please select an X variable from the sidebar", color="info"),
                "",
                html.Div()
            )
        
        df = pd.DataFrame(data)
        
        # Appliquer les filtres
        filtered_df = df.copy()
        
        # Filtre par année
        if selected_years and 'Year' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Year'].isin(selected_years)]
        
        # Filtre par tranche d'âge
        if selected_age_groups and 'Age Group Detailed' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Age Group Detailed'].isin(selected_age_groups)]
        
        # Filtre par type de diagnostic
        filtered_df = layouts.apply_malignancy_filter(filtered_df, malignancy_filter)
        
        if filtered_df.empty:
            return (
                dbc.Alert("No data available with the selected filters", color="warning"),
                "",
                html.Div()
            )
        
        # Vérifier que les colonnes existent dans les données FILTRÉES
        if x_var not in filtered_df.columns:
            return (
                dbc.Alert(f"Column '{x_var}' not found in filtered data", color="warning"),
                "",
                html.Div()
            )
        
        # Vérifier que Y existe si spécifié
        if y_var and y_var not in filtered_df.columns:
            return (
                dbc.Alert(f"Column '{y_var}' not found in filtered data", color="warning"),
                "",
                html.Div()
            )
        
        # Vérifier que Color existe si spécifié
        if color_var and color_var not in filtered_df.columns:
            color_var = None  # Reset if not in filtered data
        
        # Vérifier que Facet existe si spécifié - CRITICAL FIX
        if facet_var and facet_var not in filtered_df.columns:
            facet_var = None  # Reset if not in filtered data
        
        try:
            # Générer le graphique selon le type
            fig = create_plot(
                data=filtered_df,
                x_var=x_var,
                y_var=y_var,
                color_var=color_var,
                facet_var=facet_var,
                plot_type=plot_type,
                aggregation=aggregation,
                orientation=orientation
            )
            
            # Créer la description
            description = create_chart_description(
                x_var, y_var, color_var, facet_var, plot_type, aggregation, len(filtered_df)
            )
            
            # Créer le résumé des données
            summary_table = create_data_summary(filtered_df, x_var, y_var, color_var)
            
            return (
                dcc.Graph(
                    figure=fig,
                    style={'height': '600px'},
                    config={'responsive': True, 'displayModeBar': True}
                ),
                description,
                summary_table
            )
            
        except Exception as e:
            return (
                dbc.Alert(f"Error generating chart: {str(e)}", color="danger"),
                "",
                html.Div()
            )
    
    @app.callback(
        Output("sandbox-download-data", "data"),
        [Input("sandbox-export-btn", "n_clicks")],
        [State('data-store', 'data'),
         State('sandbox-x-variable', 'value'),
         State('sandbox-y-variable', 'value'),
         State('sandbox-color-variable', 'value'),
         State('sandbox-facet-variable', 'value'),
         State('sandbox-year-filter', 'value'),
         State('sandbox-age-filter', 'value'),
         State('sandbox-malignancy-filter', 'value')],
        prevent_initial_call=True
    )
    def export_chart_data(n_clicks, data, x_var, y_var, color_var, facet_var, 
                          selected_years, selected_age_groups, malignancy_filter):
        """Exporte les données utilisées pour le graphique"""
        if n_clicks is None or data is None:
            return dash.no_update
        
        try:
            df = pd.DataFrame(data)
            
            # Appliquer les mêmes filtres
            if selected_years and 'Year' in df.columns:
                df = df[df['Year'].isin(selected_years)]
            
            if selected_age_groups and 'Age Group Detailed' in df.columns:
                df = df[df['Age Group Detailed'].isin(selected_age_groups)]
            
            df = layouts.apply_malignancy_filter(df, malignancy_filter)
            
            # Sélectionner les colonnes pertinentes
            columns_to_export = [col for col in [x_var, y_var, color_var, facet_var] if col and col in df.columns]
            if columns_to_export:
                export_df = df[columns_to_export].copy()
            else:
                export_df = df.head(1000).copy()
            
            from datetime import datetime
            current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sandbox_data_{current_date}.csv"
            
            return dcc.send_data_frame(
                export_df.to_csv,
                filename=filename,
                index=False
            )
            
        except Exception as e:
            print(f"Error during export: {e}")
            return dash.no_update


def create_plot(data, x_var, y_var, color_var, facet_var, plot_type, aggregation, orientation):
    """
    Crée un graphique Plotly selon les paramètres spécifiés.
    """
    # Paramètres communs
    facet_col = facet_var if facet_var else None
    color_param = color_var if color_var else None
    
    # Déterminer si X est numérique
    x_is_numeric = pd.api.types.is_numeric_dtype(data[x_var])
    
    if plot_type == 'scatter':
        fig = px.scatter(
            data,
            x=x_var,
            y=y_var if y_var else x_var,
            color=color_param,
            facet_col=facet_col,
            facet_col_wrap=3 if facet_col else None,
            title=f"Scatter Plot: {x_var} vs {y_var if y_var else x_var}",
            height=600,
            opacity=0.6
        )
        
    elif plot_type == 'line':
        if y_var and not x_is_numeric:
            agg_data = aggregate_data(data, x_var, y_var, color_param, aggregation)
            fig = px.line(
                agg_data,
                x=x_var,
                y='value',
                color=color_param if color_param else None,
                facet_col=facet_col,
                facet_col_wrap=3 if facet_col else None,
                title=f"Line Chart: {aggregation} of {y_var} by {x_var}",
                height=600,
                markers=True
            )
        else:
            fig = px.line(
                data,
                x=x_var,
                y=y_var if y_var else x_var,
                color=color_param,
                facet_col=facet_col,
                facet_col_wrap=3 if facet_col else None,
                title=f"Line Chart: {x_var} vs {y_var if y_var else x_var}",
                height=600,
                markers=True
            )
            
    elif plot_type == 'bar':
        if y_var:
            agg_data = aggregate_data(data, x_var, y_var, color_param, aggregation)
            
            if orientation == 'h':
                fig = px.bar(
                    agg_data,
                    y=x_var,
                    x='value',
                    color=color_param if color_param else None,
                    facet_col=facet_col,
                    facet_col_wrap=3 if facet_col else None,
                    title=f"Bar Chart: {aggregation} of {y_var} by {x_var}",
                    height=600,
                    orientation='h'
                )
            else:
                fig = px.bar(
                    agg_data,
                    x=x_var,
                    y='value',
                    color=color_param if color_param else None,
                    facet_col=facet_col,
                    facet_col_wrap=3 if facet_col else None,
                    title=f"Bar Chart: {aggregation} of {y_var} by {x_var}",
                    height=600
                )
        else:
            count_data = data[x_var].value_counts().reset_index()
            count_data.columns = [x_var, 'count']
            
            if orientation == 'h':
                fig = px.bar(
                    count_data,
                    y=x_var,
                    x='count',
                    title=f"Bar Chart: Count by {x_var}",
                    height=600,
                    orientation='h'
                )
            else:
                fig = px.bar(
                    count_data,
                    x=x_var,
                    y='count',
                    title=f"Bar Chart: Count by {x_var}",
                    height=600
                )
                
    elif plot_type == 'box':
        if orientation == 'h' and y_var:
            fig = px.box(
                data,
                y=x_var,
                x=y_var,
                color=color_param,
                facet_col=facet_col,
                facet_col_wrap=3 if facet_col else None,
                title=f"Box Plot: {y_var} by {x_var}",
                height=600,
                orientation='h'
            )
        else:
            fig = px.box(
                data,
                x=x_var,
                y=y_var if y_var else x_var,
                color=color_param,
                facet_col=facet_col,
                facet_col_wrap=3 if facet_col else None,
                title=f"Box Plot: {y_var if y_var else x_var} by {x_var}",
                height=600
            )
            
    elif plot_type == 'histogram':
        fig = px.histogram(
            data,
            x=x_var,
            color=color_param,
            facet_col=facet_col,
            facet_col_wrap=3 if facet_col else None,
            title=f"Histogram: Distribution of {x_var}",
            height=600,
            nbins=30,
            marginal="box" if x_is_numeric else None
        )
        
    elif plot_type == 'violin':
        if orientation == 'h' and y_var:
            fig = px.violin(
                data,
                y=x_var,
                x=y_var,
                color=color_param,
                facet_col=facet_col,
                facet_col_wrap=3 if facet_col else None,
                title=f"Violin Plot: {y_var} by {x_var}",
                height=600,
                box=True,
                orientation='h'
            )
        else:
            fig = px.violin(
                data,
                x=x_var,
                y=y_var if y_var else x_var,
                color=color_param,
                facet_col=facet_col,
                facet_col_wrap=3 if facet_col else None,
                title=f"Violin Plot: {y_var if y_var else x_var} by {x_var}",
                height=600,
                box=True
            )
            
    elif plot_type == 'density':
        fig = px.histogram(
            data,
            x=x_var,
            color=color_param,
            facet_col=facet_col,
            facet_col_wrap=3 if facet_col else None,
            title=f"Density Plot: Distribution of {x_var}",
            height=600,
            nbins=50,
            histnorm='density',
            marginal="rug" if x_is_numeric else None
        )
        
    elif plot_type == 'strip':
        if orientation == 'h' and y_var:
            fig = px.strip(
                data,
                y=x_var,
                x=y_var,
                color=color_param,
                facet_col=facet_col,
                facet_col_wrap=3 if facet_col else None,
                title=f"Strip Plot: {y_var} by {x_var}",
                height=600,
                orientation='h'
            )
        else:
            fig = px.strip(
                data,
                x=x_var,
                y=y_var if y_var else x_var,
                color=color_param,
                facet_col=facet_col,
                facet_col_wrap=3 if facet_col else None,
                title=f"Strip Plot: {y_var if y_var else x_var} by {x_var}",
                height=600
            )
    else:
        fig = px.scatter(
            data,
            x=x_var,
            y=y_var if y_var else x_var,
            color=color_param,
            facet_col=facet_col,
            title=f"Plot: {x_var} vs {y_var if y_var else x_var}",
            height=600
        )
    
    # Améliorer le layout
    fig.update_layout(
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=100, r=50, b=50, l=50)
    )
    
    # Rotation des labels X si beaucoup de catégories
    if not x_is_numeric and len(data[x_var].unique()) > 5:
        fig.update_xaxes(tickangle=45)
    
    return fig


def aggregate_data(data, x_var, y_var, color_var, aggregation):
    """
    Agrège les données pour les graphiques de type bar/line.
    """
    group_cols = [x_var]
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


def create_chart_description(x_var, y_var, color_var, facet_var, plot_type, aggregation, n_obs):
    """Crée une description textuelle du graphique"""
    type_names = {
        'scatter': 'Scatter Plot',
        'line': 'Line Chart',
        'bar': 'Bar Chart',
        'box': 'Box Plot',
        'histogram': 'Histogram',
        'violin': 'Violin Plot',
        'density': 'Density Plot',
        'strip': 'Strip Plot'
    }
    
    parts = [f"{type_names.get(plot_type, plot_type)}: "]
    
    if y_var:
        if plot_type in ['bar', 'line']:
            parts.append(f"{aggregation} of {y_var} by {x_var}")
        else:
            parts.append(f"{y_var} vs {x_var}")
    else:
        parts.append(f"{x_var}")
    
    if color_var:
        parts.append(f" | Colored by: {color_var}")
    
    if facet_var:
        parts.append(f" | Subdivided by: {facet_var}")
    
    parts.append(f" | N = {n_obs:,} observations")
    
    return "".join(parts)


def create_data_summary(data, x_var, y_var, color_var):
    """Crée un tableau résumé des données"""
    
    summary_rows = []
    
    # Statistiques pour X
    if pd.api.types.is_numeric_dtype(data[x_var]):
        x_stats = data[x_var].describe()
        summary_rows.append({
            'Variable': x_var,
            'Type': 'Numeric',
            'Count': f"{int(x_stats['count']):,}",
            'Mean': f"{x_stats['mean']:.2f}",
            'Std': f"{x_stats['std']:.2f}",
            'Min': f"{x_stats['min']:.2f}",
            'Max': f"{x_stats['max']:.2f}",
            'Unique': '-'
        })
    else:
        x_unique = data[x_var].nunique()
        summary_rows.append({
            'Variable': x_var,
            'Type': 'Categorical',
            'Count': f"{len(data):,}",
            'Mean': '-',
            'Std': '-',
            'Min': '-',
            'Max': '-',
            'Unique': f"{x_unique}"
        })
    
    # Statistiques pour Y
    if y_var and y_var in data.columns:
        if pd.api.types.is_numeric_dtype(data[y_var]):
            y_stats = data[y_var].describe()
            summary_rows.append({
                'Variable': y_var,
                'Type': 'Numeric',
                'Count': f"{int(y_stats['count']):,}",
                'Mean': f"{y_stats['mean']:.2f}",
                'Std': f"{y_stats['std']:.2f}",
                'Min': f"{y_stats['min']:.2f}",
                'Max': f"{y_stats['max']:.2f}",
                'Unique': '-'
            })
        else:
            y_unique = data[y_var].nunique()
            summary_rows.append({
                'Variable': y_var,
                'Type': 'Categorical',
                'Count': f"{len(data):,}",
                'Mean': '-',
                'Std': '-',
                'Min': '-',
                'Max': '-',
                'Unique': f"{y_unique}"
            })
    
    # Statistiques pour Color
    if color_var and color_var in data.columns:
        color_unique = data[color_var].nunique()
        summary_rows.append({
            'Variable': color_var,
            'Type': 'Categorical (Color)',
            'Count': f"{len(data):,}",
            'Mean': '-',
            'Std': '-',
            'Min': '-',
            'Max': '-',
            'Unique': f"{color_unique}"
        })
    
    columns = [
        {"name": "Variable", "id": "Variable"},
        {"name": "Type", "id": "Type"},
        {"name": "Count", "id": "Count"},
        {"name": "Mean", "id": "Mean"},
        {"name": "Std", "id": "Std"},
        {"name": "Min", "id": "Min"},
        {"name": "Max", "id": "Max"},
        {"name": "Unique", "id": "Unique"},
    ]
    
    return dash_table.DataTable(
        data=summary_rows,
        columns=columns,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'center',
            'padding': '10px',
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
