# pages/home.py
from io import BytesIO

import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import docx
from pages.indics import get_variables_for_indicator
import utils.docx_helpers as docx_helpers
import utils.html_helpers as html_helpers
from docx.shared import Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn
import pandas as pd
from dash_extensions import Lottie

# Import des modules communs
import visualizations.allogreffes.graphs as gr

import xlsxwriter

def get_layout():
    """Retourne le layout de la page d'accueil"""
    return html.Div([
        # Contenu principal de l'accueil avec spinner
        dcc.Loading(
            id="loading-home-main",
            type="circle",
            delay_show=500,
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
                html.H4("Load Your Data", style={'color': '#0D3182', 'fontWeight': '700', 'marginBottom': '10px'}),
                html.P([
                    "Drag and drop your file here, or ",
                    html.Span("browse", style={'color': '#d61704', 'fontWeight': '600', 'cursor': 'pointer'})
                ], style={'color': '#6c757d', 'marginBottom': '0'}),
                html.P("Supports CSV from your favorite european registry", style={'color': '#adb5bd', 'fontSize': '12px', 'marginTop': '8px', 'marginBottom': '0'})
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

def create_import_template_section():
    """Crée la section pour télécharger le template de données"""
    return html.Div([
        # Header cliquable
        dbc.Button([
            html.I(className="bi bi-download me-2"),
            "Import your own data",
            html.I(className="bi bi-chevron-down ms-2", id="template-chevron")
        ],
        id="template-collapse-btn",
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
                    "If your data does not come from a european registry, you can use our template to format your data so that it is compatible with AlloGraph.",
                ], style={'marginBottom': '20px', 'color': '#495057'}),

                # Download card
                html.Div([
                    html.P([
                        "Download the Excel template, fill it with your patient data, and upload it using the drag-and-drop zone above.",
                    ], style={'color': '#6c757d', 'fontSize': '14px', 'marginBottom': '15px', 'textAlign': 'center'}),
                    html.Div([
                        dbc.Button([
                            html.I(className="bi bi-download me-2"),
                            "Download Template"
                        ],
                        id="download-template-btn",
                        color="success",
                        style={
                            'borderRadius': '10px',
                            'fontWeight': '600'
                        })
                    ], style={'textAlign': 'center'})
                ], style={'maxWidth': '500px', 'margin': '0 auto', 'marginBottom': '20px'}),
            ], style={
                'padding': '25px',
                'backgroundColor': '#ffffff',
                'border': '1px solid #dee2e6',
                'borderTop': 'none',
                'borderRadius': '0 0 12px 12px'
            })
        ], id="template-collapse", is_open=False),

        # Hidden download component
        dcc.Download(id="download-template")
    ])

def create_how_to_get_data_section():
    """Crée la section "Comment obtenir vos données" avec l'image EBMT"""
    return html.Div([
        # Header cliquable
        dbc.Button([
            html.I(className="bi bi-question-circle me-2"),
            "How to get your data from your favorite european registry?",
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
                    html.Strong("your favorite european registry"), 
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
                                    html.Strong("Login to your favorite european registry", style={'color': '#0D3182'}),
                                    html.P("Go to your favorite european registry and sign in with your credentials.", 
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
                        "Data Analysis Tool compliant with your favorite european registry data model"
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
                        html.Span("Transplant Data", style={'color': '#d61704'})
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
                        "clinical indicators that conform to your favorite european registry data model."
                    ], style={
                        'color': '#6c757d',
                        'fontSize': '1.1rem',
                        'lineHeight': '1.7',
                        'marginBottom': '15px'
                    }),
                    
                    # Partners
                    html.P([
                        "Developed in collaboration with ",
                        html.Strong("Association Leucémie Espoir 72"), ", ",
                        html.Strong("SFGM-TC"), ", ",
                        html.Strong("CHRU de Tours"), 
                        " and ",
                        html.Strong("Université de Tours"),
                        "."
                    ], style={
                        'color': '#6c757d',
                        'fontSize': '0.95rem',
                        'lineHeight': '1.6',
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
                "Your data exists only for this analysis session, clears when you leave, ",
                html.Strong("and is never stored on any server."),
            ], style={
                'textAlign': 'center',
                'color': '#6c757d',
                'fontSize': '14px',
                'marginBottom': '40px'
            })
        ]),
        
        # Section "Import your own data"
        dbc.Row([
            dbc.Col([
                create_import_template_section()
            ], width=12)
        ], style={'marginBottom': '20px'}),

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
                        "#d61704"
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
        ]),
        
        # Bannière
        create_banner_component()
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
        Output("template-collapse", "is_open"),
        Output("template-chevron", "className"),
        Input("template-collapse-btn", "n_clicks"),
        State("template-collapse", "is_open"),
        prevent_initial_call=True
    )
    def toggle_template_collapse(n_clicks, is_open):
        """Toggle the template section open/closed"""
        if n_clicks:
            if is_open:
                return False, "bi bi-chevron-down ms-2"
            else:
                return True, "bi bi-chevron-up ms-2"
        return is_open, "bi bi-chevron-down ms-2"

    @app.callback(
        Output("download-template", "data"),
        Input("download-template-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def download_template(n_clicks):
        """Download the data import template"""
        if n_clicks:
            return dcc.send_file("data/import_template_allograph.xlsx")
        return None

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

    @app.callback(
        Output("download-indicators-docx", "data"),
        Input("download-indicators-docx-button", "n_clicks"),
        State("year-selection-sidebar", "value"),
        State("data-store", "data"),
        State("metadata-store", "data"),
        prevent_initial_call=True
    )
    def export_indicators_to_docx(n_clicks, year_selection, indicators_df, metadata):
        """Gère l'export docx des tableaux d'Indicators"""
        if n_clicks is None:
            return dash.no_update
        
        try:
            import pages.indics as indics
            indicator_df = pd.DataFrame(indicators_df)

            # On ne garde que les données de l'année selectionner avec n-1 et n-2, si y'en a une. Sinon on prend toutes les années
            if year_selection != 0:
                indicator_df = indicator_df[indicator_df['Year'].isin([year_selection, str(int(year_selection)-1), str(int(year_selection)-2)])]

            from datetime import datetime
            current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            infusion_df: pd.DataFrame = indicator_df[['Year','Greffes']].groupby("Year").count()
            
            doc = docx.Document()
            date = current_date.split("_")[0]
            date = date[6:] + "/" + date[4:6] + "/" + date[:4]

            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture("assets/images/logo.png",width=Cm(5))

            style = doc.styles["Title"]
            pBdr = style.element.pPr.find(qn("w:pBdr"))
            if pBdr is not None:
                bottom = pBdr.find(qn("w:bottom"))
                bottom.set(qn("w:color"), "021F59") 

            # Insert into the document straight from memory
            heading = doc.add_heading("General report information", 0)
            heading.style.element.rPr.rFonts.set(qn("w:asciiTheme"), "Roboto")
            heading.style.font.color.rgb = RGBColor(0x02, 0x1F, 0x59)


            p = doc.add_paragraph("This report was produced on: " + str(date))
            p.style.font.name = "Roboto"
            p.style.font.color.rgb = RGBColor(0x02, 0x1F, 0x59)
            p = doc.add_paragraph("The input file is entitled: " + metadata["filename"]) 
            p.style.font.name = "Roboto"
            p.style.font.color.rgb = RGBColor(0x02, 0x1F, 0x59)
            p = doc.add_paragraph("The pipeline version:")
            p.style.font.name = "Roboto"
            p.style.font.color.rgb = RGBColor(0x02, 0x1F, 0x59)
            p = doc.add_paragraph("The indicators were computed with the data provided by the user.\n"
                    "Methods to compute indicators are described online.\n"
                    "All legal and privacy notice are provided on: ")
            p.style.font.name = "Roboto"
            p.style.font.color.rgb = RGBColor(0x02, 0x1F, 0x59)
            docx_helpers.add_hyperlink(p,"https://allograph.univ-tours.fr/", "allograph.univ-tours.fr")

            table_data = []
            for year, row in infusion_df.iterrows():
                table_data.append({
                    'Year': year,
                    'Infusions': int(row['Greffes']),
                })

            rows_def = [
                ("Infusions (n)", "Infusions", None),
            ]

            docx_helpers.add_docx_stat_table(doc,"Number of infusions", table_data, rows_def)

            tables = [
                (indics.process_prise_greffe_data, None, indics.create_prise_greffe_docx_table),
                (indics.process_sortie_aplasie_data, None, indics.create_sortie_aplasie_docx_table),
                (indics.process_trm_data, 1, indics.create_trm_docx_table),
                (indics.process_gvha_data, 0, indics.create_gvha_docx_table),
                (indics.process_gvhc_data, 0, indics.create_gvhc_docx_table),
                (indics.process_rechute_data, 1, indics.create_rechute_docx_table),
                (indics.process_survie_data, 1, indics.create_survie_docx_table),
            ]

            for func_process, idx, func_datatable in tables:
                result = func_process(indicator_df)
                result_df = result[idx] if idx is not None else result
                doc = func_datatable(result_df, doc)

            # Ajout de la numérotation des pages
            doc.sections[0].footer.paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
            docx_helpers.marquage(doc.sections[0].footer.paragraphs[0])
            docx_helpers.add_page_number(doc.sections[0].footer.paragraphs[0])
            

            # Enregistrement du fichier docx sous forme de bytes pour le téléchargement
            import base64
            out = BytesIO()
            doc.save(out)
            content = base64.b64encode(out.getvalue()).decode("utf-8")

            # Générer un nom de fichier avec la date
            filename = f"indicators_tables_{current_date}.docx"
            
            return dict(content=content, filename=filename, base64=True, type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


        except Exception as e:
            print(f"Error during DOCX export Indicators: {e}")
            return dash.no_update    

    @app.callback(
        Output("download-indicators-html", "data"),
        Input("download-indicators-html-button", "n_clicks"),
        State("year-selection-sidebar", "value"),
        State("data-store", "data"),
        State("metadata-store", "data"),
        prevent_initial_call=True
    )
    def export_indicators_to_html(n_clicks, year_selection, indicators_df, metadata):
        """Gère l'export html des tableaux d'Indicators"""
        if n_clicks is None:
            return dash.no_update

        try:
            import pages.indics as indics
            from datetime import datetime
            current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            indicator_df = pd.DataFrame(indicators_df)

            if year_selection != 0:
                indicator_df = indicator_df[indicator_df['Year'].isin(
                    [str(int(year_selection) - 2), str(int(year_selection) - 1), year_selection]
                )]

            infusion_df = indicator_df[['Year', 'Greffes']].groupby("Year").count()

            d = current_date.split("_")[0]
            date = d[4:6] + "/" + d[6:] + "/" + d[:4]

            components = []

            logo = html_helpers.logo_data_uri()
            if logo:
                components.append(html.Img(
                    src=logo, alt="Logo",
                    style={'display': 'block', 'margin': '0 auto 1.5rem auto', 'width': '5cm'}))
            components.extend([
                html.H1("General report information", className='mb-3'),
                html.P(f"This report was produced on: {date}"),
                html.P(f"The input file is entitled: {metadata['filename']}"),
                html.P("The pipeline version:"),
                html.P([
                    "The indicators were computed with the data provided by the user.",
                    html.Br(),
                    "Methods to compute indicators are described online.",
                    html.Br(),
                    "All legal and privacy notices are provided on: ",
                    html.A("allograph.univ-tours.fr", href="https://allograph.univ-tours.fr/"),
                ]),
                html.H1("Activity indicators", className='mt-4 mb-3'),
                html.Div(indics.create_infusions_datatable(infusion_df), className='mb-4'),
            ])

            tables = [
                (indics.process_prise_greffe_data, None, indics.create_prise_greffe_datatable),
                (indics.process_sortie_aplasie_data, None, indics.create_sortie_aplasie_datatable),
                (indics.process_trm_data, 1, indics.create_trm_datatable),
                (indics.process_gvha_data, 0, indics.create_gvha_datatable),
                (indics.process_gvhc_data, 0, indics.create_gvhc_datatable),
                (indics.process_rechute_data, 1, indics.create_rechute_datatable),
                (indics.process_survie_data, 1, indics.create_survie_datatable),
            ]

            for func_process, idx, func_datatable in tables:
                result = func_process(indicator_df)
                result_df = result[idx] if idx is not None else result
                components.append(html.Div(func_datatable(result_df), className='mb-4'))

            html_doc = html_helpers.build_html_from_components(components, app, title="Indicators report")
            filename = f"indicators_tables_{current_date}.html"

            return dict(content=html_doc, filename=filename, type="text/html")

        except Exception as e:
            print(f"Error during HTML export Indicators: {e}")
            return dash.no_update

    @app.callback(
            Output('download-all-missing-excel', 'data'),
            Input('export-all-missing-button', 'n_clicks'),
            State('data-store', 'data'),
    )
    def export_all_missing_to_csv(n_clicks, data):
        """Gère l'export de toutes les données manquante au format csv"""
        if n_clicks is None:
                    return dash.no_update
        try:
            import io
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')

            df = pd.DataFrame(data)
            if df.empty:
                return None
            
            existing_columns = [col for col in df.columns]

            # ALL
            if not existing_columns:
                return None
            
            # Utiliser la fonction existante de graphs.py
            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
            
            if detailed_missing.empty:
                return None
            
            # Adapter les noms de colonnes pour correspondre au format attendu
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Missing columns': row['Missing columns'],
                    'Nb missing': row['Nb missing']
                })
            pd.DataFrame(detailed_data).to_excel(writer, sheet_name='All', index=False)

            # Patient
            columns_to_analyze = [
                'Age At Diagnosis', 
                'Main Diagnosis', 
                'Sex', 
                'Blood + Rh', 
                'Number HCT', 
                'Number Allo HCT',
                'Performance Status At Treatment Scale',
                'Performance Status At Treatment Score'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]

            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
                        
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Missing columns': row['Missing columns'],
                    'Nb missing': row['Nb missing']
                })
            pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Patient', index=False)

            # Indications/hemopathie
            columns_to_analyze = [
                'Main Diagnosis', 
                'Subclass Diagnosis', 
                'Age Groups', 
                'Blood Group',
                'Rhesus Factor', 
                'Disease Status At Treatment'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]

            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
                        
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Missing columns': row['Missing columns'],
                    'Nb missing': row['Nb missing']
                })
            pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Indications', index=False)

            # Procedures
            columns_to_analyze = [
                'Donor Type',
                'Source Stem Cells', 
                'Match Type',
                'Conditioning Regimen Type',
                'Donor Match Category',
                'Treatment Date', 
                'Anc Recovery',
                'Date Anc Recovery',
                'Platelet Reconstitution',
                'Date Platelet Reconstitution'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]

            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
                        
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Missing columns': row['Missing columns'],
                    'Nb missing': row['Nb missing']
                })
            pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Procedures', index=False)

            # GVH
            columns_to_analyze = [
                # Variables GvH Aiguë
                'First Agvhd Occurrence',
                'First aGvHD Maximum Score',
                'First Agvhd Occurrence Date',
                
                # Variables GvH Chronique
                'First Cgvhd Occurrence', 
                'First cGvHD Maximum NIH Score',
                'First Cgvhd Occurrence Date',
                
                # Variables de suivi
                'Status Last Follow Up',
                'Date Of Last Follow Up'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]

            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
                        
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Missing columns': row['Missing columns'],
                    'Nb missing': row['Nb missing']
                })
            pd.DataFrame(detailed_data).to_excel(writer, sheet_name='GVH', index=False)

            # Relapse
            columns_to_analyze = [
                # Variables de rechute
                'First Relapse',
                'First Relapse Date',
                
                # Variables de traitement et suivi
                'Treatment Date',
                'Status Last Follow Up',
                'Date Of Last Follow Up'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]

            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
                        
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Missing columns': row['Missing columns'],
                    'Nb missing': row['Nb missing']
                })
            pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Relapse', index=False)
            
            # Survival
            columns_to_analyze = [
                'Treatment Date',
                'Date Of Last Follow Up',
                'Status Last Follow Up',
                'First Agvhd Occurrence',
                'First Agvhd Occurrence Date',
                'First Cgvhd Occurrence',
                'First Cgvhd Occurrence Date',
                'First Relapse',
                'First Relapse Date',
                'First aGvHD Maximum Score',
                'First cGvHD Maximum NIH Score',
                'Year'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]

            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
                        
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Missing columns': row['Missing columns'],
                    'Nb missing': row['Nb missing']
                })
            pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Survival', index=False)

            # Toxicity
            columns_to_analyze = [
                'Status Last Follow Up',
                'Date Of Last Follow Up',
                'First Relapse',
                'First Relapse Date',
                'Treatment Date'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]

            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
                        
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Missing columns': row['Missing columns'],
                    'Nb missing': row['Nb missing']
                })
            pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Toxicity', index=False)

            # Indicators
            indicators = ['prise_greffe', 'sortie_aplasie', 'TRM', 'gvha', 'gvhc', 'rechute', 'survie_globale' ]
            for selected_indicator in indicators:
                columns_to_analyze, indicator_name = get_variables_for_indicator(selected_indicator)
                            
                existing_columns = [col for col in columns_to_analyze if col in df.columns]
                
                # Utiliser la fonction existante de graphs.py
                _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
                
                if detailed_missing.empty:
                    return dbc.Alert("No missing data found !", color='success'), True, None, None
                
                # Adapter les noms de colonnes pour correspondre au format attendu
                detailed_data = []
                for _, row in detailed_missing.iterrows():
                    detailed_data.append({
                        'Long ID': row['Long ID'],
                        'Missing columns': row['Missing columns'],
                        'Nb missing': row['Nb missing'],
                        'Indicator': indicator_name  # Ajouter l'indicateur pour l'export
                    })
                
                pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Indicators_' + selected_indicator, index=False)


            writer.close()
            data = output.getvalue()
            
            from datetime import datetime
            current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"donnees_manquantes_{current_date}.xlsx"

            return dcc.send_bytes(data, filename)

        except Exception as e:
            print(f"Error during Excel export Relapse: {e}")
            return dash.no_update

        
