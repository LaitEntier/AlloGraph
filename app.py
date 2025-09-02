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
import pages.home as home_page
import pages.patients as patients_page
import pages.hemopathies as hemopathies_page
import pages.procedures as procedures_page
import pages.gvh as gvh_page
import pages.relapse as relapse_page
import pages.survival as survival_page
import pages.indics as indic_page


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
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.BOOTSTRAP
    ],
    suppress_callback_exceptions=True,
    assets_folder='assets',
    assets_url_path='allograph-app/assets',
)
app.title = "AlloGraph"

# Layout de base avec navigation mise à jour
app.layout = html.Div([
    layouts.create_base_layout(),
    dcc.Store(id='metadata-store')
])

# ========== CALLBACKS GLOBAUX UNIQUEMENT ==========

@app.callback(
    [Output('current-page', 'data'),
     Output('nav-home', 'className'),
     Output('nav-patients', 'className'),
     Output('nav-hemopathies', 'className'),
     Output('nav-procedures', 'className'),
     Output('nav-gvh', 'className'),
     Output('nav-relapse', 'className'),
     Output('nav-survival', 'className'),        
     Output('nav-indics', 'className'),
     Output('nav-patients', 'disabled'),
     Output('nav-hemopathies', 'disabled'),
     Output('nav-procedures', 'disabled'),
     Output('nav-gvh', 'disabled'),
     Output('nav-relapse', 'disabled'),
     Output('nav-survival', 'disabled'),         
     Output('nav-indics', 'disabled')],
    [Input('nav-home', 'n_clicks'),
     Input('nav-patients', 'n_clicks'),
     Input('nav-hemopathies', 'n_clicks'),
     Input('nav-procedures', 'n_clicks'),
     Input('nav-gvh', 'n_clicks'),
     Input('nav-relapse', 'n_clicks'),
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
            current_page = 'Home'
        
        styles = {
            'Home': 'btn btn-primary me-2 nav-button' if current_page == 'Home' else 'btn btn-secondary me-2 nav-button',
            'Patients': 'btn btn-primary me-2 nav-button' if current_page == 'Patients' else 'btn btn-secondary me-2 nav-button',
            'Hemopathies': 'btn btn-primary me-2 nav-button' if current_page == 'Hemopathies' else 'btn btn-secondary me-2 nav-button',
            'Procedures': 'btn btn-primary me-2 nav-button' if current_page == 'Procedures' else 'btn btn-secondary me-2 nav-button',
            'GvH': 'btn btn-primary me-2 nav-button' if current_page == 'GvH' else 'btn btn-secondary me-2 nav-button',
            'Relapse': 'btn btn-primary me-2 nav-button' if current_page == 'Relapse' else 'btn btn-secondary me-2 nav-button',
            'Survival': 'btn btn-primary me-2 nav-button' if current_page == 'Survival' else 'btn btn-secondary me-2 nav-button',
            'Indicators': 'btn btn-primary me-2 nav-button' if current_page == 'Indicators' else 'btn btn-secondary me-2 nav-button'
        }

        return (current_page, styles['Home'], styles['Patients'],
                styles['Hemopathies'], styles['Procedures'], styles['GvH'], styles['Relapse'], styles['Survival'], styles['Indicators'],
                disabled, disabled, disabled, disabled, disabled, disabled, disabled)
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'data-store':
        disabled = data is None
        current_page = current_page or 'Home'
        
        styles = {
            'Home': 'btn btn-primary me-2 nav-button' if current_page == 'Home' else 'btn btn-secondary me-2 nav-button',
            'Patients': 'btn btn-primary me-2 nav-button' if current_page == 'Patients' else 'btn btn-secondary me-2 nav-button',
            'Hemopathies': 'btn btn-primary me-2 nav-button' if current_page == 'Hemopathies' else 'btn btn-secondary me-2 nav-button',
            'Procedures': 'btn btn-primary me-2 nav-button' if current_page == 'Procedures' else 'btn btn-secondary me-2 nav-button',
            'GvH': 'btn btn-primary me-2 nav-button' if current_page == 'GvH' else 'btn btn-secondary me-2 nav-button',
            'Relapse': 'btn btn-primary me-2 nav-button' if current_page == 'Relapse' else 'btn btn-secondary me-2 nav-button',
            'Survival': 'btn btn-primary me-2 nav-button' if current_page == 'Survival' else 'btn btn-secondary me-2 nav-button',
            'Indicators': 'btn btn-primary me-2 nav-button' if current_page == 'Indicators' else 'btn btn-secondary me-2 nav-button'
        }

        return (current_page, styles['Home'], styles['Patients'],
                styles['Hemopathies'], styles['Procedures'], styles['GvH'], styles['Relapse'], styles['Survival'], styles['Indicators'],
                disabled, disabled, disabled, disabled, disabled, disabled, disabled)
    
    # Navigation normale
    page_map = {
        'nav-home': 'Home',
        'nav-patients': 'Patients',
        'nav-hemopathies': 'Hemopathies',
        'nav-procedures': 'Procedures',
        'nav-gvh': 'GvH',
        'nav-relapse': 'Relapse',
        'nav-survival': 'Survival',               
        'nav-indics': 'Indicators'
    }
    new_page = page_map.get(button_id, current_page or 'Home')
    
    btn_styles = {
        'Home': 'nav-home',
        'Patients': 'nav-patients',
        'Hemopathies': 'nav-hemopathies',
        'Procedures': 'nav-procedures',
        'GvH': 'nav-gvh',
        'Relapse': 'nav-relapse',
        'Survival': 'nav-survival',               
        'Indicators': 'nav-indics'
    }
    
    styles = {}
    for page, btn_id in btn_styles.items():
        styles[btn_id] = 'btn btn-primary me-2 nav-button' if new_page == page else 'btn btn-secondary me-2 nav-button'

    disabled = data is None

    return (new_page, styles['nav-home'], styles['nav-patients'],
            styles['nav-hemopathies'], styles['nav-procedures'], styles['nav-gvh'], styles['nav-relapse'], styles['nav-survival'], styles['nav-indics'],
            disabled, disabled, disabled, disabled, disabled, disabled, disabled)

@app.callback(
    Output('sidebar-content', 'children'),
    [Input('current-page', 'data'),
     Input('data-store', 'data'),
     Input('metadata-store', 'data')]
)
def update_sidebar(current_page, data, metadata):
    """Gère la sidebar selon la page active"""
    if current_page == 'Home':
        # Sidebar pour l'upload sur la page d'accueil
        if data is None:
            # Pas de données : afficher l'upload
            content = html.Div([
                layouts.create_upload_component(),
                html.Div(id='upload-status')
            ])
            return layouts.create_sidebar_layout('Upload', content)
        else:
            df = pd.DataFrame(data)
            
            # Utiliser les métadonnées si disponibles
            if metadata:
                original_shape = metadata.get('original_shape', (0, 0))
                filename = metadata.get('filename', 'Unknown')
            else:
                original_shape = (len(df), len(df.columns))
                filename = 'Data loaded'
                
            content = html.Div([
                dbc.Alert([
                    html.H6("📊 Data loaded:", className="mb-2"),
                    html.P([
                        html.Strong(filename)
                    ], className="mb-1", style={'fontSize': '11px'}),
                    html.P([
                        f"Patients: {original_shape[0]:,} | ",
                        f"Variables: {original_shape[1]:,}"
                    ], className="mb-0", style={'fontSize': '11px'})
                ], color="success", className="mb-3"),
                
                # Section pour charger un nouveau fichier
                html.Div([
                    html.H6("New file:", className="mb-2"),
                    layouts.create_upload_component(),
                    html.Div(id='upload-status')
                ])
            ])
            
            return layouts.create_sidebar_layout('Data', content)

    # Le reste du callback reste inchangé pour les autres pages
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
        return layouts.create_sidebar_layout('Parameters', content)

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
        return layouts.create_sidebar_layout('Parameters', content)
    
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
        return layouts.create_sidebar_layout('Parameters', content)
    
    elif current_page == 'Procedures' and data is not None:
        content = layouts.create_procedures_sidebar_content(data)
        return layouts.create_sidebar_layout('Parameters', content)

    elif current_page == 'GvH' and data is not None:  
        # Sidebar spécifique pour la page GvH
        content = gvh_page.create_gvh_sidebar_content(data)
        return layouts.create_sidebar_layout('Parameters GvH', content)
    
    elif current_page == 'Relapse' and data is not None:
        # Sidebar spécifique pour la page Rechute
        content = relapse_page.create_relapse_sidebar_content(data)
        return layouts.create_sidebar_layout('Parameters Relapse', content)

    elif current_page == 'Survival' and data is not None:  
        # Sidebar spécifique pour la page Survie
        content = survival_page.create_survival_sidebar_content(data)
        return layouts.create_sidebar_layout('Parameters Survival', content)
    
    elif current_page == 'Indicators' and data is not None:
        content = indic_page.create_indicators_sidebar_content(data)
        return layouts.create_sidebar_layout('Indicators', content)

    else:
        # Sidebar par défaut
        if data is None:
            content = html.Div([
                html.P('Return to the Home page to load data.', className='text-warning')
            ])
        else:
            content = html.Div([
                html.P('Data loaded. Use the navigation buttons to explore your data.', className='text-success')
            ])
        return layouts.create_sidebar_layout('Information', content)


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
            return dash.no_update, dash.no_update, dbc.Alert('Unsupported file format', color='danger')
        
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
            html.H6("✅ File uploaded successfully!", className="mb-2"),
            html.P([
                "📁 ", html.Strong(filename)
            ], className="mb-2", style={'fontSize': '12px'}),
            html.P([
                "📊 Original data: ", 
                html.Strong(f"{original_shape[0]:,} lines × {original_shape[1]} columns")
            ], className="mb-1", style={'fontSize': '11px'}),
            html.P([
                "⚙️ After processing: ", 
                html.Strong(f"{processed_shape[0]:,} lines × {processed_shape[1]} columns")
            ], className="mb-0", style={'fontSize': '11px'})
        ], color='success')
        
        return df_processed.to_dict('records'), metadata, success_message
    
    except Exception as e:
        return dash.no_update, dash.no_update, dbc.Alert(f'Error during loading: {str(e)}', color='danger')

@app.callback(
    Output('main-content', 'children'),
    [Input('current-page', 'data'),
     Input('data-store', 'data')],
     prevent_initial_call=False
)
def update_main_content(current_page, data):

    if current_page == 'Home':
        return home_page.get_layout()

    elif current_page == 'Patients':
            return patients_page.get_layout()

    elif current_page == 'Hemopathies':
            return hemopathies_page.get_layout()

    elif current_page == 'Procedures':
            return procedures_page.get_layout()
    
    elif current_page == 'GvH':  
            return gvh_page.get_layout()
            
    elif current_page == 'Relapse':
            return relapse_page.get_layout()

    elif current_page == 'Survival':  
            return survival_page.get_layout()

    elif current_page == 'Indicators':
            return indic_page.get_layout()

    return html.Div()

def create_fallback_home():
    """Fallback simple si home.py n'est pas disponible"""
    return dbc.Card([
        dbc.CardBody([
            html.H2('AlloGraph - Home page'),
            html.P('Page home.py not available.'),
            html.P('Use the sidebar to load data.')
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
     Output('metadata-store', 'data', allow_duplicate=True)],
    Input('confirm-purge', 'n_clicks'),
    prevent_initial_call=True
)
def purge_data(confirm_clicks):
    """Purge les données du cache quand la purge est confirmée"""
    if confirm_clicks and confirm_clicks > 0:
        # Vider les stores de données
        return None, None
    
    return dash.no_update, dash.no_update
  
@app.callback(
    Output("purge-data-button", "style"),
    [Input("data-store", "data")]
)
def toggle_purge_button_visibility(data):
    """Affiche le bouton Purge data seulement quand des données sont chargées"""
    if data is not None:
        return {'display': 'block'}
    else:
        return {'display': 'none'}
    
server = app.server

home_page.register_callbacks(app)
patients_page.register_callbacks(app)
hemopathies_page.register_callbacks(app)
procedures_page.register_callbacks(app)
gvh_page.register_callbacks(app)
relapse_page.register_callbacks(app)
survival_page.register_callbacks(app)
indic_page.register_callbacks(app)

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=8000,
        debug=False
    )
    
else:
    # Pour la production Heroku
    server = app.server