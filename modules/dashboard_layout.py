import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

def create_base_layout():
    """Crée la structure de base du dashboard"""
    return html.Div([
        dcc.Store(id='data-store'),  # Pour stocker les données après chargement
        html.Div(id='header', className='header', children=[
            html.H1("Dashboard REDCap"),
            html.Div([
                dcc.Upload(
                    id='upload-data',
                    children=html.Div(['Glisser-déposer ou ', html.A('sélectionner un fichier')]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                ),
                html.Div(id='output-data-upload'),
            ]),
        ]),
        html.Div(id='tabs-container', children=[
            dcc.Tabs(id='main-tabs', value='tab-overview', children=[
                dcc.Tab(label='Vue d\'ensemble', value='tab-overview'),
                dcc.Tab(label='Allogreffes', value='tab-allogreffe', id='tab-allogreffe'),
                dcc.Tab(label='CAR Injections', value='tab-car', id='tab-car'),
            ]),
        ]),
        html.Div(id='page-content')  # Contenu qui changera selon l'onglet sélectionné
    ])

def create_split_layout(left_component, top_right_component, bottom_right_component):
    """
    Crée un layout avec un grand graphique à gauche et deux plus petits à droite
    """
    return html.Div([
        dbc.Row([
            dbc.Col(left_component, width=6, className='graph-container'),
            dbc.Col([
                dbc.Row(top_right_component, className='graph-container'),
                dbc.Row(bottom_right_component, className='graph-container')
            ], width=6)
        ])
    ])

def create_quad_layout(top_left, top_right, bottom_left, bottom_right):
    """
    Crée un layout avec 4 graphiques de taille égale
    """
    return html.Div([
        dbc.Row([
            dbc.Col(top_left, width=6, className='graph-container'),
            dbc.Col(top_right, width=6, className='graph-container')
        ]),
        dbc.Row([
            dbc.Col(bottom_left, width=6, className='graph-container'),
            dbc.Col(bottom_right, width=6, className='graph-container')
        ])
    ])

def create_tabset(tabs_content):
    """
    Crée un ensemble d'onglets au sein d'une même page
    tabs_content: liste de tuples (label, contenu)
    """
    tabs = []
    contents = []
    
    for i, (label, content) in enumerate(tabs_content):
        tab_id = f'nested-tab-{i}'
        tabs.append(dcc.Tab(label=label, value=tab_id))
        contents.append(html.Div(content, id=f'{tab_id}-content', style={'display': 'none'}))
    
    return html.Div([
        dcc.Tabs(
            id='nested-tabs',
            value=f'nested-tab-0',  # Onglet par défaut
            children=tabs
        ),
        html.Div(contents, id='nested-tabs-content')
    ])