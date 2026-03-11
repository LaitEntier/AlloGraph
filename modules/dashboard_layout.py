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
                    # Logo à gauche (utilise un bouton invisible pour la navigation)
                    html.Div([
                        html.Button(
                            html.Img(
                                src="allograph-app/assets/images/logo.svg",
                                className="app-logo",
                                style={
                                    'height': '150px',
                                    'width': 'auto',
                                    'cursor': 'pointer'
                                }
                            ),
                            id='nav-home-logo',
                            n_clicks=0,
                            style={
                                'background': 'none',
                                'border': 'none',
                                'padding': '0',
                                'margin': '0'
                            }
                        )
                    ], style={'display': 'inline-block'})
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
                        html.Button('Indications', id='nav-hemopathies', className='btn btn-secondary me-2 nav-button', disabled=True),
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
                'padding': '20px 24px 10px 24px'
            })
        ])
    ])

def create_base_layout():
    """Crée la structure de base du dashboard avec toutes les pages"""
    return dbc.Container([
        # Store pour les données - full dataset (kept minimal)
        dcc.Store(id='data-store'),
        
        # Optimized slim stores for specific analyses (reduce VM network transfer)
        # These contain subsets of columns for faster callbacks
        dcc.Store(id='data-store-survival'),  # Survival analysis columns only
        dcc.Store(id='data-store-gvh'),       # GvH analysis columns only
        dcc.Store(id='data-store-viz'),       # Visualization columns (charts/tables)
        
        # Page tracking stores
        dcc.Store(id='current-page', data='Home'),
        dcc.Store(id='last-rendered-page', data=None),  # Track to prevent double renders

        dcc.Store(id='user-session-start', data=None),  # Timestamp de début de session
        dcc.Store(id='survey-shown', data=False),       # Flag pour savoir si déjà montré
        dcc.Store(id='survey-dismissed', data=False),   # Flag si l'utilisateur a fermé
        
        dcc.Interval(
            id='survey-timer',
            interval=30*1000,  # Vérifier toutes les 30 secondes
            n_intervals=0,
            disabled=False
        ),

        # Header unifié avec logo, titre et navigation
        create_header_with_logo(),
        
        dbc.Toast(
        [
            # Corps du message avec style amélioré
            html.Div([              
                # Description
                html.P([
                    "Your feedback matters ! Take part in a quick survey to help us ",
                    "better your experience."
                ], className="mb-3", style={'fontSize': '13px', 'color': '#2c3e50', 'lineHeight': '1.4'}),
                
                # Informations pratiques avec icônes
                html.Div([
                    html.Div([
                        html.I(className="fas fa-clock me-1", style={'color': '#28a745', 'fontSize': '11px'}),
                        html.Span("2-3 minutes", style={'color': '#28a745', 'fontSize': '11px', 'fontWeight': '500'})
                    ], className="mb-1")
                ]),
                
                # Boutons d'action
                html.Div([
                    dbc.Button([
                        html.I(className="fas fa-external-link-alt me-1"),
                        "Take survey"
                    ],
                    color="primary",
                    size="sm",
                    href="https://redcap.univ-tours.fr/surveys/?s=8X9F4EEXKHTNTKHE",
                    target="_blank",
                    external_link=True,
                    className="me-2",
                    style={'fontSize': '13px'}
                    ),
                    dbc.Button([
                        html.I(className="fas fa-clock me-1"),
                        "Remind me later"
                    ],
                    id="survey-later-btn",
                    color="secondary",
                    size="sm",
                    outline=True,
                    style={'fontSize': '13px'}
                    )
                ], className="d-flex justify-content-end")
            ])
        ],
        id="survey-toast",
        header=[
            html.Div([
                html.Span([
                    html.I(className="fas fa-poll me-2"),
                    "Help us improve AlloGraph !"
                ], style={'fontSize': '14px', 'fontWeight': '600'})
            ], className="d-flex align-items-center justify-content-between w-100")
        ],
        is_open=False,
        dismissable=True,
        duration=None,  # Ne disparaît pas automatiquement
        className="survey-toast",
        style={
            "position": "fixed",
            "top": "20px",
            "right": "20px",
            "z-index": "9999"
        }
    ),

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
                html.Hr(style={'borderColor': '#021F59', 'borderWidth': '2px'}),
                html.P('© 2025 - CHRU de Tours - All rights reserved', className='text-center', style={'color': '#021F59'})
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
        dbc.CardHeader(html.H4(title, style={'fontSize': '18px', 'margin': '0', 'fontWeight': '700'})),
        dbc.CardBody(content, className='p-3')
    ], style={
        'maxHeight': '85vh',
        'overflowY': 'auto'
    }, className='sidebar-card')

def create_upload_component():
    """
    Creates the standardized upload component
    """
    return dcc.Upload(
        id='upload-data',
        children=html.Div([
            html.Div('Drag and drop', style={'fontSize': '12px', 'color': '#021F59'}),
            html.Div('or', style={'fontSize': '10px', 'margin': '2px 0', 'color': '#021F59'}),
            html.A('select', style={'fontSize': '12px', 'color': '#021F59'})
        ]),
        style={
            'width': '100%',
            'height': '70px',
            'lineHeight': '16px',
            'borderWidth': '2px',
            'borderStyle': 'dashed',
            'borderRadius': '12px',
            'borderColor': '#021F59',
            'textAlign': 'center',
            'margin': '10px 0',
            'padding': '8px',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'alignItems': 'center',
            'backgroundColor': '#ffffff',
            'cursor': 'pointer',
            'transition': 'all 0.3s ease'
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
        html.Label('X-axis:', className='mb-2', style={'color': '#021F59'}),
        dcc.Dropdown(
            id='x-axis-dropdown',
            options=[
                {'label': 'Age At Diagnosis', 'value': 'Age At Diagnosis'},
                {'label': 'Age Groups', 'value': 'Age Groups'}
            ],
            value='Age Groups',  # Valeur par défaut modifiée
            className='mb-3'
        ),

        html.Label('Stack variable:', className='mb-2', style={'color': '#021F59'}),
        dcc.Dropdown(
            id='stack-variable-dropdown',
            options=stratification_options,
            value='Main Diagnosis',  # Valeur par défaut
            className='mb-3'
        ),
        
        html.Hr(),
        html.H5('Year', className='mb-2', style={'color': '#021F59'}),
        dcc.Checklist(
            id='year-filter-checklist',
            options=years_options,
            value=[year['value'] for year in years_options],
            inline=False,
            className='mb-3'
        ),
        
        html.Hr(),
        
        # Filtres par tranche d'âge
        create_age_filter_component(component_id='patients-age-filter', title='Age groups'),
        
        html.Hr(),
        
        # Filtres par type de diagnostic
        create_malignancy_filter_component(component_id='patients-malignancy-filter', title='Diagnosis type')
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
        html.Label('X-axis:', className='mb-2', style={'color': '#021F59'}),
        dcc.Dropdown(
            id='x-axis-dropdown',
            options=[
                {'label': 'Main Diagnosis', 'value': 'Main Diagnosis'},
                {'label': 'Subclass Diagnosis', 'value': 'Subclass Diagnosis'}
            ],
            value='Main Diagnosis',
            className='mb-3'
        ),

        html.Label('Stack variable:', className='mb-2', style={'color': '#021F59'}),
        dcc.Dropdown(
            id='stack-variable-dropdown',
            options=stratification_options,
            value='None',  # Valeur par défaut
            className='mb-3'
        ),
        
        html.Hr(),
        html.H5('Year', className='mb-2', style={'color': '#021F59'}),
        dcc.Checklist(
            id='year-filter-checklist',
            options=years_options,
            value=[year['value'] for year in years_options],
            inline=False,
            className='mb-3'
        ),
        
        html.Hr(),
        
        # Filtres par tranche d'âge
        create_age_filter_component(component_id='hemopathies-age-filter', title='Age groups'),
        
        html.Hr(),
        
        # Filtres par type de diagnostic
        create_malignancy_filter_component(component_id='hemopathies-malignancy-filter', title='Diagnosis type')
    ])


def create_age_filter_component(component_id='age-filter-checklist', title='Age groups'):
    """
    Crée un composant de filtrage par tranches d'âge détaillées.
    
    Args:
        component_id (str): ID du composant dcc.Checklist
        title (str): Titre affiché pour la section
        
    Returns:
        html.Div: Composant contenant le filtre d'âge
    """
    age_options = [
        {'label': '<1 year', 'value': '<1 year'},
        {'label': '1-5 years', 'value': '1-5 years'},
        {'label': '6-10 years', 'value': '6-10 years'},
        {'label': '11-15 years', 'value': '11-15 years'},
        {'label': '16-18 years', 'value': '16-18 years'},
        {'label': '>18 years', 'value': '>18 years'}
    ]
    
    return html.Div([
        html.H5(title, className='mb-2'),
        dcc.Checklist(
            id=component_id,
            options=age_options,
            value=[opt['value'] for opt in age_options],  # Toutes les tranches sélectionnées par défaut
            inline=False,
            className='mb-3'
        )
    ])


def create_malignancy_filter_component(component_id='malignancy-filter', title='Diagnosis type'):
    """
    Crée un composant de filtrage par type de diagnostic (Malignant / Non-malignant).
    Utilise des RadioItems avec 3 options pour empêcher la désélection totale.
    
    Args:
        component_id (str): ID du composant dcc.RadioItems
        title (str): Titre affiché pour la section
        
    Returns:
        html.Div: Composant contenant le filtre de malignité
    """
    return html.Div([
        html.H5(title, className='mb-2'),
        dcc.RadioItems(
            id=component_id,
            options=[
                {'label': ' Both', 'value': 'both'},
                {'label': ' Malignant', 'value': 'Malignant'},
                {'label': ' Non-malignant', 'value': 'Non-malignant'}
            ],
            value='both',  # Par défaut : les deux
            inline=False,
            className='mb-3',
            labelStyle={'display': 'block', 'marginBottom': '5px'}
        )
    ])


def apply_malignancy_filter(df, malignancy_filter_value):
    """
    Applique le filtre de malignité sur un DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame à filtrer
        malignancy_filter_value (str): Valeur du filtre ('both', 'Malignant', ou 'Non-malignant')
        
    Returns:
        pd.DataFrame: DataFrame filtré
    """
    if malignancy_filter_value is None or malignancy_filter_value == 'both':
        return df
    
    if 'Diagnosis Category' in df.columns:
        return df[df['Diagnosis Category'] == malignancy_filter_value]
    
    return df


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
        
        # Filtres par tranche d'âge
        create_age_filter_component(component_id='procedures-age-filter', title='Age groups'),
        
        html.Hr(),
        
        # Filtres par type de diagnostic
        create_malignancy_filter_component(component_id='procedures-malignancy-filter', title='Diagnosis type'),
        
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