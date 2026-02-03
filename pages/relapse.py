import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

# Import des modules nécessaires
import modules.dashboard_layout as layouts
import modules.competing_risks as cr
import visualizations.allogreffes.graphs as gr

def get_layout():
    """
    Retourne le layout de la page Rechute
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4('Competing Risks Analysis')),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-patients-normalized",
                            type="circle",
                            children=
                            html.Div(
                                id='relapse-main-graph',
                                style={'height': '800px', 'width': '100%'}
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
                        dbc.CardHeader(html.H5("Summary by column", className='mb-0')),
                        dbc.CardBody([
                            html.Div(id='relapse-missing-summary-table', children=[
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
                                    id="export-missing-relapse-button",
                                    color="primary",
                                    size="sm",
                                    disabled=True,  # Désactivé par défaut
                                )
                            ], className="d-flex justify-content-between align-items-center")
                        ]),
                        dbc.CardBody([
                            html.Div(id='relapse-missing-detail-table', children=[
                                dbc.Alert("Initial content - will be replaced by the callback", color='warning')
                            ]),
                            # Composant pour télécharger le fichier Excel (invisible)
                            dcc.Download(id="download-missing-relapse-excel")
                        ])
                    ])
                ], width=6)
            ])
    ], fluid=True)


def create_relapse_sidebar_content(data):
    """
    Crée le contenu de la sidebar spécifique à la page Rechute.
    
    Args:
        data (list): Liste de dictionnaires (format store Dash) avec les données
        
    Returns:
        html.Div: Contenu de la sidebar
    """
    if data is None or len(data) == 0:
        return html.Div([
            html.P('No data available', className='text-warning')
        ])
    
    # Convertir la liste en DataFrame
    df = pd.DataFrame(data)
    
    # Obtenir les années disponibles pour les filtres
    years_options = []
    if 'Year' in df.columns:
        available_years = sorted(df['Year'].unique().tolist())
        years_options = [{'label': f'{year}', 'value': year} for year in available_years]
    
    return html.Div([
        # Filtres par année
        html.H5('Year filters', className='mb-2'),
        dcc.Checklist(
            id='relapse-year-filter',
            options=years_options,
            value=[year['value'] for year in years_options],
            inline=False,
            className='mb-3'
        ),
        
        html.Hr(),
        
        # Informations sur les données
        html.Div([
            html.H6("📊 Information", className="mb-2"),
            html.P([
                "Patients: ", html.Strong(f"{len(df):,}")
            ], className="mb-1", style={'fontSize': '12px'}),
            html.P([
                "Years: ", html.Strong(f"{len(df['Year'].unique()) if 'Year' in df.columns else 0}")
            ], className="mb-0", style={'fontSize': '12px'})
        ])
    ])

def calculate_max_relapse_followup_days(data):
    """
    Calcule la durée maximale de suivi dans les données pour déterminer 
    jusqu'où dessiner le graphique de rechute
    
    Args:
        data (pd.DataFrame): DataFrame avec les données
        
    Returns:
        int: Durée maximale en jours (minimum 365 pour avoir au moins 1 an)
    """
    try:
        df = data.copy()
        
        # Convertir les dates nécessaires
        df['Treatment Date'] = pd.to_datetime(df['Treatment Date'], format='mixed', errors='coerce')
        df['Date Of Last Follow Up'] = pd.to_datetime(df['Date Of Last Follow Up'], format='mixed', errors='coerce')
        df['First Relapse Date'] = pd.to_datetime(df['First Relapse Date'], format='mixed', errors='coerce')

        # Calculer les durées de suivi
        df['followup_days'] = (df['Date Of Last Follow Up'] - df['Treatment Date']).dt.days
        df['relapse_days'] = (df['First Relapse Date'] - df['Treatment Date']).dt.days
        
        # Nettoyer les valeurs invalides
        valid_followup = df['followup_days'].dropna()
        valid_followup = valid_followup[valid_followup >= 0]
        
        valid_relapse = df['relapse_days'].dropna()
        valid_relapse = valid_relapse[valid_relapse >= 0]
        
        # Prendre le maximum entre suivi et événements de rechute
        max_followup = valid_followup.max() if len(valid_followup) > 0 else 365
        max_relapse = valid_relapse.max() if len(valid_relapse) > 0 else 365
        
        max_days = max(max_followup, max_relapse, 365)  # Au minimum 1 an
        
        # Limiter à une valeur raisonnable (ex: 10 ans)
        max_days = min(max_days, 3650)
        
        print(f"Maximum duration calculated for relapse: {max_days} days ({max_days/365.25:.1f} years)")
        return int(max_days)
        
    except Exception as e:
        print(f"Error during maximum duration calculation for relapse: {e}")
        return 365  # Fallback à 1 an


def create_relapse_analysis(data):
    """
    Crée l'analyse de risques compétitifs pour les rechutes - Version améliorée
    avec gestion de l'affichage initial limité
    
    Args:
        data (pd.DataFrame): DataFrame avec les données
        
    Returns:
        plotly.graph_objects.Figure: Figure de l'analyse des risques compétitifs
    """
    # Vérifier les colonnes nécessaires
    required_columns = [
        'Treatment Date', 'First Relapse', 'First Relapse Date',
        'Status Last Follow Up', 'Date Of Last Follow Up'
    ]
    
    missing_columns = [col for col in required_columns if col not in data.columns]
    
    if missing_columns:
        # Créer un graphique d'erreur informatif
        fig = go.Figure()
        fig.add_annotation(
            text=f"Missing variables for relapse analysis :<br>{', '.join(missing_columns)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            title="Competing risks analysis : relapse vs death",
            height=500,
            showlegend=False
        )
        return fig
    
    # Filtrer les données pour ne garder que celles avec les informations de base
    df_filtered = data.dropna(subset=['Treatment Date']).copy()
    
    if len(df_filtered) == 0:
        # Graphique vide si pas de données
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for the analysis",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            title="Competing risks analysis : relapse vs death",
            height=500,
            showlegend=False
        )
        return fig
    
    try:
        # Import de la classe CompetingRisksAnalyzer
        import modules.competing_risks as cr
        
        # NOUVEAUTÉ : Calculer la durée maximale réelle des données pour les rechutes
        max_days = calculate_max_relapse_followup_days(df_filtered)
        initial_display_days = 365  # Affichage initial limité à 1 an
        
        title = f"Competing risks analysis : relapse vs death (up to {max_days} days)"
        
        # Initialiser l'analyseur
        analyzer = cr.CompetingRisksAnalyzer(df_filtered, 'Treatment Date')
        
        # Configuration des événements pour la rechute
        events_config = {
            'Rechute': {
                'occurrence_col': 'First Relapse', 
                'date_col': 'First Relapse Date', 
                'label': 'Rechute',
                'color': '#f39c12'  # Orange/doré
            }
        }
        
        # Configuration du suivi
        followup_config = {
            'status_col': 'Status Last Follow Up',
            'date_col': 'Date Of Last Follow Up',
            'death_value': 'Dead'
        }
        
        # Calculer l'incidence cumulative avec la nouvelle durée maximale
        results, processed_data = analyzer.calculate_cumulative_incidence(
            events_config, followup_config, max_days=max_days
        )
        
        # Créer le graphique avec la méthode existante
        fig = analyzer.create_competing_risks_plot(
            results, processed_data, events_config, title=title
        )
        
        # NOUVEAUTÉ : Modifier l'affichage initial pour les rechutes
        if max_days > initial_display_days:
            # Limiter l'affichage initial à 1 an
            fig.update_xaxes(range=[0, initial_display_days])
            
            # Ajouter une annotation explicative
            fig.add_annotation(
                x=0.02, y=0.98,
                xref='paper', yref='paper',
                text=f"<b>Initial display: {initial_display_days} days (1 year)</b><br>" +
                     f"Data available up to {max_days} days<br>" +
                     "<i>Utilisez les contrôles de zoom pour voir au-delà</i>",
                showarrow=False,
                font=dict(size=10, color='#34495e'),
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="#f39c12",
                borderwidth=1,
                align="left"
            )
        
        return fig
        
    except Exception as e:
        # Graphique d'erreur si l'analyse échoue
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error during the analysis of competing risks :<br>{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=14
        )
        fig.update_layout(
            title="Competing risks analysis : relapse vs death",
            height=500,
            showlegend=False
        )
        return fig

def register_callbacks(app):
    """
    Enregistre les callbacks pour la page Rechute
    """
    
    # Callback principal pour le graphique Rechute
    @app.callback(
        Output('relapse-main-graph', 'children'),
        [Input('relapse-year-filter', 'value'),
         Input('data-store', 'data'),
         Input('current-page', 'data')]  # Ajouter current-page comme input
    )
    def update_relapse_main_graph(selected_years, data, current_page):
        """Met à jour le graphique principal d'analyse des risques compétitifs pour les rechutes"""
        
        # Ne rien afficher si on n'est pas sur la page Rechute
        if current_page != 'Relapse':
            return html.Div()
            
        if data is None:
            return dbc.Alert("No data available", color="warning")
        
        df = pd.DataFrame(data)
        
        # Filtrer les données par années sélectionnées
        if selected_years and 'Year' in df.columns:
            df = df[df['Year'].isin(selected_years)]
        
        try:
            fig = create_relapse_analysis(df)
            return dcc.Graph(figure=fig, style={'height': '100%', 'width': '100%'})
        except Exception as e:
            return dbc.Alert(f"Error during graph creation: {str(e)}", color="danger")
        
    @app.callback(
        Output('relapse-missing-summary-table', 'children'),
        [Input('data-store', 'data'), Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def relapse_missing_summary_callback(data, current_page):
        """Gère le tableau de résumé des données manquantes pour Rechute"""
        
        if current_page != 'Relapse' or not data:
            return html.Div("Waiting...", className='text-muted')
        
        try:
            df = pd.DataFrame(data)
            
            # Variables spécifiques à analyser pour Rechute
            columns_to_analyze = [
                # Variables de rechute
                'First Relapse',
                'First Relapse Date',
                
                # Variables de traitement et suivi
                'Treatment Date',
                'Status Last Follow Up',
                'Date Of Last Follow Up'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert("No relapse variable found", color='warning')
            
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
                            'filter_query': '{Percentage missing} > 20',
                            'column_id': 'Percentage missing'
                        },
                        'backgroundColor': '#F2A594',
                        'color': 'red',
                        'fontWeight': 'bold'
                    }
                ]
            )
            
        except Exception as e:
            return dbc.Alert(f"Error during analysis: {str(e)}", color='danger')

    @app.callback(
        [Output('relapse-missing-detail-table', 'children'),
         Output('export-missing-relapse-button', 'disabled')],
        [Input('data-store', 'data'), Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def relapse_missing_detail_callback(data, current_page):
        """Gère le tableau détaillé des patients avec données manquantes pour Rechute"""
        
        if current_page != 'Relapse' or not data:
            return html.Div("Waiting...", className='text-muted'), True
        
        try:
            df = pd.DataFrame(data)
            
            # Variables spécifiques à analyser pour Rechute
            columns_to_analyze = [
                # Variables de rechute
                'First Relapse',
                'First Relapse Date',
                
                # Variables de traitement et suivi
                'Treatment Date',
                'Status Last Follow Up',
                'Date Of Last Follow Up'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert("No relapse variable found", color='warning'), True
            
            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
            
            if detailed_missing.empty:
                return dbc.Alert("🎉 No missing data found !", color='success'), True
            
            # Adapter les noms de colonnes pour correspondre au format attendu
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Missing columns': row['Missing columns'],  
                    'Nb missing': row['Nb missing']  
                })
            
            # Sauvegarder les données pour l'export
            app.server.missing_relapse_data = detailed_data
            
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
            
            return table_content, False 
            
        except Exception as e:
            return dbc.Alert(f"Error during analysis: {str(e)}", color='danger'), True

    @app.callback(
        Output("download-missing-relapse-excel", "data"),
        Input("export-missing-relapse-button", "n_clicks"),
        prevent_initial_call=True
    )
    def export_missing_relapse_excel(n_clicks):
        """Gère l'export Excel des patients avec données manquantes pour Rechute"""
        if n_clicks is None:
            return dash.no_update
        
        try:
            # Récupérer les données stockées
            if hasattr(app.server, 'missing_relapse_data') and app.server.missing_relapse_data:
                missing_df = pd.DataFrame(app.server.missing_relapse_data)
                
                # Générer un nom de fichier avec la date
                from datetime import datetime
                current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"rechute_donnees_manquantes_{current_date}.xlsx"
                
                return dcc.send_data_frame(
                    missing_df.to_excel,
                    filename=filename,
                    index=False
                )
            else:
                return dash.no_update
                
        except Exception as e:
            print(f"Error during Excel export Relapse: {e}")
            return dash.no_update

def create_relapse_data_table(df):
    """
    Crée une table avec les données pertinentes pour les rechutes
    
    Args:
        df (pd.DataFrame): DataFrame avec les données
        
    Returns:
        html.Div: Composant contenant la table
    """
    relevant_columns = [
        'Treatment Date', 'First Relapse', 'First Relapse Date',
        'Status Last Follow Up', 'Date Of Last Follow Up', 'Year'
    ]
    
    # Filtrer les colonnes qui existent réellement
    available_columns = [col for col in relevant_columns if col in df.columns]
    
    if not available_columns:
        return dbc.Alert("Relapse data columns not found", color="warning")
    
    # Créer la table
    table_df = df[available_columns].head(100)  # Limiter à 100 lignes pour l'affichage
    
    return html.Div([
        html.H5("Relapse data", className="mb-3"),
        html.P(f"Displaying {len(table_df)} first lines out of {len(df)} total", 
               className="text-muted small"),
        dbc.Table.from_dataframe(
            table_df, 
            striped=True, 
            bordered=True, 
            hover=True, 
            responsive=True,
            size="sm"
        )
    ], style={'height': '400px', 'overflow': 'auto'})