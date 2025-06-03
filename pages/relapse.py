import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

# Import des modules nécessaires
import modules.dashboard_layout as layouts
import modules.competing_risks as cr

def get_layout():
    """
    Retourne le layout de la page Rechute
    """
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4('Analyse des Risques Compétitifs - Rechute')),
                dbc.CardBody([
                    html.Div(
                        id='relapse-main-graph',
                        style={'height': '800px', 'width': '100%'}
                    )
                ], className='p-2')
            ])
        ], width=12)
    ])

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
            html.P('Aucune donnée disponible', className='text-warning')
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
        html.H5('Filtres par année', className='mb-2'),
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
            html.H6("📊 Informations", className="mb-2"),
            html.P([
                "Patients: ", html.Strong(f"{len(df):,}")
            ], className="mb-1", style={'fontSize': '12px'}),
            html.P([
                "Années: ", html.Strong(f"{len(df['Year'].unique()) if 'Year' in df.columns else 0}")
            ], className="mb-0", style={'fontSize': '12px'})
        ])
    ])

def create_relapse_analysis(data):
    """
    Crée l'analyse de risques compétitifs pour les rechutes
    
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
            text=f"Colonnes manquantes pour l'analyse Rechute :<br>{', '.join(missing_columns)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            title="Analyse de Risques Compétitifs : Rechute vs Décès (365 jours)",
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
            text="Aucune donnée disponible pour l'analyse",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            title="Analyse de Risques Compétitifs : Rechute vs Décès (365 jours)",
            height=500,
            showlegend=False
        )
        return fig
    
    try:
        # Initialiser l'analyseur
        analyzer = cr.CompetingRisksAnalyzer(df_filtered, 'Treatment Date')
        
        # Configuration des événements pour la rechute
        events_config = {
            'Rechute': {
                'occurrence_col': 'First Relapse', 
                'date_col': 'First Relapse Date', 
                'label': 'Rechute',
                'color': 'orange'
            }
        }
        
        # Configuration du suivi
        followup_config = {
            'status_col': 'Status Last Follow Up',
            'date_col': 'Date Of Last Follow Up',
            'death_value': 'Dead'
        }
        
        # Calculer l'incidence cumulative sur 365 jours (1 an)
        results, processed_data = analyzer.calculate_cumulative_incidence(
            events_config, followup_config, max_days=365
        )
        
        # Créer le graphique
        fig = analyzer.create_competing_risks_plot(
            results, processed_data, events_config,
            title="Analyse de Risques Compétitifs : Rechute vs Décès (365 jours)"
        )
        
        return fig
        
    except Exception as e:
        # Graphique d'erreur si l'analyse échoue
        fig = go.Figure()
        fig.add_annotation(
            text=f"Erreur lors de l'analyse des risques compétitifs :<br>{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=14
        )
        fig.update_layout(
            title="Analyse de Risques Compétitifs : Rechute vs Décès (365 jours)",
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
        if current_page != 'Rechute':
            return html.Div()
            
        if data is None:
            return dbc.Alert("Aucune donnée disponible", color="warning")
        
        df = pd.DataFrame(data)
        
        # Filtrer les données par années sélectionnées
        if selected_years and 'Year' in df.columns:
            df = df[df['Year'].isin(selected_years)]
        
        try:
            fig = create_relapse_analysis(df)
            return dcc.Graph(figure=fig, style={'height': '100%', 'width': '100%'})
        except Exception as e:
            return dbc.Alert(f"Erreur lors de la création du graphique: {str(e)}", color="danger")

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
        return dbc.Alert("Colonnes de données Rechute non trouvées", color="warning")
    
    # Créer la table
    table_df = df[available_columns].head(100)  # Limiter à 100 lignes pour l'affichage
    
    return html.Div([
        html.H5("Données Rechute", className="mb-3"),
        html.P(f"Affichage des {len(table_df)} premières lignes sur {len(df)} total", 
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