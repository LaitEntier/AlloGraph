# pages/patients.py
import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import des modules communs
import modules.dashboard_layout as layouts
import visualizations.allogreffes.graphs as gr

def get_layout():
    """Retourne le layout de la page Patients avec graphiques empilés verticalement"""
    return dbc.Container([
        # Graphique 1: Barplot normalisé à 100%
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    #dbc.CardHeader(html.H5('Distribution normalisée à 100%')),
                    dbc.CardBody([
                        html.Div(
                            id='patients-normalized-chart',
                            style={'height': '450px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Graphique 2: Barplot distribution
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    #dbc.CardHeader(html.H5('Distribution des effectifs')),
                    dbc.CardBody([
                        html.Div(
                            id='patients-distribution-chart',
                            style={'height': '450px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Graphique 3: Boxplot
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    #dbc.CardHeader(html.H5('Boxplot - Age At Diagnosis')),
                    dbc.CardBody([
                        html.Div(
                            id='patients-boxplot-chart',
                            style={'height': '450px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
            # Graphique 4: DataTable avec bouton d'export
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H5('Statistiques par année', className='mb-0')
                            ], width=8),
                            dbc.Col([
                                dbc.Button(
                                    [html.I(className="fas fa-download me-2"), "Export CSV"],
                                    id="export-csv-button",
                                    color="primary",
                                    size="sm",
                                    disabled=False,  # Désactivé par défaut
                                    className="float-end"
                                )
                            ], width=4, className="d-flex justify-content-end align-items-center")
                        ])
                    ]),
                    dbc.CardBody([
                        html.Div(
                            id='patients-datatable',
                            style={'height': '450px', 'overflow': 'auto'}
                        ),
                        # Composant pour télécharger le CSV (invisible)
                        dcc.Download(id="download-csv")
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),

        # Graphique 5: Performance Scores par Age Groups
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Performance Scores par tranche d\'âge')),
                    dbc.CardBody([
                        html.Div(
                            id='patients-performance-scores-boxplot',
                            style={'height': '500px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),

        dbc.Row([
            # Tableau 1 - Résumé des colonnes
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Résumé par colonne", className='mb-0')),
                    dbc.CardBody([
                        html.Div(id='patients-missing-summary-table', children=[
                            dbc.Alert("Contenu initial - sera remplacé par le callback", color='warning')
                        ])
                    ])
                ])
            ], width=6),
            
            # Tableau 2 - Patients concernés  
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H5("Patients concernés", className='mb-0'),
                            dbc.Button(
                                [html.I(className="fas fa-download me-2"), "Export CSV"],
                                id="export-missing-patients-button",
                                color="primary",
                                size="sm",
                                disabled=True,  # Désactivé par défaut
                            )
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody([
                        html.Div(id='patients-missing-detail-table', children=[
                            dbc.Alert("Contenu initial - sera remplacé par le callback", color='warning')
                        ]),
                        # Composant pour télécharger le fichier Excel (invisible)
                        dcc.Download(id="download-missing-patients-excel")
                    ])
                ])
            ], width=6)
        ])
    ], fluid=True)

def register_callbacks(app):
    """Enregistre tous les callbacks spécifiques à la page Patients"""
    
    def create_color_map(data, color_column):
        """Crée un mapping de couleurs cohérent pour une variable"""
        if color_column not in data.columns:
            return {}
        
        # Obtenir les catégories uniques en filtrant les valeurs nulles
        categories = data[color_column].dropna().unique()
        # Trier seulement les valeurs non-nulles
        categories = sorted([cat for cat in categories if pd.notna(cat)])
        
        # Utiliser la même palette que Plotly
        colors = px.colors.qualitative.Safe
        
        # Créer le mapping
        color_map = {}
        for i, category in enumerate(categories):
            color_map[category] = colors[i % len(colors)]
        
        return color_map
    
    @app.callback(
        Output('patients-normalized-chart', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('x-axis-dropdown', 'value'),
         Input('stack-variable-dropdown', 'value'),
         Input('year-filter-checklist', 'value')]
    )
    def update_normalized_chart(data, current_page, x_axis, stack_var, selected_years):
        """Graphique 1: Barplot normalisé à 100%"""
        if current_page != 'Patients' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Valeurs par défaut
        if x_axis is None:
            x_axis = 'Age Groups'  # Valeur par défaut modifiée
        
        if stack_var is None:
            stack_var = 'Main Diagnosis'  # Valeur par défaut modifiée
        
        # Filtrer les données
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return dbc.Alert('Aucune donnée disponible avec les filtres sélectionnés', color='warning')
        
        try:
            if x_axis not in filtered_df.columns:
                return dbc.Alert(f'Colonne "{x_axis}" non trouvée dans les données', color='warning')
            
            stack_col = None if stack_var == 'Aucune' else stack_var
            
            # Choisir la fonction appropriée selon la variable de stratification
            if stack_col is None or stack_col not in filtered_df.columns:
                # Pas de stratification : barplot simple normalisé à 100%
                # Définir l'ordre personnalisé pour Age Groups
                order = None
                if x_axis == 'Age Groups':
                    order = ['18-', '18-39', '40-64', '65-74', '75+']
                
                fig = gr.create_simple_normalized_barplot(
                    data=filtered_df,
                    x_column=x_axis,
                    title=f"Distribution par {x_axis} - Sélectionnez une variable de stratification",
                    x_axis_title=x_axis,
                    y_axis_title="Proportion (%)",
                    custom_order=order,
                    height=420,
                    width=None
                )
            else:
                # Avec stratification : barplot stacké normalisé
                # Définir l'ordre personnalisé pour Age Groups
                order = None
                if x_axis == 'Age Groups':
                    order = ['18-', '18-39', '40-64', '65-74', '75+']
                
                # Créer un mapping de couleurs cohérent
                color_map = create_color_map(filtered_df, stack_col)
                
                fig = gr.create_normalized_barplot(
                    data=filtered_df,
                    x_column=x_axis,
                    y_column='Count',
                    stack_column=stack_col,
                    title=f"Distribution normalisée par {x_axis} et {stack_col}",
                    x_axis_title=x_axis,
                    y_axis_title="Proportion (%)",
                    custom_order=order,
                    height=420,
                    width=None,
                    color_map=color_map  # ← Utiliser le mapping cohérent
                )
            
            return dcc.Graph(
                figure=fig, 
                style={'height': '100%'},
                config={'responsive': True}
            )
        except Exception as e:
            return dbc.Alert(f'Erreur: {str(e)}', color='danger')

    @app.callback(
        Output('patients-distribution-chart', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('x-axis-dropdown', 'value'),
         Input('stack-variable-dropdown', 'value'),
         Input('year-filter-checklist', 'value')]
    )
    def update_distribution_chart(data, current_page, x_axis, stack_var, selected_years):
        """Graphique 2: Barplot distribution"""
        if current_page != 'Patients' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Valeurs par défaut
        if x_axis is None:
            x_axis = 'Age Groups'  # Valeur par défaut modifiée
        
        if stack_var is None:
            stack_var = 'Main Diagnosis'  # Valeur par défaut modifiée
        
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
            
            # Choisir la fonction appropriée selon la variable de stratification
            if stack_col is None or stack_col not in filtered_df.columns:
                # Pas de stratification : barplot simple
                # Définir l'ordre personnalisé pour Age Groups
                order = None
                if x_axis == 'Age Groups':
                    order = ['18-', '18-39', '40-64', '65-74', '75+']
                
                fig = gr.create_simple_barplot(
                    data=filtered_df,
                    x_column=x_axis,
                    title=f"Distribution par {x_axis}",
                    x_axis_title=x_axis,
                    y_axis_title="Nombre de greffes",
                    custom_order=order,
                    height=420,
                    width=None
                )
            else:
                # Avec stratification : barplot stacké
                # Définir l'ordre personnalisé pour Age Groups
                order = None
                if x_axis == 'Age Groups':
                    order = ['18-', '18-39', '40-64', '65-74', '75+']
                
                # Créer un mapping de couleurs cohérent
                color_map = create_color_map(filtered_df, stack_col)
                
                fig = gr.create_stacked_barplot(
                    data=filtered_df,
                    x_column=x_axis,
                    y_column='Count',
                    stack_column=stack_col,
                    title=f"Distribution par {x_axis} et {stack_col}",
                    x_axis_title=x_axis,
                    y_axis_title="Nombre de greffes",
                    custom_order=order,
                    height=420,
                    width=None,
                    color_map=color_map  # ← Utiliser le mapping cohérent
                )
            
            return dcc.Graph(
                figure=fig, 
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div(f'Erreur: {str(e)}', className='text-danger')

    @app.callback(
        Output('patients-boxplot-chart', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('x-axis-dropdown', 'value'),
         Input('stack-variable-dropdown', 'value'),
         Input('year-filter-checklist', 'value')]
    )
    def update_boxplot_chart(data, current_page, x_axis, stack_var, selected_years):
        """Graphique 3: Boxplot Age At Diagnosis par variable de stratification"""
        if current_page != 'Patients' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Valeurs par défaut
        if stack_var is None:
            stack_var = 'Main Diagnosis'  # Valeur par défaut modifiée
        
        # Vérifier si une variable de stratification est sélectionnée
        if stack_var == 'Aucune':
            return html.Div([
                dbc.Alert([
                    html.H6("📊 Sélection requise", className="mb-2"),
                    html.P("Veuillez sélectionner une variable de stratification dans la sidebar pour afficher le boxplot.", 
                           className="mb-0")
                ], color="info", className="text-center")
            ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'height': '100%'})
        
        # Filtrer les données
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            return html.Div('Aucune donnée disponible', className='text-warning text-center')
        
        try:
            # Vérifier que la variable de stratification existe dans les données
            if stack_var not in filtered_df.columns:
                return html.Div(f'Variable "{stack_var}" non trouvée dans les données', className='text-warning text-center')
            
            # Créer un mapping de couleurs cohérent avec les autres graphiques
            color_map = create_color_map(filtered_df, stack_var)
            
            # Créer le boxplot Age At Diagnosis par variable de stratification
            fig = gr.create_enhanced_boxplot(
                data=filtered_df,
                x_column=stack_var,
                y_column='Age At Diagnosis',
                color_column=stack_var,  # Utiliser la même variable pour colorer chaque box
                title=f"Boxplot Age At Diagnosis par {stack_var}",
                x_axis_title=stack_var,
                y_axis_title='Age At Diagnosis',
                height=420,
                width=None,
                show_points=True,
                point_size=4,
                color_map=color_map  # Passer le mapping de couleurs à la fonction
            )
            
            return dcc.Graph(
                figure=fig, 
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div(f'Erreur: {str(e)}', className='text-danger')

    @app.callback(
        [Output('patients-datatable', 'children'),
        Output('export-csv-button', 'disabled')],
        [Input('data-store', 'data'),
        Input('current-page', 'data'),
        Input('year-filter-checklist', 'value')]
    )
    def update_datatable(data, current_page, selected_years):
        """Graphique 4: DataTable avec statistiques par année incluant la répartition par sexe"""
        if current_page != 'Patients' or data is None:
            return html.Div(), True
        
        df = pd.DataFrame(data)
        
        # Créer la table de statistiques par année
        required_cols = ['Year', 'Age At Diagnosis', 'Sex']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return dbc.Alert(f'Colonnes manquantes: {", ".join(missing_cols)}', color='warning')
        
        # Calculer les statistiques par année
        stats_by_year = []
        
        # Filtrer selon les années sélectionnées
        if selected_years:
            years_to_process = selected_years
        else:
            years_to_process = sorted(df['Year'].unique())
        
        # Calculer les stats pour chaque année
        for year in years_to_process:
            year_data = df[df['Year'] == year]
            age_data = year_data['Age At Diagnosis']
            sex_data = year_data['Sex']
            
            if len(year_data) > 0:
                # Statistiques d'âge
                age_stats = {
                    'Age moyen': round(age_data.mean(), 1) if len(age_data) > 0 else 0,
                    'Age médian': round(age_data.median(), 1) if len(age_data) > 0 else 0,
                    'Age Q1': round(age_data.quantile(0.25), 1) if len(age_data) > 0 else 0,
                    'Age Q3': round(age_data.quantile(0.75), 1) if len(age_data) > 0 else 0,
                    'Age minimum': int(age_data.min()) if len(age_data) > 0 else 0,
                    'Age maximum': int(age_data.max()) if len(age_data) > 0 else 0,
                }
                
                # Statistiques de sexe
                sex_counts = sex_data.value_counts()
                total_patients = len(year_data)
                
                male_count = sex_counts.get('male', 0)
                female_count = sex_counts.get('female', 0)
                unknown_count = total_patients - male_count - female_count
                
                male_percent = (male_count / total_patients * 100) if total_patients > 0 else 0
                female_percent = (female_count / total_patients * 100) if total_patients > 0 else 0
                unknown_percent = (unknown_count / total_patients * 100) if total_patients > 0 else 0
                
                # Combiner toutes les statistiques
                year_stats = {
                    'Année': year,
                    **age_stats,
                    'Effectif total': total_patients,
                    'Hommes (n)': male_count,
                    'Hommes (%)': round(male_percent, 1),
                    'Femmes (n)': female_count,
                    'Femmes (%)': round(female_percent, 1)
                }
                
                # Ajouter les données inconnues seulement si il y en a
                if unknown_count > 0:
                    year_stats['Sexe inconnu (n)'] = unknown_count
                    year_stats['Sexe inconnu (%)'] = round(unknown_percent, 1)
                
                stats_by_year.append(year_stats)
        
        # Calculer la ligne 'Total' pour toutes les années sélectionnées
        if stats_by_year:
            all_data = df[df['Year'].isin(years_to_process)]
            all_ages = all_data['Age At Diagnosis']
            all_sex = all_data['Sex']
            
            if len(all_data) > 0:
                # Statistiques d'âge totales
                total_age_stats = {
                    'Age moyen': round(all_ages.mean(), 1),
                    'Age médian': round(all_ages.median(), 1),
                    'Age Q1': round(all_ages.quantile(0.25), 1),
                    'Age Q3': round(all_ages.quantile(0.75), 1),
                    'Age minimum': int(all_ages.min()),
                    'Age maximum': int(all_ages.max()),
                }
                
                # Statistiques de sexe totales
                total_sex_counts = all_sex.value_counts()
                total_all_patients = len(all_data)
                
                total_male_count = total_sex_counts.get('male', 0)
                total_female_count = total_sex_counts.get('female', 0)
                total_unknown_count = total_all_patients - total_male_count - total_female_count
                
                total_male_percent = (total_male_count / total_all_patients * 100)
                total_female_percent = (total_female_count / total_all_patients * 100)
                total_unknown_percent = (total_unknown_count / total_all_patients * 100)
                
                # Ligne total
                total_row = {
                    'Année': 'TOTAL',
                    **total_age_stats,
                    'Effectif total': total_all_patients,
                    'Hommes (n)': total_male_count,
                    'Hommes (%)': round(total_male_percent, 1),
                    'Femmes (n)': total_female_count,
                    'Femmes (%)': round(total_female_percent, 1)
                }
                
                # Ajouter les données inconnues seulement si il y en a
                if total_unknown_count > 0:
                    total_row['Sexe inconnu (n)'] = total_unknown_count
                    total_row['Sexe inconnu (%)'] = round(total_unknown_percent, 1)
                
                stats_by_year.append(total_row)
        
        if not stats_by_year:
            return dbc.Alert('Aucune donnée disponible pour les années sélectionnées', color='info')
        
        # Déterminer les colonnes selon la présence de données inconnues
        has_unknown = any('Sexe inconnu (n)' in row for row in stats_by_year)
        
        # Définir les colonnes
        base_columns = [
            {"name": "Année", "id": "Année", "type": "text"},
            {"name": "Age moyen", "id": "Age moyen", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Age médian", "id": "Age médian", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Age Q1", "id": "Age Q1", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Age Q3", "id": "Age Q3", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Age minimum", "id": "Age minimum", "type": "numeric"},
            {"name": "Age maximum", "id": "Age maximum", "type": "numeric"},
            {"name": "Effectif total", "id": "Effectif total", "type": "numeric"},
            {"name": "Hommes (n)", "id": "Hommes (n)", "type": "numeric"},
            {"name": "Hommes (%)", "id": "Hommes (%)", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Femmes (n)", "id": "Femmes (n)", "type": "numeric"},
            {"name": "Femmes (%)", "id": "Femmes (%)", "type": "numeric", "format": {"specifier": ".1f"}}
        ]
        
        # Ajouter les colonnes pour les données inconnues si nécessaire
        if has_unknown:
            base_columns.extend([
                {"name": "Sexe inconnu (n)", "id": "Sexe inconnu (n)", "type": "numeric"},
                {"name": "Sexe inconnu (%)", "id": "Sexe inconnu (%)", "type": "numeric", "format": {"specifier": ".1f"}}
            ])
        
        app.server.stats_data = stats_by_year

        # Créer la DataTable
        return html.Div([
            dash_table.DataTable(
                data=stats_by_year,
                columns=base_columns,
                style_table={'height': '400px', 'overflowY': 'auto', 'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'center',
                    'padding': '8px',
                    'fontFamily': 'Arial, sans-serif',
                    'fontSize': '11px',
                    'minWidth': '60px'
                },
                style_header={
                    'backgroundColor': '#0D3182', 
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'fontSize': '10px'
                },
                style_data_conditional=[
                    {
                        # Mise en évidence de la ligne TOTAL
                        'if': {'filter_query': '{Année} = TOTAL'},
                        'backgroundColor': '#e6f3ff',
                        'fontWeight': 'bold',
                        'border': '2px solid #0D3182'
                    },
                    {
                        # Style pour les colonnes de pourcentage hommes
                        'if': {'column_id': ['Hommes (%)', 'Hommes (n)']},
                        'backgroundColor': '#e8f4fd',
                    },
                    {
                        # Style pour les colonnes de pourcentage femmes
                        'if': {'column_id': ['Femmes (%)', 'Femmes (n)']},
                        'backgroundColor': '#fce8f3',
                    }
                ],
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'Année'},
                        'fontWeight': 'bold',
                        'textAlign': 'left',
                        'width': '80px'
                    },
                    {
                        'if': {'column_id': ['Hommes (n)', 'Femmes (n)', 'Sexe inconnu (n)']},
                        'width': '70px'
                    },
                    {
                        'if': {'column_id': ['Hommes (%)', 'Femmes (%)', 'Sexe inconnu (%)']},
                        'width': '70px'
                    }
                ]
            ),
            html.P(f'{len(stats_by_year)-1} années affichées (+ ligne total)', 
                className='text-info mt-2', style={'fontSize': '12px'})
        ]), False
    
    @app.callback(
        Output("download-csv", "data"),
        Input("export-csv-button", "n_clicks"),
        State('year-filter-checklist', 'value'),
        prevent_initial_call=True
    )
    def export_csv(n_clicks, selected_years):
        """Gère l'export CSV des statistiques"""
        if n_clicks is None:
            return dash.no_update
        
        try:
            # Récupérer les données stockées
            if hasattr(app.server, 'stats_data') and app.server.stats_data:
                stats_df = pd.DataFrame(app.server.stats_data)
                
                # Générer un nom de fichier avec la date et les années sélectionnées
                from datetime import datetime
                current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if selected_years:
                    years_str = "_".join(map(str, sorted(selected_years)))
                    filename = f"statistiques_patients_{years_str}_{current_date}.csv"
                else:
                    filename = f"statistiques_patients_toutes_annees_{current_date}.csv"
                
                return dcc.send_data_frame(
                    stats_df.to_csv, 
                    filename=filename,
                    index=False  # Ne pas inclure l'index dans le CSV
                )
            else:
                return dash.no_update
                
        except Exception as e:
            print(f"Erreur lors de l'export CSV: {e}")
            return dash.no_update
        
    @app.callback(
        Output('patients-performance-scores-boxplot', 'children'),
        [Input('data-store', 'data'),
        Input('current-page', 'data'),
        Input('year-filter-checklist', 'value')]
    )
    def update_patients_performance_scores_boxplot(data, current_page, selected_years):
        """Boxplot des Performance Scores par Age Groups avec boutons pour switcher entre les échelles"""
        if current_page != 'Patients' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Filtrer les données par année
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        # Vérifier que la colonne Age Groups existe
        if 'Age Groups' not in filtered_df.columns:
            return html.Div('Colonne Age Groups non disponible', className='text-warning text-center')
        
        # Vérifier que les colonnes Performance Status existent
        scale_col = 'Performance Status At Treatment Scale'
        score_col = 'Performance Status At Treatment Score'
        
        if scale_col not in filtered_df.columns or score_col not in filtered_df.columns:
            return html.Div('Colonnes Performance Status manquantes', className='text-warning text-center')
        
        try:
            # Nettoyer les données
            clean_df = filtered_df.dropna(subset=['Age Groups', scale_col, score_col])
            
            # Obtenir les échelles uniques disponibles
            available_scales = clean_df[scale_col].dropna().unique()
            
            if len(available_scales) == 0:
                return html.Div('Aucune échelle de performance disponible', className='text-warning text-center')
            
            # Créer la figure
            fig = go.Figure()
            
            # Fonction pour convertir le score en numérique
            def convert_score_to_numeric(score):
                if pd.isna(score) or str(score).strip().lower() in ['unknown', 'nan', '']:
                    return None
                try:
                    return float(score)
                except (ValueError, TypeError):
                    return None
            
            # Ordre des groupes d'âge
            age_order = ['18-', '18-39', '40-64', '65-74', '75+']
            
            # Créer les traces pour chaque échelle
            for i, scale in enumerate(available_scales):
                # Filtrer les données pour cette échelle
                scale_df = clean_df[clean_df[scale_col] == scale].copy()
                scale_df['numeric_score'] = scale_df[score_col].apply(convert_score_to_numeric)
                scale_df = scale_df.dropna(subset=['numeric_score'])
                
                # S'assurer que les groupes d'âge sont dans le bon ordre
                scale_df['Age Groups'] = pd.Categorical(scale_df['Age Groups'], categories=age_order, ordered=True)
                scale_df = scale_df.sort_values('Age Groups')
                
                # Créer un boxplot pour chaque groupe d'âge
                for age_group in age_order:
                    if age_group in scale_df['Age Groups'].values:
                        group_data = scale_df[scale_df['Age Groups'] == age_group]['numeric_score']
                        
                        fig.add_trace(go.Box(
                            y=group_data,
                            x=[age_group] * len(group_data),
                            name=age_group,
                            showlegend=False,
                            marker_color='#2E86AB',
                            boxpoints='all',
                            jitter=0.3,
                            pointpos=0,
                            marker=dict(size=4, opacity=0.6),
                            visible=(i == 0)  # Seule la première échelle est visible au début
                        ))
            
            # Fonction pour déterminer la plage Y selon l'échelle
            def get_y_axis_config(scale_name):
                if 'ECOG' in scale_name:
                    return {'range': [0, 5], 'dtick': 1}
                elif 'Karnofsky' in scale_name or 'Lansky' in scale_name:
                    return {'range': [0, 100], 'dtick': 10}
                else:
                    return {'range': [0, None], 'dtick': 1}
            
            # Créer les boutons pour switcher entre les échelles
            buttons = []
            for i, scale in enumerate(available_scales):
                # Créer la visibilité pour ce bouton
                visibility = []
                for j in range(len(available_scales)):
                    # Compter combien de groupes d'âge ont des données pour cette échelle
                    scale_df_check = clean_df[clean_df[scale_col] == available_scales[j]]
                    n_age_groups = len([ag for ag in age_order if ag in scale_df_check['Age Groups'].values])
                    if j == i:
                        visibility.extend([True] * n_age_groups)
                    else:
                        visibility.extend([False] * n_age_groups)
                
                # Obtenir la configuration de l'axe Y pour cette échelle
                y_config = get_y_axis_config(scale)
                
                buttons.append(
                    dict(
                        label=scale,
                        method='update',
                        args=[
                            {
                                'visible': visibility
                            },
                            {
                                'title': f'Performance Score ({scale}) par tranche d\'âge',
                                'yaxis': dict(
                                    title='Performance Score',
                                    range=y_config['range'],
                                    dtick=y_config['dtick'],
                                    tick0=0
                                )
                            }
                        ]
                    )
                )
            
            # Configuration initiale de l'axe Y
            initial_y_config = get_y_axis_config(available_scales[0])
            
            # Mise en forme du graphique
            fig.update_layout(
                title=f'Performance Score ({available_scales[0]}) par tranche d\'âge',
                xaxis_title='Tranche d\'âge',
                yaxis_title='Performance Score',
                height=480,
                width=None,
                template='plotly_white',
                showlegend=False,
                margin=dict(t=80, r=200, b=80, l=80),  # Marge droite pour le menu
                updatemenus=[
                    dict(
                        buttons=buttons,
                        direction='down',
                        pad={'r': 10, 't': 10},
                        showactive=True,
                        x=1.02,  # Position à droite du graphique
                        xanchor='left',
                        y=1,     # Aligné en haut
                        yanchor='top',
                        bgcolor='rgba(255, 255, 255, 0.9)',
                        bordercolor='#2E86AB',
                        borderwidth=1
                    )
                ],
                yaxis=dict(
                    range=initial_y_config['range'],
                    dtick=initial_y_config['dtick'],
                    tick0=0
                ),
                xaxis=dict(
                    categoryorder='array',
                    categoryarray=age_order
                )
            )
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div(f'Erreur: {str(e)}', className='text-danger text-center')
      
    @callback(
        Output('patients-missing-summary-table', 'children'),
        [Input('data-store', 'data'), Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def final_summary_callback(data, current_page):
        """Version finale avec analyse réelle"""
        
        if current_page != 'Patients' or not data:
            return html.Div("En attente...", className='text-muted')
        
        try:
            df = pd.DataFrame(data)
            
            # Colonnes à analyser
            columns_to_analyze = ['Age At Diagnosis', 'Main Diagnosis', 'Sex', 'Blood + Rh', 'Number HCT', 'Number Allo HCT']
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            print(f"🔍 FINAL - Colonnes existantes: {existing_columns}")
            
            if not existing_columns:
                return dbc.Alert("Aucune colonne trouvée", color='warning')
            
            # Analyse simple
            summary_data = []
            for col in existing_columns:
                missing_count = df[col].isna().sum()
                total = len(df)
                percentage = round((missing_count / total) * 100, 1)
                
                summary_data.append({
                    'Colonne': col,
                    'Total': total,
                    'Manquantes': missing_count,
                    '% Manquant': percentage
                })
            
            print(f"🔍 FINAL - Données du tableau: {summary_data}")
            
            return dash_table.DataTable(
                data=summary_data,
                columns=[
                    {"name": "Colonne", "id": "Colonne"},
                    {"name": "Total", "id": "Total", "type": "numeric"},
                    {"name": "Manquantes", "id": "Manquantes", "type": "numeric"},
                    {"name": "% Manquant", "id": "% Manquant", "type": "numeric"}
                ],
                style_table={'height': '350px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'center', 'padding': '10px'},
                style_header={'backgroundColor': '#0D3182', 'color': 'white', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'},
                    {'if': {'filter_query': '{% Manquant} = 0', 'column_id': '% Manquant'}, 
                    'backgroundColor': '#d4edda', 'color': 'green'},
                    {'if': {'filter_query': '{% Manquant} > 10', 'column_id': '% Manquant'}, 
                    'backgroundColor': '#f8d7da', 'color': 'red'}
                ]
            )
            
        except Exception as e:
            print(f"🔍 FINAL - ERREUR: {e}")
            return dbc.Alert(f"Erreur: {str(e)}", color='danger')

    @callback(
        [Output('patients-missing-detail-table', 'children'),
        Output('export-missing-patients-button', 'disabled')],  # Contrôler l'état du bouton
        [Input('data-store', 'data'), Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def final_detail_callback(data, current_page):
        """Version finale détail avec analyse réelle"""
        
        if current_page != 'Patients' or not data:
            return html.Div("En attente...", className='text-muted'), True
        
        try:
            df = pd.DataFrame(data)
            columns_to_analyze = ['Age At Diagnosis', 'Main Diagnosis', 'Sex', 'Blood + Rh', 'Number HCT', 'Number Allo HCT']
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            # Trouver les patients avec données manquantes
            detailed_data = []
            for _, row in df.iterrows():
                patient_id = row.get('Long ID', f'Patient_{row.name}')
                missing_cols = [col for col in existing_columns if pd.isna(row[col])]
                
                if missing_cols:
                    detailed_data.append({
                        'Long ID': patient_id,
                        'Colonnes manquantes': ', '.join(missing_cols),
                        'Nb manquant': len(missing_cols)
                    })
            
            print(f"🔍 FINAL - Patients avec données manquantes: {len(detailed_data)}")
            
            if not detailed_data:
                return dbc.Alert("🎉 Aucune donnée manquante !", color='success'), True
            
            # Sauvegarder les données pour l'export
            app.server.missing_patients_data = detailed_data
            
            table_content = html.Div([
                dash_table.DataTable(
                    data=detailed_data,
                    columns=[
                        {"name": "Long ID", "id": "Long ID"},
                        {"name": "Colonnes manquantes", "id": "Colonnes manquantes"},
                        {"name": "Nb", "id": "Nb manquant", "type": "numeric"}
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
            
            return table_content, False  # Activer le bouton
            
        except Exception as e:
            print(f"🔍 FINAL DETAIL - ERREUR: {e}")

    @app.callback(
        Output("download-missing-patients-excel", "data"),
        Input("export-missing-patients-button", "n_clicks"),
        prevent_initial_call=True
    )
    def export_missing_patients_excel(n_clicks):
        """Gère l'export Excel des patients avec données manquantes"""
        if n_clicks is None:
            return dash.no_update
        
        try:
            # Récupérer les données stockées
            if hasattr(app.server, 'missing_patients_data') and app.server.missing_patients_data:
                missing_df = pd.DataFrame(app.server.missing_patients_data)
                
                # Générer un nom de fichier avec la date
                from datetime import datetime
                current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"patients_donnees_manquantes_{current_date}.csv"
                
                return dcc.send_data_frame(
                    missing_df.to_csv, 
                    filename=filename,
                    index=False
                )
            else:
                return dash.no_update
                
        except Exception as e:
            print(f"Erreur lors de l'export Excel: {e}")
            return dash.no_update