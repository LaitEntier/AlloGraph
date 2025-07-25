import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io
import os
import sys
import plotly
# Import des modules
import modules.data_processing as data_processing
import modules.dashboard_layout as layouts

# Import des pages
try:
    import pages.home as home_page
    HOME_PAGE_AVAILABLE = True
except ImportError as e:
    print(f"Attention: Impossible d'importer pages.home: {e}")
    HOME_PAGE_AVAILABLE = False

try:
    import pages.patients as patients_page
    PATIENTS_PAGE_AVAILABLE = True
except ImportError as e:
    print(f"Attention: Impossible d'importer pages.patients: {e}")
    PATIENTS_PAGE_AVAILABLE = False
    
try:
    import pages.hemopathies as hemopathies_page
    HEMOPATHIES_PAGE_AVAILABLE = True
except ImportError as e:
    print(f"Attention: Impossible d'importer pages.hemopathies: {e}")
    HEMOPATHIES_PAGE_AVAILABLE = False

try:
    import pages.procedures as procedures_page
    PROCEDURES_PAGE_AVAILABLE = True
except ImportError as e:
    print(f"Attention: Impossible d'importer pages.procedures: {e}")
    PROCEDURES_PAGE_AVAILABLE = False
    
try:
    import pages.gvh as gvh_page
    GVH_PAGE_AVAILABLE = True
except ImportError as e:
    print(f"Attention: Impossible d'importer pages.gvh: {e}")
    GVH_PAGE_AVAILABLE = False

try:
    import pages.relapse as relapse_page
    RELAPSE_PAGE_AVAILABLE = True
except ImportError as e:
    print(f"Attention: Impossible d'importer pages.relapse: {e}")
    RELAPSE_PAGE_AVAILABLE = False

try:
    import pages.survival as survival_page
    SURVIVAL_PAGE_AVAILABLE = True
except ImportError as e:
    print(f"Attention: Impossible d'importer pages.survival: {e}")
    SURVIVAL_PAGE_AVAILABLE = False

try:
    import pages.indics as indic_page
    INDIC_PAGE_AVAILABLE = True
except ImportError as e:
    print(f"Attention: Impossible d'importer pages.indic: {e}")
    INDIC_PAGE_AVAILABLE = False

def get_asset_path(filename):
    """
    Retourne le chemin correct vers les assets, 
    que l'app soit compilée ou non
    """
    if hasattr(sys, '_MEIPASS'):
        # Mode exécutable PyInstaller
        return os.path.join(sys._MEIPASS, 'assets', filename)
    else:
        # Mode développement
        return os.path.join('assets', filename)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Initialisation de l'app Dash
app = dash.Dash(
    __name__, 
    assets_folder=resource_path('assets'),
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.BOOTSTRAP
    ],
    suppress_callback_exceptions=True,
)
app.title = "AlloGraph"

# Layout de base avec navigation mise à jour
app.layout = html.Div([
    layouts.create_base_layout(),
    dcc.Store(id='metadata-store')
])

# Enregistrement des callbacks des pages
if HOME_PAGE_AVAILABLE:
    home_page.register_callbacks(app)

if PATIENTS_PAGE_AVAILABLE:
    patients_page.register_callbacks(app)

if HEMOPATHIES_PAGE_AVAILABLE:
    hemopathies_page.register_callbacks(app)

if PROCEDURES_PAGE_AVAILABLE:
    procedures_page.register_callbacks(app)

if GVH_PAGE_AVAILABLE:
    gvh_page.register_callbacks(app)

if RELAPSE_PAGE_AVAILABLE:
    relapse_page.register_callbacks(app)

if SURVIVAL_PAGE_AVAILABLE:
    survival_page.register_callbacks(app)

if INDIC_PAGE_AVAILABLE:
    indic_page.register_callbacks(app)

# ========== CALLBACKS GLOBAUX UNIQUEMENT ==========

@app.callback(
    [Output('current-page', 'data'),
     Output('nav-accueil', 'className'),
     Output('nav-patients', 'className'),
     Output('nav-page1', 'className'),
     Output('nav-procedures', 'className'),
     Output('nav-gvh', 'className'),
     Output('nav-rechute', 'className'),
     Output('nav-survival', 'className'),        
     Output('nav-indics', 'className'),
     Output('nav-patients', 'disabled'),
     Output('nav-page1', 'disabled'),
     Output('nav-procedures', 'disabled'),
     Output('nav-gvh', 'disabled'),
     Output('nav-rechute', 'disabled'),
     Output('nav-survival', 'disabled'),         
     Output('nav-indics', 'disabled')],
    [Input('nav-accueil', 'n_clicks'),
     Input('nav-patients', 'n_clicks'),
     Input('nav-page1', 'n_clicks'),
     Input('nav-procedures', 'n_clicks'),
     Input('nav-gvh', 'n_clicks'),
     Input('nav-rechute', 'n_clicks'),
     Input('nav-survival', 'n_clicks'),          
     Input('nav-indics', 'n_clicks'),
     Input('data-store', 'data')],
    [State('current-page', 'data')]
)
def navigate(acc_clicks, pat_clicks, p1_clicks, proc_clicks, gvh_clicks, rechute_clicks, surv_clicks, indics_clicks, data, current_page):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        disabled = data is None
        if current_page is None:
            current_page = 'Accueil'
        
        styles = {
            'Accueil': 'btn btn-primary me-2 nav-button' if current_page == 'Accueil' else 'btn btn-secondary me-2 nav-button',
            'Patients': 'btn btn-primary me-2 nav-button' if current_page == 'Patients' else 'btn btn-secondary me-2 nav-button',
            'Hemopathies': 'btn btn-primary me-2 nav-button' if current_page == 'Hemopathies' else 'btn btn-secondary me-2 nav-button',
            'Procedures': 'btn btn-primary me-2 nav-button' if current_page == 'Procedures' else 'btn btn-secondary me-2 nav-button',
            'GvH': 'btn btn-primary me-2 nav-button' if current_page == 'GvH' else 'btn btn-secondary me-2 nav-button',
            'Rechute': 'btn btn-primary me-2 nav-button' if current_page == 'Rechute' else 'btn btn-secondary me-2 nav-button',
            'Survie': 'btn btn-primary me-2 nav-button' if current_page == 'Survie' else 'btn btn-secondary me-2 nav-button',
            'Indicateurs': 'btn btn-primary me-2 nav-button' if current_page == 'Indicateurs' else 'btn btn-secondary me-2 nav-button'
        }

        return (current_page, styles['Accueil'], styles['Patients'],
                styles['Hemopathies'], styles['Procedures'], styles['GvH'], styles['Rechute'], styles['Survie'], styles['Indicateurs'],
                disabled, disabled, disabled, disabled, disabled, disabled, disabled)
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'data-store':
        disabled = data is None
        current_page = current_page or 'Accueil'
        
        styles = {
            'Accueil': 'btn btn-primary me-2 nav-button' if current_page == 'Accueil' else 'btn btn-secondary me-2 nav-button',
            'Patients': 'btn btn-primary me-2 nav-button' if current_page == 'Patients' else 'btn btn-secondary me-2 nav-button',
            'Hemopathies': 'btn btn-primary me-2 nav-button' if current_page == 'Hemopathies' else 'btn btn-secondary me-2 nav-button',
            'Procedures': 'btn btn-primary me-2 nav-button' if current_page == 'Procedures' else 'btn btn-secondary me-2 nav-button',
            'GvH': 'btn btn-primary me-2 nav-button' if current_page == 'GvH' else 'btn btn-secondary me-2 nav-button',
            'Rechute': 'btn btn-primary me-2 nav-button' if current_page == 'Rechute' else 'btn btn-secondary me-2 nav-button',
            'Survie': 'btn btn-primary me-2 nav-button' if current_page == 'Survie' else 'btn btn-secondary me-2 nav-button',
            'Indicateurs': 'btn btn-primary me-2 nav-button' if current_page == 'Indicateurs' else 'btn btn-secondary me-2 nav-button'
        }

        return (current_page, styles['Accueil'], styles['Patients'],
                styles['Hemopathies'], styles['Procedures'], styles['GvH'], styles['Rechute'], styles['Survie'], styles['Indicateurs'],
                disabled, disabled, disabled, disabled, disabled, disabled, disabled)
    
    # Navigation normale
    page_map = {
        'nav-accueil': 'Accueil',
        'nav-patients': 'Patients',
        'nav-page1': 'Hemopathies',
        'nav-procedures': 'Procedures',
        'nav-gvh': 'GvH',
        'nav-rechute': 'Rechute',
        'nav-survival': 'Survie',               
        'nav-indics': 'Indicateurs'
    }
    new_page = page_map.get(button_id, current_page or 'Accueil')
    
    btn_styles = {
        'Accueil': 'nav-accueil',
        'Patients': 'nav-patients',
        'Hemopathies': 'nav-page1',
        'Procedures': 'nav-procedures',
        'GvH': 'nav-gvh',
        'Rechute': 'nav-rechute',
        'Survie': 'nav-survival',               
        'Indicateurs': 'nav-indics'
    }
    
    styles = {}
    for page, btn_id in btn_styles.items():
        styles[btn_id] = 'btn btn-primary me-2 nav-button' if new_page == page else 'btn btn-secondary me-2 nav-button'

    disabled = data is None

    return (new_page, styles['nav-accueil'], styles['nav-patients'],
            styles['nav-page1'], styles['nav-procedures'], styles['nav-gvh'], styles['nav-rechute'], styles['nav-survival'], styles['nav-indics'],
            disabled, disabled, disabled, disabled, disabled, disabled, disabled)

@app.callback(
    Output('sidebar-content', 'children'),
    [Input('current-page', 'data'),
     Input('data-store', 'data'),
     Input('metadata-store', 'data')]
)
def update_sidebar(current_page, data, metadata):
    """Gère la sidebar selon la page active"""
    if current_page == 'Accueil':
        # Sidebar pour l'upload sur la page d'accueil
        if data is None:
            # Pas de données : afficher l'upload
            content = html.Div([
                layouts.create_upload_component(),
                html.Div(id='upload-status')
            ])
            return layouts.create_sidebar_layout('Chargement', content)
        else:
            # Données chargées : afficher les informations
            df = pd.DataFrame(data)
            
            # Utiliser les métadonnées si disponibles
            if metadata:
                original_shape = metadata.get('original_shape', (0, 0))
                filename = metadata.get('filename', 'Fichier inconnu')
                content = html.Div([
                    # Informations sur le dataset
                    dbc.Alert([
                        html.H6("✅ Données chargées", className="mb-2"),
                        html.P([
                            "📁 ", html.Strong(filename)
                        ], className="mb-2", style={'fontSize': '11px'}),
                        html.P([
                            "📊 Dimensions: ", html.Strong(f"{original_shape[0]:,} × {original_shape[1]}")
                        ], className="mb-1", style={'fontSize': '12px'}),
                        html.Hr(className="my-2"),
                        html.P("Naviguez vers les autres pages pour analyser vos données", 
                               className="mb-0", style={'fontSize': '10px'})
                    ], color="success", className="mb-3"),
                    
                    # Bouton de purge des données
                    html.Div([
                        html.H6("Gestion des données :", className="mb-2"),
                        dbc.Button(
                            [
                                html.I(className="fas fa-trash-alt me-2"),
                                "Purger les données"
                            ],
                            id="purge-data-button",
                            color="danger",
                            size="sm",
                            className="mb-3 w-100",
                            outline=True
                        ),
                        # Composant de confirmation
                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle("Confirmer la purge")),
                            dbc.ModalBody([
                                html.P("Êtes-vous sûr de vouloir supprimer toutes les données chargées ?"),
                                html.P("Cette action est irréversible.", className="text-muted small")
                            ]),
                            dbc.ModalFooter([
                                dbc.Button(
                                    "Annuler", 
                                    id="cancel-purge", 
                                    className="ms-auto", 
                                    n_clicks=0,
                                    color="secondary"
                                ),
                                dbc.Button(
                                    "Confirmer", 
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
                    ], className="mb-3"),
                    
                    # Option pour recharger des données
                    html.Div([
                        html.H6("Nouveau fichier :", className="mb-2"),
                        layouts.create_upload_component(),
                        html.Div(id='upload-status')
                    ])
                ])
            else:
                # Fallback si pas de métadonnées
                content = html.Div([
                    dbc.Alert([
                        html.H6("✅ Données chargées", className="mb-2"),
                        html.P([
                            html.Strong(f"{df.shape[0]:,}"), " lignes"
                        ], className="mb-1", style={'fontSize': '14px'}),
                        html.P([
                            html.Strong(f"{df.shape[1]}"), " colonnes"
                        ], className="mb-1", style={'fontSize': '14px'}),
                        html.Hr(className="my-2"),
                        html.P("Naviguez vers les autres pages pour analyser vos données", 
                               className="mb-0", style={'fontSize': '11px'})
                    ], color="success", className="mb-3"),
                    
                    # Bouton de purge des données
                    html.Div([
                        html.H6("Gestion des données :", className="mb-2"),
                        dbc.Button(
                            [
                                html.I(className="fas fa-trash-alt me-2"),
                                "Purger les données"
                            ],
                            id="purge-data-button",
                            color="danger",
                            size="sm",
                            className="mb-3 w-100",
                            outline=True
                        ),
                        # Composant de confirmation
                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle("Confirmer la purge")),
                            dbc.ModalBody([
                                html.P("Êtes-vous sûr de vouloir supprimer toutes les données chargées ?"),
                                html.P("Cette action est irréversible.", className="text-muted small")
                            ]),
                            dbc.ModalFooter([
                                dbc.Button(
                                    "Annuler", 
                                    id="cancel-purge", 
                                    className="ms-auto", 
                                    n_clicks=0,
                                    color="secondary"
                                ),
                                dbc.Button(
                                    "Confirmer", 
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
                    ], className="mb-3"),
                    
                    html.Div([
                        html.H6("Nouveau fichier :", className="mb-2"),
                        layouts.create_upload_component(),
                        html.Div(id='upload-status')
                    ])
                ])
            
            return layouts.create_sidebar_layout('Données', content)

    
    elif current_page == 'Patients' and data is not None:
        # Sidebar avec filtres pour la page Patients
        df = pd.DataFrame(data)
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        if 'Year' in categorical_columns:
            categorical_columns.remove('Year')
        
        years_options = []
        if 'Year' in df.columns:
            available_years = sorted(df['Year'].unique().tolist())
            years_options = [{'label': f'{year}', 'value': year} for year in available_years]
        
        content = layouts.create_filter_controls(categorical_columns, years_options)
        return layouts.create_sidebar_layout('Paramètres', content)
    
    elif current_page == 'Hemopathies' and data is not None:
        # Sidebar avec filtres pour la page Hemopathies
        df = pd.DataFrame(data)
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        # Retirer les colonnes spéciales
        for col in ['Year', 'Main Diagnosis', 'Subclass Diagnosis']:
            if col in categorical_columns:
                categorical_columns.remove(col)
        
        years_options = []
        if 'Year' in df.columns:
            available_years = sorted(df['Year'].unique().tolist())
            years_options = [{'label': f'{year}', 'value': year} for year in available_years]
        
        content = layouts.create_hemopathies_filter_controls(categorical_columns, years_options)
        return layouts.create_sidebar_layout('Paramètres', content)
    
    elif current_page == 'Procedures' and data is not None:
        content = layouts.create_procedures_sidebar_content(data)
        return layouts.create_sidebar_layout('Paramètres', content)

    elif current_page == 'GvH' and data is not None:  
        # Sidebar spécifique pour la page GvH
        content = gvh_page.create_gvh_sidebar_content(data)
        return layouts.create_sidebar_layout('Paramètres GvH', content)
    
    elif current_page == 'Rechute' and data is not None:
        # Sidebar spécifique pour la page Rechute
        content = relapse_page.create_relapse_sidebar_content(data)
        return layouts.create_sidebar_layout('Paramètres Rechute', content)

    elif current_page == 'Survie' and data is not None:  
        # Sidebar spécifique pour la page Survie
        content = survival_page.create_survival_sidebar_content(data)
        return layouts.create_sidebar_layout('Paramètres Survie', content)
    
    elif current_page == 'Indicateurs' and data is not None:
        # Sidebar spécifique pour la page Indicateurs
        content = indic_page.create_indicators_sidebar_content(data)
        return layouts.create_sidebar_layout('Indicateurs', content)

    else:
        # Sidebar par défaut
        if data is None:
            content = html.Div([
                html.P('Retournez à la page Accueil pour charger des données.', 
                       className='text-info', style={'fontSize': '12px'})
            ])
        else:
            df = pd.DataFrame(data)
            content = html.Div([
                dbc.Alert([
                    html.P([
                        "✅ ", html.Strong(f"{df.shape[0]:,}"), " lignes"
                    ], className="mb-1", style={'fontSize': '13px'}),
                    html.P([
                        "📊 ", html.Strong(f"{df.shape[1]}"), " colonnes"
                    ], className="mb-0", style={'fontSize': '13px'})
                ], color="info", className="py-2")
            ])
        return layouts.create_sidebar_layout('Navigation', content)

@app.callback(
    [Output('data-store', 'data'),
     Output('metadata-store', 'data'),
     Output('upload-status', 'children')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def process_uploaded_file(contents, filename):
    """Traite l'upload de fichier - callback global"""
    if contents is None:
        return dash.no_update, dash.no_update, dash.no_update
    
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        if filename.endswith('.csv'):
            df_original = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith(('.xlsx', '.xls')):
            df_original = pd.read_excel(io.BytesIO(decoded))
        else:
            return dash.no_update, dash.no_update, dbc.Alert('Format de fichier non supporté', color='danger')
        
        # Stocker les dimensions originales
        original_shape = df_original.shape
        
        # Traitement des données
        df_processed = data_processing.process_data(df_original)
        processed_shape = df_processed.shape
        
        # Créer les métadonnées
        metadata = {
            'original_shape': original_shape,
            'processed_shape': processed_shape,
            'filename': filename
        }
        
        # Message de succès avec les deux dimensions
        success_message = dbc.Alert([
            html.H6("✅ Fichier chargé avec succès!", className="mb-2"),
            html.P([
                "📁 ", html.Strong(filename)
            ], className="mb-2", style={'fontSize': '12px'}),
            html.P([
                "📊 Données originales: ", 
                html.Strong(f"{original_shape[0]:,} lignes × {original_shape[1]} colonnes")
            ], className="mb-1", style={'fontSize': '11px'}),
            html.P([
                "⚙️ Après traitement: ", 
                html.Strong(f"{processed_shape[0]:,} lignes × {processed_shape[1]} colonnes")
            ], className="mb-0", style={'fontSize': '11px'})
        ], color='success')
        
        return df_processed.to_dict('records'), metadata, success_message
    
    except Exception as e:
        return dash.no_update, dash.no_update, dbc.Alert(f'Erreur lors du chargement: {str(e)}', color='danger')

@app.callback(
    Output('main-content', 'children'),
    [Input('current-page', 'data'),
     Input('data-store', 'data')]
)
def update_main_content(current_page, data):
    """Callback de routage principal - délègue aux pages"""
    
    if current_page == 'Accueil':
        if HOME_PAGE_AVAILABLE:
            return home_page.get_layout()
        else:
            return create_fallback_home()
    
    elif current_page == 'Patients':
        if data is not None:
            if PATIENTS_PAGE_AVAILABLE:
                return patients_page.get_layout()
            else:
                return dbc.Alert('Page Patients non disponible', color='warning')
        else:
            return dbc.Alert('Veuillez charger un fichier de données pour accéder à cette page.', color='info')
    
    elif current_page == 'Hemopathies':
        if data is not None:
            if HEMOPATHIES_PAGE_AVAILABLE:
                return hemopathies_page.get_layout()
            else:
                return dbc.Alert('Page Hemopathies non disponible', color='warning')
        else:
            return dbc.Alert('Veuillez charger un fichier de données pour accéder à cette page.', color='info')
    
    elif current_page == 'Procedures':
        if data is not None:
            if PROCEDURES_PAGE_AVAILABLE:
                return procedures_page.get_layout()
            else:
                return dbc.Alert('Page Procedures non disponible', color='warning')
        else:
            return dbc.Alert('Veuillez charger un fichier de données pour accéder à cette page.', color='info')
    
    elif current_page == 'GvH':  
        if data is not None:
            if GVH_PAGE_AVAILABLE:
                return gvh_page.get_layout()
            else:
                return dbc.Alert('Page GvH non disponible', color='warning')
        else:
            return dbc.Alert('Veuillez charger un fichier de données pour accéder à cette page.', color='info')
    
    elif current_page == 'Rechute':
        if data is not None:
            if RELAPSE_PAGE_AVAILABLE:
                return relapse_page.get_layout()
            else:
                return dbc.Alert('Page Rechute non disponible', color='warning')
        else:
            return dbc.Alert('Veuillez charger un fichier de données pour accéder à cette page.', color='info')

    elif current_page == 'Survie':  
        if data is not None:
            if SURVIVAL_PAGE_AVAILABLE:
                return survival_page.get_layout()
            else:
                return dbc.Alert('Page Survie non disponible', color='warning')
        else:
            return dbc.Alert('Veuillez charger un fichier de données pour accéder à cette page.', color='info')

    elif current_page == 'Indicateurs':
        if data is not None:
            if INDIC_PAGE_AVAILABLE:
                return indic_page.get_layout()
            else:
                return dbc.Alert('Page Indicateurs non disponible', color='warning')
        else:
            return dbc.Alert('Veuillez charger un fichier de données pour accéder à cette page.', color='info')
    
    return html.Div()

def create_fallback_home():
    """Fallback simple si home.py n'est pas disponible"""
    return dbc.Card([
        dbc.CardBody([
            html.H2('AlloGraph - Page d\'accueil'),
            html.P('Page home.py non disponible.'),
            html.P('Utilisez la sidebar pour charger des données.')
        ])
    ])

# Callback pour ouvrir/fermer la modal de confirmation
@app.callback(
    Output("purge-confirmation-modal", "is_open"),
    [Input("purge-data-button", "n_clicks"), 
     Input("cancel-purge", "n_clicks"),
     Input("confirm-purge", "n_clicks")],
    [State("purge-confirmation-modal", "is_open")],
)
def toggle_purge_modal(purge_clicks, cancel_clicks, confirm_clicks, is_open):
    """Gère l'ouverture/fermeture de la modal de confirmation de purge"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return is_open
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "purge-data-button":
        return True
    elif button_id in ["cancel-purge", "confirm-purge"]:
        return False
    
    return is_open

# Callback pour effectuer la purge des données
@app.callback(
    [Output('data-store', 'data', allow_duplicate=True),
     Output('metadata-store', 'data', allow_duplicate=True),
     Output('upload-status', 'children', allow_duplicate=True)],
    Input('confirm-purge', 'n_clicks'),
    prevent_initial_call=True
)

def purge_data(confirm_clicks):
    """Purge les données du cache quand la purge est confirmée"""
    if confirm_clicks and confirm_clicks > 0:
        # Vider les stores de données
        success_message = dbc.Alert([
            html.H6("🗑️ Données purgées!", className="mb-2"),
            html.P("Toutes les données ont été supprimées du cache.", className="mb-0", style={'fontSize': '12px'})
        ], color='info', dismissable=True)
        
        return None, None, success_message
    
    return dash.no_update, dash.no_update, dash.no_update

server = app.server

if __name__ == '__main__':
    app.run_server(
        host='0.0.0.0',
        port=8000,
        debug=False  # Important pour la production
    )
    
else:
    # Pour la production Heroku
    server = app.server