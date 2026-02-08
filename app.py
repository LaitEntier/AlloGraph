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

# Performance optimization: Response compression for VM deployments (optional)
try:
    from flask_compress import Compress
    _compress_available = True
except ImportError:
    _compress_available = False
    print("Note: flask-compress not installed. Install with: pip install flask-compress")

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
    # Note: compress=True requires flask-compress, we handle it separately below
)
app.title = "AlloGraph"

# Enable Flask-Compress for better compression (GDPR compliant - no persistence)
# This is optional - app works without it, but VM performance is better with it
if _compress_available:
    try:
        Compress(app.server)
        print("Flask-Compress enabled for better VM performance")
    except Exception as e:
        print(f"Note: Could not enable Flask-Compress: {e}")

# Custom index string with SVG favicon
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" type="image/svg+xml" href="/allograph-app/assets/images/ico.svg">
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

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
     Input('nav-home-logo', 'n_clicks'),
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
def navigate(acc_clicks, logo_clicks, pat_clicks, p1_clicks, proc_clicks, gvh_clicks, rechute_clicks, surv_clicks, indics_clicks, data, current_page):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        disabled = data is None
        if current_page is None:
            current_page = 'Home'
        
        styles = {
            'Home': 'btn btn-primary me-2 nav-button' if current_page == 'Home' else 'btn btn-secondary me-2 nav-button',
            'Patients': 'btn btn-primary me-2 nav-button' if current_page == 'Patients' else 'btn btn-secondary me-2 nav-button',
            'Indications': 'btn btn-primary me-2 nav-button' if current_page == 'Indications' else 'btn btn-secondary me-2 nav-button',
            'Procedures': 'btn btn-primary me-2 nav-button' if current_page == 'Procedures' else 'btn btn-secondary me-2 nav-button',
            'GvH': 'btn btn-primary me-2 nav-button' if current_page == 'GvH' else 'btn btn-secondary me-2 nav-button',
            'Relapse': 'btn btn-primary me-2 nav-button' if current_page == 'Relapse' else 'btn btn-secondary me-2 nav-button',
            'Survival': 'btn btn-primary me-2 nav-button' if current_page == 'Survival' else 'btn btn-secondary me-2 nav-button',
            'Indicators': 'btn btn-primary me-2 nav-button' if current_page == 'Indicators' else 'btn btn-secondary me-2 nav-button'
        }

        return (current_page, styles['Home'], styles['Patients'],
                styles['Indications'], styles['Procedures'], styles['GvH'], styles['Relapse'], styles['Survival'], styles['Indicators'],
                disabled, disabled, disabled, disabled, disabled, disabled, disabled)
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'data-store':
        disabled = data is None
        current_page = current_page or 'Home'
        
        styles = {
            'Home': 'btn btn-primary me-2 nav-button' if current_page == 'Home' else 'btn btn-secondary me-2 nav-button',
            'Patients': 'btn btn-primary me-2 nav-button' if current_page == 'Patients' else 'btn btn-secondary me-2 nav-button',
            'Indications': 'btn btn-primary me-2 nav-button' if current_page == 'Indications' else 'btn btn-secondary me-2 nav-button',
            'Procedures': 'btn btn-primary me-2 nav-button' if current_page == 'Procedures' else 'btn btn-secondary me-2 nav-button',
            'GvH': 'btn btn-primary me-2 nav-button' if current_page == 'GvH' else 'btn btn-secondary me-2 nav-button',
            'Relapse': 'btn btn-primary me-2 nav-button' if current_page == 'Relapse' else 'btn btn-secondary me-2 nav-button',
            'Survival': 'btn btn-primary me-2 nav-button' if current_page == 'Survival' else 'btn btn-secondary me-2 nav-button',
            'Indicators': 'btn btn-primary me-2 nav-button' if current_page == 'Indicators' else 'btn btn-secondary me-2 nav-button'
        }

        return (current_page, styles['Home'], styles['Patients'],
                styles['Indications'], styles['Procedures'], styles['GvH'], styles['Relapse'], styles['Survival'], styles['Indicators'],
                disabled, disabled, disabled, disabled, disabled, disabled, disabled)
    
    # Navigation normale
    page_map = {
        'nav-home': 'Home',
        'nav-home-logo': 'Home',
        'nav-patients': 'Patients',
        'nav-hemopathies': 'Indications',
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
        'Indications': 'nav-hemopathies',
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
            # Pas de données : afficher l'upload ET le bouton test sample
            content = html.Div([
                # Section upload classique
                html.Div([
                    html.H6("Upload your data:", className="mb-2", style={'color': '#021F59'}),
                    layouts.create_upload_component(),
                    html.Div(id='upload-status')
                ], className="mb-4"),
                
                # Séparateur
                html.Div([
                    html.Div(style={
                        'display': 'flex',
                        'alignItems': 'center',
                        'textAlign': 'center',
                        'margin': '20px 0'
                    }, children=[
                        html.Div(style={
                            'flex': '1',
                            'height': '1px',
                            'backgroundColor': '#77ACF2'
                        }),
                        html.Span("Or", style={
                            'padding': '0 15px',
                            'color': '#021F59',
                            'fontSize': '12px',
                            'fontWeight': '500',
                            'textTransform': 'uppercase'
                        }),
                        html.Div(style={
                            'flex': '1',
                            'height': '1px',
                            'backgroundColor': '#dee2e6'
                        })
                    ])
                ]),
                
                # Section test sample
                html.Div([
                    html.H6("Test with sample data:", className="mb-2", style={'color': '#021F59'}),
                    html.P("Load a de-identified representative dataset to explore the application.", 
                          style={'fontSize': '11px', 'color': '#021F59'}),
                    dbc.Button([
                        html.I(className="bi bi-flask me-2"),
                        "Load test sample"
                    ], 
                    id="load-test-sample-btn", 
                    className="btn btn-secondary nav-button w-100",
                    size="sm")
                ])
            ])
            return layouts.create_sidebar_layout('Data', content)
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
                    html.H6("📊 Data loaded:", className="mb-2", style={'color': '#021F59'}),
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
                    html.H6("New file:", className="mb-2", style={'color': '#021F59'}),
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
    
    elif current_page == 'Indications' and data is not None:
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
    [Output('sidebar-content', 'style'),
     Output('main-content', 'width')],
    [Input('current-page', 'data'),
     Input('data-store', 'data')]
)
def toggle_sidebar_visibility(current_page, data):
    """Cache la sidebar sur la page d'accueil quand aucune donnée n'est chargée"""
    if current_page == 'Home' and data is None:
        # Cacher la sidebar et élargir le contenu principal
        return {'display': 'none'}, 12
    else:
        # Afficher la sidebar normalement
        return {
            'position': 'sticky',
            'top': '20px',
            'height': 'fit-content',
            'z-index': '1000'
        }, 10


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
            # Détection automatique du séparateur
            decoded_content = decoded.decode('utf-8')
            separator = data_processing.detect_csv_separator(decoded_content, is_file_path=False)
            df_original = pd.read_csv(io.StringIO(decoded_content), sep=separator)
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


# Helper function to create slim data stores (reduces VM network transfer)
def _create_slim_stores(df_full: pd.DataFrame) -> tuple:
    """
    Create optimized slim data stores for specific analyses.
    Reduces network payload for VM deployments.
    """
    print(f"DEBUG _create_slim_stores: Input columns: {list(df_full.columns)}")
    
    # Core columns that should always be included if they exist
    core_cols = ['Long ID', 'Year', 'Patient ID', 'ID']
    core_cols = [c for c in core_cols if c in df_full.columns]
    print(f"DEBUG _create_slim_stores: Core cols found: {core_cols}")
    
    # Survival analysis columns - base columns needed for survival calculations
    survival_needed = ['Treatment Date', 'Date Of Last Follow Up', 'Status Last Follow Up']
    survival_cols = core_cols + survival_needed
    survival_cols = [c for c in survival_cols if c in df_full.columns]
    print(f"DEBUG _create_slim_stores: Survival cols found: {survival_cols}")
    df_survival = df_full[survival_cols] if survival_cols else df_full[core_cols] if core_cols else df_full.iloc[:, :5]
    
    # GvH analysis columns - base columns needed for GvH calculations
    gvh_needed = [
        'Treatment Date', 'Date Of Last Follow Up', 'Status Last Follow Up',
        'First Agvhd Occurrence', 'First Agvhd Occurrence Date', 'First aGvHD Maximum Score',
        'First Cgvhd Occurrence', 'First Cgvhd Occurrence Date', 'First cGvHD Maximum NIH Score'
    ]
    gvh_cols = core_cols + gvh_needed
    gvh_cols = [c for c in gvh_cols if c in df_full.columns]
    print(f"DEBUG _create_slim_stores: GvH cols found: {gvh_cols}")
    df_gvh = df_full[gvh_cols] if gvh_cols else df_full[core_cols] if core_cols else df_full.iloc[:, :5]
    
    # Visualization columns - demographic and clinical data for charts
    viz_needed = [
        'Age At Diagnosis', 'Age Groups', 'Sex',
        'Main Diagnosis', 'Subclass Diagnosis', 'Donor Type', 
        'Source Stem Cells', 'Greffes', 'Blood + Rh', 'Donor Match Category',
        'Conditioning Regimen Type', 'Match Type', 'Performance Status At Treatment Scale',
        'Performance Status At Treatment Score', 'CMV Status Donor', 'CMV Status Patient'
    ]
    viz_cols = core_cols + viz_needed
    viz_cols = [c for c in viz_cols if c in df_full.columns]
    print(f"DEBUG _create_slim_stores: Viz cols found: {viz_cols}")
    df_viz = df_full[viz_cols] if viz_cols else df_full[core_cols] if core_cols else df_full.iloc[:, :5]
    
    return df_survival.to_dict('records'), df_gvh.to_dict('records'), df_viz.to_dict('records')


@app.callback(
    [Output('data-store-survival', 'data'),
     Output('data-store-gvh', 'data'),
     Output('data-store-viz', 'data')],
    Input('data-store', 'data')
    # NOTE: No prevent_initial_call - this MUST run when data is first loaded
)
def update_slim_stores(data):
    """
    Update slim data stores when main data changes.
    Reduces network transfer for VM deployments.
    """
    if data is None:
        print("DEBUG: Slim stores - data is None")
        return None, None, None
    
    try:
        df = pd.DataFrame(data)
        print(f"DEBUG: Creating slim stores from DataFrame with columns: {list(df.columns)}")
        survival_data, gvh_data, viz_data = _create_slim_stores(df)
        print(f"DEBUG: Slim stores created - survival: {len(survival_data) if survival_data else 0} rows, "
              f"gvh: {len(gvh_data) if gvh_data else 0} rows, viz: {len(viz_data) if viz_data else 0} rows")
        return survival_data, gvh_data, viz_data
    except Exception as e:
        print(f"Error creating slim stores: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


@app.callback(
    Output('main-content', 'children'),
    [Input('current-page', 'data'),
     Input('data-store', 'data')],
     prevent_initial_call=True
)
def update_main_content(current_page, data):

    if current_page == 'Home':
        return home_page.get_layout()

    elif current_page == 'Patients':
            return patients_page.get_layout()

    elif current_page == 'Indications':
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
     Output('metadata-store', 'data', allow_duplicate=True),
     Output('data-store-survival', 'data', allow_duplicate=True),
     Output('data-store-gvh', 'data', allow_duplicate=True),
     Output('data-store-viz', 'data', allow_duplicate=True)],
    Input('confirm-purge', 'n_clicks'),
    prevent_initial_call=True
)
def purge_data(confirm_clicks):
    """Purge les données du cache quand la purge est confirmée"""
    if confirm_clicks and confirm_clicks > 0:
        # Vider tous les stores de données (GDPR compliant - no persistence)
        return None, None, None, None, None
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
  
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

@app.callback(
    [Output('data-store', 'data', allow_duplicate=True),
     Output('metadata-store', 'data', allow_duplicate=True),
     Output('upload-status', 'children', allow_duplicate=True)],
    Input('load-test-sample-btn', 'n_clicks'),
    prevent_initial_call=True
)
def load_test_sample(n_clicks):
    """Charge le fichier test sample quand le bouton est cliqué"""
    if n_clicks is None:
        return dash.no_update, dash.no_update, dash.no_update
    
    try:
        # Chemin vers le fichier test sample
        test_file_path = 'data/test_sample.csv'
        
        # Vérifier que le fichier existe
        if not os.path.exists(test_file_path):
            return (dash.no_update, dash.no_update, 
                    dbc.Alert('Test sample file not found: data/test_sample.csv', 
                             color='danger'))
        
        # Charger le fichier CSV avec détection automatique du séparateur
        separator = data_processing.detect_csv_separator(test_file_path, is_file_path=True)
        df_original = pd.read_csv(test_file_path, sep=separator)
        
        # Stocker les dimensions originales
        original_shape = df_original.shape
        
        # Traitement des données (même logique que l'upload)
        df_processed = data_processing.process_data(df_original)
        processed_shape = df_processed.shape
        
        # Créer les métadonnées
        metadata = {
            'original_shape': original_shape,
            'processed_shape': processed_shape,
            'filename': 'test_sample.csv (sample data)'
        }
        
        # Message de succès
        success_message = dbc.Alert([
            html.H6("✅ Test sample loaded successfully!", className="mb-2"),
            html.P([
                "📁 ", html.Strong("test_sample.csv (sample data)")
            ], className="mb-2", style={'fontSize': '12px'}),
            html.P([
                "📊 Original data: ", 
                html.Strong(f"{original_shape[0]:,} lines × {original_shape[1]} columns")
            ], className="mb-1", style={'fontSize': '11px'}),
            html.P([
                "⚙️ After processing: ", 
                html.Strong(f"{processed_shape[0]:,} lines × {processed_shape[1]} columns")
            ], className="mb-0", style={'fontSize': '11px'})
        ], color='info')
        
        return df_processed.to_dict('records'), metadata, success_message
    
    except Exception as e:
        return (dash.no_update, dash.no_update, 
                dbc.Alert(f'Error loading test sample: {str(e)}', color='danger'))
    
@app.callback(
    [Output('user-session-start', 'data'),
     Output('survey-toast', 'is_open'),  # ou 'survey-modal' si vous utilisez la modal
     Output('survey-shown', 'data')],
    [Input('survey-timer', 'n_intervals'),
     Input('data-store', 'data'),
     Input('survey-later-btn', 'n_clicks'),  # Bouton "Plus tard"
     Input('survey-toast', 'is_open')],      # Quand le toast se ferme
    [State('user-session-start', 'data'),
     State('survey-shown', 'data'),
     State('survey-dismissed', 'data')]
)
def manage_survey_notification(n_intervals, data, later_clicks, toast_is_open, 
                             session_start, survey_shown, survey_dismissed):
    """
    Gère l'affichage de la notification questionnaire
    """
    import time
    from dash import callback_context
    
    ctx = callback_context
    current_time = time.time()
    
    # Initialiser le timestamp de début de session
    if session_start is None:
        return current_time, False, False
    
    # Ne pas montrer si déjà montré ou si l'utilisateur l'a fermé
    if survey_shown or survey_dismissed:
        return session_start, False, survey_shown
    
    # Ne montrer que si des données sont chargées (utilisateur actif)
    if data is None:
        return session_start, False, survey_shown
    
    # Calculer le temps écoulé (en secondes)
    elapsed_time = current_time - session_start
    
    # Condition pour déclencher la notification
    TRIGGER_TIME = 5  # 5 secondes

    # Si le bouton "Plus tard" a été cliqué
    if ctx.triggered and 'survey-later-btn' in ctx.triggered[0]['prop_id']:
        # Reporter la notification de 5 minutes
        new_start_time = current_time - (TRIGGER_TIME - 180)  # Reporter de 3 min
        return new_start_time, False, False
    
    # Si le toast se ferme (dismissed), marquer comme montré
    if ctx.triggered and 'survey-toast.is_open' in ctx.triggered[0]['prop_id'] and not toast_is_open:
        return session_start, False, True
    
    # Déclencher la notification si le temps est écoulé
    if elapsed_time >= TRIGGER_TIME and not survey_shown:
        return session_start, True, True
    
    return session_start, False, survey_shown

@app.callback(
    Output('survey-dismissed', 'data'),
    [Input('survey-later-btn', 'n_clicks')],
    prevent_initial_call=True
)
def handle_survey_later(n_clicks):
    """Marque temporairement comme fermé quand on clique sur Plus tard"""
    if n_clicks:
        return True
    return False

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
    app.run_server(
        host='0.0.0.0',
        port=8000,
        debug=False
    )
    
else:
    # Pour la production Heroku
    server = app.server