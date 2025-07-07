# pages/home.py
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd

# Import des modules communs
import visualizations.allogreffes.graphs as gr
from modules.translations import t

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


def register_callbacks(app):
    """Enregistre tous les callbacks spécifiques à la page d'accueil"""
    
    @app.callback(
        Output('home-main-content', 'children'),
        [Input('data-store', 'data'), Input('lang-store', 'data')]
    )
    def update_home_content(data, lang):
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
            return create_welcome_content(lang)

def create_welcome_content(lang='fr'):
    """Crée le contenu d'accueil quand aucune donnée n'est chargée"""
    return dbc.Card([
        dbc.CardBody([
            # En-tête avec logo/titre
            html.Div([
                html.H1([
                    html.I(className="fas fa-chart-line me-3", style={'color': '#0D3182'}),
                    t('home_welcome_title', lang)
                ], className="text-center mb-4"),
                html.Hr()
            ]),
            # Description
            html.Div([
                html.P([
                    t('home_description', lang),
                    html.Strong(t('home_description_strong', lang)),
                    t('home_description_end', lang)
                ], className="lead text-center mb-4"),
            ]),
            # Instructions
            html.Div([
                html.H4(t('home_start_title', lang), className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="fas fa-upload me-2", style={'color': '#28a745'}),
                                    t('home_step1_title', lang)
                                ]),
                                html.P([
                                    t('home_step1_desc', lang),
                                    html.Code(t('home_step1_csv', lang)),
                                    t('home_step1_or', lang),
                                    html.Code(t('home_step1_excel', lang)),
                                    t('home_step1_end', lang)
                                ])
                            ])
                        ], color="light", outline=True)
                    ], width=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="fas fa-chart-bar me-2", style={'color': '#007bff'}),
                                    t('home_step2_title', lang)
                                ]),
                                html.P([
                                    t('home_step2_desc', lang),
                                    html.Strong(t('home_step2_patients', lang)), ", ",
                                    html.Strong(t('home_step2_hemo', lang)),
                                    t('home_step2_etc', lang)
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
                                    t('home_step3_title', lang)
                                ]),
                                html.P(t('home_step3_desc', lang))
                            ])
                        ], color="light", outline=True)
                    ], width=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5([
                                    html.I(className="fas fa-download me-2", style={'color': '#6f42c1'}),
                                    t('home_step4_title', lang)
                                ]),
                                html.P(t('home_step4_desc', lang))
                            ])
                        ], color="light", outline=True)
                    ], width=6)
                ])
            ]),
            # Informations techniques
            html.Hr(),
            html.Div([
                html.H5(t('home_formats_title', lang), className="mb-2"),
                dbc.Row([
                    dbc.Col([
                        html.Ul([
                            html.Li([html.I(className="fas fa-file-csv me-2"), t('home_format_csv', lang)]),
                            html.Li([html.I(className="fas fa-file-excel me-2"), t('home_format_excel', lang)]),
                        ], className="list-unstyled")
                    ], width=6),
                    dbc.Col([
                        html.Ul([
                            html.Li([html.I(className="fas fa-database me-2"), t('home_format_struct', lang)]),
                            html.Li([html.I(className="fas fa-chart-pie me-2"), t('home_format_ebmt', lang)])
                        ], className="list-unstyled")
                    ], width=6)
                ])
            ], className="text-muted")
        ], className="p-4")
    ])