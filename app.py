import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import base64
import io
import modules.data_processing as data_processing
import visualizations.allogreffes.graphs as gr
import modules.dashboard_layout as layouts  # Import du module de layouts

# Initialisation de l'app Dash avec Bootstrap
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
app.title = "AlloGraph"

# Layout principal utilisant le module de layouts
app.layout = layouts.create_base_layout()

# Callback pour la navigation
@app.callback(
    [Output('current-page', 'data'),
     Output('nav-accueil', 'className'),
     Output('nav-patients', 'className'),
     Output('nav-page1', 'className'),
     Output('nav-page2', 'className'),
     Output('nav-patients', 'disabled'),
     Output('nav-page1', 'disabled'),
     Output('nav-page2', 'disabled')],
    [Input('nav-accueil', 'n_clicks'),
     Input('nav-patients', 'n_clicks'),
     Input('nav-page1', 'n_clicks'),
     Input('nav-page2', 'n_clicks')],
    [State('data-store', 'data'),
     State('current-page', 'data')]
)
def navigate(acc_clicks, pat_clicks, p1_clicks, p2_clicks, data, current_page):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return current_page, 'btn btn-primary me-2', 'btn btn-secondary me-2', 'btn btn-secondary me-2', 'btn btn-secondary me-2', True, True, True
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Déterminer la nouvelle page
    page_map = {
        'nav-accueil': 'Accueil',
        'nav-patients': 'Patients',
        'nav-page1': 'Page 1',
        'nav-page2': 'Page 2'
    }
    new_page = page_map.get(button_id, current_page or 'Accueil')
    
    # Styles des boutons
    btn_styles = {
        'Accueil': 'nav-accueil',
        'Patients': 'nav-patients',
        'Page 1': 'nav-page1',
        'Page 2': 'nav-page2'
    }
    
    styles = {}
    for page, btn_id in btn_styles.items():
        styles[btn_id] = 'btn btn-primary me-2' if new_page == page else 'btn btn-secondary me-2'
    
    # Désactiver les boutons si pas de données
    disabled = data is None
    
    return (new_page, 
            styles['nav-accueil'], 
            styles['nav-patients'], 
            styles['nav-page1'], 
            styles['nav-page2'],
            disabled, disabled, disabled)

# Callback pour le titre de la page
@app.callback(
    Output('page-title', 'children'),
    Input('current-page', 'data')
)
def update_title(current_page):
    return f'Dashboard - {current_page or "Accueil"}'

# Callback pour la sidebar
@app.callback(
    Output('sidebar-content', 'children'),
    [Input('current-page', 'data'),
     Input('data-store', 'data')]
)
def update_sidebar(current_page, data):
    if current_page == 'Accueil':
        content = html.Div([
            layouts.create_upload_component(),
            html.Div(id='upload-status')
        ])
        return layouts.create_sidebar_layout('Chargement des données', content)
    
    elif current_page == 'Patients' and data is not None:
        df = pd.DataFrame(data)
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        if 'Year' in categorical_columns:
            categorical_columns.remove('Year')
        
        # Récupérer les années disponibles
        years_options = []
        if 'Year' in df.columns:
            available_years = sorted(df['Year'].unique().tolist())
            years_options = [{'label': f'{year}', 'value': year} for year in available_years]
        
        content = layouts.create_filter_controls(categorical_columns, years_options)
        return layouts.create_sidebar_layout('Paramètres', content)
    
    else:
        if data is None:
            content = html.P('Retournez à la page Accueil pour charger des données.', className='text-info')
            return layouts.create_sidebar_layout('Navigation', content)
        else:
            df = pd.DataFrame(data)
            content = html.Div([
                html.P('Données chargées', className='text-success'),
                html.P(f'{df.shape[0]} lignes, {df.shape[1]} colonnes', className='text-info')
            ])
            return layouts.create_sidebar_layout('Navigation', content)

# Callback pour traiter l'upload de fichier
@app.callback(
    [Output('data-store', 'data'),
     Output('upload-status', 'children')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def process_uploaded_file(contents, filename):
    if contents is None:
        return dash.no_update, dash.no_update
    
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return dash.no_update, dbc.Alert('Format de fichier non supporté', color='danger')
        
        # Traitement des données avec data_processing
        df = data_processing.process_data(df)
        
        return df.to_dict('records'), dbc.Alert(
            f'Données chargées avec succès! {df.shape[0]} lignes et {df.shape[1]} colonnes.',
            color='success'
        )
    
    except Exception as e:
        return dash.no_update, dbc.Alert(f'Erreur lors du chargement: {str(e)}', color='danger')

# Callback pour le contenu principal
@app.callback(
    Output('main-content', 'children'),
    [Input('current-page', 'data'),
     Input('data-store', 'data')]
)
def update_main_content(current_page, data):
    if current_page == 'Accueil':
        if data is not None:
            df = pd.DataFrame(data)
            
            if 'Year' in df.columns:
                try:
                    fig = gr.create_cumulative_barplot(
                        data=df,
                        category_column='Year',
                        title="Nombre de greffes par an",
                        x_axis_title="Année",
                        bar_y_axis_title="Nombre de greffes",
                        line_y_axis_title="Effectif cumulé",
                        custom_order=df['Year'].unique().tolist()
                    )
                    return dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(figure=fig, style={'height': '600px'})
                        ])
                    ])
                except Exception as e:
                    return dbc.Alert(f'Erreur lors de la création du graphique: {str(e)}', color='danger')
            else:
                available_cols = ', '.join(df.columns.tolist()[:10])
                return dbc.Alert([
                    html.H5('Colonne "Year" non trouvée dans les données'),
                    html.P(f'Colonnes disponibles: {available_cols}...')
                ], color='warning')
        else:
            return dbc.Card([
                dbc.CardBody([
                    html.H2('Bienvenue dans AlloGraph'),
                    html.P('Cette application vous permet d\'analyser des données de patients depuis le modèle de données EBMT.'),
                    html.Hr(),
                    html.H4('Instructions:'),
                    html.Ol([
                        html.Li('Utilisez le bouton dans la barre latérale pour télécharger votre fichier CSV ou Excel.'),
                        html.Li('Une fois les données chargées, vous pourrez naviguer entre différentes pages d\'analyse.')
                    ])
                ])
            ])
    
    elif current_page == 'Patients':
        if data is not None:
            # Utiliser le layout spécifique pour la page Patients
            # Les placeholders seront remplis par les callbacks
            return layouts.create_patients_layout(
                main_content=html.Div(),  # Sera rempli par le callback tab-content
                boxplot_content=html.Div(),  # Sera rempli par le callback boxplot-container
                barplot_content=html.Div()  # Sera rempli par le callback barplot-container
            )
        else:
            return dbc.Alert('Veuillez charger un fichier de données pour accéder à cette page.', color='info')
    
    elif current_page in ['Page 1', 'Page 2']:
        return dbc.Card([
            dbc.CardBody([
                html.H3(f'Contenu de la {current_page}'),
                html.P('En cours de développement')
            ])
        ])
    
    return html.Div()

# Callback pour les onglets de la page Patients
@app.callback(
    Output('tab-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('data-store', 'data'),
     Input('x-axis-dropdown', 'value'),
     Input('stack-variable-dropdown', 'value'),
     Input('year-filter-checklist', 'value')],
    prevent_initial_call=True
)
def update_tab_content(tab, data, x_axis, stack_var, selected_years):
    if data is None:
        return html.Div()
    
    df = pd.DataFrame(data)
    
    # Filtrer les données
    if selected_years and 'Year' in df.columns:
        filtered_df = df[df['Year'].isin(selected_years)]
    else:
        filtered_df = df
    
    if filtered_df.empty:
        return dbc.Alert('Aucune donnée disponible avec les filtres sélectionnés', color='warning')
    
    if tab == 'tab-normalized':
        try:
            if x_axis not in filtered_df.columns:
                return dbc.Alert(f'Colonne "{x_axis}" non trouvée dans les données', color='warning')
            
            stack_col = None if stack_var == 'Aucune' else stack_var
            fig = gr.create_normalized_barplot(
                data=filtered_df,
                x_column=x_axis,
                y_column='Count',
                stack_column=stack_col,
                title=f"Distribution normalisée par {x_axis}",
                x_axis_title=x_axis,
                y_axis_title="Proportion (%)",
                height=420,  # Ajusté pour le conteneur principal
                width=None
            )
            return dcc.Graph(
                figure=fig, 
                style={'height': '100%'},
                config={'responsive': True}
            )
        except Exception as e:
            return dbc.Alert(f'Erreur: {str(e)}', color='danger')
    
    elif tab == 'tab-table':
        return html.Div([
            dash_table.DataTable(
                data=filtered_df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in filtered_df.columns],
                page_size=20,
                style_table={'height': '400px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'left'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                filter_action="native",
                sort_action="native",
                page_action="native"
            ),
            html.P(f'{len(filtered_df)} lignes affichées sur {len(df)} au total', 
                   className='text-info mt-2')
        ])
    
    return html.Div()

# Callback pour le boxplot
@app.callback(
    Output('boxplot-container', 'children'),
    [Input('data-store', 'data'),
     Input('x-axis-dropdown', 'value'),
     Input('stack-variable-dropdown', 'value'),
     Input('year-filter-checklist', 'value')],
    prevent_initial_call=True
)
def update_boxplot(data, x_axis, stack_var, selected_years):
    if data is None:
        return html.Div()
    
    df = pd.DataFrame(data)
    
    # Filtrer les données
    if selected_years and 'Year' in df.columns:
        filtered_df = df[df['Year'].isin(selected_years)]
    else:
        filtered_df = df
    
    if filtered_df.empty:
        return html.Div('Aucune donnée disponible', className='text-warning text-center')
    
    try:
        # Déterminer la variable Y pour le boxplot
        numeric_columns = filtered_df.select_dtypes(include=[np.number]).columns.tolist()
        
        if x_axis and x_axis in numeric_columns:
            y_variable = x_axis
        else:
            y_variable = numeric_columns[0] if numeric_columns else None
        
        if y_variable:
            group_col = None if stack_var == 'Aucune' else stack_var
            fig = gr.create_boxplot(
                data=filtered_df,
                x_column=group_col,
                y_column=y_variable,
                title=f"Boxplot de {y_variable}" + (f" par {group_col}" if group_col else ""),
                x_axis_title=group_col,
                y_axis_title=y_variable,
                height=320,  # Ajusté pour s'adapter au container
                width=None  # Laisser Plotly gérer la largeur
            )
            
            return dcc.Graph(
                figure=fig, 
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        else:
            return html.Div('Aucune variable numérique disponible', className='text-warning text-center')
    
    except Exception as e:
        return html.Div(f'Erreur: {str(e)}', className='text-danger')

# Callback pour le barplot
@app.callback(
    Output('barplot-container', 'children'),
    [Input('data-store', 'data'),
     Input('x-axis-dropdown', 'value'),
     Input('stack-variable-dropdown', 'value'),
     Input('year-filter-checklist', 'value')],
    prevent_initial_call=True
)
def update_barplot(data, x_axis, stack_var, selected_years):
    if data is None:
        return html.Div()
    
    df = pd.DataFrame(data)
    
    # Filtrer les données
    if selected_years and 'Year' in df.columns:
        filtered_df = df[df['Year'].isin(selected_years)]
    else:
        filtered_df = df
    
    if filtered_df.empty:
        return html.Div('Aucune donnée disponible', className='text-warning text-center')
    
    try:
        if x_axis not in filtered_df.columns:
            return html.Div(f'Colonne "{x_axis}" non trouvée', className='text-warning text-center')
        
        stack_col = None if stack_var == 'Aucune' else stack_var
        fig = gr.create_stacked_barplot(
            data=filtered_df,
            x_column=x_axis,
            y_column='Count',
            stack_column=stack_col,
            title=f"Barplot de {x_axis}" + (f" par {stack_col}" if stack_col else ""),
            x_axis_title=x_axis,
            y_axis_title="Nombre de greffes",
            custom_order=filtered_df[x_axis].unique().tolist(),
            height=320,  # Ajusté pour s'adapter au container
            width=None  # Laisser Plotly gérer la largeur
        )
        
        return dcc.Graph(
            figure=fig, 
            style={'height': '100%'},
            config={'responsive': True, 'displayModeBar': False}
        )
    
    except Exception as e:
        return html.Div(f'Erreur: {str(e)}', className='text-danger')

if __name__ == '__main__':
    app.run(debug=True)