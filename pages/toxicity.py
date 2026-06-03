import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

# Import des modules nécessaires
import modules.dashboard_layout as layouts
from modules.dashboard_layout import apply_malignancy_filter
import modules.competing_risks as cr
import visualizations.allogreffes.graphs as gr


NRM_INFO_TEXT = """Event = Death without prior relapse (NRM)
Competing = Death after relapse"""


def get_layout():
    """
    Retourne le layout de la page Toxicity
    """
    return dbc.Container([
        dcc.Store(id='toxicity-missing-store'),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Div([
                            html.H4('Non-Relapse Mortality', className='mb-0 d-inline'),
                            html.Span(layouts.create_info_tooltip(NRM_INFO_TEXT, "toxicity-main-info"))
                        ])
                    ),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-toxicity-nrm",
                            type="circle",
                            children=
                            html.Div(
                                id='toxicity-nrm-graph',
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
                        html.Div(id='toxicity-missing-summary-table', children=[
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
                                id="export-missing-toxicity-button",
                                color="primary",
                                size="sm",
                                disabled=True,  # Désactivé par défaut
                            )
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody([
                        html.Div(id='toxicity-missing-detail-table', children=[
                            dbc.Alert("Initial content - will be replaced by the callback", color='warning')
                        ]),
                        # Composant pour télécharger le fichier Excel (invisible)
                        dcc.Download(id="download-missing-toxicity-excel")
                    ])
                ])
            ], width=6)
        ])
    ], fluid=True)


def create_toxicity_sidebar_content(data, pediatric_view=False):
    """
    Crée le contenu de la sidebar spécifique à la page Toxicity.

    Args:
        data (list): Liste de dictionnaires (format store Dash) avec les données
        pediatric_view (bool): Si True, affiche le filtre d'âge pédiatrique

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

    controls = [
        layouts.create_pediatric_switch_component(pediatric_view),

        # Filtres par année
        html.H5('Year filters', className='mb-2'),
        dcc.Checklist(
            id='toxicity-year-filter',
            options=years_options,
            value=[year['value'] for year in years_options],
            inline=False,
            className='mb-3'
        ),

        html.Hr(),
        # Filtre d'âge toujours présent dans le DOM mais caché en vue normale
        layouts.create_age_filter_component(
            component_id='toxicity-age-filter',
            title='Age groups',
            pediatric_only=pediatric_view,
            hidden=not pediatric_view
        ),

        html.Hr(),

        # Filtres par type de diagnostic
        layouts.create_malignancy_filter_component(component_id='toxicity-malignancy-filter', title='Diagnosis type'),

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
    ]

    return html.Div(controls)


def calculate_max_relapse_followup_days(data):
    """
    Calcule la durée maximale de suivi dans les données pour déterminer
    jusqu'où dessiner le graphique

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

        print(f"Maximum duration calculated for toxicity: {max_days} days ({max_days/365.25:.1f} years)")
        return int(max_days)

    except Exception as e:
        print(f"Error during maximum duration calculation for toxicity: {e}")
        return 365  # Fallback à 1 an


def create_trm_competing_risks_analysis(data):
    """
    Crée l'analyse de risques compétitifs pour la TRM (Treatment-Related Mortality)

    Event = décès sans rechute préalable (TRM)
    Competing = rechute

    Args:
        data (pd.DataFrame): DataFrame avec les données

    Returns:
        plotly.graph_objects.Figure: Figure de l'analyse des risques compétitifs
    """
    required_columns = [
        'Treatment Date', 'First Relapse', 'First Relapse Date',
        'Status Last Follow Up', 'Date Of Last Follow Up'
    ]

    missing_columns = [col for col in required_columns if col not in data.columns]

    if missing_columns:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Missing variables for TRM analysis :<br>{', '.join(missing_columns)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            title="Competing risks analysis : NRM vs relapse",
            height=500,
            showlegend=False
        )
        return fig

    df_filtered = data.dropna(subset=['Treatment Date']).copy()

    if len(df_filtered) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for the analysis",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            title="Competing risks analysis : NRM vs relapse",
            height=500,
            showlegend=False
        )
        return fig

    try:
        import modules.competing_risks as cr

        # Créer les colonnes TRM
        df_filtered['Treatment Date_dt'] = pd.to_datetime(df_filtered['Treatment Date'], format='mixed', errors='coerce')
        df_filtered['Date Of Last Follow Up_dt'] = pd.to_datetime(df_filtered['Date Of Last Follow Up'], format='mixed', errors='coerce')
        df_filtered['First Relapse Date_dt'] = pd.to_datetime(df_filtered['First Relapse Date'], format='mixed', errors='coerce')

        # TRM = décès sans rechute préalable
        death_mask = df_filtered['Status Last Follow Up'].astype(str).str.strip().str.lower() == 'dead'
        relapse_mask = df_filtered['First Relapse'].astype(str).str.strip().str.lower() == 'yes'

        # Rechute avant ou au moment du décès
        relapse_before_death = (
            relapse_mask &
            df_filtered['First Relapse Date_dt'].notna() &
            df_filtered['Date Of Last Follow Up_dt'].notna() &
            (df_filtered['First Relapse Date_dt'] <= df_filtered['Date Of Last Follow Up_dt'])
        )

        trm_mask = death_mask & ~relapse_before_death

        df_filtered['TRM Event'] = 'No'
        df_filtered.loc[trm_mask, 'TRM Event'] = 'Yes'
        df_filtered['TRM Date'] = pd.NaT
        df_filtered.loc[trm_mask, 'TRM Date'] = df_filtered.loc[trm_mask, 'Date Of Last Follow Up']

        # Calculer la durée maximale
        max_days = calculate_max_relapse_followup_days(df_filtered)
        initial_display_days = 365

        title = f"Competing risks analysis : NRM vs relapse (up to {max_days} days)"

        analyzer = cr.CompetingRisksAnalyzer(df_filtered, 'Treatment Date')

        events_config = {
            'NRM': {
                'occurrence_col': 'TRM Event',
                'date_col': 'TRM Date',
                'label': 'NRM (death without relapse)',
                'color': '#e74c3c'
            },
            'Relapse': {
                'occurrence_col': 'First Relapse',
                'date_col': 'First Relapse Date',
                'label': 'Relapse',
                'color': '#f39c12'
            }
        }

        followup_config = {
            'status_col': 'Status Last Follow Up',
            'date_col': 'Date Of Last Follow Up',
            'death_value': 'Dead'
        }

        results, processed_data = analyzer.calculate_cumulative_incidence(
            events_config, followup_config, max_days=max_days, death_as_competing=False
        )

        fig = analyzer.create_competing_risks_plot(
            results, processed_data, events_config, title=title
        )

        if max_days > initial_display_days:
            fig.update_xaxes(range=[0, initial_display_days])
            fig.add_annotation(
                x=0.02, y=0.98,
                xref='paper', yref='paper',
                text=f"<b>Initial display: {initial_display_days} days (1 year)</b><br>" +
                     f"Data available up to {max_days} days<br>" +
                     "<i>Use zoom & pan controls to see beyond</i>",
                showarrow=False,
                font=dict(size=10, color='#34495e'),
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="#e74c3c",
                borderwidth=1,
                align="left"
            )

        return fig

    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error during the analysis of competing risks :<br>{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=14
        )
        fig.update_layout(
            title="Competing risks analysis : NRM vs relapse",
            height=500,
            showlegend=False
        )
        return fig


def register_callbacks(app):
    """
    Enregistre les callbacks pour la page Toxicity
    """

    # Callback principal pour le graphique NRM
    @app.callback(
        Output('toxicity-nrm-graph', 'children'),
        [Input('toxicity-year-filter', 'value'),
         Input('toxicity-age-filter', 'value'),
         Input('toxicity-malignancy-filter', 'value'),
         Input('data-store', 'data'),
         Input('current-page', 'data')]
    )
    def update_toxicity_nrm_graph(selected_years, selected_age_groups, malignancy_filter, data, current_page):
        """Met à jour le graphique d'analyse des risques compétitifs pour la TRM"""

        if current_page != 'Toxicity':
            return html.Div()

        if data is None:
            return dbc.Alert("No data available", color="warning")

        df = pd.DataFrame(data)

        # Filtrer les données par années sélectionnées
        if selected_years and 'Year' in df.columns:
            df = df[df['Year'].isin(selected_years)]

        # Filtrer par tranches d'âge
        if selected_age_groups and 'Age Group Detailed' in df.columns:
            df = df[df['Age Group Detailed'].isin(selected_age_groups)]

        # Filtrer par type de diagnostic
        df = apply_malignancy_filter(df, malignancy_filter)

        try:
            fig = create_trm_competing_risks_analysis(df)
            return dcc.Graph(figure=fig, style={'height': '100%', 'width': '100%'})
        except Exception as e:
            return dbc.Alert(f"Error during TRM graph creation: {str(e)}", color="danger")

    @app.callback(
        Output('toxicity-missing-summary-table', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('toxicity-year-filter', 'value'),
         Input('toxicity-age-filter', 'value'),
         Input('toxicity-malignancy-filter', 'value')],
        prevent_initial_call=False
    )
    def toxicity_missing_summary_callback(data, current_page, selected_years, selected_age_groups, malignancy_filter):
        """Gère le tableau de résumé des données manquantes pour Toxicity"""

        if current_page != 'Toxicity' or not data:
            return html.Div("Waiting...", className='text-muted')

        try:
            df = pd.DataFrame(data)

            # Filtrer par années si spécifié
            if selected_years and 'Year' in df.columns:
                df = df[df['Year'].isin(selected_years)]

            # Filtrer par tranches d'âge
            if selected_age_groups and 'Age Group Detailed' in df.columns:
                df = df[df['Age Group Detailed'].isin(selected_age_groups)]

            # Filtrer par type de diagnostic
            df = apply_malignancy_filter(df, malignancy_filter)

            if df.empty:
                return html.Div('No data for the selected years', className='text-warning text-center')

            # Variables spécifiques à analyser pour Toxicity / NRM
            columns_to_analyze = [
                # Variables de suivi et décès
                'Status Last Follow Up',
                'Date Of Last Follow Up',

                # Variables de rechute (utilisées pour définir TRM)
                'First Relapse',
                'First Relapse Date',

                # Variables de traitement
                'Treatment Date'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]

            if not existing_columns:
                return dbc.Alert("No variable found for toxicity analysis", color='warning')

            missing_summary, _ = gr.analyze_missing_data(df, existing_columns, 'Long ID')

            # Calculer le nombre de patients décédés pendant le conditionnement
            died_during_conditioning = 0
            if 'Status Last Follow Up' in df.columns and 'Treatment Date' in df.columns and 'Date Of Last Follow Up' in df.columns:
                died_during_conditioning = df.apply(gr._is_patient_died_during_conditioning, axis=1).sum()

            # Créer le contenu avec optionnellement l'info sur les décès pendant conditionnement
            content = []

            if died_during_conditioning > 0:
                content.append(
                    dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        html.Strong(f"{died_during_conditioning} patient(s) "),
                        "died during conditioning. TRM data are not applicable for these patients and are excluded from missing data counts."
                    ], color='info', className='mb-2', style={'fontSize': '12px'})
                )

            content.append(
                dash_table.DataTable(
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
            )

            return html.Div(content)

        except Exception as e:
            return dbc.Alert(f"Error during analysis: {str(e)}", color='danger')

    @app.callback(
        [Output('toxicity-missing-detail-table', 'children'),
         Output('export-missing-toxicity-button', 'disabled'),
         Output('toxicity-missing-store', 'data')],
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('toxicity-year-filter', 'value'),
         Input('toxicity-age-filter', 'value'),
         Input('toxicity-malignancy-filter', 'value')],
        prevent_initial_call=False
    )
    def toxicity_missing_detail_callback(data, current_page, selected_years, selected_age_groups, malignancy_filter):
        """Gère le tableau détaillé des patients avec données manquantes pour Toxicity"""

        if current_page != 'Toxicity' or not data:
            return html.Div("Waiting...", className='text-muted'), True, None

        try:
            df = pd.DataFrame(data)

            # Filtrer par années si spécifié
            if selected_years and 'Year' in df.columns:
                df = df[df['Year'].isin(selected_years)]

            # Filtrer par tranches d'âge
            if selected_age_groups and 'Age Group Detailed' in df.columns:
                df = df[df['Age Group Detailed'].isin(selected_age_groups)]

            # Filtrer par type de diagnostic
            df = apply_malignancy_filter(df, malignancy_filter)

            if df.empty:
                return html.Div('No data for the selected years', className='text-warning text-center'), True, None

            # Variables spécifiques à analyser pour Toxicity / NRM
            columns_to_analyze = [
                'Status Last Follow Up',
                'Date Of Last Follow Up',
                'First Relapse',
                'First Relapse Date',
                'Treatment Date'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]

            if not existing_columns:
                return dbc.Alert("No variable found for toxicity analysis", color='warning'), True, None

            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')

            if detailed_missing.empty:
                return dbc.Alert("🎉 No missing data found !", color='success'), True, None

            # Adapter les noms de colonnes pour correspondre au format attendu
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Missing columns': row['Missing columns'],
                    'Nb missing': row['Nb missing']
                })

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

            return table_content, False, detailed_data

        except Exception as e:
            return dbc.Alert(f"Error during analysis: {str(e)}", color='danger'), True, None

    @app.callback(
        Output("download-missing-toxicity-excel", "data"),
        Input("export-missing-toxicity-button", "n_clicks"),
        State('toxicity-missing-store', 'data'),
        prevent_initial_call=True
    )
    def export_missing_toxicity_excel(n_clicks, missing_data):
        """Gère l'export Excel des patients avec données manquantes pour Toxicity"""
        if n_clicks is None:
            return dash.no_update

        try:
            # Récupérer les données stockées
            if missing_data:
                missing_df = pd.DataFrame(missing_data)

                # Générer un nom de fichier avec la date
                from datetime import datetime
                current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"toxicite_donnees_manquantes_{current_date}.xlsx"

                return dcc.send_data_frame(
                    missing_df.to_excel,
                    filename=filename,
                    index=False
                )
            else:
                return dash.no_update

        except Exception as e:
            print(f"Error during Excel export Toxicity: {e}")
            return dash.no_update
