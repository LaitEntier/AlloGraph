# pages/home.py
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd

# Import des modules communs
import visualizations.allogreffes.graphs as gr

def get_layout():
    """Retourne le layout de la page d'accueil"""
    return html.Div([
        # Contenu principal de l'accueil
        html.Div(id='home-main-content')
    ])

def register_callbacks(app):
    """Enregistre tous les callbacks spécifiques à la page d'accueil"""
    
    @app.callback(
        Output('home-main-content', 'children'),
        Input('data-store', 'data')
    )
    def update_home_content(data):
        """Met à jour le contenu principal de la page d'accueil"""
        
        if data is not None:
            # Données chargées : afficher le graphique
            df = pd.DataFrame(data)
            
            if 'Year' in df.columns:
                try:
                    fig = gr.create_cumulative_barplot(
                        data=df,
                        category_column='Year',
                        title="Nombre de greffes par an",
                        x_axis_title="Année",
                        bar_y_axis_title="Nombre de greffes",
                        line_y_axis_title="Effectif cumulé",
                        custom_order=sorted(df['Year'].unique().tolist()),
                        height=500,  # Hauteur réduite pour mieux s'adapter
                        width=None   # Largeur automatique
                    )
                    
                    return dbc.Card([
                        dbc.CardHeader([
                            html.H4("Vue d'ensemble des données", className="mb-0")
                        ]),
                        dbc.CardBody([
                            dcc.Graph(
                                figure=fig, 
                                style={'height': '500px'},  # Hauteur fixe pour éviter le débordement
                                config={'responsive': True}
                            )
                        ], className="p-3")
                    ], className="h-100")
                    
                except Exception as e:
                    return dbc.Alert(
                        f'Erreur lors de la création du graphique: {str(e)}', 
                        color='danger'
                    )
            else:
                available_cols = ', '.join(df.columns.tolist()[:10])
                return dbc.Alert([
                    html.H5('Colonne "Year" non trouvée dans les données'),
                    html.P(f'Colonnes disponibles: {available_cols}...')
                ], color='warning')
        
        else:
            # Pas de données : afficher le message d'accueil
            return create_welcome_content()

def create_welcome_content():
    """Crée le contenu d'accueil quand aucune donnée n'est chargée"""
    return dbc.Card([
        dbc.CardBody([
            # En-tête avec logo/titre
            html.Div([
                html.H1([
                    html.I(className="fas fa-chart-line me-3", style={'color': '#0D3182'}),
                    "Bienvenue dans AlloGraph"
                ], className="text-center mb-4"),
                html.Hr()
            ]),
            
            # Description
            html.Div([
                html.P([
                    "Cette application vous permet d'analyser des données de patients depuis le ",
                    html.Strong("modèle de données de l'EBMT Registry"),
                    ". Explorez les distributions, tendances et corrélations dans vos données de greffe."
                ], className="lead text-center mb-4"),
            ]),
            
            # Instructions
            html.Div([
                html.H4("🔎 Pour commencer :", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="fas fa-upload me-2", style={'color': '#28a745'}),
                                    "1. Chargez vos données"
                                ]),
                                html.P([
                                    "Utilisez le bouton de téléchargement dans la barre latérale pour charger votre fichier ",
                                    html.Code("CSV"), " ou ", html.Code("Excel"), "."
                                ])
                            ])
                        ], color="light", outline=True)
                    ], width=6),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="fas fa-chart-bar me-2", style={'color': '#007bff'}),
                                    "2. Explorez les analyses"
                                ]),
                                html.P([
                                    "Naviguez entre les différentes pages d'analyse : ",
                                    html.Strong("Patients"), ", ", 
                                    html.Strong("Hémopathies"), ", etc."
                                ])
                            ])
                        ], color="light", outline=True)
                    ], width=6)
                ], className="mb-4"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="fas fa-filter me-2", style={'color': '#ffc107'}),
                                    "3. Filtrez et stratifiez"
                                ]),
                                html.P([
                                    "Utilisez les contrôles de la barre latérale pour filtrer par année, ",
                                    "stratifier par variables, et personnaliser vos analyses."
                                ])
                            ])
                        ], color="light", outline=True)
                    ], width=6),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="fas fa-download me-2", style={'color': '#6f42c1'}),
                                    "4. Exportez vos résultats"
                                ]),
                                html.P([
                                    "Téléchargez vos graphiques et tableaux pour vos rapports ",
                                    "et présentations."
                                ])
                            ])
                        ], color="light", outline=True)
                    ], width=6)
                ])
            ]),
            
            # Informations techniques
            html.Hr(),
            html.Div([
                html.H5("📋 Formats supportés :", className="mb-2"),
                dbc.Row([
                    dbc.Col([
                        html.Ul([
                            html.Li([html.I(className="fas fa-file-csv me-2"), "Fichiers CSV (.csv)"]),
                            html.Li([html.I(className="fas fa-file-excel me-2"), "Fichiers Excel (.xlsx, .xls)"]),
                        ], className="list-unstyled")
                    ], width=6),
                    dbc.Col([
                        html.Ul([
                            html.Li([html.I(className="fas fa-database me-2"), "Données structurées"]),
                            html.Li([html.I(className="fas fa-chart-pie me-2"), "sur le modèle EBMT"])
                        ], className="list-unstyled")
                    ], width=6)
                ])
            ], className="text-muted")
            
        ], className="p-4")
    ])