import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly
import modules.dashboard_layout as layouts
import visualizations.allogreffes.graphs as gr
import visualizations.allogreffes.upsetjs_embed as upsetjs

def get_layout():
    """Retourne le layout de la page Procedures avec graphiques empilés verticalement et spinners"""
    return dbc.Container([
        # Premier graphique - Évolution par année avec sélecteur intégré
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5('Yearly evolution'),
                        # Sélecteur de variable intégré dans le header
                        html.Div([
                            html.Label('Variable to analyze:', 
                                     style={'fontSize': '12px', 'marginRight': '10px', 'marginBottom': '0'}),
                            dcc.Dropdown(
                                id='procedures-main-variable-integrated',
                                style={'width': '250px', 'fontSize': '12px'},
                                placeholder="Select a variable..."
                            )
                        ], style={
                            'display': 'flex', 
                            'alignItems': 'center', 
                            'marginTop': '10px',
                            'flexWrap': 'wrap',
                            'gap': '5px'
                        })
                    ]),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-procedures-main",
                            type="circle",
                            children=html.Div(
                                id='procedures-main-chart',
                                style={'height': '500px', 'overflow': 'hidden'}
                            )
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),

        # Deuxième graphique - Analyse du statut CMV
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('CMV status analysis')),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-procedures-cmv",
                            type="circle",
                            children=html.Div(
                                id='procedures-cmv-charts',
                                style={'height': '450px', 'overflow': 'hidden'}
                            )
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),

        # Troisième graphique - Traitements Prophylactiques (avec onglets)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5('Prophylactic treatments'),
                    ]),
                    dbc.CardBody([
                        dcc.Tabs(
                            id='procedures-prophylaxis-tabs',
                            value='tab-barplot',
                            children=[
                                dcc.Tab(label='Treatment proportions', value='tab-barplot'),
                                dcc.Tab(label='Combination analysis', value='tab-upset')
                            ]
                        ),
                        html.Div(
                            style={'marginTop': '15px', 'minHeight': '580px'},
                            children=[
                                dcc.Loading(
                                    id="loading-procedures-prophylaxis",
                                    type="circle",
                                    children=html.Div(
                                        id='procedures-prophylaxis-content',
                                        style={'width': '100%', 'overflow': 'auto'}
                                    )
                                )
                            ]
                        )
                    ], className='p-3')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Quatrième graphique - Traitements de Préparation (avec onglets)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Conditioning regimen')),
                    dbc.CardBody([
                        dcc.Tabs(
                            id='procedures-treatment-tabs',
                            value='tab-barplot',
                            children=[
                                dcc.Tab(label='Treatment proportions', value='tab-barplot'),
                                dcc.Tab(label='Combination analysis (UpSet)', value='tab-upset')
                            ]
                        ),
                        html.Div(
                            style={'marginTop': '15px', 'minHeight': '580px'},
                            children=[
                                dcc.Loading(
                                    id="loading-procedures-treatment",
                                    type="circle",
                                    children=html.Div(
                                        id='procedures-treatment-content',
                                        style={'width': '100%', 'overflow': 'auto'}
                                    )
                                )
                            ]
                        )
                    ], className='p-3')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Cinquième section - Durée d'aplasie et thrombopénie avec onglets
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("ANC Recovery & Platelet Reconstitution duration analysis")),
                    dbc.CardBody([
                        dcc.Tabs(
                            id='procedures-aplasia-tabs',
                            value='tab-global',
                            children=[
                                dcc.Tab(label='ANC Recovery - Global view', value='tab-global'),
                                dcc.Tab(label='ANC Recovery - By year', value='tab-stratified'),
                                dcc.Tab(label='Platelet Reconstitution - Global view', value='tab-thrombopenia-global'),
                                dcc.Tab(label='Platelet Reconstitution - By year', value='tab-thrombopenia-stratified')
                            ]
                        ),
                        html.Div(
                            style={'marginTop': '20px', 'height': '500px'},
                            children=[
                                dcc.Loading(
                                    id="loading-procedures-aplasia",
                                    type="circle",
                                    children=html.Div(
                                        id='procedures-aplasia-tab-content',
                                        style={'height': '100%', 'overflow': 'hidden'}
                                    )
                                )
                            ]
                        )
                    ], className='p-3')
                ])
            ], width=12)
        ], className='mb-4'),

        html.Hr(style={
            'border': '2px solid #dee2e6',
            'margin': '3rem 0 2rem 0'
        }),

                # Section données manquantes - À ajouter à la fin avant ], fluid=True)
        dbc.Row([
            # Tableau 1 - Résumé des colonnes
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Column summary", className='mb-0')),
                    dbc.CardBody([
                        html.Div(id='procedures-missing-summary-table', children=[
                            dbc.Alert("Initial content - will be replaced by the callback", color='warning')
                        ])
                    ])
                ])
            ], width=6),
            
            # Tableau 2 - Patients concernés  
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H5("Lines affected", className='mb-0'),
                            dbc.Button(
                                [html.I(className="fas fa-download me-2"), "Export CSV"],
                                id="export-missing-procedures-button",
                                color="primary",
                                size="sm",
                                disabled=True,  # Désactivé par défaut
                            )
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody([
                        html.Div(id='procedures-missing-detail-table', children=[
                            dbc.Alert("Initial content - will be replaced by the callback", color='warning')
                        ]),
                        # Composant pour télécharger le fichier CSV (invisible)
                        dcc.Download(id="download-missing-procedures-excel")
                    ])
                ])
            ], width=6),
        ]),
        # Filtre des années (optionnel si vous en avez un)
        dcc.Store(id='procedures-year-filter')  # Store pour les filtres d'années
    ], fluid=True)

def get_main_chart_variable_options(data):
    """
    Crée les options pour le dropdown de sélection de variable principale
    
    Args:
        data (list): Liste de dictionnaires (format store Dash) avec les données
        
    Returns:
        list: Liste des options pour le dropdown
    """
    if data is None or len(data) == 0:
        return [{'label': 'No data available', 'value': 'none'}]
    
    # Convertir la liste en DataFrame
    df = pd.DataFrame(data)
    
    # Variables disponibles pour le graphique principal
    main_chart_options = []
    
    # Vérifier les colonnes disponibles (ordre de priorité)
    possible_columns = {
        'Donor Type': 'Donor type',
        'Source Stem Cells': 'Source of stem cells', 
        'Match Type': 'Match type',
        'Conditioning Regimen Type': 'Conditioning regimen type',
        'Compatibilité HLA': 'HLA Compatibility'
    }
    
    # Ajouter les colonnes qui existent réellement
    for col, label in possible_columns.items():
        if col in df.columns:
            # Vérifier qu'il y a des données non nulles dans cette colonne
            non_null_count = df[col].notna().sum()
            unique_values = df[col].nunique()
        
            if non_null_count > 0 and unique_values > 1:  # Au moins quelques données et de la variabilité
                main_chart_options.append({'label': label, 'value': col})
    
    return main_chart_options

def register_callbacks(app):
    """Enregistre tous les callbacks spécifiques à la page Procedures"""
    
    # Nouveau callback pour initialiser les options du dropdown intégré
    @app.callback(
        [Output('procedures-main-variable-integrated', 'options'),
         Output('procedures-main-variable-integrated', 'value')],
        [Input('data-store', 'data'),
         Input('current-page', 'data')],
        prevent_initial_call=False  # Changé à False pour permettre l'exécution initiale
    )
    def update_main_variable_options(data, current_page):
        """Met à jour les options du dropdown de variable principale"""
        
        if current_page != 'Procedures':
            return [], None
            
        if data is None:
            return [{'label': 'Loading...', 'value': 'loading'}], None
        
        options = get_main_chart_variable_options(data)

        # Sélectionner la première option valide par défaut
        default_value = None
        if options and len(options) > 0:
            # Prendre la première option qui n'est pas 'none', 'loading' ou 'Aucune variable disponible'
            for option in options:
                if option['value'] not in ['none', 'loading'] and 'None' not in option['label']:
                    default_value = option['value']
                    break
            
            # Si pas d'option valide trouvée, prendre la première
            if default_value is None:
                default_value = options[0]['value']

        return options, default_value

    @app.callback(
        Output('procedures-main-chart', 'children'),
        [Input('data-store', 'data'),
        Input('current-page', 'data'),
        Input('procedures-main-variable-integrated', 'value'),  
        Input('procedures-year-filter', 'value')]
    )
    def update_main_chart(data, current_page, main_variable, selected_years):
        """Met à jour le graphique principal avec effectifs cumulés par catégorie"""
        if current_page != 'Procedures' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Vérifier les données nécessaires
        if 'Year' not in df.columns:
            return html.Div('Column "Year" not available', className='text-warning text-center')
        
        if main_variable is None:
            return html.Div([
                dbc.Alert([
                    html.H6("Selection required", className="mb-2"),
                    html.P("Please select a variable to analyze in the dropdown menu above.", 
                        className="mb-0")
                ], color="info", className="text-center")
            ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'height': '400px'})
        
        if main_variable == 'none' or main_variable not in df.columns:
            return html.Div('Selected variable not available', className='text-warning text-center')
        
        # Filtrer par années
        if selected_years:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return html.Div('No data for the selected years', className='text-warning text-center')
        
        try:
            # Ordre chronologique des années
            year_order = sorted(filtered_df['Year'].unique())
            
            # Obtenir le label pour le titre
            options = get_main_chart_variable_options(df.to_dict('records'))
            variable_label = main_variable
            for option in options:
                if option['value'] == main_variable:
                    variable_label = option['label']
                    break
            
            fig = gr.create_grouped_barplot_with_cumulative_by_category(
                data=filtered_df,
                x_column='Year',
                group_column=main_variable,
                title=f"Evolution and cumulative counts by {variable_label}",
                x_axis_title="Year",
                bar_y_axis_title="Number of patients per year",
                line_y_axis_title="Cumulative count by category",
                custom_x_order=year_order,
                height=480,
                width=None,
                show_bars=True  # Mettre False pour n'avoir que les courbes
            )
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True}
            )
        
        except Exception as e:
            return html.Div(f'Erreur: {str(e)}', className='text-danger text-center')
        
    @app.callback(
        Output('procedures-cmv-charts', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('procedures-year-filter', 'value')]
    )
    def update_cmv_charts(data, current_page, selected_years):
        """Met à jour les pie charts d'analyse du statut CMV"""
        if current_page != 'Procedures' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Filtrer par années si spécifié
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return html.Div('No data for the selected years', className='text-warning text-center')
        
        try:
            # Créer la visualisation CMV
            fig = gr.create_cmv_status_pie_charts(
                data=filtered_df,
                title="CMV status analysis - Donors and Recipients",
                width=None
            )
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%', 'width': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div(f'Erreur: {str(e)}', className='text-danger text-center')
            
    @app.callback(
        Output('procedures-aplasia-tab-content', 'children'),
        [Input('procedures-aplasia-tabs', 'value'),
        Input('data-store', 'data'),
        Input('current-page', 'data'),
        Input('procedures-year-filter', 'value')]
    )
    def update_aplasia_tab_content(active_tab, data, current_page, selected_years):
        """Met à jour le contenu de l'onglet sélectionné pour l'analyse d'aplasie et thrombopénie"""
        if current_page != 'Procedures' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Filtrer par années si spécifié
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return html.Div('No data for the selected years', className='text-warning text-center')
        
        # Initialiser fig à None pour éviter l'erreur
        fig = None
        
        try:
            if active_tab == 'tab-global':
                # Vue globale aplasie
                required_cols = ['Anc Recovery', 'Treatment Date', 'Date Anc Recovery']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    return html.Div([
                        html.P("Missing columns for calculating ANC Recovery duration:", className='text-warning text-center'),
                        html.P(f"Missing columns: {', '.join(missing_cols)}", className='text-muted text-center', style={'fontSize': '10px'})
                    ])
                
                fig = gr.create_histogram_with_density(
                    data=filtered_df,
                    value_column='duree_aplasie',
                    filter_column='Anc Recovery',
                    filter_value='Yes',
                    date_columns=('Treatment Date', 'Date Anc Recovery'),
                    title="Global distribution of ANC Recovery duration",
                    x_axis_title="Days",
                    y_axis_title="Number of patients",
                    bin_size=2,
                    height=400,
                    opacity=0.6,
                    percentile_limit=0.99
                )

            elif active_tab == 'tab-stratified':
                # Vue stratifiée par années aplasie
                required_cols = ['Anc Recovery', 'Treatment Date', 'Date Anc Recovery']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    return html.Div([
                        html.P("Missing columns for calculating ANC Recovery duration:", className='text-warning text-center'),
                        html.P(f"Missing columns: {', '.join(missing_cols)}", className='text-muted text-center', style={'fontSize': '10px'})
                    ])
                
                if 'Year' not in filtered_df.columns:
                    return html.Div([
                        html.P("Missing column 'Year' for stratification", className='text-warning text-center')
                    ])
                
                available_years = sorted(filtered_df['Year'].unique())
                if len(available_years) >= 2:
                    if len(available_years) >= 3:
                        years_to_display = available_years[-3:]
                    else:
                        years_to_display = available_years
                    
                    fig = gr.create_stratified_histogram_with_density(
                        data=filtered_df,
                        value_column='duree_aplasie',
                        stratification_column='Year',
                        filter_column='Anc Recovery',
                        filter_value='Yes',
                        date_columns=('Treatment Date', 'Date Anc Recovery'),
                        selected_strata=years_to_display,
                        max_strata=3,
                        title=f"ANC Recovery duration by year ({', '.join(map(str, years_to_display))})",
                        x_axis_title="Days",
                        y_axis_title="Number of patients",
                        bin_size=2,
                        height=400,
                        opacity=0.6,
                        percentile_limit=0.99
                    )
                else:
                    return html.Div([
                        html.P("Stratification impossible", className='text-warning text-center'),
                        html.P("At least 2 years of data are necessary for comparison", 
                            className='text-muted text-center', style={'fontSize': '12px'})
                    ])

            elif active_tab == 'tab-thrombopenia-global':
                # Vue globale thrombopénie
                required_cols = ['Platelet Reconstitution', 'Treatment Date', 'Date Platelet Reconstitution']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    return html.Div([
                        html.P("Missing columns for calculating thrombocytopenia duration:", className='text-warning text-center'),
                        html.P(f"Missing columns: {', '.join(missing_cols)}", className='text-muted text-center', style={'fontSize': '10px'})
                    ])
                
                fig = gr.create_histogram_with_density(
                    data=filtered_df,
                    value_column='duree_thrombopenie',
                    filter_column='Platelet Reconstitution',
                    filter_value='Yes',
                    date_columns=('Treatment Date', 'Date Platelet Reconstitution'),
                    title="Global distribution of Platelet Reconstitution duration",
                    x_axis_title="Days",
                    y_axis_title="Number of patients",
                    bin_size=2,
                    height=400,
                    color_histogram='#8e44ad',
                    color_density='#e74c3c',
                    percentile_limit=0.99
                )

            elif active_tab == 'tab-thrombopenia-stratified':
                # Vue stratifiée par années thrombopénie
                required_cols = ['Platelet Reconstitution', 'Treatment Date', 'Date Platelet Reconstitution']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    return html.Div([
                        html.P("Missing columns for calculating Platelet Reconstitution duration:", className='text-warning text-center'),
                        html.P(f"Missing columns: {', '.join(missing_cols)}", className='text-muted text-center', style={'fontSize': '10px'})
                    ])
                
                if 'Year' not in filtered_df.columns:
                    return html.Div([
                        html.P("Missing column 'Year' for stratification", className='text-warning text-center')
                    ])
                
                available_years = sorted(filtered_df['Year'].unique())
                if len(available_years) >= 2:
                    if len(available_years) >= 3:
                        years_to_display = available_years[-3:]
                    else:
                        years_to_display = available_years
                    
                    fig = gr.create_stratified_histogram_with_density(
                        data=filtered_df,
                        value_column='duree_thrombopenie',
                        stratification_column='Year',
                        filter_column='Platelet Reconstitution',
                        filter_value='Yes',
                        date_columns=('Treatment Date', 'Date Platelet Reconstitution'),
                        selected_strata=years_to_display,
                        max_strata=3,
                        title=f"Platelet Reconstitution duration by year ({', '.join(map(str, years_to_display))})",
                        x_axis_title="Days",
                        y_axis_title="Number of patients",
                        bin_size=2,
                        height=400,
                        opacity=0.6,
                        percentile_limit=0.99
                    )
                else:
                    return html.Div([
                        html.P("Impossible to stratify", className='text-warning text-center'),
                        html.P("At least 2 years of data are necessary for comparison", 
                            className='text-muted text-center', style={'fontSize': '12px'})
                    ])
            
            # Vérifier si fig a été défini avant de l'utiliser
            if fig is not None:
                return dcc.Graph(
                    figure=fig,
                    style={'height': '100%'},
                    config={'responsive': True, 'displayModeBar': False}
                )
            else:
                return html.Div([
                    html.P("Unrecognized tab or configuration error", className='text-warning text-center'),
                    html.P(f"Current tab received: '{active_tab}'", className='text-muted text-center', style={'fontSize': '10px'})
                ])
        
        except Exception as e:
            return html.Div([
                html.P(f'Error during calculation: {str(e)}', className='text-danger text-center'),
                html.P('Check that the date columns contain valid data', className='text-muted text-center', style={'fontSize': '10px'})
            ])

    
    @app.callback(
        Output('procedures-treatment-content', 'children'),
        [Input('procedures-treatment-tabs', 'value'),
         Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('procedures-year-filter', 'value')]
    )
    def update_treatment_chart(active_tab, data, current_page, selected_years):
        """Met à jour le contenu des onglets de traitement de préparation (barplot ou UpSet)"""
        if current_page != 'Procedures' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Vérifier les données nécessaires
        if 'Year' not in df.columns:
            return html.Div('Column "Year" not available', className='text-warning text-center')
        
        # Colonnes de traitement à analyser (Prep Regimen + TBI)
        treatment_columns = [
            'Prep Regimen Bendamustine',
            'Prep Regimen Busulfan', 
            'Prep Regimen Cyclophosphamide',
            'Prep Regimen Fludarabine',
            'Prep Regimen Melphalan',
            'Prep Regimen Thiotepa',
            'Prep Regimen Treosulfan',
            'TBI'
        ]
        
        # Vérifier quelles colonnes existent
        available_treatment_cols = [col for col in treatment_columns if col in df.columns]
        
        if not available_treatment_cols:
            return html.Div([
                html.P('Treatment columns not available', className='text-warning text-center'),
                html.P('Searched columns:', className='text-muted text-center', style={'fontSize': '10px'}),
                html.P(', '.join(treatment_columns), className='text-muted text-center', style={'fontSize': '8px'})
            ])
        
        # Filtrer par années
        if selected_years:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return html.Div('No data for the selected years', className='text-warning text-center')
        
        try:
            # Standardiser les données : convertir 'Yes'/vide en 'Oui'/'Non'
            df_processed = filtered_df.copy()
            for col in available_treatment_cols:
                df_processed[col] = df_processed[col].apply(
                    lambda x: 'Oui' if x == 'Yes' else 'Non'
                )
            
            if active_tab == 'tab-barplot':
                # Afficher le barplot des proportions
                fig = gr.create_unified_treatment_barplot(
                    data=df_processed,
                    treatment_columns=available_treatment_cols,
                    title="Proportion of patients receiving each conditioning regimen",
                    x_axis_title="Treatment",
                    y_axis_title="Proportion (%)",
                    width=None,
                    show_values=True,
                    remove_prefix="Prep Regimen "  # Supprimer le préfixe pour l'affichage (TBI restera inchangé)
                )
                
                return dcc.Graph(
                    figure=fig,
                    style={'height': '100%'},
                    config={'responsive': True, 'displayModeBar': False}
                )
            else:  # tab-upset
                # Afficher le UpSet plot SVG interactif pour les combinaisons de traitement
                dynamic_height = max(580, 280 + len(available_treatment_cols) * 30)
                
                component_config = upsetjs.create_upsetjs_dash_component(
                    data=df_processed,
                    set_columns=available_treatment_cols,
                    title=f"Conditioning regimen combinations (n={len(df_processed)} patients)",
                    height=dynamic_height,
                    max_combinations=20,
                    min_patients=1,
                    remove_prefix="Prep Regimen "  # Remove prefix for cleaner display
                )
                
                # Create iframe with data URL
                return html.Iframe(
                    src=component_config.get('src'),
                    style={'width': '100%', 'height': f'{dynamic_height}px', 'border': 'none'}
                )
        
        except Exception as e:
            return html.Div(f'Error: {str(e)}', className='text-danger text-center')

    @app.callback(
        Output('procedures-prophylaxis-content', 'children'),
        [Input('procedures-prophylaxis-tabs', 'value'),
         Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('procedures-year-filter', 'value')]
    )
    def update_prophylaxis_chart(active_tab, data, current_page, selected_years):
        """Met à jour le contenu des onglets de prophylaxie (barplot ou UpSet)"""
        if current_page != 'Procedures' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Vérifier les données nécessaires
        if 'Year' not in df.columns:
            return html.Div('Column "Year" not available', className='text-warning text-center')
        
        # Identifier les colonnes de prophylaxie (Oui/Non, excluant les autres variables)
        excluded_prefixes = ['Prep Regimen', 'Age Groups', 'Year', 'Greffes', 'Treatment Date', 
                           'Date Diagnosis', 'Date Of Birth', 'Age At Diagnosis', 'Donor Type', 
                           'Source Stem Cells', 'Main Diagnosis', 'Subclass Diagnosis']
        
        prophylaxis_columns = []
        for col in df.columns:
            # Vérifier si c'est une colonne binaire Oui/Non
            if df[col].isin(['Oui', 'Non']).any():
                # Exclure les colonnes système
                is_excluded = any(col.startswith(prefix) for prefix in excluded_prefixes)
                if not is_excluded:
                    prophylaxis_columns.append(col)
                    
        
        if not prophylaxis_columns:
            return html.Div([
                html.P('Prophylaxis columns not available', className='text-warning text-center'),
                html.P('No prophylaxis data detected in the dataset', className='text-muted text-center', style={'fontSize': '10px'}),
                html.P(f'Available columns: {list(df.columns)[:10]}...', className='text-muted text-center', style={'fontSize': '8px'})
            ])
        
        # Filtrer par années
        if selected_years:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return html.Div('No data for the selected years', className='text-warning text-center')
        
        try:
            if active_tab == 'tab-barplot':
                # Afficher le barplot des proportions
                fig = gr.create_unified_treatment_barplot(
                    data=filtered_df,
                    treatment_columns=prophylaxis_columns,
                    title="Proportion of patients receiving each prophylactic treatment",
                    x_axis_title="Treatment",
                    y_axis_title="Proportion (%)",
                    width=None,
                    show_values=True,
                    remove_prefix=None
                )
                
                return dcc.Graph(
                    figure=fig,
                    style={'height': '100%'},
                    config={'responsive': True, 'displayModeBar': False}
                )
            else:  # tab-upset
                # Afficher le UpSet plot SVG interactif
                dynamic_height = max(580, 280 + len(prophylaxis_columns) * 30)
                
                component_config = upsetjs.create_upsetjs_dash_component(
                    data=filtered_df,
                    set_columns=prophylaxis_columns,
                    title=f"Prophylactic treatment combinations (n={len(filtered_df)} patients)",
                    height=dynamic_height,
                    max_combinations=20,
                    min_patients=1
                )
                
                # Create iframe with data URL
                return html.Iframe(
                    src=component_config.get('src'),
                    style={'width': '100%', 'height': f'{dynamic_height}px', 'border': 'none'}
                )
        
        except Exception as e:
            return html.Div(f'Error: {str(e)}', className='text-danger text-center')
    
    @callback(
        Output('procedures-missing-summary-table', 'children'),
        [Input('data-store', 'data'), Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def procedures_missing_summary_callback(data, current_page):
        """Gère le tableau de résumé des données manquantes pour Procedures"""
        
        if current_page != 'Procedures' or not data:
            return html.Div("Waiting...", className='text-muted')
        
        try:
            df = pd.DataFrame(data)
            
            # Variables spécifiques à analyser pour Procedures
            columns_to_analyze = [
                'Donor Type',
                'Source Stem Cells', 
                'Match Type',
                'Conditioning Regimen Type',
                'Compatibilité HLA',
                'Treatment Date', 
                'Anc Recovery',
                'Date Anc Recovery',
                'Platelet Reconstitution',
                'Date Platelet Reconstitution'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert("No Procedures variable found", color='warning')
            
            # Utiliser la fonction existante de graphs.py
            missing_summary, _ = gr.analyze_missing_data(df, existing_columns, 'Long ID')
            
            return dash_table.DataTable(
                data=missing_summary.to_dict('records'),
                columns=[
                    {"name": "Column", "id": "Column", "type": "text"},
                    {"name": "Total", "id": "Total patients", "type": "numeric"},
                    {"name": "Missing", "id": "Missing data", "type": "numeric"},
                    {"name": "% Missing", "id": "Percentage missing", "type": "numeric", 
                     "format": {"specifier": ".1f"}}
                ],
                style_table={'height': '300px', 'overflowY': 'auto'},
                style_cell={
                    'textAlign': 'center',
                    'padding': '8px',
                    'fontSize': '12px',
                    'fontFamily': 'Arial, sans-serif'
                },
                style_header={
                    'backgroundColor': '#0D3182',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'},
                    {
                        'if': {
                            'filter_query': '{Percentage missing} > 20',
                            'column_id': 'Percentage missing'
                        },
                        'backgroundColor': '#ffebee',
                        'color': 'red',
                        'fontWeight': 'bold'
                    }
                ]
            )
            
        except Exception as e:
            return dbc.Alert(f"Error during analysis: {str(e)}", color='danger')

    @callback(
        [Output('procedures-missing-detail-table', 'children'),
         Output('export-missing-procedures-button', 'disabled')],
        [Input('data-store', 'data'), Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def procedures_missing_detail_callback(data, current_page):
        """Gère le tableau détaillé des patients avec données manquantes pour Procedures"""
        
        if current_page != 'Procedures' or not data:
            return html.Div("Waiting...", className='text-muted'), True
        
        try:
            df = pd.DataFrame(data)
            
            # Variables spécifiques à analyser pour Procedures
            columns_to_analyze = [
                'Donor Type',
                'Source Stem Cells', 
                'Match Type',
                'Conditioning Regimen Type',
                'Compatibilité HLA',
                'Treatment Date', 
                'Anc Recovery',
                'Date Anc Recovery',
                'Platelet Reconstitution',
                'Date Platelet Reconstitution'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert("No Procedures variable found", color='warning'), True
            
            # Utiliser la fonction existante de graphs.py
            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
            
            if detailed_missing.empty:
                return dbc.Alert("No missing data found !", color='success'), True
            
            # Adapter les noms de colonnes pour correspondre au format attendu
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Missing columns': row['Missing columns'],
                    'Nb missing': row['Nb missing']
                })
            
            # Sauvegarder les données pour l'export
            app.server.missing_procedures_data = detailed_data
            
            table_content = html.Div([
                dash_table.DataTable(
                    data=detailed_data,
                    columns=[
                        {"name": "Long ID", "id": "Long ID"},
                        {"name": "Missing variables", "id": "Missing columns"},
                        {"name": "Nb", "id": "Nb missing", "type": "numeric"}
                    ],
                    style_table={'height': '300px', 'overflowY': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '12px'},
                    style_header={'backgroundColor': '#0D3182', 'color': 'white', 'fontWeight': 'bold'},
                    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}],
                    filter_action='native',
                    sort_action='native',
                    page_size=10
                )
            ])
            
            return table_content, False  # Activer le bouton d'export
            
        except Exception as e:
            return dbc.Alert(f"Error during analysis: {str(e)}", color='danger'), True
        
    @callback(
        Output("download-missing-procedures-excel", "data"),
        Input("export-missing-procedures-button", "n_clicks"),
        prevent_initial_call=True
    )
    def export_missing_procedures_excel(n_clicks):
        """Gère l'export csv des patients avec données manquantes pour Procedures"""
        if n_clicks is None:
            return dash.no_update
        
        try:
            # Récupérer les données stockées
            if hasattr(app.server, 'missing_procedures_data') and app.server.missing_procedures_data:
                missing_df = pd.DataFrame(app.server.missing_procedures_data)
                
                # Générer un nom de fichier avec la date
                from datetime import datetime
                current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"procedures_missing_data_{current_date}.xlsx"

                return dcc.send_data_frame(
                    missing_df.to_excel,
                    filename=filename,
                    index=False
                )
            else:
                return dash.no_update
                
        except Exception as e:
            print(f"Error during Excel export Procedures: {e}")
            return dash.no_update
        
def get_prophylaxis_columns(df):
    """
    Fonction utilitaire pour identifier les colonnes de prophylaxie
    
    Args:
        df (pd.DataFrame): DataFrame avec les données
        
    Returns:
        list: Liste des colonnes de prophylaxie
    """
    excluded_prefixes = ['Prep Regimen', 'Age Groups', 'Year', 'Greffes', 'Treatment Date', 
                        'Date Diagnosis', 'Date Of Birth', 'Age At Diagnosis', 'Donor Type', 
                        'Source Stem Cells']
    
    prophylaxis_columns = []
    for col in df.columns:
        # Vérifier si c'est une colonne binaire Oui/Non
        if df[col].isin(['Yes', 'No']).any():
            # Exclure les colonnes système
            is_excluded = any(col.startswith(prefix) for prefix in excluded_prefixes)
            if not is_excluded:
                prophylaxis_columns.append(col)
    
    return prophylaxis_columns