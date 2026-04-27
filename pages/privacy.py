from dash import html
import dash_bootstrap_components as dbc


def get_layout():
    """Retourne le layout de la page Privacy Policy"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H3("Privacy Notice", className="mb-0", style={'color': '#ffffff', 'fontWeight': '700'})
                    ),
                    dbc.CardBody([
                        html.P([
                            html.Strong("Last updated: April 2026")
                        ], style={'color': '#6c757d', 'marginBottom': '20px'}),

                        html.H5("1. Data Controller", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '20px'}),
                        html.P([
                            "The data controllers for this platform are:",
                            html.Br(),
                            html.Strong("CHRU de Tours"),
                            " and ",
                            html.Strong("Université de Tours"),
                            ", 2 Boulevard Tonnelé, 37044 Tours Cedex 9, France."
                        ]),
                        html.H5("2. Purpose of Processing", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "AlloGraph is a client-side analytical tool intended for healthcare professionals and researchers. ",
                            "Its sole purpose is to enable users to perform statistical analyses on allogeneic hematopoietic stem cell transplantation datasets ",
                            "that they upload themselves. The platform does not collect, store, or process any data for its own purposes."
                        ]),

                        html.H5("3. Legal Basis", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "The processing of personal data within AlloGraph is based on the explicit consent of the user (Article 9(2)(a) GDPR) ",
                            "and/or the legitimate interest of the data controller in providing analytical tools for clinical research and quality improvement (Article 6(1)(f) GDPR). ",
                            "Users remain solely responsible for ensuring that they have a valid legal basis for uploading and analysing any patient data, ",
                            "including compliance with hospital policies, ethics approvals, and applicable data protection laws."
                        ]),

                        html.H5("4. Categories of Data", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "When a user uploads a dataset, the platform processes the data contained in that file. ",
                            "This may include:",
                            html.Ul([
                                html.Li("Patient identifiers (e.g., 'Long ID')"),
                                html.Li("Demographic data (date of birth, sex, blood group)"),
                                html.Li("Medical data (diagnoses, treatment dates, procedural details, follow-up status)"),
                                html.Li("Clinical scores and performance status")
                            ]),
                            "These data may qualify as personal data and/or special category data (health data) under the GDPR."
                        ]),

                        html.H5("5. How Data Is Processed", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            html.Strong("Client-side only:"),
                            " All data uploaded by the user is processed entirely within the user's own web browser. ",
                            "No data is transmitted to, stored on, or backed up by any remote server operated by the publishers of AlloGraph."
                        ]),
                        html.P([
                            html.Strong("Zero-persistence:"),
                            " Data exists only for the duration of the browser session. ",
                            "It is automatically cleared when the user closes the tab or navigates away. ",
                            "Users may also manually delete data at any time using the 'Void data' button."
                        ]),
                        html.P([
                            html.Strong("No automated decision-making:"),
                            " The platform does not perform any automated individual decision-making or profiling."
                        ]),

                        html.H5("6. Data Retention", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "Data is retained only for the duration of the active browser session. ",
                            "There is no server-side storage, logging, or archiving of uploaded datasets. ",
                            "Temporary in-memory caching of statistical results occurs solely on the application server and is cleared on restart, ",
                            "with no personal health information used in cache keys."
                        ]),

                        html.H5("7. Data Transfers", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "No personal data is transferred outside the European Economic Area (EEA). ",
                            "All processing occurs client-side within the user's browser."
                        ]),

                        html.H5("8. Your Rights", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P("Under the GDPR, data subjects have the following rights:"),
                        html.Ul([
                            html.Li("Right of access to their personal data"),
                            html.Li("Right to rectification of inaccurate data"),
                            html.Li("Right to erasure ('right to be forgotten')"),
                            html.Li("Right to restriction of processing"),
                            html.Li("Right to data portability"),
                            html.Li("Right to object to processing")
                        ]),
                        html.P([
                            "Because AlloGraph does not store data on its servers, the exercise of these rights is primarily the responsibility of the user ",
                            "who uploaded the data. The user may exercise these rights at any time by deleting the dataset using the 'Void data' function."
                        ]),

                        html.H5("9. Security Measures", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "The platform employs the following technical and organisational measures to protect data:"
                        ]),
                        html.Ul([
                            html.Li("No server-side persistence of uploaded files"),
                            html.Li("In-memory processing only"),
                            html.Li("Gzip compression of network traffic (Flask-Compress) with no retention of payload data"),
                            html.Li("Session-scoped in-memory caching with hashed, non-identifying cache keys"),
                            html.Li("HTTPS enforcement recommended for production deployments")
                        ]),

                        html.H5("10. Changes to This Notice", style={'color': '#0D3182', 'fontWeight': '700', 'marginTop': '25px'}),
                        html.P([
                            "We may update this Privacy Notice from time to time. Any changes will be posted on this page with an updated revision date."
                        ]),

                        html.Hr(),
                        html.P([
                            html.I(className="bi bi-shield-check me-2"),
                            html.Strong("User responsibility:"),
                            " By uploading data to AlloGraph, you confirm that you are authorised to process the data, ",
                            "that you have a valid legal basis for doing so, and that you remain solely responsible for the lawfulness of the processing."
                        ], style={'color': '#6c757d', 'fontSize': '14px'})
                    ], className="p-4")
                ], style={'border': 'none', 'borderRadius': '16px', 'boxShadow': '0 2px 12px rgba(0,0,0,0.06)'})
            ], width=12)
        ])
    ], style={'padding': '20px 10px'})


def register_callbacks(app):
    """Pas de callbacks spécifiques pour cette page statique"""
    pass
