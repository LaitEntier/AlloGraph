from dash import html
import dash_bootstrap_components as dbc


def get_layout():
    """Retourne le layout de la page Cookie Policy"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H3("Cookie Policy", className="mb-0", style={'color': '#ffffff', 'fontWeight': '700'})
                    ),
                    dbc.CardBody([
                        html.P([
                            html.Strong("Last updated: April 2026")
                        ], style={'color': '#6c757d', 'marginBottom': '20px'}),

                        html.H5("1. What Are Cookies?", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '20px'}),
                        html.P([
                            "Cookies are small text files that websites place on your computer or mobile device when you visit them. ",
                            "They are widely used to make websites work more efficiently, as well as to provide information to the site owners."
                        ]),

                        html.H5("2. Our Use of Cookies and Similar Technologies", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            html.Strong("AlloGraph does not use third-party cookies, analytics cookies, advertising cookies, or social media trackers. ")
                        ]),
                        html.P([
                            "However, the platform uses standard browser storage mechanisms to maintain the state of the application during your session. ",
                            "This is necessary for the core functionality of the tool and does not involve tracking your activity across different websites."
                        ]),

                        html.H5("3. Browser Storage Used by AlloGraph", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "The application uses the following client-side storage technologies:"
                        ]),
                        html.Ul([
                            html.Li([
                                html.Strong("Dash dcc.Store (localStorage / sessionStorage):"),
                                " Used to hold the dataset you upload and derived analytical results while you interact with the platform. ",
                                "This storage is limited to the browser tab/session and is cleared when you close the tab or click 'Void data'."
                            ]),
                            html.Li([
                                html.Strong("Session cookies (essential):"),
                                " The underlying web framework (Flask/Dash) may issue a minimal session cookie to maintain the server-side session state. ",
                                "This cookie does not contain personal data and is essential for the operation of the application."
                            ])
                        ]),

                        html.H5("4. No Third-Party Tracking", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "We do not use:"
                        ]),
                        html.Ul([
                            html.Li("Google Analytics or any other web analytics service"),
                            html.Li("Advertising or behavioural targeting cookies"),
                            html.Li("Social media plugins or trackers"),
                            html.Li("Third-party content delivery networks (CDNs) that set cookies")
                        ]),

                        html.H5("5. Managing Your Preferences", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "Because AlloGraph only uses essential, session-bound storage necessary for the functioning of the tool, ",
                            "no cookie consent banner is required under current regulations. ",
                            "If you wish to clear all stored data, you may do so at any time by clicking the ",
                            html.Strong("'Void data'"),
                            " button or by closing your browser tab."
                        ]),
                        html.P([
                            "Most web browsers allow you to control cookies through their settings. ",
                            "Please note that disabling essential cookies or browser storage may prevent AlloGraph from functioning correctly."
                        ]),

                        html.H5("6. Changes to This Policy", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "We may update this Cookie Policy from time to time to reflect changes in technology or regulation. ",
                            "Any changes will be posted on this page with an updated revision date."
                        ]),

                        html.Hr(),
                        html.P([
                            html.I(className="bi bi-info-circle me-2"),
                            html.Strong("Contact:"),
                            " If you have any questions about our use of cookies or similar technologies, please contact us using the details provided in the ",
                            html.Strong("Legal Notices"),
                            " page."
                        ], style={'color': '#6c757d', 'fontSize': '14px'})
                    ], className="p-4")
                ], style={'border': 'none', 'borderRadius': '16px', 'boxShadow': '0 2px 12px rgba(0,0,0,0.06)'})
            ], width=12)
        ])
    ], style={'padding': '20px 10px'})


def register_callbacks(app):
    """Pas de callbacks spécifiques pour cette page statique"""
    pass
