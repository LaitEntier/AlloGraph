# pages/patients.py
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
    """Retourne le layout de la page Patients avec graphiques empilés verticalement"""
    return dbc.Container([
        # Graphique 1: Barplot normalisé à 100%
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    #dbc.CardHeader(html.H5('Distribution normalisée à 100%')),
                    dbc.CardBody([
                        html.Div(
                            id='patients-normalized-chart',
                            style={'height': '450px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Graphique 2: Barplot distribution
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    #dbc.CardHeader(html.H5('Distribution des effectifs')),
                    dbc.CardBody([
                        html.Div(
                            id='patients-distribution-chart',
                            style={'height': '450px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Graphique 3: Boxplot
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    #dbc.CardHeader(html.H5('Boxplot - Age At Diagnosis')),
                    dbc.CardBody([
                        html.Div(
                            id='patients-boxplot-chart',
                            style={'height': '450px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Graphique 4: DataTable avec bouton d'export
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H5('Statistiques par année', className='mb-0')
                            ], width=8),
                            dbc.Col([
                                dbc.Button(
                                    [html.I(className="fas fa-download me-2"), "Exporter CSV"],
                                    id="export-csv-button",
                                    color="primary",
                                    size="sm",
                                    disabled=True,  # Désactivé par défaut
                                    className="float-end"
                                )
                            ], width=4, className="d-flex justify-content-end align-items-center")
                        ])
                    ]),
                    dbc.CardBody([
                        html.Div(
                            id='patients-datatable',
                            style={'height': '450px', 'overflow': 'auto'}
                        ),
                        # Composant pour télécharger le CSV (invisible)
                        dcc.Download(id="download-csv")
                    ], className='p-2')
                ])
            ], width=12)
        ])
    ], fluid=True)

def register_callbacks(app):
    """Enregistre tous les callbacks spécifiques à la page Patients"""
    
    def create_color_map(data, color_column):
        """Crée un mapping de couleurs cohérent pour une variable"""
        if color_column not in data.columns:
            return {}
        
        # Obtenir les catégories uniques en filtrant les valeurs nulles
        categories = data[color_column].dropna().unique()
        # Trier seulement les valeurs non-nulles
        categories = sorted([cat for cat in categories if pd.notna(cat)])
        
        # Utiliser la même palette que Plotly
        colors = px.colors.qualitative.Plotly
        
        # Créer le mapping
        color_map = {}
        for i, category in enumerate(categories):
            color_map[category] = colors[i % len(colors)]
        
        return color_map
    
    @app.callback(
        Output('patients-normalized-chart', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('x-axis-dropdown', 'value'),
         Input('stack-variable-dropdown', 'value'),
         Input('year-filter-checklist', 'value')]
    )
    def update_normalized_chart(data, current_page, x_axis, stack_var, selected_years):
        """Graphique 1: Barplot normalisé à 100%"""
        if current_page != 'Patients' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Valeurs par défaut
        if x_axis is None:
            x_axis = 'Age Groups'  # Valeur par défaut modifiée
        
        if stack_var is None:
            stack_var = 'Main Diagnosis'  # Valeur par défaut modifiée
        
        # Filtrer les données
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return dbc.Alert('Aucune donnée disponible avec les filtres sélectionnés', color='warning')
        
        try:
            if x_axis not in filtered_df.columns:
                return dbc.Alert(f'Colonne "{x_axis}" non trouvée dans les données', color='warning')
            
            stack_col = None if stack_var == 'Aucune' else stack_var
            
            # Choisir la fonction appropriée selon la variable de stratification
            if stack_col is None or stack_col not in filtered_df.columns:
                # Pas de stratification : barplot simple normalisé à 100%
                # Définir l'ordre personnalisé pour Age Groups
                order = None
                if x_axis == 'Age Groups':
                    order = ['18-', '18-39', '40-64', '65-74', '75+']
                
                fig = gr.create_simple_normalized_barplot(
                    data=filtered_df,
                    x_column=x_axis,
                    title=f"Distribution par {x_axis} - Sélectionnez une variable de stratification",
                    x_axis_title=x_axis,
                    y_axis_title="Proportion (%)",
                    custom_order=order,
                    height=420,
                    width=None
                )
            else:
                # Avec stratification : barplot stacké normalisé
                # Définir l'ordre personnalisé pour Age Groups
                order = None
                if x_axis == 'Age Groups':
                    order = ['18-', '18-39', '40-64', '65-74', '75+']
                
                # Créer un mapping de couleurs cohérent
                color_map = create_color_map(filtered_df, stack_col)
                
                fig = gr.create_normalized_barplot(
                    data=filtered_df,
                    x_column=x_axis,
                    y_column='Count',
                    stack_column=stack_col,
                    title=f"Distribution normalisée par {x_axis} et {stack_col}",
                    x_axis_title=x_axis,
                    y_axis_title="Proportion (%)",
                    custom_order=order,
                    height=420,
                    width=None,
                    color_map=color_map  # ← Utiliser le mapping cohérent
                )
            
            return dcc.Graph(
                figure=fig, 
                style={'height': '100%'},
                config={'responsive': True}
            )
        except Exception as e:
            return dbc.Alert(f'Erreur: {str(e)}', color='danger')

    @app.callback(
        Output('patients-distribution-chart', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('x-axis-dropdown', 'value'),
         Input('stack-variable-dropdown', 'value'),
         Input('year-filter-checklist', 'value')]
    )
    def update_distribution_chart(data, current_page, x_axis, stack_var, selected_years):
        """Graphique 2: Barplot distribution"""
        if current_page != 'Patients' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Valeurs par défaut
        if x_axis is None:
            x_axis = 'Age Groups'  # Valeur par défaut modifiée
        
        if stack_var is None:
            stack_var = 'Main Diagnosis'  # Valeur par défaut modifiée
        
        # Filtrer les données
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return html.Div('Aucune donnée disponible', className='text-warning text-center')
        
        try:
            if x_axis not in filtered_df.columns:
                return html.Div(f'Colonne "{x_axis}" non trouvée', className='text-warning text-center')
            
            stack_col = None if stack_var == 'Aucune' else stack_var
            
            # Choisir la fonction appropriée selon la variable de stratification
            if stack_col is None or stack_col not in filtered_df.columns:
                # Pas de stratification : barplot simple
                # Définir l'ordre personnalisé pour Age Groups
                order = None
                if x_axis == 'Age Groups':
                    order = ['18-', '18-39', '40-64', '65-74', '75+']
                
                fig = gr.create_simple_barplot(
                    data=filtered_df,
                    x_column=x_axis,
                    title=f"Distribution par {x_axis}",
                    x_axis_title=x_axis,
                    y_axis_title="Nombre de greffes",
                    custom_order=order,
                    height=420,
                    width=None
                )
            else:
                # Avec stratification : barplot stacké
                # Définir l'ordre personnalisé pour Age Groups
                order = None
                if x_axis == 'Age Groups':
                    order = ['18-', '18-39', '40-64', '65-74', '75+']
                
                # Créer un mapping de couleurs cohérent
                color_map = create_color_map(filtered_df, stack_col)
                
                fig = gr.create_stacked_barplot(
                    data=filtered_df,
                    x_column=x_axis,
                    y_column='Count',
                    stack_column=stack_col,
                    title=f"Distribution par {x_axis} et {stack_col}",
                    x_axis_title=x_axis,
                    y_axis_title="Nombre de greffes",
                    custom_order=order,
                    height=420,
                    width=None,
                    color_map=color_map  # ← Utiliser le mapping cohérent
                )
            
            return dcc.Graph(
                figure=fig, 
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div(f'Erreur: {str(e)}', className='text-danger')

    @app.callback(
        Output('patients-boxplot-chart', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('x-axis-dropdown', 'value'),
         Input('stack-variable-dropdown', 'value'),
         Input('year-filter-checklist', 'value')]
    )
    def update_boxplot_chart(data, current_page, x_axis, stack_var, selected_years):
        """Graphique 3: Boxplot Age At Diagnosis par variable de stratification"""
        if current_page != 'Patients' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Valeurs par défaut
        if stack_var is None:
            stack_var = 'Main Diagnosis'  # Valeur par défaut modifiée
        
        # Vérifier si une variable de stratification est sélectionnée
        if stack_var == 'Aucune':
            return html.Div([
                dbc.Alert([
                    html.H6("📊 Sélection requise", className="mb-2"),
                    html.P("Veuillez sélectionner une variable de stratification dans la sidebar pour afficher le boxplot.", 
                           className="mb-0")
                ], color="info", className="text-center")
            ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'height': '100%'})
        
        # Filtrer les données
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return html.Div('Aucune donnée disponible', className='text-warning text-center')
        
        try:
            # Vérifier que la variable de stratification existe dans les données
            if stack_var not in filtered_df.columns:
                return html.Div(f'Variable "{stack_var}" non trouvée dans les données', className='text-warning text-center')
            
            # Créer un mapping de couleurs cohérent avec les autres graphiques
            color_map = create_color_map(filtered_df, stack_var)
            
            # Créer le boxplot Age At Diagnosis par variable de stratification
            fig = gr.create_enhanced_boxplot(
                data=filtered_df,
                x_column=stack_var,
                y_column='Age At Diagnosis',
                color_column=stack_var,  # Utiliser la même variable pour colorer chaque box
                title=f"Boxplot Age At Diagnosis par {stack_var}",
                x_axis_title=stack_var,
                y_axis_title='Age At Diagnosis',
                height=420,
                width=None,
                show_points=True,
                point_size=4,
                color_map=color_map  # Passer le mapping de couleurs à la fonction
            )
            
            return dcc.Graph(
                figure=fig, 
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div(f'Erreur: {str(e)}', className='text-danger')

    @app.callback(
        [Output('patients-datatable', 'children'),
         Output('export-csv-button', 'disabled')],
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('year-filter-checklist', 'value')]
    )
    def update_datatable(data, current_page, selected_years):
        """Graphique 4: DataTable avec statistiques par année et gestion du bouton d'export"""
        if current_page != 'Patients' or data is None:
            return html.Div(), True  # Désactiver le bouton si pas de données
        
        df = pd.DataFrame(data)
        
        # Créer la table de statistiques par année
        if 'Year' not in df.columns or 'Age At Diagnosis' not in df.columns:
            return dbc.Alert('Colonnes "Year" ou "Age At Diagnosis" non trouvées dans les données', color='warning'), True
        
        # Calculer les statistiques par année
        stats_by_year = []
        
        # Filtrer selon les années sélectionnées
        if selected_years:
            years_to_process = selected_years
        else:
            years_to_process = sorted(df['Year'].unique())
        
        # Calculer les stats pour chaque année
        for year in years_to_process:
            year_data = df[df['Year'] == year]['Age At Diagnosis']
            
            if len(year_data) > 0:
                stats_by_year.append({
                    'Année': year,
                    'Age moyen': round(year_data.mean(), 1),
                    'Age médian': round(year_data.median(), 1),
                    'Age Q1': round(year_data.quantile(0.25), 1),
                    'Age Q3': round(year_data.quantile(0.75), 1),
                    'Age minimum': int(year_data.min()),
                    'Age maximum': int(year_data.max()),
                    'Effectif total': len(year_data)
                })
        
        # Calculer la ligne 'Total' pour toutes les années sélectionnées
        if stats_by_year:
            all_ages = df[df['Year'].isin(years_to_process)]['Age At Diagnosis']
            
            if len(all_ages) > 0:
                total_row = {
                    'Année': 'TOTAL',
                    'Age moyen': round(all_ages.mean(), 1),
                    'Age médian': round(all_ages.median(), 1),
                    'Age Q1': round(all_ages.quantile(0.25), 1),
                    'Age Q3': round(all_ages.quantile(0.75), 1),
                    'Age minimum': int(all_ages.min()),
                    'Age maximum': int(all_ages.max()),
                    'Effectif total': len(all_ages)
                }
                stats_by_year.append(total_row)
        
        if not stats_by_year:
            return dbc.Alert('Aucune donnée disponible pour les années sélectionnées', color='info'), True
        
        # Stocker les données pour l'export (dans un Store invisible)
        app.server.stats_data = stats_by_year  # Stockage temporaire côté serveur
        
        # Créer la DataTable
        table_content = html.Div([
            dash_table.DataTable(
                data=stats_by_year,
                columns=[
                    {"name": "Année", "id": "Année", "type": "text"},
                    {"name": "Age moyen", "id": "Age moyen", "type": "numeric", "format": {"specifier": ".1f"}},
                    {"name": "Age médian", "id": "Age médian", "type": "numeric", "format": {"specifier": ".1f"}},
                    {"name": "Age Q1", "id": "Age Q1", "type": "numeric", "format": {"specifier": ".1f"}},
                    {"name": "Age Q3", "id": "Age Q3", "type": "numeric", "format": {"specifier": ".1f"}},
                    {"name": "Age minimum", "id": "Age minimum", "type": "numeric"},
                    {"name": "Age maximum", "id": "Age maximum", "type": "numeric"},
                    {"name": "Effectif total", "id": "Effectif total", "type": "numeric"}
                ],
                style_table={'height': '400px', 'overflowY': 'auto'},
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px',
                    'fontFamily': 'Arial, sans-serif'
                },
                style_header={
                    'backgroundColor': '#0D3182', 
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'center'
                },
                style_data_conditional=[
                    {
                        # Mise en évidence de la ligne TOTAL
                        'if': {'filter_query': '{Année} = TOTAL'},
                        'backgroundColor': '#e6f3ff',
                        'fontWeight': 'bold',
                        'border': '2px solid #0D3182'
                    }
                ],
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'Année'},
                        'fontWeight': 'bold',
                        'textAlign': 'left'
                    }
                ]
            ),
            html.P(f'{len(stats_by_year)-1} années affichées (+ ligne total)', 
                   className='text-info mt-2')
        ])
        
        return table_content, False  # Activer le bouton d'export
    
    @app.callback(
        Output("download-csv", "data"),
        Input("export-csv-button", "n_clicks"),
        State('year-filter-checklist', 'value'),
        prevent_initial_call=True
    )
    def export_csv(n_clicks, selected_years):
        """Gère l'export CSV des statistiques"""
        if n_clicks is None:
            return dash.no_update
        
        try:
            # Récupérer les données stockées
            if hasattr(app.server, 'stats_data') and app.server.stats_data:
                stats_df = pd.DataFrame(app.server.stats_data)
                
                # Générer un nom de fichier avec la date et les années sélectionnées
                from datetime import datetime
                current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if selected_years:
                    years_str = "_".join(map(str, sorted(selected_years)))
                    filename = f"statistiques_patients_{years_str}_{current_date}.csv"
                else:
                    filename = f"statistiques_patients_toutes_annees_{current_date}.csv"
                
                return dcc.send_data_frame(
                    stats_df.to_csv, 
                    filename=filename,
                    index=False  # Ne pas inclure l'index dans le CSV
                )
            else:
                return dash.no_update
                
        except Exception as e:
            print(f"Erreur lors de l'export CSV: {e}")
            return dash.no_update