import dash
from dash import html, dcc, Input, Output, State
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
                        html.Button('Toxicity', id='nav-toxicity', className='btn btn-secondary me-2 nav-button', disabled=True),
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

        # Header unifié avec logo, titre et navigation
        create_header_with_logo(),

        # Modal de confirmation pour la purge (déplacée ici pour être globale)
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Confirmer la purge")),
            dbc.ModalBody([
                html.P("Are you sure you want to erase all the loaded data ?"),
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
                html.P([
                    '© 2026 - CHRU de Tours - All rights reserved',
                    html.Span(' | ', style={'margin': '0 8px'}),
                    html.Button('Legal Notices', id='footer-nav-legal', n_clicks=0, style={
                        'background': 'none', 'border': 'none', 'padding': '0', 'margin': '0',
                        'color': '#021F59', 'textDecoration': 'underline', 'cursor': 'pointer',
                        'fontSize': '13px'
                    }),
                    html.Span(' | ', style={'margin': '0 8px'}),
                    html.Button('Privacy Notice', id='footer-nav-privacy', n_clicks=0, style={
                        'background': 'none', 'border': 'none', 'padding': '0', 'margin': '0',
                        'color': '#021F59', 'textDecoration': 'underline', 'cursor': 'pointer',
                        'fontSize': '13px'
                    }),
                    html.Span(' | ', style={'margin': '0 8px'}),
                    html.Button('Cookie Policy', id='footer-nav-cookies', n_clicks=0, style={
                        'background': 'none', 'border': 'none', 'padding': '0', 'margin': '0',
                        'color': '#021F59', 'textDecoration': 'underline', 'cursor': 'pointer',
                        'fontSize': '13px'
                    })
                ], className='text-center', style={'color': '#021F59', 'marginBottom': '4px'}),
                html.Div([
                    html.Img(
                        src="allograph-app/assets/images/QRCodeIDDN.jpg",
                        id='footer-qrcode-img',
                        style={
                            'height': '60px',
                            'width': '60px',
                            'cursor': 'pointer',
                            'borderRadius': '4px',
                            'border': '1px solid #dee2e6'
                        }
                    ),
                    html.P([
                        'Deposited at the ',
                        html.Strong('Agence de la Protection des Programmes (APP)'),
                        html.Br(),
                        html.Span('IDDN.FR.001.090021.000.S.P.2026.000.31230', style={'fontSize': '10px'})
                    ], className='text-center', style={'color': '#6c757d', 'fontSize': '11px', 'marginTop': '4px', 'marginBottom': '4px'})
                ], className='text-center'),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("IDDN Registration")),
                        dbc.ModalBody([
                            html.Div([
                                html.Img(
                                    src="allograph-app/assets/images/QRCodeIDDN.jpg",
                                    style={
                                        'height': '250px',
                                        'width': '250px',
                                        'borderRadius': '8px',
                                        'border': '1px solid #dee2e6'
                                    }
                                ),
                            ], className='text-center'),
                            html.P([
                                'Deposited at the ',
                                html.Strong('Agence pour la Protection des Programmes (APP)')
                            ], className='text-center mt-3', style={'color': '#021F59'})
                        ])
                    ],
                    id='footer-qrcode-modal',
                    centered=True,
                    size='sm'
                ),
                html.P([
                    'Design by Lucie Clarysse ',
                    html.A('@Com&Sci', href='https://comsci.art', target='_blank', style={'color': '#021F59', 'textDecoration': 'underline'})
                ], className='text-center', style={'color': '#6c757d', 'fontSize': '11px', 'marginBottom': '4px'})
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

def create_pediatric_switch_component(pediatric_view=False):
    """
    Crée le switch pour basculer entre la vue normale et la vue pédiatrique.
    
    Args:
        pediatric_view (bool): État initial du switch
        
    Returns:
        html.Div: Composant contenant le switch
    """
    return html.Div([
        dbc.Switch(
            id='pediatric-view-switch',
            label='Pediatric view',
            value=pediatric_view,
            className='mb-3'
        )
    ])


def create_filter_controls(categorical_columns, years_options, pediatric_view=False):
    """
    Crée les contrôles de filtrage pour la sidebar de la page Patients.
    Limite les variables de stratification aux variables importantes uniquement.
    
    Args:
        categorical_columns (list): Liste des colonnes catégorielles disponibles (non utilisée maintenant)
        years_options (list): Options pour le filtre des années
        pediatric_view (bool): Si True, affiche le filtre d'âge pédiatrique
        
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
    
    controls = [
        create_pediatric_switch_component(pediatric_view),
        
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
        # Filtre d'âge toujours présent dans le DOM mais caché en vue normale
        create_age_filter_component(
            component_id='patients-age-filter',
            title='Age groups',
            pediatric_only=pediatric_view,
            hidden=not pediatric_view
        ),
        
        html.Hr(),
        create_malignancy_filter_component(component_id='patients-malignancy-filter', title='Diagnosis type')
    ]
    
    return html.Div(controls)


def create_info_tooltip(tooltip_text, tooltip_id):
    """Crée un icône info-circle avec un tooltip dbc au survol"""
    return [
        html.I(
            className="bi bi-info-circle",
            id=tooltip_id,
            style={
                'cursor': 'pointer',
                'fontSize': '16px',
                'marginLeft': '10px',
                'color': '#77ACF2',
                'verticalAlign': 'middle'
            }
        ),
        dbc.Tooltip(
            tooltip_text,
            target=tooltip_id,
            placement="top",
            style={'maxWidth': '400px', 'textAlign': 'left', 'fontSize': '13px', 'whiteSpace': 'pre-line'}
        )
    ]

def create_hemopathies_filter_controls(categorical_columns, years_options, pediatric_view=False):
    """
    Crée les contrôles de filtrage spécifiques pour la page Hemopathies.
    Limite les variables de stratification aux variables importantes uniquement.
    
    Args:
        categorical_columns (list): Liste des colonnes catégorielles disponibles (non utilisée maintenant)
        years_options (list): Options pour le filtre des années
        pediatric_view (bool): Si True, affiche le filtre d'âge pédiatrique
        
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
    
    controls = [
        create_pediatric_switch_component(pediatric_view),
        
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
        # Filtre d'âge toujours présent dans le DOM mais caché en vue normale
        create_age_filter_component(
            component_id='hemopathies-age-filter',
            title='Age groups',
            pediatric_only=pediatric_view,
            hidden=not pediatric_view
        ),
        
        html.Hr(),
        create_malignancy_filter_component(component_id='hemopathies-malignancy-filter', title='Diagnosis type')
    ]
    
    return html.Div(controls)


def create_age_filter_component(component_id='age-filter-checklist', title='Age groups', pediatric_only=False, hidden=False):
    """
    Crée un composant de filtrage par tranches d'âge détaillées.
    Inclut un switch pour basculer vers un slider de plage d'âge personnalisée.
    
    Args:
        component_id (str): ID du composant dcc.Checklist
        title (str): Titre affiché pour la section
        pediatric_only (bool): Si True, limite aux tranches pédiatriques uniquement (<1 à 16-18)
        hidden (bool): Si True, cache le composant dans le DOM (style display: none)
        
    Returns:
        html.Div: Composant contenant le filtre d'âge et le slider personnalisé
    """
    if pediatric_only:
        age_options = [
            {'label': '<1 year', 'value': '<1 year'},
            {'label': '1-5 years', 'value': '1-5 years'},
            {'label': '6-10 years', 'value': '6-10 years'},
            {'label': '11-15 years', 'value': '11-15 years'},
            {'label': '16-18 years', 'value': '16-18 years'}
        ]
    else:
        age_options = [
            {'label': '<1 year', 'value': '<1 year'},
            {'label': '1-5 years', 'value': '1-5 years'},
            {'label': '6-10 years', 'value': '6-10 years'},
            {'label': '11-15 years', 'value': '11-15 years'},
            {'label': '16-18 years', 'value': '16-18 years'},
            {'label': '>18 years', 'value': '>18 years'}
        ]
    
    container_style = {}
    if hidden:
        container_style['display'] = 'none'
    
    # Derive slider IDs from checklist ID (e.g., 'patients-age-filter' -> 'patients-custom-age-slider')
    base_id = component_id.replace('-age-filter', '')
    switch_id = f"{base_id}-custom-age-switch"
    slider_id = f"{base_id}-custom-age-slider"
    wrapper_id = f"{base_id}-age-filter-wrapper"
    
    return html.Div([
        html.H5(title, className='mb-2'),
        html.Div(
            id=wrapper_id,
            className='mb-3',
            children=[
                dcc.Checklist(
                    id=component_id,
                    options=age_options,
                    value=[opt['value'] for opt in age_options],  # Toutes les tranches sélectionnées par défaut
                    inline=False
                )
            ]
        ),
        html.Div(
            className='mb-2',
            style={
                'display': 'flex',
                'alignItems': 'center',
                'textAlign': 'center',
                'color': '#6c757d',
                'fontSize': '11px',
                'fontWeight': '500',
                'textTransform': 'uppercase'
            },
            children=[
                html.Div(style={'flex': '1', 'height': '1px', 'backgroundColor': '#dee2e6'}),
                html.Span('OR', style={'padding': '0 10px'}),
                html.Div(style={'flex': '1', 'height': '1px', 'backgroundColor': '#dee2e6'})
            ]
        ),
        dbc.Switch(
            id=switch_id,
            label='Use custom age range',
            value=False,
            className='mb-2'
        ),
        html.Label('Age range (years):', className='mb-1', style={'fontSize': '12px', 'color': '#6c757d'}),
        dcc.RangeSlider(
            id=slider_id,
            min=0,
            max=30,
            step=1,
            value=[0, 30],
            disabled=True,
            marks={i: str(i) for i in range(0, 31, 5)},
            className='mb-3'
        )
    ], style=container_style)


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


def apply_age_filter(df, selected_age_groups, use_custom_age=False, custom_age_range=None):
    """
    Applique le filtre d'âge sur un DataFrame.
    Si use_custom_age est True, filtre par la plage numérique Age At Diagnosis.
    Sinon, filtre par les tranches catégorielles Age Group Detailed.
    
    Args:
        df (pd.DataFrame): DataFrame à filtrer
        selected_age_groups (list): Liste des tranches d'âge sélectionnées
        use_custom_age (bool): Si True, utilise custom_age_range
        custom_age_range (list/tuple): [min_age, max_age]
        
    Returns:
        pd.DataFrame: DataFrame filtré
    """
    if use_custom_age and custom_age_range is not None and len(custom_age_range) == 2 and 'Age At Diagnosis' in df.columns:
        min_age, max_age = custom_age_range
        return df[(df['Age At Diagnosis'] >= min_age) & (df['Age At Diagnosis'] <= max_age)]
    elif selected_age_groups and 'Age Group Detailed' in df.columns:
        return df[df['Age Group Detailed'].isin(selected_age_groups)]
    return df


def register_age_toggle_callback(app, switch_id, wrapper_id, slider_id):
    """
    Enregistre un callback pour activer/désactiver le slider d'âge personnalisé
    et désactiver/activer les checkboxes de tranches d'âge.
    Utilise une classe CSS sur le wrapper car dcc.Checklist ne supporte pas disabled.
    
    Args:
        app: L'application Dash
        switch_id (str): ID du dbc.Switch qui contrôle le mode
        wrapper_id (str): ID du html.Div wrapper autour du dcc.Checklist
        slider_id (str): ID du dcc.RangeSlider de plage d'âge
    """
    @app.callback(
        [Output(wrapper_id, 'className'),
         Output(slider_id, 'disabled')],
        Input(switch_id, 'value'),
        prevent_initial_call=True
    )
    def toggle_age_filter_mode(use_custom_age):
        """Active le slider et désactive les checkboxes quand le switch est ON"""
        wrapper_class = 'mb-3 age-filter-disabled' if use_custom_age else 'mb-3'
        return wrapper_class, not bool(use_custom_age)


def create_procedures_sidebar_content(data, pediatric_view=False):
    """
    Crée le contenu de la sidebar spécifique à la page Procedures.
    Simplifié car le sélecteur de variable principale est maintenant intégré dans l'interface.
    
    Args:
        data (list): Liste de dictionnaires (format store Dash) avec les données
        pediatric_view (bool): Si True, affiche le filtre d'âge pédiatrique
        
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
    
    controls = [
        create_pediatric_switch_component(pediatric_view),
        
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
        # Filtre d'âge toujours présent dans le DOM mais caché en vue normale
        create_age_filter_component(
            component_id='procedures-age-filter',
            title='Age groups',
            pediatric_only=pediatric_view,
            hidden=not pediatric_view
        ),
        
        html.Hr(),
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
    ]
    
    return html.Div(controls)

def register_callbacks(app):
    """Callbacks pour le layout global (footer, modales, etc.)"""
    
    @app.callback(
        Output('footer-qrcode-modal', 'is_open'),
        Input('footer-qrcode-img', 'n_clicks'),
        State('footer-qrcode-modal', 'is_open'),
        prevent_initial_call=True
    )
    def toggle_qrcode_modal(n_clicks, is_open):
        """Ouvre/ferme la modale du QR code au clic"""
        if n_clicks:
            return not is_open
        return is_open
