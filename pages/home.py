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

def create_hero_animation():
    """Crée le composant d'animation video (WebM)"""
    return html.Div([
        html.Video(
            src="allograph-app/assets/allogif.webm",
            autoPlay=True,
            loop=True,
            muted=True,
            style={
                'width': '100%',
                'height': 'auto',
                'maxWidth': '650px',
                'display': 'block',
                'margin': '0 auto'
            }
        )
    ], style={
        'width': '100%',
        'maxWidth': '650px',
        'margin': '0 auto',
        'display': 'block',
        'textAlign': 'center'
    })

def create_upload_zone():
    """Crée une zone d'upload moderne et attrayante"""
    return dcc.Upload(
        id='upload-data',
        children=html.Div([
            # Header de la zone
            html.Div([
                html.I(className="bi bi-cloud-upload fs-1", style={'color': '#0D3182', 'marginBottom': '15px'}),
                html.H4("Upload Your Data", style={'color': '#0D3182', 'fontWeight': '700', 'marginBottom': '10px'}),
                html.P([
                    "Drag and drop your file here, or ",
                    html.Span("browse", style={'color': '#c0392b', 'fontWeight': '600', 'cursor': 'pointer'})
                ], style={'color': '#6c757d', 'marginBottom': '0'}),
                html.P("Supports CSV, Excel (.xlsx, .xls)", style={'color': '#adb5bd', 'fontSize': '12px', 'marginTop': '8px', 'marginBottom': '0'})
            ], style={
                'border': '3px dashed #0D3182',
                'borderRadius': '16px',
                'padding': '40px 30px',
                'textAlign': 'center',
                'backgroundColor': '#f8f9fa',
                'transition': 'all 0.3s ease',
                'cursor': 'pointer'
            }, id="upload-zone-hover"),
        ]),
        style={
            'width': '100%',
        },
        multiple=False
    )

def create_how_to_get_data_section():
    """Crée la section "Comment obtenir vos données" avec l'image EBMT"""
    return html.Div([
        # Header cliquable
        dbc.Button([
            html.I(className="bi bi-question-circle me-2"),
            "How to get your data from EBMT Registry?",
            html.I(className="bi bi-chevron-down ms-2", id="tutorial-chevron")
        ], 
        id="tutorial-collapse-btn",
        color="light",
        className="w-100 text-start",
        style={
            'backgroundColor': '#f8f9fa',
            'border': '1px solid #dee2e6',
            'borderRadius': '12px',
            'color': '#0D3182',
            'fontWeight': '600',
            'padding': '15px 20px',
            'boxShadow': 'none'
        }),
        
        # Contenu collapsible
        dbc.Collapse([
            html.Div([
                # Introduction
                html.P([
                    "To use AlloGraph, you need to export your data from the ",
                    html.Strong("EBMT Registry"), 
                    ". Follow these steps:"
                ], style={'marginBottom': '20px', 'color': '#495057'}),
                
                # L'image du tutoriel
                html.Div([
                    html.Img(
                        src="allograph-app/assets/images/EBMTtuto.png",
                        style={
                            'width': '100%',
                            'maxWidth': '900px',
                            'height': 'auto',
                            'display': 'block',
                            'margin': '0 auto',
                            'borderRadius': '12px',
                            'boxShadow': '0 4px 20px rgba(0,0,0,0.1)'
                        },
                        className="img-fluid"
                    )
                ], style={'textAlign': 'center', 'marginBottom': '20px'}),
                
                # Résumé textuel des étapes
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Div("1", style={
                                    'width': '32px', 'height': '32px', 'borderRadius': '50%',
                                    'backgroundColor': '#0D3182', 'color': 'white',
                                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                                    'fontWeight': '700', 'marginRight': '12px', 'flexShrink': '0'
                                }),
                                html.Div([
                                    html.Strong("Login to EBMT Registry", style={'color': '#0D3182'}),
                                    html.P("Go to ebmt.registry.org and sign in with your credentials.", 
                                           style={'fontSize': '13px', 'color': '#6c757d', 'marginBottom': '0'})
                                ])
                            ], style={'display': 'flex', 'alignItems': 'flex-start', 'marginBottom': '15px'})
                        ], width=6),
                        dbc.Col([
                            html.Div([
                                html.Div("2", style={
                                    'width': '32px', 'height': '32px', 'borderRadius': '50%',
                                    'backgroundColor': '#0D3182', 'color': 'white',
                                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                                    'fontWeight': '700', 'marginRight': '12px', 'flexShrink': '0'
                                }),
                                html.Div([
                                    html.Strong("Select MicroStrategy", style={'color': '#0D3182'}),
                                    html.P("On the left panel, click on 'MicroStrategy' to access the reporting tool.", 
                                           style={'fontSize': '13px', 'color': '#6c757d', 'marginBottom': '0'})
                                ])
                            ], style={'display': 'flex', 'alignItems': 'flex-start', 'marginBottom': '15px'})
                        ], width=6),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Div("3", style={
                                    'width': '32px', 'height': '32px', 'borderRadius': '50%',
                                    'backgroundColor': '#0D3182', 'color': 'white',
                                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                                    'fontWeight': '700', 'marginRight': '12px', 'flexShrink': '0'
                                }),
                                html.Div([
                                    html.Strong("Choose Treatment Overview", style={'color': '#0D3182'}),
                                    html.P("Select 'Treatment overview report' from the available reports.", 
                                           style={'fontSize': '13px', 'color': '#6c757d', 'marginBottom': '0'})
                                ])
                            ], style={'display': 'flex', 'alignItems': 'flex-start', 'marginBottom': '15px'})
                        ], width=6),
                        dbc.Col([
                            html.Div([
                                html.Div("4", style={
                                    'width': '32px', 'height': '32px', 'borderRadius': '50%',
                                    'backgroundColor': '#0D3182', 'color': 'white',
                                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                                    'fontWeight': '700', 'marginRight': '12px', 'flexShrink': '0'
                                }),
                                html.Div([
                                    html.Strong("Filter & Export", style={'color': '#0D3182'}),
                                    html.P("Select 'Allogeneic HCT' as treatment type, then export to CSV format.", 
                                           style={'fontSize': '13px', 'color': '#6c757d', 'marginBottom': '0'})
                                ])
                            ], style={'display': 'flex', 'alignItems': 'flex-start', 'marginBottom': '15px'})
                        ], width=6),
                    ]),
                ], style={'marginTop': '20px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '12px'}),
                
                # Note finale
                html.Div([
                    html.I(className="bi bi-info-circle me-2", style={'color': '#2E86AB'}),
                    html.Strong("Tip: ", style={'color': '#2E86AB'}),
                    "The exported CSV file is ready to be loaded into AlloGraph without any modifications!"
                ], style={
                    'marginTop': '20px', 
                    'padding': '15px 20px', 
                    'backgroundColor': '#e7f3ff', 
                    'borderRadius': '10px',
                    'borderLeft': '4px solid #2E86AB',
                    'color': '#0D3182'
                })
            ], style={
                'padding': '25px',
                'backgroundColor': '#ffffff',
                'border': '1px solid #dee2e6',
                'borderTop': 'none',
                'borderRadius': '0 0 12px 12px'
            })
        ], id="tutorial-collapse", is_open=False)
    ])

def create_feature_card(icon, title, description, color):
    """Crée une carte de fonctionnalité"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"bi {icon} fs-2", style={'color': color})
            ], style={
                'width': '60px', 'height': '60px', 'borderRadius': '12px',
                'backgroundColor': f'{color}20', 'display': 'flex',
                'alignItems': 'center', 'justifyContent': 'center',
                'marginBottom': '15px'
            }),
            html.H5(title, style={'color': '#0D3182', 'fontWeight': '700', 'marginBottom': '10px'}),
            html.P(description, style={'color': '#6c757d', 'fontSize': '14px', 'marginBottom': '0'})
        ])
    ], style={
        'border': 'none', 
        'borderRadius': '16px',
        'boxShadow': '0 2px 12px rgba(0,0,0,0.06)',
        'height': '100%',
        'transition': 'transform 0.2s ease, box-shadow 0.2s ease'
    }, className="feature-card")

def create_test_data_card():
    """Crée la carte pour charger les données de test"""
    return html.Div([
        html.I(className="bi bi-flask fs-1", style={'color': '#28a745', 'marginBottom': '15px'}),
        html.H4("Preview with Sample Dataset", style={'color': '#0D3182', 'fontWeight': '700', 'marginBottom': '10px'}),
        html.P([
            "Load a de-identified test dataset to preview the application's capabilities."
        ], style={'color': '#6c757d', 'fontSize': '14px', 'marginBottom': '20px'}),
        dbc.Button([
            html.I(className="bi bi-play-fill me-2"),
            "Load Test Sample"
        ], 
        id="load-test-sample-btn",
        color="success",
        className="w-100",
        style={'borderRadius': '10px', 'fontWeight': '600'})
    ], style={
        'border': '3px dashed #28a745',
        'borderRadius': '16px',
        'padding': '40px 30px',
        'textAlign': 'center',
        'backgroundColor': '#f8fff8',
        'height': '100%',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center',
        'transition': 'all 0.3s ease',
        'cursor': 'pointer'
    }, id="test-data-card")

def create_welcome_content():
    """Crée le contenu d'accueil quand aucune donnée n'est chargée"""
    return html.Div([
        # Section Hero
        dbc.Row([
            dbc.Col([
                html.Div([
                    # Badge
                    html.Div([
                        html.I(className="bi bi-graph-up me-2"),
                        "EBMT-Compliant Data Analysis Tool"
                    ], style={
                        'display': 'inline-flex', 'alignItems': 'center',
                        'backgroundColor': '#0D318220', 'color': '#0D3182',
                        'padding': '8px 16px', 'borderRadius': '20px',
                        'fontSize': '13px', 'fontWeight': '600',
                        'marginBottom': '20px'
                    }),
                    
                    # Titre principal
                    html.H1([
                        "Analyze Your ",
                        html.Span("Transplant Data", style={'color': '#c0392b'})
                    ], style={
                        'color': '#0D3182', 
                        'fontWeight': '800', 
                        'fontSize': '3rem',
                        'marginBottom': '20px',
                        'lineHeight': '1.2'
                    }),
                    
                    # Description
                    html.P([
                        "AlloGraph is a comprehensive analytics platform designed for ",
                        html.Strong("allogeneic hematopoietic stem cell transplantation"),
                        " data. Visualize trends, perform survival analysis, and generate ",
                        "clinical indicators that conform to the EBMT registry data model."
                    ], style={
                        'color': '#6c757d', 
                        'fontSize': '1.1rem',
                        'lineHeight': '1.7',
                        'marginBottom': '30px'
                    }),
                    
                    # Key capabilities
                    html.Div([
                        html.Div([
                            html.Strong("Cohort-based", style={'color': '#0D3182', 'fontSize': '1.1rem'}),
                            html.P("Population-level analysis", style={'color': '#6c757d', 'fontSize': '13px', 'marginBottom': '0'})
                        ], style={'textAlign': 'center', 'padding': '0 15px'}),
                        html.Div(style={'width': '1px', 'height': '35px', 'backgroundColor': '#dee2e6'}),
                        html.Div([
                            html.Strong("Temporal", style={'color': '#0D3182', 'fontSize': '1.1rem'}),
                            html.P("Follow-up over time", style={'color': '#6c757d', 'fontSize': '13px', 'marginBottom': '0'})
                        ], style={'textAlign': 'center', 'padding': '0 15px'}),
                        html.Div(style={'width': '1px', 'height': '35px', 'backgroundColor': '#dee2e6'}),
                        html.Div([
                            html.Strong("Visual", style={'color': '#0D3182', 'fontSize': '1.1rem'}),
                            html.P("Interactive charts and tables", style={'color': '#6c757d', 'fontSize': '13px', 'marginBottom': '0'})
                        ], style={'textAlign': 'center', 'padding': '0 15px'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '30px'}),
                    
                ], style={'paddingRight': '30px'})
            ], width=7),
            
            dbc.Col([
                # Animation Lottie
                create_hero_animation()
            ], width=5, style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})
        ], style={'marginBottom': '40px', 'alignItems': 'center'}),
        
        # Section Upload + Test Sample
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                create_upload_zone()
                            ], width=7),
                            dbc.Col([
                                create_test_data_card()
                            ], width=5)
                        ], className="g-4")
                    ], className="p-4")
                ], className="upload-section-card")
            ], width=12)
        ], style={'marginBottom': '20px'}),
        
        # Privacy notice below upload
        html.Div([
            html.P([
                html.I(className="bi bi-shield-check me-2", style={'color': '#28a745'}),
                "Your transplant data is processed ",
                html.Strong("locally in your browser"),
                " and is never uploaded to any server."
            ], style={
                'textAlign': 'center',
                'color': '#6c757d',
                'fontSize': '14px',
                'marginBottom': '40px'
            })
        ]),
        
        # Section "How to get your data"
        dbc.Row([
            dbc.Col([
                create_how_to_get_data_section()
            ], width=12)
        ], style={'marginBottom': '40px'}),
        
        # Section Features (5 cards - first row: 3 cards, second row: 2 cards centered)
        html.Div([
            html.H3("Available Analyses", style={'color': '#0D3182', 'fontWeight': '700', 'marginBottom': '25px', 'textAlign': 'center'}),
            dbc.Row([
                dbc.Col([
                    create_feature_card(
                        "bi-people",
                        "Patient Demographics",
                        "Analyze age distributions, blood groups, and patient stratification by various clinical parameters.",
                        "#0D3182"
                    )
                ], width=4, className="mb-4"),
                dbc.Col([
                    create_feature_card(
                        "bi-file-medical",
                        "Disease Analysis",
                        "Examine diagnosis distributions and disease classifications with interactive visualizations.",
                        "#2E86AB"
                    )
                ], width=4, className="mb-4"),
                dbc.Col([
                    create_feature_card(
                        "bi-hospital",
                        "Procedural Insights",
                        "Study donor types, stem cell sources, conditioning regimens, and prophylaxis combinations.",
                        "#c0392b"
                    )
                ], width=4, className="mb-4"),
            ]),
            dbc.Row([
                dbc.Col([], width=2),
                dbc.Col([
                    create_feature_card(
                        "bi-heart-pulse",
                        "GvHD Analysis",
                        "Perform competing risks analysis for acute and chronic Graft-versus-Host Disease.",
                        "#0D3182"
                    )
                ], width=4, className="mb-4"),
                dbc.Col([
                    create_feature_card(
                        "bi-graph-up",
                        "Survival Analysis",
                        "Generate Kaplan-Meier curves with confidence intervals and long-term follow-up metrics.",
                        "#2E86AB"
                    )
                ], width=4, className="mb-4"),
                dbc.Col([], width=2),
            ])
        ])
    ], style={'padding': '20px 10px'})

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
                                html.H4("Data Overview", className="mb-0", style={'color': '#ffffff', 'fontWeight': '700'})
                            ]),
                            dbc.CardBody([
                                dcc.Graph(
                                    figure=fig, 
                                    style={'height': '500px'},
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
            # Pas de données : afficher le nouveau design d'accueil
            return create_welcome_content()
    
    @app.callback(
        Output("tutorial-collapse", "is_open"),
        Output("tutorial-chevron", "className"),
        Input("tutorial-collapse-btn", "n_clicks"),
        State("tutorial-collapse", "is_open"),
        prevent_initial_call=True
    )
    def toggle_tutorial_collapse(n_clicks, is_open):
        """Toggle the tutorial section open/closed"""
        if n_clicks:
            if is_open:
                return False, "bi bi-chevron-down ms-2"
            else:
                return True, "bi bi-chevron-up ms-2"
        return is_open, "bi bi-chevron-down ms-2"
