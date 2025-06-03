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
    Retourne le layout de la page GvH
    """
    return dbc.Row([
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
    
    # Callback principal pour le graphique GvH
    @app.callback(
        Output('gvh-main-graph', 'children'),
        [Input('gvh-type-selection', 'value'),
         Input('gvh-year-filter', 'value'),
         Input('data-store', 'data')],
        prevent_initial_call=True
    )
    def update_gvh_main_graph(gvh_type, selected_years, data):
        """Met à jour le graphique principal d'analyse des risques compétitifs"""
        if data is None:
            return dbc.Alert("Aucune donnée disponible", color="warning")
        
        df = pd.DataFrame(data)
        
        # Filtrer les données par années sélectionnées
        if selected_years and 'Year' in df.columns:
            df = df[df['Year'].isin(selected_years)]
        
        try:
            fig = gr.create_competing_risks_analysis(df, gvh_type)
            return dcc.Graph(figure=fig, style={'height': '100%', 'width': '100%'})
        except Exception as e:
            return dbc.Alert(f"Erreur lors de la création du graphique: {str(e)}", color="danger")

def create_gvh_data_table(df, gvh_type):
    """
    Crée une table avec les données pertinentes pour le type de GvH sélectionné
    
    Args:
        df (pd.DataFrame): DataFrame avec les données
        gvh_type (str): Type de GvH ('acute' ou 'chronic')
        
    Returns:
        html.Div: Composant contenant la table
    """
    if gvh_type == 'acute':
        relevant_columns = [
            'Treatment Date', 'First Agvhd Occurrence', 'First Agvhd Occurrence Date',
            'Status Last Follow Up', 'Date Of Last Follow Up', 'Year'
        ]
        title = "Données GvH Aiguë"
    else:
        relevant_columns = [
            'Treatment Date', 'First Cgvhd Occurrence', 'First Cgvhd Occurrence Date',
            'Status Last Follow Up', 'Date Of Last Follow Up', 'Year'
        ]
        title = "Données GvH Chronique"
    
    # Filtrer les colonnes qui existent réellement
    available_columns = [col for col in relevant_columns if col in df.columns]
    
    if not available_columns:
        return dbc.Alert("Colonnes de données GvH non trouvées", color="warning")
    
    # Créer la table
    table_df = df[available_columns].head(100)  # Limiter à 100 lignes pour l'affichage
    
    return html.Div([
        html.H5(title, className="mb-3"),
        html.P(f"Affichage des {len(table_df)} premières lignes sur {len(df)} total", 
               className="text-muted small"),
        dbc.Table.from_dataframe(
            table_df, 
            striped=True, 
            bordered=True, 
            hover=True, 
            responsive=True,
            size="sm"
        )
    ], style={'height': '400px', 'overflow': 'auto'})