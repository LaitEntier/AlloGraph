import dash
from dash import dcc, html, Input, Output, State
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