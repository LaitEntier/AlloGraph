import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

# Import des modules nécessaires
import modules.dashboard_layout as layouts
from modules.dashboard_layout import apply_malignancy_filter
import visualizations.allogreffes.graphs as gr
import modules.data_processing as data_processing

def get_layout():
    """
    Retourne le layout de la page GvH avec uniquement le graphique de risques compétitifs
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4('Competing Risks Analysis')),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-patients-normalized",
                            type="circle",
                            children=
                            html.Div(
                                id='gvh-main-graph',
                                style={'height': '800px', 'width': '100%'}
                            )
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),

        html.Hr(style={
            'border': '2px solid #d4c4b5',
            'margin': '3rem 0 2rem 0'
        }),
        
        dbc.Row([
            # Tableau 1 - Résumé des colonnes
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Summary by column", className='mb-0')),
                    dbc.CardBody([
                        html.Div(id='gvh-missing-summary-table', children=[
                            dbc.Alert("Contenu initial - sera remplacé par le callback", color='warning')
                        ])
                    ])
                ])
            ], width=6),
            
            # Tableau 2 - Patients concernés  
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H5("Lines affected", className='mb-0', style={'color': '#ffffff'}),
                            dbc.Button(
                                [html.I(className="fas fa-download me-2"), "Export CSV"],
                                id="export-missing-gvh-button",
                                color="primary",
                                size="sm",
                                disabled=True,  # Désactivé par défaut
                            )
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody([
                        html.Div(id='gvh-missing-detail-table', children=[
                            dbc.Alert("Contenu initial - sera remplacé par le callback", color='warning')
                        ]),
                        # Composant pour télécharger le fichier Excel (invisible)
                        dcc.Download(id="download-missing-gvh-excel")
                    ])
                ])
            ], width=6)
        ])

    ], fluid=True)

def create_gvh_sidebar_content(data):
    """
    Crée le contenu de la sidebar spécifique à la page GvH.
    
    Args:
        data (list): Liste de dictionnaires (format store Dash) avec les données
        
    Returns:
        html.Div: Contenu de la sidebar
    """
    if data is None or len(data) == 0:
        return html.Div([
            html.P('No data available', className='text-warning')
        ])
    
    # Convertir la liste en DataFrame
    df = pd.DataFrame(data)
    
    # Obtenir les années disponibles pour les filtres
    years_options = []
    if 'Year' in df.columns:
        available_years = sorted(df['Year'].unique().tolist())
        years_options = [{'label': f'{year}', 'value': year} for year in available_years]
    
    return html.Div([
        # Sélection du type de GvH
        html.Label('GvH type:', className='mb-2', style={'color': '#021F59'}),
        dcc.RadioItems(
            id='gvh-type-selection',
            options=[
                {'label': 'Acute GvH', 'value': 'acute'},
                {'label': 'Chronic GvH', 'value': 'chronic'}
            ],
            value='acute',
            className='mb-3'
        ),
        
        html.Hr(),
        
        # Filtres de grade/score dynamiques
        html.Div(id='gvh-grade-filter-container'),
        
        html.Hr(),
        
        # Filtres par année
        html.H5('Year filters', className='mb-2'),
        dcc.Checklist(
            id='gvh-year-filter',
            options=years_options,
            value=[year['value'] for year in years_options],
            inline=False,
            className='mb-3'
        ),
        
        html.Hr(),
        
        # Filtres par tranche d'âge
        layouts.create_age_filter_component(component_id='gvh-age-filter', title='Age groups'),
        
        html.Hr(),
        
        # Filtres par type de diagnostic
        layouts.create_malignancy_filter_component(component_id='gvh-malignancy-filter', title='Diagnosis type'),
        
        html.Hr(),
        
        # Informations sur les données
        html.Div([
            html.H6("📊 Information", className="mb-2"),
            html.P([
                "Patients: ", html.Strong(f"{len(df):,}")
            ], className="mb-1", style={'fontSize': '12px'}),
            html.P([
                "Years: ", html.Strong(f"{len(df['Year'].unique()) if 'Year' in df.columns else 0}")
            ], className="mb-0", style={'fontSize': '12px'})
        ])
    ])

def register_callbacks(app):
    """
    Enregistre les callbacks pour la page GvH
    """
    # Import caching utility
    from modules.cache_utils import cache_gvh_result
    
    # Cached version of competing risks calculation
    @cache_gvh_result
    def _cached_competing_risks(data_json_str, gvh_type, selected_years_tuple, selected_grades_tuple, selected_age_groups_tuple, malignancy_filter):
        """Cached version of GvH competing risks calculation"""
        import json
        # Convert JSON string back to DataFrame
        data_list = json.loads(data_json_str)
        df = pd.DataFrame(data_list)
        
        print(f"DEBUG _cached_competing_risks: Columns in df: {list(df.columns)}")
        
        # Apply GVHc transformation for chronic
        if gvh_type == 'chronic':
            df = data_processing.transform_gvhc_scores(df)
        
        # Filter by years
        if selected_years_tuple and 'Year' in df.columns:
            df = df[df['Year'].isin(list(selected_years_tuple))]
        
        if df.empty:
            return None
        
        # Filter by age groups
        if selected_age_groups_tuple and 'Age Group Detailed' in df.columns:
            df = df[df['Age Group Detailed'].isin(list(selected_age_groups_tuple))]
        
        if df.empty:
            return None
        
        # Filter by diagnosis category
        df = apply_malignancy_filter(df, malignancy_filter)
        
        # Filter by grades
        if gvh_type == 'acute':
            column_name = 'First aGvHD Maximum Score'
            occurrence_col = 'First Agvhd Occurrence'
        else:
            column_name = 'First cGvHD Maximum NIH Score'
            occurrence_col = 'First Cgvhd Occurrence'
        
        if column_name in df.columns and selected_grades_tuple:
            patients_sans_gvh = df[df[occurrence_col] != 'Yes']
            patients_avec_gvh_filtre = df[
                (df[occurrence_col] == 'Yes') & 
                (df[column_name].isin(list(selected_grades_tuple)))
            ]
            df = pd.concat([patients_sans_gvh, patients_avec_gvh_filtre], ignore_index=True)
        
        if df.empty:
            return None
        
        # Create the competing risks figure
        import visualizations.allogreffes.graphs as gr
        fig = gr.create_competing_risks_analysis(df, gvh_type)
        return fig.to_dict() if fig else None
    
    # Callback pour mettre à jour les filtres de grade/score selon le type de GvH
    @app.callback(
        Output('gvh-grade-filter-container', 'children'),
        [Input('gvh-type-selection', 'value'),
         Input('data-store', 'data')],
        prevent_initial_call=False
    )
    def update_grade_filters(gvh_type, data):
        """Met à jour les filtres de grade/score selon le type de GvH sélectionné"""
        if data is None:
            return html.Div()
    
        df = pd.DataFrame(data)
        
        # NOUVEAU : Appliquer la transformation GVHc avant d'analyser les valeurs disponibles
        if gvh_type == 'chronic':
            df = data_processing.transform_gvhc_scores(df)
        
        if gvh_type == 'acute':
            # Filtres pour GvH Aiguë (inchangé)
            column_name = 'First aGvHD Maximum Score'
            title = 'Grade filters for aGvH'
            filter_id = 'gvh-grade-filter'
            
            grade_order = ['Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Unknown']
            
            if column_name in df.columns:
                available_grades = df[column_name].dropna().unique().tolist()
                # Filtrer explicitement le Grade 0 (none)
                available_grades = [g for g in available_grades if g != 'Grade 0 (none)']
                
                grade_options = []
                for grade in grade_order:
                    if grade in available_grades:
                        grade_options.append({'label': grade, 'value': grade})
                
                for grade in available_grades:
                    if grade not in grade_order:
                        grade_options.append({'label': grade, 'value': grade})
                
                default_values = [option['value'] for option in grade_options]
            else:
                grade_options = []
                default_values = []
        
        else:  # chronic
            # Filtres pour GvH Chronique (MISE À JOUR : Limited et Extensive retirés)
            column_name = 'First cGvHD Maximum NIH Score'
            title = 'Score filters for cGvH'
            filter_id = 'gvh-grade-filter'
            
            # Ordre mis à jour sans Limited et Extensive (car transformés)
            score_order = ['Mild', 'Moderate', 'Severe', 'Not done', 'Unknown']
            
            if column_name in df.columns:
                available_scores = df[column_name].dropna().unique().tolist()
                
                grade_options = []
                for score in score_order:
                    if score in available_scores:
                        grade_options.append({'label': score, 'value': score})
                
                for score in available_scores:
                    if score not in score_order:
                        grade_options.append({'label': score, 'value': score})
                
                default_values = [option['value'] for option in grade_options]
            else:
                grade_options = []
                default_values = []

        
        if not grade_options:
            return html.Div([
                html.H6(title, className='mb-2'),
                html.P(f'Column "{column_name}" not available', className='text-muted small')
            ])
        
        return html.Div([
            html.H6(title, className='mb-2'),
            dcc.Checklist(
                id='gvh-grade-filter',  # ID unique pour les deux types
                options=grade_options,
                value=default_values,
                inline=False,
                className='mb-3',
                style={'fontSize': '12px'}
            )
        ])
    
    # Callback principal pour le graphique GvH (mis à jour avec les nouveaux filtres)
    @app.callback(
        Output('gvh-main-graph', 'children'),
        [Input('gvh-type-selection', 'value'),
         Input('gvh-year-filter', 'value'),
         Input('gvh-grade-filter', 'value'),
         Input('gvh-age-filter', 'value'),
         Input('gvh-malignancy-filter', 'value'),
         Input('data-store-gvh', 'data'),  # Use slim store
         Input('current-page', 'data')]
        # Note: No prevent_initial_call - must run when page loads with data
    )
    def update_gvh_main_graph(gvh_type, selected_years, selected_grades, selected_age_groups, malignancy_filter, data, current_page):
        """Met à jour le graphique principal d'analyse des risques compétitifs"""
        # Ne rien afficher si on n'est pas sur la page GvH
        if current_page != 'GvH':
            return html.Div()
            
        if data is None:
            return dbc.Alert("No data available", color="warning")
        
        try:
            # Use cached calculation for better VM performance
            import json
            data_json = json.dumps(data) if isinstance(data, list) else '[]'
            years_tuple = tuple(selected_years) if selected_years else tuple()
            grades_tuple = tuple(selected_grades) if selected_grades else tuple()
            age_groups_tuple = tuple(selected_age_groups) if selected_age_groups else tuple()
            
            fig_dict = _cached_competing_risks(data_json, gvh_type, years_tuple, grades_tuple, age_groups_tuple, malignancy_filter)
            
            if fig_dict is None:
                return dbc.Alert("No data available with selected filters", color="warning")
            
            # Reconstruct figure from dict
            import plotly.graph_objects as go
            fig = go.Figure(fig_dict)
            
            return dcc.Graph(
                figure=fig, 
                style={'height': '100%', 'width': '100%'},
                config={'responsive': True}
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return dbc.Alert(f"Error during graph creation: {str(e)}", color="danger")
    
    @app.callback(
        Output('gvh-missing-summary-table', 'children'),
        [Input('data-store', 'data'), 
         Input('current-page', 'data'),
         Input('gvh-year-filter', 'value'),
         Input('gvh-age-filter', 'value')],
        prevent_initial_call=False
    )
    def gvh_missing_summary_callback(data, current_page, selected_years, selected_age_groups):
        """Gère le tableau de résumé des données manquantes pour GvH"""
        
        if current_page != 'GvH' or not data:
            return html.Div("Waiting...", className='text-muted')
        
        try:
            df = pd.DataFrame(data)
            
            # Filtrer par années si spécifié
            if selected_years and 'Year' in df.columns:
                df = df[df['Year'].isin(selected_years)]
            
            # Filtrer par tranches d'âge
            if selected_age_groups and 'Age Group Detailed' in df.columns:
                df = df[df['Age Group Detailed'].isin(selected_age_groups)]
            
            # Filtrer par type de diagnostic
            df = apply_malignancy_filter(df, malignancy_filter)
            
            if df.empty:
                return html.Div('No data for the selected years', className='text-warning text-center')
            
            # Variables spécifiques à analyser pour GvH
            columns_to_analyze = [
                # Variables GvH Aiguë
                'First Agvhd Occurrence',
                'First aGvHD Maximum Score',
                'First Agvhd Occurrence Date',
                
                # Variables GvH Chronique
                'First Cgvhd Occurrence', 
                'First cGvHD Maximum NIH Score',
                'First Cgvhd Occurrence Date',
                
                # Variables de suivi
                'Status Last Follow Up',
                'Date Of Last Follow Up'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert("No GvH variable found", color='warning')
            
            # Utiliser la fonction existante de graphs.py
            missing_summary, _ = gr.analyze_missing_data(df, existing_columns, 'Long ID')
            
            # Calculer le nombre de patients décédés pendant le conditionnement
            died_during_conditioning = 0
            if 'Status Last Follow Up' in df.columns and 'Treatment Date' in df.columns and 'Date Of Last Follow Up' in df.columns:
                died_during_conditioning = df.apply(gr._is_patient_died_during_conditioning, axis=1).sum()
            
            # Créer le contenu avec optionnellement l'info sur les décès pendant conditionnement
            content = []
            
            if died_during_conditioning > 0:
                content.append(
                    dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        html.Strong(f"{died_during_conditioning} patient(s) "),
                        "died during conditioning. Data for post-transplant events (GvH, engraftment, relapse) "
                        "are not applicable for these patients and are excluded from missing data counts."
                    ], color='info', className='mb-2', style={'fontSize': '12px'})
                )
            
            content.append(
                dash_table.DataTable(
                    data=missing_summary.to_dict('records'),
                    columns=[
                        {"name": "Column", "id": "Column", "type": "text"},
                        {"name": "Total", "id": "Total patients", "type": "numeric"},
                        {"name": "Missing", "id": "Missing data", "type": "numeric"},
                        {"name": "% Missing", "id": "Percentage missing", "type": "numeric", 
                         "format": {"specifier": ".1f"}}
                    ],
                    style_table={'height': '300px', 'overflowY': 'auto'},
                    style_cell={
                        'textAlign': 'center',
                        'padding': '8px',
                        'fontSize': '12px',
                        'fontFamily': 'Arial, sans-serif',
                        'color': '#021F59'
                    },
                    style_header={
                        'backgroundColor': '#021F59',
                        'color': 'white',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
                        {
                            'if': {
                                'filter_query': '{Percentage missing} > 20',
                                'column_id': 'Percentage missing'
                            },
                            'backgroundColor': '#F2A594',
                            'color': 'red',
                            'fontWeight': 'bold'
                        }
                    ]
                )
            )
            
            return html.Div(content)
            
        except Exception as e:
            return dbc.Alert(f"Error during analysis: {str(e)}", color='danger')

    @app.callback(
        [Output('gvh-missing-detail-table', 'children'),
         Output('export-missing-gvh-button', 'disabled')],
        [Input('data-store', 'data'), 
         Input('current-page', 'data'),
         Input('gvh-year-filter', 'value'),
         Input('gvh-age-filter', 'value')],
        prevent_initial_call=False
    )
    def gvh_missing_detail_callback(data, current_page, selected_years, selected_age_groups):
        """Gère le tableau détaillé des patients avec données manquantes pour GvH"""
        
        if current_page != 'GvH' or not data:
            return html.Div("Waiting...", className='text-muted'), True
        
        try:
            df = pd.DataFrame(data)
            
            # Filtrer par années si spécifié
            if selected_years and 'Year' in df.columns:
                df = df[df['Year'].isin(selected_years)]
            
            # Filtrer par tranches d'âge
            if selected_age_groups and 'Age Group Detailed' in df.columns:
                df = df[df['Age Group Detailed'].isin(selected_age_groups)]
            
            # Filtrer par type de diagnostic
            df = apply_malignancy_filter(df, malignancy_filter)
            
            if df.empty:
                return html.Div('No data for the selected years', className='text-warning text-center'), True
            
            # Variables spécifiques à analyser pour GvH
            columns_to_analyze = [
                # Variables GvH Aiguë
                'First Agvhd Occurrence',
                'First aGvHD Maximum Score',
                'First Agvhd Occurrence Date',
                
                # Variables GvH Chronique
                'First Cgvhd Occurrence', 
                'First cGvHD Maximum NIH Score',
                'First Cgvhd Occurrence Date',
                
                # Variables de suivi
                'Status Last Follow Up',
                'Date Of Last Follow Up'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert("No GvH variable found", color='warning'), True
            
            # Utiliser la fonction existante de graphs.py
            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
            
            if detailed_missing.empty:
                return dbc.Alert("🎉 No missing data found !", color='success'), True
            
            # Adapter les noms de colonnes pour correspondre au format attendu
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Missing columns': row['Missing columns'],  # ← Corrigé
                    'Nb missing': row['Nb missing']  # ← Corrigé
                })
            
            # Sauvegarder les données pour l'export
            app.server.missing_gvh_data = detailed_data
            
            table_content = html.Div([
                dash_table.DataTable(
                    data=detailed_data,
                    columns=[
                        {"name": "Long ID", "id": "Long ID"},
                        {"name": "Missing variables", "id": "Missing columns"},
                        {"name": "Nb", "id": "Nb missing", "type": "numeric"}  # ← Corrigé
                    ],
                    style_table={'height': '300px', 'overflowY': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '12px', 'color': '#021F59'},
                    style_header={'backgroundColor': '#021F59', 'color': 'white', 'fontWeight': 'bold'},
                    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'}],
                    filter_action='native',
                    sort_action='native',
                    page_size=10
                )
            ])
            
            return table_content, False  # Activer le bouton d'export
            
        except Exception as e:
            return dbc.Alert(f"Error during analysis: {str(e)}", color='danger'), True

    @app.callback(
        Output("download-missing-gvh-excel", "data"),  # ← ID changé
        Input("export-missing-gvh-button", "n_clicks"),
        prevent_initial_call=True
    )
    def export_missing_gvh_excel(n_clicks):  # ← Nom de fonction changé
        """Gère l'export csv des patients avec données manquantes pour GvH"""
        if n_clicks is None:
            return dash.no_update
        
        try:
            # Récupérer les données stockées
            if hasattr(app.server, 'missing_gvh_data') and app.server.missing_gvh_data:
                missing_df = pd.DataFrame(app.server.missing_gvh_data)
                
                # Générer un nom de fichier avec la date
                from datetime import datetime
                current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"gvh_missing_data_{current_date}.xlsx"

                return dcc.send_data_frame(
                    missing_df.to_excel,
                    filename=filename,
                    index=False
                )
            else:
                return dash.no_update
                
        except Exception as e:
            print(f"Error during Excel export GvH: {e}")
            return dash.no_update