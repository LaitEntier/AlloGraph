import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

# Import des modules communs
import modules.dashboard_layout as layouts
import visualizations.allogreffes.graphs as gr

def get_layout():
    """Retourne le layout de la page Hemopathies avec graphiques empilés verticalement"""
    return dbc.Container([
        # Premier graphique - Distribution simple
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Diagnostics distribution')),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-patients-normalized",
                            type="circle",
                            children=
                            html.Div(
                                id='hemopathies-barplot-simple',
                                style={'height': '400px', 'overflow': 'hidden'}
                            )
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Deuxième graphique - Distribution normalisée
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Normalized diagnostics distribution')),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-patients-normalized",
                            type="circle",
                            children=
                            html.Div(
                                id='hemopathies-barplot-normalized',
                                style={'height': '400px', 'overflow': 'hidden'}
                            )
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Troisième graphique - Boxplot des Performance Scores
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Performance Scores by diagnosis')),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-patients-normalized",
                            type="circle",
                            children=
                            html.Div(
                                id='hemopathies-performance-scores-boxplot',
                                style={'height': '500px', 'overflow': 'hidden'}
                            )
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),

        # Quatrième section - DataTable Main Diagnosis par année
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Main diagnoses distribution by year')),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-patients-normalized",
                            type="circle",
                            children=
                            html.Div(
                                id='hemopathies-datatable',
                                style={'height': '500px', 'overflow': 'auto'}
                            )
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),

        html.Hr(style={
            'border': '2px solid #d4c4b5',
            'margin': '3rem 0 2rem 0'
        }),

        dbc.Row([
            # Tableau 1 - Résumé des colonnes
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Column summary", className='mb-0', style={'color': '#ffffff'})),
                    dbc.CardBody([
                        html.Div(id='hemopathies-missing-summary-table', children=[
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
                            html.H5("Lines affected", className='mb-0', style={'color': '#ffffff'}),
                            dbc.Button(
                                [html.I(className="fas fa-download me-2"), "Export CSV"],
                                id="export-missing-hemopathies-button",
                                color="primary",
                                size="sm",
                                disabled=True,  # Désactivé par défaut
                            )
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody([
                        html.Div(id='hemopathies-missing-detail-table', children=[
                            dbc.Alert("Initial content - will be replaced by the callback", color='warning')
                        ]),
                        # Composant pour télécharger le fichier Excel (invisible)
                        dcc.Download(id="download-missing-hemopathies-excel")
                    ])
                ])
            ], width=6)
        ])
        
    ], fluid=True)


def create_safe_truncated_mapping(processed_df, x_axis, truncated_col):
    """
    Crée un mapping sûr entre les valeurs originales et tronquées.
    """
    mapping = {}
    
    # Grouper par valeur originale et prendre la première valeur tronquée
    for original_val in processed_df[x_axis].unique():
        if pd.notna(original_val):
            truncated_vals = processed_df[processed_df[x_axis] == original_val][truncated_col]
            if len(truncated_vals) > 0:
                mapping[original_val] = truncated_vals.iloc[0]
            else:
                # Fallback : utiliser la fonction de troncature directement
                mapping[original_val] = gr.truncate_diagnosis_names(str(original_val), 20)
        else:
            mapping[original_val] = original_val
    
    return mapping

def register_callbacks(app):
    """Enregistre tous les callbacks spécifiques à la page Hemopathies"""
    
    @app.callback(
        Output('hemopathies-barplot-simple', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('x-axis-dropdown', 'value'),
         Input('stack-variable-dropdown', 'value'),
         Input('year-filter-checklist', 'value')]
    )
    def update_simple_barplot(data, current_page, x_axis, stack_var, selected_years):
        """Barplot simple - distribution des diagnostics du plus au moins commun"""
        if current_page != 'Indications' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Valeurs par défaut pour Hemopathies
        if x_axis is None:
            x_axis = 'Main Diagnosis' if 'Main Diagnosis' in df.columns else None
        
        if stack_var is None:
            stack_var = 'None'
        
        # Filtrer les données par année
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty or x_axis not in filtered_df.columns:
            return html.Div('No data available', className='text-warning text-center')
        
        try:
            # Vérifier si on doit tourner les labels (pour les diagnostics)
            should_rotate = x_axis in ['Main Diagnosis', 'Subclass Diagnosis']
            
            # Préparer les données avec labels tronqués si c'est un diagnostic
            if should_rotate:
                max_length = 20
                processed_df, truncated_col = gr.prepare_data_with_truncated_labels(
                    filtered_df, x_axis, max_length
                )
                display_column = truncated_col
                
                # Calculer l'ordre par fréquence sur les données originales
                freq_order_original = filtered_df[x_axis].value_counts().index.tolist()
                
                # Créer le mapping de manière sûre
                truncated_mapping = create_safe_truncated_mapping(processed_df, x_axis, truncated_col)
                
                # Créer l'ordre tronqué sans doublons
                freq_order = []
                seen = set()
                for orig_name in freq_order_original:
                    if orig_name in truncated_mapping:
                        trunc_name = truncated_mapping[orig_name]
                        if trunc_name and trunc_name not in seen:
                            freq_order.append(trunc_name)
                            seen.add(trunc_name)
            else:
                processed_df = filtered_df
                display_column = x_axis
                freq_order = filtered_df[x_axis].value_counts().index.tolist()
            
            stack_col = None if stack_var == 'None' else stack_var
            
            if stack_col is None:
                # Barplot simple
                fig = gr.create_simple_barplot(
                    data=processed_df,
                    x_column=display_column,
                    title=f"Distribution of {x_axis.lower()}",
                    x_axis_title=x_axis,
                    y_axis_title="Number of patients",
                    custom_order=freq_order,
                    height=380,  # Ajusté pour le nouveau layout
                    width=None,
                    rotate_x_labels=should_rotate,
                    x_rotation_angle=45
                )
                
                # Ajouter le texte complet au hover si c'est tronqué
                if should_rotate:
                    fig.update_traces(
                        hovertemplate=f'<b>%{{x}}</b><br>{x_axis}: %{{customdata}}<br>Number: %{{y}}<extra></extra>',
                        customdata=processed_df[x_axis]
                    )
            else:
                # Barplot stacké - CONSERVER L'ORDRE du barplot simple
                fig = gr.create_stacked_barplot(
                    data=processed_df,
                    x_column=display_column,
                    y_column='Count',
                    stack_column=stack_col,
                    title=f"Distribution of {x_axis.lower()} by {stack_col.lower()}",
                    x_axis_title=x_axis,
                    y_axis_title="Number of patients",
                    custom_order=freq_order,
                    height=380,  # Ajusté pour le nouveau layout
                    width=None,
                    rotate_x_labels=should_rotate,
                    x_rotation_angle=45
                )
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div(f'Erreur: {str(e)}', className='text-danger text-center')

    @app.callback(
        Output('hemopathies-barplot-normalized', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('x-axis-dropdown', 'value'),
         Input('stack-variable-dropdown', 'value'),
         Input('year-filter-checklist', 'value')]
    )
    def update_normalized_barplot(data, current_page, x_axis, stack_var, selected_years):
        """Barplot normalisé à 100% - même ordre que le barplot simple"""
        if current_page != 'Indications' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Valeurs par défaut pour Hemopathies
        if x_axis is None:
            x_axis = 'Main Diagnosis' if 'Main Diagnosis' in df.columns else None
        
        if stack_var is None:
            stack_var = 'None'
        
        # Filtrer les données par année
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty or x_axis not in filtered_df.columns:
            return html.Div('No data available', className='text-warning text-center')
        
        try:
            # Vérifier si on doit tourner les labels (pour les diagnostics)
            should_rotate = x_axis in ['Main Diagnosis', 'Subclass Diagnosis']
            
            # Préparer les données avec labels tronqués si c'est un diagnostic
            if should_rotate:
                max_length = 20
                processed_df, truncated_col = gr.prepare_data_with_truncated_labels(
                    filtered_df, x_axis, max_length
                )
                display_column = truncated_col
                
                freq_order_original = filtered_df[x_axis].value_counts().index.tolist()
                truncated_mapping = create_safe_truncated_mapping(processed_df, x_axis, truncated_col)
                
                freq_order = []
                seen = set()
                for orig_name in freq_order_original:
                    if orig_name in truncated_mapping:
                        trunc_name = truncated_mapping[orig_name]
                        if trunc_name and trunc_name not in seen:
                            freq_order.append(trunc_name)
                            seen.add(trunc_name)
            else:
                processed_df = filtered_df
                display_column = x_axis
                freq_order = filtered_df[x_axis].value_counts().index.tolist()
            
            stack_col = None if stack_var == 'None' else stack_var
            
            if stack_col is None:
                fig = gr.create_simple_normalized_barplot(
                    data=processed_df,
                    x_column=display_column,
                    title=f"Relative distribution of {x_axis.lower()}",
                    x_axis_title=x_axis,
                    y_axis_title="Proportion (%)",
                    custom_order=freq_order,
                    height=380,  # Ajusté pour le nouveau layout
                    width=None,
                    rotate_x_labels=should_rotate,
                    x_rotation_angle=45
                )

            else:
                fig = gr.create_normalized_barplot(
                    data=processed_df,
                    x_column=display_column,
                    y_column='Count',
                    stack_column=stack_col,
                    title=f"Normalized distribution of {x_axis.lower()} by {stack_col.lower()}",
                    x_axis_title=x_axis,
                    y_axis_title="Proportion (%)",
                    custom_order=freq_order,
                    height=380,  # Ajusté pour le nouveau layout
                    width=None,
                    rotate_x_labels=should_rotate,
                    x_rotation_angle=45
                )
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div(f'Error: {str(e)}', className='text-danger text-center')

    @app.callback(
        Output('hemopathies-performance-scores-boxplot', 'children'),
        [Input('data-store', 'data'),
        Input('current-page', 'data'),
        Input('x-axis-dropdown', 'value'),
        Input('year-filter-checklist', 'value')]
    )
    def update_performance_scores_boxplot(data, current_page, x_axis, selected_years):
        """Boxplot des Performance Scores avec boutons pour switcher entre les échelles"""
        if current_page != 'Indications' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Valeurs par défaut
        if x_axis is None:
            x_axis = 'Main Diagnosis' if 'Main Diagnosis' in df.columns else None
        
        # Filtrer les données par année
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty or x_axis not in filtered_df.columns:
            return html.Div('No data available', className='text-warning text-center')
        
        # Vérifier que les colonnes nécessaires existent
        scale_col = 'Performance Status At Treatment Scale'
        score_col = 'Performance Status At Treatment Score'
        
        if scale_col not in filtered_df.columns or score_col not in filtered_df.columns:
            return html.Div('Performance Status columns missing', className='text-warning text-center')
        
        try:
            # Nettoyer les données pour x_axis
            clean_df = filtered_df.dropna(subset=[x_axis, scale_col, score_col])
            
            # Obtenir les échelles uniques disponibles
            available_scales = clean_df[scale_col].dropna().unique()
            
            if len(available_scales) == 0:
                return html.Div('No performance scale available', className='text-warning text-center')
            
            # Préparer les données avec labels tronqués si c'est un diagnostic
            if x_axis in ['Main Diagnosis', 'Subclass Diagnosis']:
                max_length = 20
                processed_df, truncated_col = gr.prepare_data_with_truncated_labels(
                    clean_df, x_axis, max_length
                )
                display_column = truncated_col
            else:
                processed_df = clean_df
                display_column = x_axis
            
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
            
            # Créer les traces pour chaque échelle
            for i, scale in enumerate(available_scales):
                # Filtrer les données pour cette échelle
                scale_df = processed_df[processed_df[scale_col] == scale].copy()
                scale_df['numeric_score'] = scale_df[score_col].apply(convert_score_to_numeric)
                scale_df = scale_df.dropna(subset=['numeric_score'])
                
                # Obtenir les catégories
                categories = sorted(scale_df[display_column].unique())
                
                # Créer un boxplot pour chaque catégorie
                for category in categories:
                    cat_data = scale_df[scale_df[display_column] == category]['numeric_score']
                    
                    fig.add_trace(go.Box(
                        y=cat_data,
                        x=[category] * len(cat_data),
                        name=category,
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
                    n_categories = len(processed_df[processed_df[scale_col] == available_scales[j]][display_column].unique())
                    if j == i:
                        visibility.extend([True] * n_categories)
                    else:
                        visibility.extend([False] * n_categories)
                
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
                                'title': f'Performance Score ({scale}) par {x_axis}',
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
            
            # Mise en forme du graphique avec marges ajustées
            fig.update_layout(
                title=f'Performance Score ({available_scales[0]}) par {x_axis}',
                xaxis_title=x_axis,
                yaxis_title='Performance Score',
                height=480,
                width=None,
                template='plotly_white',
                showlegend=False,
                margin=dict(t=80, r=200, b=80, l=80),  # Marge droite augmentée pour le menu
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
                    tickangle=45 if x_axis in ['Main Diagnosis', 'Subclass Diagnosis'] else 0,
                    tickmode='linear'
                )
            )
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div(f'Error: {str(e)}', className='text-danger text-center')
        
    @app.callback(
        Output('hemopathies-datatable', 'children'),
        [Input('data-store', 'data'),
        Input('current-page', 'data'),
        Input('year-filter-checklist', 'value')]
    )
    def update_hemopathies_datatable(data, current_page, selected_years):
        """DataTable avec la répartition des Main Diagnosis par année"""
        if current_page != 'Indications' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Vérifier les colonnes nécessaires
        required_cols = ['Year', 'Main Diagnosis']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return dbc.Alert(f'Missing columns: {", ".join(missing_cols)}', color='warning')
        
        # Filtrer selon les années sélectionnées
        if selected_years:
            filtered_df = df[df['Year'].isin(selected_years)]
            years_to_process = selected_years
        else:
            filtered_df = df
            years_to_process = sorted(df['Year'].unique())
        
        if filtered_df.empty:
            return dbc.Alert('No data available for the selected years', color='info')
        
        # Calculer la table croisée Year x Main Diagnosis
        crosstab = pd.crosstab(filtered_df['Year'], filtered_df['Main Diagnosis'], margins=True, margins_name='TOTAL')
        
        # Calculer les pourcentages par année (ligne)
        crosstab_percent = crosstab.div(crosstab['TOTAL'], axis=0) * 100
        
        # Créer les données pour la table
        table_data = []
        
        # Obtenir tous les diagnostics (colonnes sauf TOTAL)
        diagnoses = [col for col in crosstab.columns if col != 'TOTAL']
        
        # Tronquer les noms de diagnostics longs pour l'affichage
        def truncate_diagnosis(diagnosis, max_length=30):
            if pd.isna(diagnosis) or len(str(diagnosis)) <= max_length:
                return str(diagnosis)
            return str(diagnosis)[:max_length-3] + "..."
        
        # Créer les lignes pour chaque année
        for year in crosstab.index:
            row_data = {'Year': str(year)}
            
            # Ajouter l'effectif total
            row_data['Effectif total'] = int(crosstab.loc[year, 'TOTAL'])
            
            # Ajouter chaque diagnostic avec count et pourcentage
            for diagnosis in diagnoses:
                count = int(crosstab.loc[year, diagnosis])
                percent = crosstab_percent.loc[year, diagnosis]
                
                # Nom tronqué pour les colonnes
                trunc_diagnosis = truncate_diagnosis(diagnosis, 25)
                
                # Colonnes count et pourcentage
                row_data[f'{trunc_diagnosis} (n)'] = count
                row_data[f'{trunc_diagnosis} (%)'] = round(percent, 1)
            
            table_data.append(row_data)
        
        # Préparer les colonnes pour la DataTable
        columns = [
            {"name": "Year", "id": "Year", "type": "text"},
            {"name": "Total patients", "id": "Total patients", "type": "numeric"}
        ]
        
        # Ajouter les colonnes pour chaque diagnostic
        for diagnosis in diagnoses:
            trunc_diagnosis = truncate_diagnosis(diagnosis, 25)
            columns.extend([
                {
                    "name": f"{trunc_diagnosis} (n)", 
                    "id": f"{trunc_diagnosis} (n)", 
                    "type": "numeric"
                },
                {
                    "name": f"{trunc_diagnosis} (%)", 
                    "id": f"{trunc_diagnosis} (%)", 
                    "type": "numeric",
                    "format": {"specifier": ".1f"}
                }
            ])
        
        # Créer la DataTable
        return html.Div([
            html.P(f"Distribution of {len(diagnoses)} main diagnoses over {len(years_to_process)} years", 
                className='text-info mb-3', style={'fontSize': '12px'}),
            
            dash_table.DataTable(
                data=table_data,
                columns=columns,
                style_table={
                    'height': '400px', 
                    'overflowY': 'auto', 
                    'overflowX': 'auto',
                    'border': '1px solid #ddd'
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '6px',
                    'fontFamily': 'Arial, sans-serif',
                    'fontSize': '10px',
                    'minWidth': '60px',
                    'maxWidth': '120px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'color': '#021F59'
                },
                style_header={
                    'backgroundColor': '#021F59', 
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'fontSize': '9px',
                    'padding': '8px',
                    'border': '1px solid white'
                },
                style_data_conditional=[
                    {
                        # Mise en évidence de la ligne TOTAL
                        'if': {'filter_query': '{Year} = TOTAL'},
                        'backgroundColor': '#F2E9DF',
                        'fontWeight': 'bold',
                        'border': '2px solid #021F59'
                    },
                    {
                        # Style pour les colonnes de nombres (alternance)
                        'if': {'column_id': [col['id'] for col in columns if '(n)' in col['id']]},
                        'backgroundColor': '#F2E9DF',
                    },
                    {
                        # Style pour les colonnes de pourcentages
                        'if': {'column_id': [col['id'] for col in columns if '(%)' in col['id']]},
                        'backgroundColor': '#e8f5e8',
                    }
                ],
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'Year'},
                        'fontWeight': 'bold',
                        'textAlign': 'left',
                        'width': '80px',
                        'backgroundColor': '#f0f0f0',
                        'position': 'sticky',
                        'left': 0
                    },
                    {
                        'if': {'column_id': 'Total patients'},
                        'width': '90px',
                        'fontWeight': 'bold',
                        'backgroundColor': '#fff2cc'
                    },
                    {
                        # Largeur pour les colonnes de count
                        'if': {'column_id': [col['id'] for col in columns if '(n)' in col['id']]},
                        'width': '60px'
                    },
                    {
                        # Largeur pour les colonnes de pourcentage  
                        'if': {'column_id': [col['id'] for col in columns if '(%)' in col['id']]},
                        'width': '60px'
                    }
                ],
                # Retirer fixed_columns car non supporté dans toutes les versions
                # Supprimer les tooltips qui peuvent causer des problèmes
                # tooltip_data et tooltip_duration supprimés pour compatibilité
            )
        ], style={'height': '100%'})
    
    @callback(
        Output('hemopathies-missing-summary-table', 'children'),
        [Input('data-store', 'data'), Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def hemopathies_missing_summary_callback(data, current_page):
        """Gère le tableau de résumé des données manquantes pour Hemopathies"""
        
        if current_page != 'Indications' or not data:
            return html.Div("Waiting...", className='text-muted')
        
        try:
            df = pd.DataFrame(data)
            
            # Variables spécifiques à analyser pour Hemopathies
            columns_to_analyze = [
                'Main Diagnosis', 
                'Subclass Diagnosis', 
                'Age Groups', 
                'Blood Group',
                'Rhesus Factor', 
                'Disease Status At Treatment'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert("No Indications variable found", color='warning')
            
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
                    'fontFamily': 'Arial, sans-serif',
                    'color': '#021F59'
                },
                style_header={
                    'backgroundColor': '#021F59',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
                    {
                        'if': {
                            'filter_query': '{Pourcentage manquant} > 20',
                            'column_id': 'Pourcentage manquant'
                        },
                        'backgroundColor': '#F2A594',
                        'color': 'red',
                        'fontWeight': 'bold'
                    }
                ]
            )
            
        except Exception as e:
            return dbc.Alert(f"Error during analysis: {str(e)}", color='danger')

    @callback(
        [Output('hemopathies-missing-detail-table', 'children'),
         Output('export-missing-hemopathies-button', 'disabled')],
        [Input('data-store', 'data'), Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def hemopathies_missing_detail_callback(data, current_page):
        """Gère le tableau détaillé des patients avec données manquantes pour Hemopathies"""
        
        if current_page != 'Indications' or not data:
            return html.Div("Waiting...", className='text-muted'), True
        
        try:
            df = pd.DataFrame(data)
            
            # Variables spécifiques à analyser pour Hemopathies
            columns_to_analyze = [
                'Main Diagnosis', 
                'Subclass Diagnosis', 
                'Age Groups', 
                'Blood Group',
                'Rhesus Factor', 
                'Disease Status At Treatment'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert("No Indications variable found", color='warning'), True
            
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
            app.server.missing_hemopathies_data = detailed_data
            
            table_content = html.Div([
                dash_table.DataTable(
                    data=detailed_data,
                    columns=[
                        {"name": "Long ID", "id": "Long ID"},
                        {"name": "Missing variables", "id": "Missing columns"},
                        {"name": "Nb", "id": "Nb missing", "type": "numeric"}
                    ],
                    style_table={'height': '300px', 'overflowY': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '12px', 'color': '#021F59'},
                    style_header={'backgroundColor': '#021F59', 'color': 'white', 'fontWeight': 'bold'},
                    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'}],
                    filter_action='native',
                    sort_action='native',
                    page_size=10
                )
            ])
            
            return table_content, False  # Activer le bouton d'export
            
        except Exception as e:
            return dbc.Alert(f"Error during analysis: {str(e)}", color='danger'), True

    @callback(
        Output("download-missing-hemopathies-excel", "data"),
        Input("export-missing-hemopathies-button", "n_clicks"),
        prevent_initial_call=True
    )
    def export_missing_hemopathies_excel(n_clicks):
        """Gère l'export csv des patients avec données manquantes pour Hemopathies"""
        if n_clicks is None:
            return dash.no_update
        
        try:
            # Récupérer les données stockées
            if hasattr(app.server, 'missing_hemopathies_data') and app.server.missing_hemopathies_data:
                missing_df = pd.DataFrame(app.server.missing_hemopathies_data)
                
                # Générer un nom de fichier avec la date
                from datetime import datetime
                current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"hemopathies_missing_data_{current_date}.xlsx"

                return dcc.send_data_frame(
                    missing_df.to_excel,
                    filename=filename,
                    index=False
                )
            else:
                return dash.no_update
                
        except Exception as e:
            print(f"Error during Excel export Indications: {e}")
            return dash.no_update