# pages/home.py
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
from dash_extensions import Lottie

# Import des modules communs
import visualizations.allogreffes.graphs as gr

def get_layout():
    """Retourne le layout de la page d'accueil"""
    return html.Div([
        # Contenu principal de l'accueil avec spinner
        dcc.Loading(
            id="loading-home-main",
            type="circle",
            children=html.Div(id='home-main-content')
        )
    ])

def create_banner_component():
    """Crée le composant bannière"""
    return html.Div([
        html.Img(
            src="allograph-app/assets/images/banner.png",
            style={
                'width': '100%',
                'maxWidth': '800px',
                'height': 'auto',
                'display': 'block',
                'margin': '0 auto',
                'borderRadius': '0px'
            },
            className="img-fluid"
        )
    ], style={'textAlign': 'center', 'marginTop': '30px', 'marginBottom': '20px'})

def create_lottie_animation():
    """Crée le composant d'animation Lottie"""
    return html.Div([
        Lottie(
            options={
                "loop": True,
                "autoplay": True, 
                "path": "allograph-app/assets/home.json"
            }
        )
    ], style={
        'width': '400px',
        'height': '400px',
        'margin': '0 auto',
        'display': 'block',
        'textAlign': 'center',
        'marginBottom': '30px'
    })
    
def create_welcome_content():
    """Crée le contenu d'accueil quand aucune donnée n'est chargée"""
    return dbc.Card([
        dbc.CardBody([
            # En-tête avec logo/titre
            html.Div([
                html.H1([
                    html.I(className="fas fa-chart-line me-3", style={'color': '#0D3182'}),
                    "Welcome to AlloGraph"
                ], className="text-center mb-4"),
                html.Hr()
            ]),
            
            create_lottie_animation(),

            # Description
            html.Div([
                html.P([
                    "This application allows you to analyze patient data from the ",
                    html.Strong("EBMT Registry data model"),
                    ". Explore the distributions, trends and correlations in your data."
                ], className="lead text-center mb-4"),
            ]),
            
            # Instructions
            html.Div([
                html.H4("🔎 To get started :", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="fas fa-upload me-2", style={'color': '#28a745'}),
                                    "1. Upload your data"
                                ]),
                                html.P([
                                    "Use the upload button in the sidebar to upload your file ",
                                    html.Code("CSV"), " or ", html.Code("Excel"), "."
                                ])
                            ])
                        ], color="light", outline=True)
                    ], width=6),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="fas fa-chart-bar me-2", style={'color': '#007bff'}),
                                    "2. Explore the analyses"
                                ]),
                                html.P([
                                    "Navigate between the different analysis pages : ",
                                    html.Strong("Patients"), ", ", 
                                    html.Strong("Hemopathies"), ", etc."
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
                                    "3. Filter and stratify"
                                ]),
                                html.P([
                                    "Use the controls in the sidebar to filter, ",
                                    "stratify, and personalize your analyses."
                                ])
                            ])
                        ], color="light", outline=True)
                    ], width=6),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="fas fa-download me-2", style={'color': '#6f42c1'}),
                                    "4. Export your results"
                                ]),
                                html.P([
                                    "Download your graphs and tables for your reports ",
                                    "and presentations."
                                ])
                            ])
                        ], color="light", outline=True)
                    ], width=6)
                ])
            ]),
        ], className="p-4")
    ], className="shadow-sm")

def register_callbacks(app):
    """Enregistre tous les callbacks spécifiques à la page d'accueil"""
    
    @app.callback(
        Output('home-main-content', 'children'),
        Input('data-store', 'data')
    )
    def update_home_content(data):
        """Met à jour le contenu principal de la page d'accueil"""
        
        if data is not None:
            # Données chargées : afficher le graphique + bannière
            df = pd.DataFrame(data)
            
            if 'Year' in df.columns:
                try:
                    fig = gr.create_cumulative_barplot(
                        data=df,
                        category_column='Year',
                        title="Number of transplants per year",
                        x_axis_title="Year",
                        bar_y_axis_title="Transplant count",
                        line_y_axis_title="Cumulative frequency",
                        custom_order=sorted(df['Year'].unique().tolist()),
                        height=500,  # Hauteur réduite pour mieux s'adapter
                        width=None   # Largeur automatique
                    )
                    
                    # Retourner le graphique ET la bannière
                    return html.Div([
                        # Graphique principal
                        dbc.Card([
                            dbc.CardHeader([
                                html.H4("Data Overview", className="mb-0")
                            ]),
                            dbc.CardBody([
                                dcc.Graph(
                                    figure=fig, 
                                    style={'height': '500px'},  # Hauteur fixe pour éviter le débordement
                                    config={'responsive': True}
                                )
                            ], className="p-3")
                        ], className="h-100 mb-4"),
                        
                        # Bannière sous le graphique
                        create_banner_component()
                    ])
                    
                except Exception as e:
                    return html.Div([
                        dbc.Alert(
                            f'Error creating the graph: {str(e)}', 
                            color='danger'
                        ),
                        # Bannière même en cas d'erreur
                        create_banner_component()
                    ])
            
            else:
                # Pas de colonne Year, mais données chargées
                available_cols = ', '.join(df.columns.tolist()[:10])
                return html.Div([
                    dbc.Alert([
                        html.H5('Column "Year" not found in the data'),
                        html.P(f'Available columns: {available_cols}...')
                    ], color='warning'),
                    # Bannière après le message d'erreur
                    create_banner_component()
                ])
        
        else:
            # Pas de données : afficher le cadran explicatif + bannière
            return html.Div([
                # Cadran explicatif existant
                create_welcome_content(),
                
                # Bannière sous le cadran
                create_banner_component()
            ])