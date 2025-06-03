import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd

# Import des modules communs
import modules.dashboard_layout as layouts
import visualizations.allogreffes.graphs as gr

def get_layout():
    """Retourne le layout de la page Procedures avec graphiques empilés verticalement"""
    return dbc.Container([
        # Premier graphique - Évolution par année
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Évolution par année')),
                    dbc.CardBody([
                        html.Div(
                            id='procedures-main-chart',
                            style={'height': '500px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Deuxième graphique - Traitements Prophylactiques
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
        
        # Troisième graphique - Traitements de Préparation
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
        
        # Quatrième graphique - Durée d'aplasie (vue globale)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Durée d'aplasie - Vue d'ensemble")),
                    dbc.CardBody([
                        html.Div(
                            id='procedures-aplasia-duration-chart',
                            style={'height': '420px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Cinquième graphique - Durée d'aplasie stratifiée par années
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Durée d'aplasie - Comparaison avec années n-1 et n-2")),
                    dbc.CardBody([
                        html.Div(
                            id='procedures-aplasia-duration-stratified-chart',
                            style={'height': '420px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ])
    ], fluid=True)

def register_callbacks(app):
    """Enregistre tous les callbacks spécifiques à la page Procedures"""
    
    @app.callback(
        Output('procedures-main-chart', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('procedures-main-variable', 'value'),
         Input('procedures-year-filter', 'value')]
    )
    def update_main_chart(data, current_page, main_variable, selected_years):
        """Met à jour le graphique principal avec barres groupées et cumul"""
        if current_page != 'Procedures' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Vérifier les données nécessaires
        if 'Year' not in df.columns:
            return html.Div('Colonne "Year" non disponible', className='text-warning text-center')
        
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
            
            # Cas spécial pour "Greffes" : graphique simple avec cumul (pas de groupement)
            if main_variable == 'Greffes':
                fig = gr.create_cumulative_barplot(
                    data=filtered_df,
                    category_column='Year',
                    title="Nombre de greffes par année",
                    x_axis_title="Année",
                    bar_y_axis_title="Nombre de greffes",
                    line_y_axis_title="Effectif cumulé",
                    custom_order=year_order,
                    height=480,  # Ajusté pour le nouveau layout
                    width=None
                )
            else:
                # Autres variables : graphique groupé avec cumul
                fig = gr.create_grouped_barplot_with_cumulative(
                    data=filtered_df,
                    x_column='Year',
                    group_column=main_variable,
                    title=f"Évolution par année selon {main_variable}",
                    x_axis_title="Année",
                    bar_y_axis_title="Nombre de patients",
                    line_y_axis_title="Effectif cumulé",
                    custom_x_order=year_order,
                    height=480,  # Ajusté pour le nouveau layout
                    width=None
                )
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True}
            )
        
        except Exception as e:
            return html.Div(f'Erreur: {str(e)}', className='text-danger text-center')

    @app.callback(
        Output('procedures-aplasia-duration-chart', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('procedures-year-filter', 'value')]
    )
    def update_aplasia_duration_chart(data, current_page, selected_years):
        """Met à jour le graphique de la durée d'aplasie"""
        if current_page != 'Procedures' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Vérifier les colonnes nécessaires pour la durée d'aplasie
        required_cols = ['Anc Recovery', 'Treatment Date', 'Date Anc Recovery']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return html.Div([
                html.P("Colonnes manquantes pour calculer la durée d'aplasie:", className='text-warning text-center'),
                html.P(f"Colonnes requises: {', '.join(required_cols)}", className='text-muted text-center', style={'fontSize': '10px'}),
                html.P(f"Colonnes manquantes: {', '.join(missing_cols)}", className='text-muted text-center', style={'fontSize': '10px'})
            ])
        
        # Filtrer par années si spécifié
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return html.Div('Aucune donnée pour les années sélectionnées', className='text-warning text-center')
        
        try:
            # Créer l'histogramme simple avec densité pour la durée d'aplasie (vue globale)
            fig = gr.create_histogram_with_density(
                data=filtered_df,
                value_column='duree_aplasie',  # Nom temporaire, sera calculé
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
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div([
                html.P(f'Erreur lors du calcul de la durée d\'aplasie: {str(e)}', className='text-danger text-center'),
                html.P('Vérifiez que les colonnes de dates contiennent des données valides', className='text-muted text-center', style={'fontSize': '10px'})
            ])

    @app.callback(
        Output('procedures-aplasia-duration-stratified-chart', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('procedures-year-filter', 'value')]
    )
    def update_aplasia_duration_stratified_chart(data, current_page, selected_years):
        """Met à jour le graphique stratifié de la durée d'aplasie par années"""
        if current_page != 'Procedures' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Vérifier les colonnes nécessaires pour la durée d'aplasie
        required_cols = ['Anc Recovery', 'Treatment Date', 'Date Anc Recovery', 'Year']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return html.Div([
                html.P("Colonnes manquantes pour la stratification par années:", className='text-warning text-center'),
                html.P(f"Colonnes requises: {', '.join(required_cols)}", className='text-muted text-center', style={'fontSize': '10px'}),
                html.P(f"Colonnes manquantes: {', '.join(missing_cols)}", className='text-muted text-center', style={'fontSize': '10px'})
            ])
        
        # Filtrer par années si spécifié
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return html.Div('Aucune donnée pour les années sélectionnées', className='text-warning text-center')
        
        try:
            # Déterminer les années à afficher (3 dernières années disponibles)
            available_years = sorted(filtered_df['Year'].unique())
            if len(available_years) >= 2:  # Au moins 2 années pour que la stratification ait du sens
                if len(available_years) >= 3:
                    # Prendre les 3 dernières années
                    years_to_display = available_years[-3:]
                else:
                    # Prendre toutes les années disponibles
                    years_to_display = available_years
                
                # Créer l'histogramme stratifié par année
                fig = gr.create_stratified_histogram_with_density(
                    data=filtered_df,
                    value_column='duree_aplasie',  # Nom temporaire, sera calculé
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
                # Une seule année ou pas assez de données pour stratifier
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
                html.P(f'Erreur lors du calcul de la durée d\'aplasie: {str(e)}', className='text-danger text-center'),
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
        
        # Colonnes de traitement à analyser (Prep Regimen)
        treatment_columns = [
            'Prep Regimen Bendamustine',
            'Prep Regimen Busulfan', 
            'Prep Regimen Cyclophosphamide',
            'Prep Regimen Fludarabine',
            'Prep Regimen Melphalan',
            'Prep Regimen Thiotepa',
            'Prep Regimen Treosulfan'
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
            
            # Utiliser la fonction pour créer un graphique avec barres empilées Oui/Non
            # Si cette fonction n'existe pas, il faudra l'adapter ou en créer une nouvelle
            fig = gr.create_stacked_yes_no_barplot(
                data=df_processed,
                treatment_columns=available_treatment_cols,
                title="Proportion de patients ayant reçu chaque traitement de préparation",
                x_axis_title="Traitement",
                y_axis_title="Proportion (%)",
                height=230,  # Ajusté pour le layout
                width=None,
                show_values=True
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
        """Met à jour le graphique des proportions de prophylaxie"""
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
        
        print(f"Colonnes de prophylaxie détectées : {prophylaxis_columns}")  # Debug
        
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
            # Créer le graphique des proportions de prophylaxie par traitement
            fig = gr.create_prophylaxis_treatments_barplot(
                data=filtered_df,
                prophylaxis_columns=prophylaxis_columns,
                title="Proportion de patients ayant reçu chaque traitement prophylactique",
                x_axis_title="Traitement",
                y_axis_title="Proportion (%)",
                height=400,  # Ajusté pour le nouveau layout
                width=None,
                show_values=True
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