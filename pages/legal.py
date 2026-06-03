from dash import html
import dash_bootstrap_components as dbc


def get_layout():
    """Retourne le layout de la page Mentions légales"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H3("Legal Notices", className="mb-0", style={'color': '#ffffff', 'fontWeight': '700'})
                    ),
                    dbc.CardBody([
                        html.H5("Publisher", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '20px'}),
                        html.P([
                            "This website is published by the ",
                            html.Strong("Centre Hospitalier Régional Universitaire (CHRU) de Tours"),
                            " and the ",
                            html.Strong("Université de Tours"),
                            "."
                        ]),
                        html.P([
                            html.Strong("Address:"),
                            html.Br(),
                            "CHRU de Tours",
                            html.Br(),
                            "2 Boulevard Tonnelé",
                            html.Br(),
                            "37044 Tours Cedex 9",
                            html.Br(),
                            "France"
                        ]),
                        html.P([
                            "With the support of our partners: ",
                            html.Strong("Association Leucémie Espoir 72"),
                            " and ",
                            html.Strong("SFGM-TC"),
                            "."
                        ]),

                        html.H5("Contact", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "For any questions regarding this platform, please contact:",
                            html.Br(),
                            html.Strong("contact@allograph.eu")
                        ]),

                        html.H5("Hosting", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "This platform is hosted by the ",
                            html.Strong("Université de Tours"),
                            ", 2 Boulevard Tonnelé, 37044 Tours Cedex 9, France."
                        ]),

                        html.H5("Intellectual Property", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "AlloGraph is an open-source project licensed under the Apache License 2.0.",
                            html.Br(),
                            "Deposited at the ",
                            html.Strong("Agence pour la Protection des Programmes (APP)"),
                            ".",
                            html.Br(),
                            "IDDN registration: ",
                            html.Strong("IDDN.FR.001.090021.000.S.P.2026.000.31230"),
                            html.Br(),
                            html.Img(
                                src="allograph-app/assets/images/QRCodeIDDN.jpg",
                                style={
                                    'height': '160px',
                                    'width': '160px',
                                    'marginTop': '10px',
                                    'borderRadius': '8px',
                                    'border': '1px solid #dee2e6'
                                }
                            )
                        ]),

                        html.H5("Nature of the Service", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "AlloGraph is a standalone analytical tool designed for healthcare professionals and researchers. ",
                            "Loaded data is transmitted to the application server for real-time processing and visualization. ",
                            "However, patient data is never stored, logged, archived, or persisted on any remote server beyond the duration of the active session.",
                            "AlloGraph does not communicate directly with the EBMT Registry or any external databases. "
                        ]),


                    ], className="p-4")
                ], style={'border': 'none', 'borderRadius': '16px', 'boxShadow': '0 2px 12px rgba(0,0,0,0.06)'})
            ], width=12)
        ])
    ], style={'padding': '20px 10px'})


def register_callbacks(app):
    """Pas de callbacks spécifiques pour cette page statique"""
    pass
