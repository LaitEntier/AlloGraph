# pages/hemopathies.py
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd

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
                    dbc.CardHeader(html.H5('Distribution des diagnostics')),
                    dbc.CardBody([
                        html.Div(
                            id='hemopathies-barplot-simple',
                            style={'height': '400px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Deuxième graphique - Distribution normalisée
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Distribution normalisée des diagnostics')),
                    dbc.CardBody([
                        html.Div(
                            id='hemopathies-barplot-normalized',
                            style={'height': '400px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Troisième graphique - Performance Status
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Performance Status par diagnostic')),
                    dbc.CardBody([
                        html.Div(
                            id='hemopathies-performance-viz',
                            style={'height': '400px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Quatrième graphique - Number Allo HCT
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Number Allo HCT par diagnostic')),
                    dbc.CardBody([
                        html.Div(
                            id='hemopathies-boxplot',
                            style={'height': '400px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
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
        if current_page != 'Hemopathies' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Valeurs par défaut pour Hemopathies
        if x_axis is None:
            x_axis = 'Main Diagnosis' if 'Main Diagnosis' in df.columns else None
        
        if stack_var is None:
            stack_var = 'Aucune'
        
        # Filtrer les données par année
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty or x_axis not in filtered_df.columns:
            return html.Div('Aucune donnée disponible', className='text-warning text-center')
        
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
            
            stack_col = None if stack_var == 'Aucune' else stack_var
            
            if stack_col is None:
                # Barplot simple
                fig = gr.create_simple_barplot(
                    data=processed_df,
                    x_column=display_column,
                    title=f"Distribution des {x_axis.lower()}",
                    x_axis_title=x_axis,
                    y_axis_title="Nombre de patients",
                    custom_order=freq_order,
                    height=380,  # Ajusté pour le nouveau layout
                    width=None,
                    rotate_x_labels=should_rotate,
                    x_rotation_angle=45
                )
                
                # Ajouter le texte complet au hover si c'est tronqué
                if should_rotate:
                    fig.update_traces(
                        hovertemplate=f'<b>%{{x}}</b><br>{x_axis}: %{{customdata}}<br>Nombre: %{{y}}<extra></extra>',
                        customdata=processed_df[x_axis]
                    )
            else:
                # Barplot stacké - CONSERVER L'ORDRE du barplot simple
                fig = gr.create_stacked_barplot(
                    data=processed_df,
                    x_column=display_column,
                    y_column='Count',
                    stack_column=stack_col,
                    title=f"Distribution des {x_axis.lower()} par {stack_col.lower()}",
                    x_axis_title=x_axis,
                    y_axis_title="Nombre de patients",
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
        if current_page != 'Hemopathies' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Valeurs par défaut pour Hemopathies
        if x_axis is None:
            x_axis = 'Main Diagnosis' if 'Main Diagnosis' in df.columns else None
        
        if stack_var is None:
            stack_var = 'Aucune'
        
        # Filtrer les données par année
        if selected_years and 'Year' in df.columns:
            filtered_df = df[df['Year'].isin(selected_years)]
        else:
            filtered_df = df
        
        if filtered_df.empty or x_axis not in filtered_df.columns:
            return html.Div('Aucune donnée disponible', className='text-warning text-center')
        
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
                
                # Ordre sans doublons - méthode sûre
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
            
            stack_col = None if stack_var == 'Aucune' else stack_var
            
            if stack_col is None:
                # Barplot normalisé simple
                fig = gr.create_simple_normalized_barplot(
                    data=processed_df,
                    x_column=display_column,
                    title=f"Distribution relative des {x_axis.lower()}",
                    x_axis_title=x_axis,
                    y_axis_title="Proportion (%)",
                    custom_order=freq_order,
                    height=380,  # Ajusté pour le nouveau layout
                    width=None,
                    rotate_x_labels=should_rotate,
                    x_rotation_angle=45
                )

            else:
                # Barplot stacké normalisé - CONSERVER L'ORDRE du barplot simple
                fig = gr.create_normalized_barplot(
                    data=processed_df,
                    x_column=display_column,
                    y_column='Count',
                    stack_column=stack_col,
                    title=f"Distribution normalisée des {x_axis.lower()} par {stack_col.lower()}",
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
            return html.Div(f'Erreur: {str(e)}', className='text-danger text-center')

    @app.callback(
        Output('hemopathies-performance-viz', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('x-axis-dropdown', 'value'),
         Input('stack-variable-dropdown', 'value'),
         Input('year-filter-checklist', 'value')]
    )
    def update_performance_visualization(data, current_page, x_axis, stack_var, selected_years):
        """Visualisation du Performance Status par diagnostic"""
        if current_page != 'Hemopathies' or data is None:
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
        
        # Vérifier les colonnes nécessaires
        required_cols = ['Performance Status At Treatment Score', 'Performance Status At Treatment Scale']
        available_cols = [col for col in required_cols if col in filtered_df.columns]
        
        if not available_cols or x_axis not in filtered_df.columns:
            return html.Div([
                html.P('Colonnes Performance Status non disponibles', className='text-warning text-center'),
                html.P(f'Colonnes trouvées: {", ".join(available_cols)}', className='text-muted text-center', style={'fontSize': '10px'})
            ])
        
        try:
            # Utiliser le score comme variable principale
            score_col = 'Performance Status At Treatment Score'
            scale_col = 'Performance Status At Treatment Scale' if 'Performance Status At Treatment Scale' in filtered_df.columns else None
            
            # Nettoyer les données (supprimer les valeurs nulles et "Unknown")
            clean_df = filtered_df.dropna(subset=[score_col, x_axis])
            
            # Convertir le score en numérique en gérant les cas "Unknown"
            def convert_score_to_numeric(score):
                if pd.isna(score) or str(score).strip().lower() in ['unknown', 'nan', '']:
                    return None
                try:
                    return float(score)
                except (ValueError, TypeError):
                    return None
            
            clean_df = clean_df.copy()
            clean_df['numeric_score'] = clean_df[score_col].apply(convert_score_to_numeric)
            
            # Supprimer les lignes où la conversion a échoué
            clean_df = clean_df.dropna(subset=['numeric_score'])
            
            if clean_df.empty:
                return html.Div('Aucune donnée numérique valide pour le Performance Status', className='text-warning text-center')
            
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
            
            # Créer un boxplot avec le score numérique par diagnostic
            color_col = None
            if stack_var == 'Aucune' and scale_col:
                color_col = scale_col
            elif stack_var != 'Aucune':
                color_col = stack_var
            
            fig = gr.create_enhanced_boxplot(
                data=processed_df,
                x_column=display_column,
                y_column='numeric_score',
                color_column=color_col,
                title=f"Performance Status Score par {x_axis.lower()}",
                x_axis_title=x_axis,
                y_axis_title="Performance Status Score",
                height=380,  # Ajusté pour le nouveau layout
                width=None,
                show_points=True,
                force_zero_start=True
            )
            
            # Ajouter rotation pour les diagnostics
            if x_axis in ['Main Diagnosis', 'Subclass Diagnosis']:
                fig.update_layout(
                    xaxis=dict(
                        title=x_axis,
                        tickangle=45,
                        tickmode='linear'
                    )
                )
                
                # Ajouter le texte complet au hover si c'est tronqué
                try:
                    fig.update_traces(
                        hovertemplate=f'<b>%{{x}}</b><br>{x_axis}: %{{customdata}}<br>Score: %{{y}}<extra></extra>',
                        customdata=processed_df[x_axis]
                    )
                except:
                    pass
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div(f'Erreur: {str(e)}', className='text-danger text-center')

    @app.callback(
        Output('hemopathies-boxplot', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('x-axis-dropdown', 'value'),
         Input('stack-variable-dropdown', 'value'),
         Input('year-filter-checklist', 'value')]
    )
    def update_number_allo_boxplot(data, current_page, x_axis, stack_var, selected_years):
        """Boxplot de Number Allo HCT par diagnostic"""
        if current_page != 'Hemopathies' or data is None:
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
        
        # Vérifier les colonnes nécessaires
        y_col = 'Number Allo HCT'
        if y_col not in filtered_df.columns or x_axis not in filtered_df.columns:
            return html.Div('Colonne "Number Allo HCT" non disponible', className='text-warning text-center')
        
        try:
            # Nettoyer les données
            clean_df = filtered_df.dropna(subset=[y_col, x_axis])
            
            if clean_df.empty:
                return html.Div('Aucune donnée valide pour Number Allo HCT', className='text-warning text-center')
            
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
            
            # Utiliser la variable de stratification pour colorer les points
            color_col = None if stack_var == 'Aucune' else stack_var
            
            fig = gr.create_enhanced_boxplot(
                data=processed_df,
                x_column=display_column,
                y_column=y_col,
                color_column=color_col,
                title=f"Number Allo HCT par {x_axis.lower()}",
                x_axis_title=x_axis,
                y_axis_title="Number Allo HCT",
                height=380,  # Ajusté pour le nouveau layout
                width=None,
                show_points=True,
                force_zero_start=True
            )
            
            # Ajouter rotation pour les diagnostics
            if x_axis in ['Main Diagnosis', 'Subclass Diagnosis']:
                fig.update_layout(
                    xaxis=dict(
                        title=x_axis,
                        tickangle=45,
                        tickmode='linear'
                    )
                )
                
                # Ajouter le texte complet au hover si c'est tronqué
                try:
                    fig.update_traces(
                        hovertemplate=f'<b>%{{x}}</b><br>{x_axis}: %{{customdata}}<br>{y_col}: %{{y}}<extra></extra>',
                        customdata=processed_df[x_axis]
                    )
                except:
                    pass
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True, 'displayModeBar': False}
            )
        
        except Exception as e:
            return html.Div(f'Erreur: {str(e)}', className='text-danger text-center')