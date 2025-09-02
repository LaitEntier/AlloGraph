import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd

def create_header_with_logo():
    """Crée le header unifié avec logo, titre et navigation"""
    return dbc.Row([
        dbc.Col([
            html.Div([
                # Section supérieure : Logo et titre
                html.Div([
                    # Logo à gauche
                    html.Img(
                        src="allograph-app/assets/images/logo.svg",
                        className="app-logo",
                        style={
                            'height': '50px',
                            'width': 'auto',
                            'marginRight': '15px'
                        }
                    ),
                    # Titre avec styling spécial
                    html.H1([
                        html.Span("Allo", style={'color': '#2c3e50'}),
                        html.Span("Graph", style={'color': '#c0392b'})
                    ], className="main-title", style={
                        'margin': '0',
                        'fontSize': '32px',
                        'fontWeight': 'bold',
                        'fontFamily': 'Arial, sans-serif'
                    })
                ], style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'flex-start',
                    'marginBottom': '15px'
                }),
                
                # Section navigation intégrée avec bouton Purge data à droite
                html.Div([
                    # Boutons de navigation à gauche
                    html.Div([
                        html.Button('Home', id='nav-home', className='btn btn-primary me-2 nav-button'),
                        html.Button('Patients', id='nav-patients', className='btn btn-secondary me-2 nav-button', disabled=True),
                        html.Button('Hemopathies', id='nav-hemopathies', className='btn btn-secondary me-2 nav-button', disabled=True),
                        html.Button('Procedures', id='nav-procedures', className='btn btn-secondary me-2 nav-button', disabled=True),
                        html.Button('GVH', id='nav-gvh', className='btn btn-secondary me-2 nav-button', disabled=True),
                        html.Button('Relapse', id='nav-relapse', className='btn btn-secondary me-2 nav-button', disabled=True),
                        html.Button('Survival', id='nav-survival', className='btn btn-secondary me-2 nav-button', disabled=True),
                        html.Button('Indicators', id='nav-indics', className='btn btn-secondary me-2 nav-button', disabled=True),
                    ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap', 'gap': '8px'}),
                    
                    # Bouton Purge data à droite
                    html.Div([
                        dbc.Button(
                            [
                                html.I(className="bi bi-trash me-2"),
                                "Void data"
                            ],
                            id="purge-data-button",
                            color="danger",
                            size="sm",
                            outline=True,
                            style={'display': 'none'}  # Caché par défaut, visible seulement quand des données sont chargées
                        )
                    ], style={'marginLeft': 'auto'})  # Push vers la droite
                    
                ], style={
                    'display': 'flex', 
                    'alignItems': 'center', 
                    'justifyContent': 'space-between',  # Espace les éléments
                    'width': '100%'
                })
                
            ], className="header-container", style={
                'padding': '20px',
                'backgroundColor': '#ffffff00',
                'marginBottom': '20px',
                'borderRadius': '0 0 0 0',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
            })
        ])
    ])

def create_base_layout():
    """Crée la structure de base du dashboard avec toutes les pages"""
    return dbc.Container([
        # Store pour les données
        dcc.Store(id='data-store'),
        dcc.Store(id='current-page', data='Home'),
        
        # Header unifié avec logo, titre et navigation
        create_header_with_logo(),
        
        # Modal de confirmation pour la purge (déplacée ici pour être globale)
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Confirmer la purge")),
            dbc.ModalBody([
                html.P("Are you sure you want to delete all the uploaded data?"),
                html.P("This action is irreversible.", className="text-muted small")
            ]),
            dbc.ModalFooter([
                dbc.Button(
                    "Cancel", 
                    id="cancel-purge", 
                    className="ms-auto", 
                    n_clicks=0,
                    color="secondary"
                ),
                dbc.Button(
                    "Confirm", 
                    id="confirm-purge", 
                    className="ms-2", 
                    n_clicks=0,
                    color="danger"
                ),
            ]),
        ],
        id="purge-confirmation-modal",
        is_open=False,
        ),
        
        # Container principal avec sidebar et contenu
        dbc.Row([
            # Sidebar (réduite) avec position sticky
            dbc.Col(
                id='sidebar-content', 
                width=2,
                style={
                    'position': 'sticky',
                    'top': '20px',
                    'height': 'fit-content',
                    'z-index': '1000'
                }
            ),
            
            # Contenu principal (élargi)
            dbc.Col(id='main-content', width=10)
        ]),
        
        # Footer
        dbc.Row([
            dbc.Col([
                html.Hr(),
                html.P('© 2025 - CHRU de Tours - All rights reserved', className='text-center text-muted')
            ])
        ])
    ], fluid=True, className='p-4')

def create_split_layout(left_component, right_components):
    """
    Crée un layout avec un grand composant à gauche et plusieurs composants empilés à droite
    
    Args:
        left_component: Composant principal (prend 50% de l'espace)
        right_components: Liste de composants à empiler verticalement à droite
    """
    right_rows = [dbc.Row([comp], className='mb-3') for comp in right_components]
    
    return dbc.Row([
        dbc.Col(left_component, width=6, className='h-100'),
        dbc.Col(right_rows, width=6)
    ], className='h-100')

def create_quad_layout(top_left, top_right, bottom_left, bottom_right):
    """
    Crée un layout avec 4 graphiques de taille égale
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody(top_left)
                ])
            ], width=6, className='mb-3'),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody(top_right)
                ])
            ], width=6, className='mb-3')
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody(bottom_left)
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody(bottom_right)
                ])
            ], width=6)
        ])
    ], fluid=True)

def create_sidebar_layout(title, content):
    """
    Crée un layout standardisé pour la sidebar avec style sticky amélioré
    """
    return dbc.Card([
        dbc.CardHeader(html.H4(title, style={'fontSize': '16px', 'margin': '0'})),
        dbc.CardBody(content, className='p-3')
    ], style={
        'maxHeight': '85vh',  # Hauteur maximale pour éviter que la sidebar soit trop haute
        'overflowY': 'auto',  # Scroll interne si le contenu est trop long
        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'  # Ombre légère pour un effet visuel
    })

def create_upload_component():
    """
    Crée le composant d'upload standardisé
    """
    return dcc.Upload(
        id='upload-data',
        children=html.Div([
            html.Div('Glissez-déposez', style={'fontSize': '12px'}),
            html.Div('ou', style={'fontSize': '10px', 'margin': '2px 0'}),
            html.A('sélectionnez', style={'fontSize': '12px'})
        ]),
        style={
            'width': '100%',
            'height': '70px',
            'lineHeight': '16px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px 0',
            'padding': '8px',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'alignItems': 'center'
        },
        multiple=False
    )

def create_filter_controls(categorical_columns, years_options):
    """
    Crée les contrôles de filtrage pour la sidebar de la page Patients.
    Limite les variables de stratification aux variables importantes uniquement.
    
    Args:
        categorical_columns (list): Liste des colonnes catégorielles disponibles (non utilisée maintenant)
        years_options (list): Options pour le filtre des années
        
    Returns:
        html.Div: Composant contenant les contrôles de filtrage
    """
    # Variables de stratification spécifiquement sélectionnées pour la page Patients
    stratification_variables = [
        'Sex',
        'Blood + Rh', 
        'Main Diagnosis',
        'Number HCT',
        'Number Allo HCT'
    ]
    
    # Créer les options pour le dropdown de stratification
    stratification_options = [{'label': 'None', 'value': 'None'}]
    stratification_options.extend([{'label': var, 'value': var} for var in stratification_variables])
    
    return html.Div([
        html.Label('X-axis:', className='mb-2'),
        dcc.Dropdown(
            id='x-axis-dropdown',
            options=[
                {'label': 'Age At Diagnosis', 'value': 'Age At Diagnosis'},
                {'label': 'Age Groups', 'value': 'Age Groups'}
            ],
            value='Age Groups',  # Valeur par défaut modifiée
            className='mb-3'
        ),

        html.Label('Stack variable:', className='mb-2'),
        dcc.Dropdown(
            id='stack-variable-dropdown',
            options=stratification_options,
            value='Main Diagnosis',  # Valeur par défaut
            className='mb-3'
        ),
        
        html.Hr(),
        html.H5('Year', className='mb-2'),
        dcc.Checklist(
            id='year-filter-checklist',
            options=years_options,
            value=[year['value'] for year in years_options],
            inline=False,
            className='mb-3'
        )
    ])

def create_hemopathies_filter_controls(categorical_columns, years_options):
    """
    Crée les contrôles de filtrage spécifiques pour la page Hemopathies.
    Limite les variables de stratification aux variables importantes uniquement.
    
    Args:
        categorical_columns (list): Liste des colonnes catégorielles disponibles (non utilisée maintenant)
        years_options (list): Options pour le filtre des années
        
    Returns:
        html.Div: Composant contenant les contrôles de filtrage
    """
    # Variables de stratification spécifiquement sélectionnées pour la page Hemopathies
    stratification_variables = [
        'Age Groups',
        'Blood + Rh',
        'Disease Status At Treatment'
    ]
    
    # Créer les options pour le dropdown de stratification
    stratification_options = [{'label': 'None', 'value': 'None'}]
    stratification_options.extend([{'label': var, 'value': var} for var in stratification_variables])
    
    return html.Div([
        html.Label('X-axis:', className='mb-2'),
        dcc.Dropdown(
            id='x-axis-dropdown',
            options=[
                {'label': 'Main Diagnosis', 'value': 'Main Diagnosis'},
                {'label': 'Subclass Diagnosis', 'value': 'Subclass Diagnosis'}
            ],
            value='Main Diagnosis',
            className='mb-3'
        ),

        html.Label('Stack variable:', className='mb-2'),
        dcc.Dropdown(
            id='stack-variable-dropdown',
            options=stratification_options,
            value='None',  # Valeur par défaut
            className='mb-3'
        ),
        
        html.Hr(),
        html.H5('Year', className='mb-2'),
        dcc.Checklist(
            id='year-filter-checklist',
            options=years_options,
            value=[year['value'] for year in years_options],
            inline=False,
            className='mb-3'
        )
    ])


def create_procedures_sidebar_content(data):
    """
    Crée le contenu de la sidebar spécifique à la page Procedures.
    Simplifié car le sélecteur de variable principale est maintenant intégré dans l'interface.
    
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
        # Filtres par année
        html.H5('Filtres par année', className='mb-2'),
        dcc.Checklist(
            id='procedures-year-filter',
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