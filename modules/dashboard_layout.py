import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

def create_base_layout():
    """Crée la structure de base du dashboard"""
    return dbc.Container([
        # Store pour les données
        dcc.Store(id='data-store'),
        dcc.Store(id='current-page', data='Accueil'),
        
        # Header avec navigation
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Button('Accueil', id='nav-accueil', className='btn btn-primary me-2'),
                    html.Button('Patients', id='nav-patients', className='btn btn-secondary me-2', disabled=False),
                    html.Button('Page 1', id='nav-page1', className='btn btn-secondary me-2', disabled=True),
                    html.Button('Page 2', id='nav-page2', className='btn btn-secondary me-2', disabled=True),
                ], className='d-flex mb-3 p-3', style={'background-color': '#f0f2f6', 'border-radius': '5px'})
            ])
        ]),
        
        # Titre dynamique
        dbc.Row([
            dbc.Col([
                html.H1(id='page-title', className='mb-4')
            ])
        ]),
        
        # Container principal avec sidebar et contenu
        dbc.Row([
            # Sidebar
            dbc.Col(id='sidebar-content', width=3),
            
            # Contenu principal
            dbc.Col(id='main-content', width=9)
        ]),
        
        # Footer
        dbc.Row([
            dbc.Col([
                html.Hr(),
                html.P('© 2025 - CHRU de Tours - Tous droits réservés', className='text-center text-muted')
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

def create_patients_layout(main_content, boxplot_content, barplot_content):
    """
    Crée le layout spécifique pour la page Patients
    
    Args:
        main_content: Contenu principal avec les onglets
        boxplot_content: Contenu du boxplot
        barplot_content: Contenu du barplot
    """
    return dbc.Row([
        # Colonne principale (50% de l'espace)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4('Analyses principales')),
                dbc.CardBody([
                    dcc.Tabs(id='main-tabs', value='tab-normalized', children=[
                        dcc.Tab(label='Graphique normalisé', value='tab-normalized'),
                        dcc.Tab(label='Table de données', value='tab-table')
                    ]),
                    html.Div(id='tab-content', className='mt-3', style={'height': '450px', 'overflow': 'hidden'})
                ], className='p-2')
            ])
        ], width=6),
        
        # Colonne avec les deux graphiques empilés (50% de l'espace)
        dbc.Col([
            # Boxplot
            dbc.Card([
                dbc.CardHeader(html.H5('Boxplot')),
                dbc.CardBody([
                    html.Div(id='boxplot-container', style={'height': '350px', 'overflow': 'hidden'})
                ], className='p-2')
            ], className='mb-3'),
            
            # Barplot
            dbc.Card([
                dbc.CardHeader(html.H5('Barplot')),
                dbc.CardBody([
                    html.Div(id='barplot-container', style={'height': '350px', 'overflow': 'hidden'})
                ], className='p-2')
            ])
        ], width=6)
    ])

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
    Crée un layout standardisé pour la sidebar
    """
    return dbc.Card([
        dbc.CardHeader(html.H4(title)),
        dbc.CardBody(content)
    ])

def create_upload_component():
    """
    Crée le composant d'upload standardisé
    """
    return dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Glissez-déposez ou ',
            html.A('sélectionnez un fichier')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px 0'
        },
        multiple=False
    )

def create_filter_controls(categorical_columns, years_options):
    """
    Crée les contrôles de filtrage pour la sidebar
    """
    return html.Div([
        html.Label('Axe X des graphiques:', className='mb-2'),
        dcc.Dropdown(
            id='x-axis-dropdown',
            options=[
                {'label': 'Age At Diagnosis', 'value': 'Age At Diagnosis'},
                {'label': 'Age Groups', 'value': 'Age Groups'}
            ],
            value='Age At Diagnosis',
            className='mb-3'
        ),
        
        html.Label('Variable de stratification:', className='mb-2'),
        dcc.Dropdown(
            id='stack-variable-dropdown',
            options=[{'label': 'Aucune', 'value': 'Aucune'}] + 
                    [{'label': col, 'value': col} for col in categorical_columns],
            value='Aucune',
            className='mb-3'
        ),
        
        html.Hr(),
        html.H5('Filtres par année', className='mb-2'),
        dcc.Checklist(
            id='year-filter-checklist',
            options=years_options,
            value=[year['value'] for year in years_options],
            inline=False,
            className='mb-3'
        )
    ])