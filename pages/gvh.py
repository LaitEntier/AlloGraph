import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

# Import des modules nécessaires
import modules.dashboard_layout as layouts
import visualizations.allogreffes.graphs as gr

def get_layout():
    """
    Retourne le layout de la page GvH avec uniquement le graphique de risques compétitifs
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4('Analyse des Risques Compétitifs GvH')),
                    dbc.CardBody([
                        html.Div(
                            id='gvh-main-graph',
                            style={'height': '800px', 'width': '100%'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),

        dbc.Row([
            # Tableau 1 - Résumé des colonnes
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Résumé par colonne", className='mb-0')),
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
                            html.H5("Patients concernés", className='mb-0'),
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
                        # Composant pour télécharger le fichier CSV (invisible)
                        dcc.Download(id="download-missing-gvh-csv")
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
            html.P('Aucune donnée disponible', className='text-warning')
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
        html.Label('Type de GvH:', className='mb-2'),
        dcc.RadioItems(
            id='gvh-type-selection',
            options=[
                {'label': 'GvH Aiguë', 'value': 'acute'},
                {'label': 'GvH Chronique', 'value': 'chronic'}
            ],
            value='acute',
            className='mb-3'
        ),
        
        html.Hr(),
        
        # Filtres de grade/score dynamiques
        html.Div(id='gvh-grade-filter-container'),
        
        html.Hr(),
        
        # Filtres par année
        html.H5('Filtres par année', className='mb-2'),
        dcc.Checklist(
            id='gvh-year-filter',
            options=years_options,
            value=[year['value'] for year in years_options],
            inline=False,
            className='mb-3'
        ),
        
        html.Hr(),
        
        # Informations sur les données
        html.Div([
            html.H6("📊 Informations", className="mb-2"),
            html.P([
                "Patients: ", html.Strong(f"{len(df):,}")
            ], className="mb-1", style={'fontSize': '12px'}),
            html.P([
                "Années: ", html.Strong(f"{len(df['Year'].unique()) if 'Year' in df.columns else 0}")
            ], className="mb-0", style={'fontSize': '12px'})
        ])
    ])

def register_callbacks(app):
    """
    Enregistre les callbacks pour la page GvH
    """
    
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
        
        if gvh_type == 'acute':
            # Filtres pour GvH Aiguë
            column_name = 'First aGvHD Maximum Score'
            title = 'Filtres par Grade aGvH'
            filter_id = 'gvh-grade-filter'
            
            # Ordre spécifique demandé
            grade_order = ['Grade 0 (none)', 'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Unknown']
            
            if column_name in df.columns:
                # Obtenir les valeurs disponibles dans les données
                available_grades = df[column_name].dropna().unique().tolist()
                
                # Créer les options dans l'ordre spécifié, seulement pour les valeurs présentes
                grade_options = []
                for grade in grade_order:
                    if grade in available_grades:
                        grade_options.append({'label': grade, 'value': grade})
                
                # Ajouter les valeurs non prévues qui pourraient exister
                for grade in available_grades:
                    if grade not in grade_order:
                        grade_options.append({'label': grade, 'value': grade})
                
                # Sélectionner toutes les valeurs par défaut
                default_values = [option['value'] for option in grade_options]
            else:
                grade_options = []
                default_values = []
        
        else:  # chronic
            # Filtres pour GvH Chronique
            column_name = 'First cGvHD Maximum NIH Score'
            title = 'Filtres par Score NIH cGvH'
            filter_id = 'gvh-grade-filter'
            
            # Ordre spécifique demandé
            score_order = ['Mild', 'Limited', 'Moderate', 'Extensive', 'Severe', 'Not done', 'Unknown']
            
            if column_name in df.columns:
                # Obtenir les valeurs disponibles dans les données
                available_scores = df[column_name].dropna().unique().tolist()
                
                # Créer les options dans l'ordre spécifié, seulement pour les valeurs présentes
                grade_options = []
                for score in score_order:
                    if score in available_scores:
                        grade_options.append({'label': score, 'value': score})
                
                # Ajouter les valeurs non prévues qui pourraient exister
                for score in available_scores:
                    if score not in score_order:
                        grade_options.append({'label': score, 'value': score})
                
                # Sélectionner toutes les valeurs par défaut
                default_values = [option['value'] for option in grade_options]
            else:
                grade_options = []
                default_values = []
        
        if not grade_options:
            return html.Div([
                html.H6(title, className='mb-2'),
                html.P(f'Colonne "{column_name}" non disponible', className='text-muted small')
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
         Input('data-store', 'data'),
         Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def update_gvh_main_graph(gvh_type, selected_years, selected_grades, data, current_page):
        """Met à jour le graphique principal d'analyse des risques compétitifs"""
        # Ne rien afficher si on n'est pas sur la page GvH
        if current_page != 'GvH':
            return html.Div()
            
        if data is None:
            return dbc.Alert("Aucune donnée disponible", color="warning")
        
        df = pd.DataFrame(data)
        print(f"Dataset initial: {len(df)} patients")
        
        # Filtrer les données par années sélectionnées
        if selected_years and 'Year' in df.columns:
            df = df[df['Year'].isin(selected_years)]
            print(f"Après filtre années: {len(df)} patients")
        
        # CORRECTION : Filtrer par grade/score SEULEMENT pour les patients avec GvH
        if gvh_type == 'acute':
            column_name = 'First aGvHD Maximum Score'
            occurrence_col = 'First Agvhd Occurrence'
        else:
            column_name = 'First cGvHD Maximum NIH Score'
            occurrence_col = 'First Cgvhd Occurrence'
        
        # Appliquer le filtre de grade/score UNIQUEMENT aux patients avec GvH = "Yes"
        if column_name in df.columns and selected_grades:
            # Garder tous les patients SANS GvH (occurrence != "Yes") 
            # + les patients AVEC GvH qui ont le bon grade/score
            patients_sans_gvh = df[df[occurrence_col] != 'Yes']
            patients_avec_gvh_filtre = df[
                (df[occurrence_col] == 'Yes') & 
                (df[column_name].isin(selected_grades))
            ]
            
            # Combiner les deux groupes
            df = pd.concat([patients_sans_gvh, patients_avec_gvh_filtre], ignore_index=True)
            print(f"Après filtre grade/score: {len(df)} patients")
            print(f"  - Patients sans GvH: {len(patients_sans_gvh)}")
            print(f"  - Patients avec GvH et grade sélectionné: {len(patients_avec_gvh_filtre)}")
            
        elif column_name in df.columns and not selected_grades:
            # Si aucun grade n'est sélectionné, garder seulement les patients sans GvH
            df = df[df[occurrence_col] != 'Yes']
            print(f"Aucun grade sélectionné - gardé seulement patients sans GvH: {len(df)} patients")
            
            if len(df) == 0:
                return dbc.Alert(
                    f"Aucun {'grade' if gvh_type == 'acute' else 'score'} sélectionné pour l'analyse", 
                    color="info"
                )
        
        if df.empty:
            return dbc.Alert("Aucune donnée disponible avec les filtres sélectionnés", color="warning")
        
        print(f"Dataset final pour analyse: {len(df)} patients")
        
        try:
            fig = gr.create_competing_risks_analysis(df, gvh_type)
            return dcc.Graph(
                figure=fig, 
                style={'height': '100%', 'width': '100%'},
                config={'responsive': True}
            )
        except Exception as e:
            return dbc.Alert(f"Erreur lors de la création du graphique: {str(e)}", color="danger")
    
    @app.callback(
        Output('gvh-missing-summary-table', 'children'),
        [Input('data-store', 'data'), Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def gvh_missing_summary_callback(data, current_page):
        """Gère le tableau de résumé des données manquantes pour GvH"""
        
        if current_page != 'GvH' or not data:
            return html.Div("En attente...", className='text-muted')
        
        try:
            df = pd.DataFrame(data)
            
            # Variables spécifiques à analyser pour GvH
            columns_to_analyze = [
                # Variables GvH Aiguë
                'First aGvHD Maximum Score',
                'First Agvhd Occurrence',
                'First Agvhd Occurrence Date',
                
                # Variables GvH Chronique
                'First cGvHD Maximum NIH Score',
                'First Cgvhd Occurrence', 
                'First Cgvhd Occurrence Date',
                
                # Variables de suivi
                'Status Last Follow Up',
                'Date Of Last Follow Up'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert("Aucune variable GvH trouvée", color='warning')
            
            # Utiliser la fonction existante de graphs.py
            missing_summary, _ = gr.analyze_missing_data(df, existing_columns, 'Long ID')
            
            return dash_table.DataTable(
                data=missing_summary.to_dict('records'),
                columns=[
                    {"name": "Variable", "id": "Colonne"},
                    {"name": "Total", "id": "Total patients", "type": "numeric"},
                    {"name": "Manquantes", "id": "Données manquantes", "type": "numeric"},
                    {"name": "% Manquant", "id": "Pourcentage manquant", "type": "numeric", 
                     "format": {"specifier": ".1f"}}
                ],
                style_table={'height': '300px', 'overflowY': 'auto'},
                style_cell={
                    'textAlign': 'center',
                    'padding': '8px',
                    'fontSize': '12px',
                    'fontFamily': 'Arial, sans-serif'
                },
                style_header={
                    'backgroundColor': '#0D3182',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'},
                    {
                        'if': {
                            'filter_query': '{Pourcentage manquant} > 20',
                            'column_id': 'Pourcentage manquant'
                        },
                        'backgroundColor': '#ffebee',
                        'color': 'red',
                        'fontWeight': 'bold'
                    }
                ]
            )
            
        except Exception as e:
            return dbc.Alert(f"Erreur lors de l'analyse: {str(e)}", color='danger')

    @app.callback(
        [Output('gvh-missing-detail-table', 'children'),
         Output('export-missing-gvh-button', 'disabled')],
        [Input('data-store', 'data'), Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def gvh_missing_detail_callback(data, current_page):
        """Gère le tableau détaillé des patients avec données manquantes pour GvH"""
        
        if current_page != 'GvH' or not data:
            return html.Div("En attente...", className='text-muted'), True
        
        try:
            df = pd.DataFrame(data)
            
            # Variables spécifiques à analyser pour GvH
            columns_to_analyze = [
                # Variables GvH Aiguë
                'First aGvHD Maximum Score',
                'First Agvhd Occurrence',
                'First Agvhd Occurrence Date',
                
                # Variables GvH Chronique
                'First cGvHD Maximum NIH Score',
                'First Cgvhd Occurrence', 
                'First Cgvhd Occurrence Date',
                
                # Variables de suivi
                'Status Last Follow Up',
                'Date Of Last Follow Up'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert("Aucune variable GvH trouvée", color='warning'), True
            
            # Utiliser la fonction existante de graphs.py
            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
            
            if detailed_missing.empty:
                return dbc.Alert("🎉 Aucune donnée manquante trouvée !", color='success'), True
            
            # Adapter les noms de colonnes pour correspondre au format attendu
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Colonnes manquantes': row['Colonnes avec données manquantes'],
                    'Nb manquant': row['Nombre de colonnes manquantes']
                })
            
            # Sauvegarder les données pour l'export
            app.server.missing_gvh_data = detailed_data
            
            table_content = html.Div([
                dash_table.DataTable(
                    data=detailed_data,
                    columns=[
                        {"name": "Long ID", "id": "Long ID"},
                        {"name": "Variables manquantes", "id": "Colonnes manquantes"},
                        {"name": "Nb", "id": "Nb manquant", "type": "numeric"}
                    ],
                    style_table={'height': '300px', 'overflowY': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '12px'},
                    style_header={'backgroundColor': '#0D3182', 'color': 'white', 'fontWeight': 'bold'},
                    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}],
                    filter_action='native',
                    sort_action='native',
                    page_size=10
                )
            ])
            
            return table_content, False  # Activer le bouton d'export
            
        except Exception as e:
            return dbc.Alert(f"Erreur lors de l'analyse: {str(e)}", color='danger'), True

    @app.callback(
        Output("download-missing-gvh-csv", "data"),
        Input("export-missing-gvh-button", "n_clicks"),
        prevent_initial_call=True
    )
    def export_missing_gvh_csv(n_clicks):
        """Gère l'export CSV des patients avec données manquantes pour GvH"""
        if n_clicks is None:
            return dash.no_update
        
        try:
            # Récupérer les données stockées
            if hasattr(app.server, 'missing_gvh_data') and app.server.missing_gvh_data:
                missing_df = pd.DataFrame(app.server.missing_gvh_data)
                
                # Générer un nom de fichier avec la date
                from datetime import datetime
                current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"gvh_donnees_manquantes_{current_date}.csv"
                
                return dcc.send_data_frame(
                    missing_df.to_csv, 
                    filename=filename,
                    index=False
                )
            else:
                return dash.no_update
                
        except Exception as e:
            print(f"Erreur lors de l'export CSV GvH: {e}")
            return dash.no_update