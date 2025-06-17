import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly
import modules.dashboard_layout as layouts
import visualizations.allogreffes.graphs as gr

def get_layout():
    """Retourne le layout de la page Procedures avec graphiques empilés verticalement"""
    return dbc.Container([
        # Premier graphique - Évolution par année avec sélecteur intégré
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5('Évolution par année'),
                        # Sélecteur de variable intégré dans le header
                        html.Div([
                            html.Label('Variable à analyser:', 
                                     style={'fontSize': '12px', 'marginRight': '10px', 'marginBottom': '0'}),
                            dcc.Dropdown(
                                id='procedures-main-variable-integrated',
                                style={'width': '250px', 'fontSize': '12px'},
                                placeholder="Sélectionnez une variable..."
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
                        html.Div(
                            id='procedures-main-chart',
                            style={'height': '500px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),

        # Deuxième graphique - Analyse du statut CMV
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Analyse du statut CMV (Cytomégalovirus)')),
                    dbc.CardBody([
                        html.Div(
                            id='procedures-cmv-charts',
                            style={'height': '450px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),

        # Troisième graphique - Traitements Prophylactiques
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Traitements Prophylactiques')),
                    dbc.CardBody([
                        html.Div(
                            id='procedures-prophylaxis-chart',
                            style={'height': '420px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Quatrième graphique - Traitements de Préparation
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Traitements de Préparation')),
                    dbc.CardBody([
                        html.Div(
                            id='procedures-treatment-chart',
                            style={'height': '420px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Cinquième section - Durée d'aplasie et thrombopénie avec onglets
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Analyse de la durée d'aplasie")),
                    dbc.CardBody([
                        dcc.Tabs(
                            id='procedures-aplasia-tabs',
                            value='tab-global',
                            children=[
                                dcc.Tab(label='Aplasie - Vue globale', value='tab-global'),
                                dcc.Tab(label='Aplasie - Par années', value='tab-stratified'),
                                dcc.Tab(label='Thrombopénie - Vue globale', value='tab-thrombopenie-global'),
                                dcc.Tab(label='Thrombopénie - Par années', value='tab-thrombopenie-stratified')
                            ]
                        ),
                        html.Div(
                            id='procedures-aplasia-tab-content',
                            style={'marginTop': '20px'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ])
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
        return [{'label': 'Aucune donnée disponible', 'value': 'none'}]
    
    # Convertir la liste en DataFrame
    df = pd.DataFrame(data)
    
    # Variables disponibles pour le graphique principal
    main_chart_options = []
    
    # Vérifier les colonnes disponibles (ordre de priorité)
    possible_columns = {
        'Donor Type': 'Type de donneur',
        'Source Stem Cells': 'Source des cellules souches', 
        'Match Type': 'Type de compatibilité',
        'Conditioning Regimen Type': 'Type de conditionnement',
        'Compatibilité HLA': 'Compatibilité HLA'
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
            return [{'label': 'Chargement...', 'value': 'loading'}], None
        
        options = get_main_chart_variable_options(data)

        # Sélectionner la première option valide par défaut
        default_value = None
        if options and len(options) > 0:
            # Prendre la première option qui n'est pas 'none', 'loading' ou 'Aucune variable disponible'
            for option in options:
                if option['value'] not in ['none', 'loading'] and 'Aucune' not in option['label']:
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
            return html.Div('Colonne "Year" non disponible', className='text-warning text-center')
        
        if main_variable is None:
            return html.Div([
                dbc.Alert([
                    html.H6("Sélection requise", className="mb-2"),
                    html.P("Veuillez sélectionner une variable à analyser dans le menu déroulant ci-dessus.", 
                        className="mb-0")
                ], color="info", className="text-center")
            ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'height': '400px'})
        
        if main_variable == 'none' or main_variable not in df.columns:
            return html.Div('Variable sélectionnée non disponible', className='text-warning text-center')
        
        # Filtrer par années
        if selected_years:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return html.Div('Aucune donnée pour les années sélectionnées', className='text-warning text-center')
        
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
                title=f"Évolution et effectifs cumulés par {variable_label}",
                x_axis_title="Année",
                bar_y_axis_title="Nombre de patients par année",
                line_y_axis_title="Effectif cumulé par catégorie",
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
            return html.Div('Aucune donnée pour les années sélectionnées', className='text-warning text-center')
        
        try:
            # Créer la visualisation CMV
            fig = gr.create_cmv_status_pie_charts(
                data=filtered_df,
                title="Analyse du statut CMV - Donneurs et Receveurs",
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
            return html.Div('Aucune donnée pour les années sélectionnées', className='text-warning text-center')
        
        try:
            if active_tab == 'tab-global':
                # Vue globale aplasie
                required_cols = ['Anc Recovery', 'Treatment Date', 'Date Anc Recovery']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    return html.Div([
                        html.P("Colonnes manquantes pour calculer la durée d'aplasie:", className='text-warning text-center'),
                        html.P(f"Colonnes manquantes: {', '.join(missing_cols)}", className='text-muted text-center', style={'fontSize': '10px'})
                    ])
                
                fig = gr.create_histogram_with_density(
                    data=filtered_df,
                    value_column='duree_aplasie',
                    filter_column='Anc Recovery',
                    filter_value='Yes',
                    date_columns=('Treatment Date', 'Date Anc Recovery'),
                    title="Distribution globale de la durée d'aplasie",
                    x_axis_title="Jours",
                    y_axis_title="Nombre de patients",
                    bin_size=2,
                    height=400,
                    color_histogram='#27BDBE',
                    color_density='#FF6B6B',
                    percentile_limit=0.99
                )
                    
            elif active_tab == 'tab-stratified':
                # Vue stratifiée par années aplasie
                required_cols = ['Anc Recovery', 'Treatment Date', 'Date Anc Recovery']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    return html.Div([
                        html.P("Colonnes manquantes pour calculer la durée d'aplasie:", className='text-warning text-center'),
                        html.P(f"Colonnes manquantes: {', '.join(missing_cols)}", className='text-muted text-center', style={'fontSize': '10px'})
                    ])
                
                if 'Year' not in filtered_df.columns:
                    return html.Div([
                        html.P("Colonne 'Year' manquante pour la stratification", className='text-warning text-center')
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
                        title=f"Durée d'aplasie par année ({', '.join(map(str, years_to_display))})",
                        x_axis_title="Jours",
                        y_axis_title="Nombre de patients",
                        bin_size=2,
                        height=400,
                        opacity=0.6,
                        percentile_limit=0.99
                    )
                else:
                    return html.Div([
                        html.P("Stratification impossible", className='text-warning text-center'),
                        html.P("Au moins 2 années de données sont nécessaires pour la comparaison", 
                            className='text-muted text-center', style={'fontSize': '12px'})
                    ])

            elif active_tab == 'tab-thrombopenie-global':
                # Vue globale thrombopénie
                required_cols = ['Platelet Reconstitution', 'Treatment Date', 'Date Platelet Reconstitution']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    return html.Div([
                        html.P("Colonnes manquantes pour calculer la durée de thrombopénie:", className='text-warning text-center'),
                        html.P(f"Colonnes manquantes: {', '.join(missing_cols)}", className='text-muted text-center', style={'fontSize': '10px'})
                    ])
                
                fig = gr.create_histogram_with_density(
                    data=filtered_df,
                    value_column='duree_thrombopenie',
                    filter_column='Platelet Reconstitution',
                    filter_value='Yes',
                    date_columns=('Treatment Date', 'Date Platelet Reconstitution'),
                    title="Distribution globale de la durée de thrombopénie",
                    x_axis_title="Jours",
                    y_axis_title="Nombre de patients",
                    bin_size=2,
                    height=400,
                    color_histogram='#8e44ad',
                    color_density='#e74c3c',
                    percentile_limit=0.99
                )

            elif active_tab == 'tab-thrombopenie-stratified':
                # Vue stratifiée par années thrombopénie
                required_cols = ['Platelet Reconstitution', 'Treatment Date', 'Date Platelet Reconstitution']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    return html.Div([
                        html.P("Colonnes manquantes pour calculer la durée de thrombopénie:", className='text-warning text-center'),
                        html.P(f"Colonnes manquantes: {', '.join(missing_cols)}", className='text-muted text-center', style={'fontSize': '10px'})
                    ])
                
                if 'Year' not in filtered_df.columns:
                    return html.Div([
                        html.P("Colonne 'Year' manquante pour la stratification", className='text-warning text-center')
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
                        title=f"Durée de thrombopénie par année ({', '.join(map(str, years_to_display))})",
                        x_axis_title="Jours",
                        y_axis_title="Nombre de patients",
                        bin_size=2,
                        height=400,
                        opacity=0.6,
                        percentile_limit=0.99
                    )
                else:
                    return html.Div([
                        html.P("Stratification impossible", className='text-warning text-center'),
                        html.P("Au moins 2 années de données sont nécessaires pour la comparaison", 
                            className='text-muted text-center', style={'fontSize': '12px'})
                    ])
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div([
                html.P(f'Erreur lors du calcul: {str(e)}', className='text-danger text-center'),
                html.P('Vérifiez que les colonnes de dates contiennent des données valides', className='text-muted text-center', style={'fontSize': '10px'})
            ])
    
    @app.callback(
        Output('procedures-treatment-chart', 'children'),
        [Input('data-store', 'data'),
        Input('current-page', 'data'),
        Input('procedures-year-filter', 'value')]
    )
    def update_treatment_chart(data, current_page, selected_years):
        """Met à jour le graphique des proportions de traitement de préparation avec barres empilées Oui/Non"""
        if current_page != 'Procedures' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Vérifier les données nécessaires
        if 'Year' not in df.columns:
            return html.Div('Colonne "Year" non disponible', className='text-warning text-center')
        
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
                html.P('Colonnes de traitement non disponibles', className='text-warning text-center'),
                html.P('Colonnes recherchées:', className='text-muted text-center', style={'fontSize': '10px'}),
                html.P(', '.join(treatment_columns), className='text-muted text-center', style={'fontSize': '8px'})
            ])
        
        # Filtrer par années
        if selected_years:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return html.Div('Aucune donnée pour les années sélectionnées', className='text-warning text-center')
        
        try:
            # Standardiser les données : convertir 'Yes'/vide en 'Oui'/'Non'
            df_processed = filtered_df.copy()
            for col in available_treatment_cols:
                df_processed[col] = df_processed[col].apply(
                    lambda x: 'Oui' if x == 'Yes' else 'Non'
                )
            
            # Utiliser la fonction unifiée
            fig = gr.create_unified_treatment_barplot(
                data=df_processed,
                treatment_columns=available_treatment_cols,
                title="Proportion de patients ayant reçu chaque traitement de préparation",
                x_axis_title="Traitement",
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
        
        except Exception as e:
            return html.Div(f'Erreur: {str(e)}', className='text-danger text-center')

    @app.callback(
        Output('procedures-prophylaxis-chart', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('procedures-year-filter', 'value')]
    )
    def update_prophylaxis_chart(data, current_page, selected_years):
        """Met à jour le graphique des proportions de prophylaxie avec style unifié"""
        if current_page != 'Procedures' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Vérifier les données nécessaires
        if 'Year' not in df.columns:
            return html.Div('Colonne "Year" non disponible', className='text-warning text-center')
        
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
                html.P('Colonnes de prophylaxie non disponibles', className='text-warning text-center'),
                html.P('Aucune donnée de prophylaxie détectée dans le dataset', className='text-muted text-center', style={'fontSize': '10px'}),
                html.P(f'Colonnes disponibles : {list(df.columns)[:10]}...', className='text-muted text-center', style={'fontSize': '8px'})
            ])
        
        # Filtrer par années
        if selected_years:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return html.Div('Aucune donnée pour les années sélectionnées', className='text-warning text-center')
        
        try:
            # Utiliser la fonction unifiée (les données sont déjà en format Oui/Non)
            fig = gr.create_unified_treatment_barplot(
                data=filtered_df,
                treatment_columns=prophylaxis_columns,
                title="Proportion de patients ayant reçu chaque traitement prophylactique",
                x_axis_title="Traitement",
                y_axis_title="Proportion (%)",
                width=None,
                show_values=True,
                remove_prefix=None  # Pas de préfixe à supprimer pour la prophylaxie
            )
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div(f'Erreur: {str(e)}', className='text-danger text-center')

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
        if df[col].isin(['Oui', 'Non']).any():
            # Exclure les colonnes système
            is_excluded = any(col.startswith(prefix) for prefix in excluded_prefixes)
            if not is_excluded:
                prophylaxis_columns.append(col)
    
    return prophylaxis_columns

    