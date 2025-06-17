import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import des modules communs
import modules.dashboard_layout as layouts

def get_layout():
    """Retourne le layout de la page Indicateurs"""
    return dbc.Container([
        # Zone principale pour l'affichage de l'indicateur sélectionné
        dbc.Row([
            dbc.Col([
                html.Div(
                    id='indicator-content',
                    style={'min-height': '600px'}
                )
            ], width=12)
        ])
    ], fluid=True)

def create_indicators_sidebar_content(data):
    """
    Crée le contenu de la sidebar spécifique à la page Indicateurs.
    
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
    
    # Obtenir les années disponibles
    years_options = []
    if 'Year' in df.columns:
        available_years = sorted(df['Year'].unique().tolist())
        # Pour TRM, on a besoin de l'année n-2, donc on retire les 2 premières années
        # de la liste pour l'input (on sélectionne 2025 pour voir les stats de 2023)
        if len(available_years) > 2:
            selectable_years = available_years[2:]  # On retire les 2 premières années
            years_options = [{'label': f'{year}', 'value': year} for year in selectable_years]
    
    return html.Div([
        # Sélection de l'indicateur
        html.Label('Indicateur:', className='mb-2'),
        dcc.Dropdown(
            id='indicator-selection',
            options=[
                {'label': 'TRM (Mortalité liée au traitement)', 'value': 'TRM'},
                {'label': 'Survie globale', 'value': 'survie_globale'},
                {'label': 'Prise de greffe', 'value': 'prise_greffe'},
                {'label': 'Sortie d\'aplasie', 'value': 'sortie_aplasie'},
                {'label': 'GVH aiguë', 'value': 'gvha'},
                {'label': 'GVH chronique', 'value': 'gvhc'},
                {'label': 'Rechute', 'value': 'rechute'}
            ],
            value='TRM',
            className='mb-3'
        ),
        
        html.Hr(),
        
        # Sélection de l'année
        html.Label('Année de référence:', className='mb-2'),
        dcc.Dropdown(
            id='indicator-year-selection',
            options=years_options,
            value=years_options[-1]['value'] if years_options else None,
            className='mb-3'
        ),
        
        html.Div([
            html.P("Note: Les statistiques affichées correspondent à l'année n-2", 
                   className='text-info small', style={'fontSize': '11px'})
        ], id='year-note', style={'display': 'none'}),  # Caché par défaut
        
        html.Hr(),
        
        # Informations sur les données
        html.Div([
            html.H6("📊 Informations", className="mb-2"),
            html.P([
                "Patients: ", html.Strong(f"{len(df):,}")
            ], className="mb-1", style={'fontSize': '12px'}),
            html.P([
                "Années disponibles: ", html.Strong(f"{len(available_years) if 'Year' in df.columns else 0}")
            ], className="mb-0", style={'fontSize': '12px'})
        ])
    ])

def process_trm_data(df):
    """
    Traite les données pour calculer les indicateurs TRM
    
    Args:
        df (pd.DataFrame): DataFrame avec les données
        
    Returns:
        pd.DataFrame: DataFrame avec les statistiques TRM par année et jour
    """
    # Vérifier les colonnes nécessaires
    required_cols = ['Year', 'Status Last Follow Up', 'Death Cause', 'Treatment Date', 'Date Of Last Follow Up']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Colonnes manquantes pour l'analyse TRM: {missing_cols}")
    
    # Calculer Follow_up_days si nécessaire
    if 'Follow_up_days' not in df.columns:
        df = df.copy()
        df['Treatment Date'] = pd.to_datetime(df['Treatment Date'])
        df['Date Of Last Follow Up'] = pd.to_datetime(df['Date Of Last Follow Up'])
        df['Follow_up_days'] = (df['Date Of Last Follow Up'] - df['Treatment Date']).dt.days
    
    # Compter le nombre de greffes par année
    nb_greffe_year = df.groupby('Year').size().reset_index(name='nb_greffe')
    
    # Filtrer et transformer les données
    filtered_df = df[['Year', 'Follow_up_days', 'Status Last Follow Up', 'Death Cause']].copy()
    
    # Filtrer les causes de décès spécifiques (TRM)
    filtered_df = filtered_df[filtered_df['Death Cause'].isin([
        'Cellular therapy-related cause of death', 
        'HCT-related cause of death'
    ])]
    
    # Appliquer les filtres pour le statut de décès et le suivi
    filtered_df = filtered_df[
        (filtered_df['Status Last Follow Up'] == 'Dead') | 
        ((filtered_df['Status Last Follow Up'] == 'Alive') & (filtered_df['Follow_up_days'] >= 365))
    ]
    
    # Calculer les indicateurs de décès à J30, J100 et J365
    filtered_df['trm_j30'] = np.where(
        (filtered_df['Status Last Follow Up'] == 'Dead') & (filtered_df['Follow_up_days'] <= 30), 
        1, 0
    )
    filtered_df['trm_j100'] = np.where(
        (filtered_df['Status Last Follow Up'] == 'Dead') & (filtered_df['Follow_up_days'] <= 100), 
        1, 0
    )
    filtered_df['trm_j365'] = np.where(
        (filtered_df['Status Last Follow Up'] == 'Dead') & (filtered_df['Follow_up_days'] <= 365), 
        1, 0
    )
    
    # Grouper par année et calculer les sommes
    death_summary = filtered_df.groupby('Year').agg({
        'trm_j30': 'sum',
        'trm_j100': 'sum',
        'trm_j365': 'sum'
    }).reset_index()
    
    # Fusionner avec le nombre total de greffes par année
    result_df = pd.merge(death_summary, nb_greffe_year, on='Year', how='left')
    
    # Ajouter une colonne pour J0 (toujours 0)
    result_df['trm_j0'] = 0
    
    # Calculer les pourcentages de décès
    result_df['0'] = 0.0  # Toujours 0% à J0
    result_df['30'] = round(result_df['trm_j30'] / result_df['nb_greffe'] * 100, 1)
    result_df['100'] = round(result_df['trm_j100'] / result_df['nb_greffe'] * 100, 1)
    result_df['365'] = round(result_df['trm_j365'] / result_df['nb_greffe'] * 100, 1)
    
    # Transformer en format long
    result_long = result_df[['Year', '0', '30', '100', '365']].melt(
        id_vars=['Year'],
        value_vars=['0', '30', '100', '365'],
        var_name='j',
        value_name='pourcentage_deces'
    )
    
    # Convertir la colonne 'j' en numérique
    result_long['j'] = result_long['j'].astype(int)
    
    return result_long, result_df

def create_trm_visualization(df, selected_year):
    """
    Crée la visualisation complète pour l'indicateur TRM
    Args:
        df (pd.DataFrame): DataFrame avec les données
        selected_year (int): Année sélectionnée (on affichera l'année n-2)
    Returns:
        html.Div: Composant contenant la visualisation complète
    """
    try:
        # Traiter les données
        result_long, result_df = process_trm_data(df)
        
        # Convertir l'année en int et calculer n-2
        selected_year = int(selected_year)
        analysis_year = selected_year - 2
        
        # S'assurer que la colonne Year est de type int
        result_df['Year'] = result_df['Year'].astype(int)
        
        # Créer le layout avec deux colonnes
        return dbc.Row([
            # Colonne gauche : Graphique des courbes (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_trm_curves_plot(result_long),
                    style={'height': '600px'},
                    config={'responsive': True}
                )
            ], width=7),
            # Colonne droite : DataTable et jauges (40%)
            dbc.Col([
                # DataTable
                create_trm_datatable(result_df),
                html.Hr(className='my-3'),
                # Jauges pour l'année sélectionnée
                html.H6(f"Indicateurs {selected_year} pour l'année {analysis_year}", className='text-center mb-3'),
                create_trm_gauges(result_df, analysis_year)
            ], width=5)
        ])
    except Exception as e:
        return dbc.Alert(f"Erreur lors du calcul des indicateurs TRM: {str(e)}", color="danger")

def create_trm_curves_plot(result_long):
    """
    Crée le graphique des courbes TRM par année
    
    Args:
        result_long (pd.DataFrame): DataFrame en format long avec les données TRM
        
    Returns:
        plotly.graph_objects.Figure: Figure Plotly
    """
    fig = go.Figure()
    
    # Obtenir les années uniques
    years = sorted(result_long['Year'].unique())
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    
    # Créer une courbe pour chaque année
    for i, year in enumerate(years):
        year_data = result_long[result_long['Year'] == year].sort_values('j')
        
        fig.add_trace(go.Scatter(
            x=year_data['j'],
            y=year_data['pourcentage_deces'],
            mode='lines+markers',
            name=f'Année {year}',
            line=dict(color=colors[i % len(colors)], width=3),
            marker=dict(size=8),
            customdata=[year] * len(year_data)
        ))
    
    # Ajouter des lignes verticales pour J30, J100 et J365
    for day in [30, 100, 365]:
        fig.add_vline(
            x=day, 
            line_dash="dash", 
            line_color="gray", 
            opacity=0.5,
            annotation_text=f"J{day}",
            annotation_position="top"
        )
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': '<b>Évolution de la mortalité liée au traitement (TRM)</b>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='<b>Jours post-greffe</b>',
        yaxis_title='<b>Taux de mortalité (%)</b>',
        xaxis=dict(
            tickmode='array',
            tickvals=[0, 30, 100, 200, 365],
            ticktext=['J0', 'J30', 'J100', 'J200', 'J365'],
            range=[-10, 380]
        ),
        yaxis=dict(
            range=[0, max(result_long['pourcentage_deces'].max() * 1.1, 10)],
            tickformat='.1f'
        ),
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        template='plotly_white',
        margin=dict(r=150)
    )
    
    return fig

def create_trm_datatable(result_df):
    """
    Crée la DataTable pour afficher les statistiques TRM par année
    
    Args:
        result_df (pd.DataFrame): DataFrame avec les statistiques TRM
        
    Returns:
        html.Div: Composant DataTable
    """
    # Préparer les données pour la table
    table_data = []
    for _, row in result_df.iterrows():
        table_data.append({
            'Année': int(row['Year']),
            'Décès J30': int(row['trm_j30']),
            '% J30': f"{row['30']:.1f}%",
            'Décès J100': int(row['trm_j100']),
            '% J100': f"{row['100']:.1f}%",
            'Décès J365': int(row['trm_j365']),
            '% J365': f"{row['365']:.1f}%"
        })
    
    return html.Div([
        html.H6("Statistiques par année", className='mb-2'),
        dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Année", "id": "Année"},
                {"name": "Décès J30", "id": "Décès J30"},
                {"name": "% J30", "id": "% J30"},
                {"name": "Décès J100", "id": "Décès J100"},
                {"name": "% J100", "id": "% J100"},
                {"name": "Décès J365", "id": "Décès J365"},
                {"name": "% J365", "id": "% J365"}
            ],
            style_table={'height': '250px', 'overflowY': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '8px',
                'fontSize': '12px'
            },
            style_header={
                'backgroundColor': '#0D3182',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ]
        )
    ])

def create_trm_gauges(result_df, analysis_year):
    """
    Crée les jauges modernes style flexDashboard pour afficher les taux de mortalité
    """
    # S'assurer que analysis_year est de type int
    analysis_year = int(analysis_year)
    
    # Obtenir les données pour l'année spécifiée
    year_data = result_df[result_df['Year'] == analysis_year]
    
    if year_data.empty:
        available_years = result_df['Year'].unique()
        return dbc.Alert(
            f"Aucune donnée disponible pour l'année {analysis_year} (années disponibles: {sorted(available_years)})", 
            color="warning"
        )
    
    # Extraire les valeurs
    val_j30 = year_data['30'].iloc[0]
    val_j100 = year_data['100'].iloc[0]
    val_j365 = year_data['365'].iloc[0]
    
    # Configuration commune
    common_gauge_config = {
        'axis': {
            'range': [None, 100],
            'tickwidth': 1,
            'tickcolor': 'rgba(0,0,0,0.3)',
            'tickfont': {'size': 10},
            'ticksuffix': '%'
        },
        'bar': {
            'color': '#2c3e50',
            'thickness': 0.25
        },
        'bgcolor': 'white',
        'borderwidth': 0,
        'bordercolor': 'rgba(0,0,0,0)',
        'threshold': {
            'line': {'color': '#2c3e50', 'width': 2},
            'thickness': 0.75
        }
    }
    
    # Créer les 3 jauges avec un subplot
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}]],
        subplot_titles=['<b>J30</b>', '<b>J100</b>', '<b>J365</b>'],
        horizontal_spacing=0.15
    )
    
    # Jauge J30
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=val_j30,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={
            'suffix': '%',
            'font': {'size': 24, 'color': '#2c3e50'},
            'valueformat': '.1f'
        },
        gauge={
            **common_gauge_config,
            'steps': [
                {'range': [0, 5], 'color': '#27ae60'},
                {'range': [5, 10], 'color': '#f39c12'},
                {'range': [10, 100], 'color': '#e74c3c'}
            ],
            'threshold': {'value': val_j30}
        },
        title={
            'text': f"<b>J30</b>",
            'font': {'size': 14, 'color': '#2c3e50'},
            'align': 'center'
        }
    ), row=1, col=1)
    
    # Jauge J100
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=val_j100,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={
            'suffix': '%',
            'font': {'size': 24, 'color': '#2c3e50'},
            'valueformat': '.1f'
        },
        gauge={
            **common_gauge_config,
            'steps': [
                {'range': [0, 10], 'color': '#27ae60'},
                {'range': [10, 20], 'color': '#f39c12'},
                {'range': [20, 100], 'color': '#e74c3c'}
            ],
            'threshold': {'value': val_j100}
        },
        title={
            'text': f"<b>J100</b>",
            'font': {'size': 14, 'color': '#2c3e50'},
            'align': 'center'
        }
    ), row=1, col=2)
    
    # Jauge J365
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=val_j365,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={
            'suffix': '%',
            'font': {'size': 24, 'color': '#2c3e50'},
            'valueformat': '.1f'
        },
        gauge={
            **common_gauge_config,
            'steps': [
                {'range': [0, 20], 'color': '#27ae60'},
                {'range': [20, 40], 'color': '#f39c12'},
                {'range': [40, 100], 'color': '#e74c3c'}
            ],
            'threshold': {'value': val_j365}
        },
        title={
            'text': f"<b>J365</b>",
            'font': {'size': 14, 'color': '#2c3e50'},
            'align': 'center'
        }
    ), row=1, col=3)
    
    # Mise en forme globale
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=80, b=20),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial, sans-serif"),
        annotations=[
            dict(
                x=0.5,
                y=1.15,
                showarrow=False,
                text="Taux de mortalité liée au traitement",
                xref="paper",
                yref="paper",
                font=dict(size=14, color='#2c3e50')
            )
        ]
    )
    
    # Style des sous-titres
    fig.update_annotations(
        font_size=12,
        font_color="#7f8c8d"
    )
    
    return dcc.Graph(
        figure=fig,
        config={'displayModeBar': False},
        style={
            'border-radius': '10px',
            'box-shadow': '0 2px 5px rgba(0,0,0,0.1)',
            'background': 'white',
            'padding': '10px'
        }
    )

def process_survie_data(df):
    """
    Traite les données pour calculer les indicateurs de Survie Globale
    """
    # Calculer Follow_up_days si nécessaire
    if 'Follow_up_days' not in df.columns:
        df = df.copy()
        df['Treatment Date'] = pd.to_datetime(df['Treatment Date'])
        df['Date Of Last Follow Up'] = pd.to_datetime(df['Date Of Last Follow Up'])
        df['Follow_up_days'] = (df['Date Of Last Follow Up'] - df['Treatment Date']).dt.days

    required_cols = ['Year', 'Status Last Follow Up', 'Follow_up_days']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes pour l'analyse Survie Globale: {missing_cols}")

    # Compter le nombre de greffes par année
    nb_greffe_year = df.groupby('Year').size().reset_index(name='nb_greffe')

    # Filtrer et transformer les données
    filtered_df = df[['Year', 'Follow_up_days', 'Status Last Follow Up']].copy()

    # Appliquer les filtres pour le statut de décès et le suivi
    filtered_df = filtered_df[
        (filtered_df['Status Last Follow Up'].isin(['Dead', 'Died after conditioning but before main treatment'])) |
        ((filtered_df['Status Last Follow Up'] == 'Alive') & (filtered_df['Follow_up_days'] >= 365))
    ]

    # Calcul des indicateurs
    filtered_df['deces_j30'] = np.where(
        (filtered_df['Status Last Follow Up'].isin(['Dead', 'Died after conditioning but before main treatment'])) & 
        (filtered_df['Follow_up_days'] <= 30),
        1, 0
    )
    filtered_df['deces_j100'] = np.where(
        (filtered_df['Status Last Follow Up'].isin(['Dead', 'Died after conditioning but before main treatment'])) & 
        (filtered_df['Follow_up_days'] <= 100),
        1, 0
    )
    filtered_df['deces_j365'] = np.where(
        (filtered_df['Status Last Follow Up'].isin(['Dead', 'Died after conditioning but before main treatment'])) & 
        (filtered_df['Follow_up_days'] <= 365),
        1, 0
    )

    # Agrégation par année
    death_summary = filtered_df.groupby('Year').agg({
        'deces_j30': 'sum',
        'deces_j100': 'sum',
        'deces_j365': 'sum'
    }).reset_index()

    # Fusion avec le nombre total de greffes
    result_df = pd.merge(death_summary, nb_greffe_year, on='Year', how='left')

    # Calcul des survivants et pourcentages
    result_df['vivants_j30'] = result_df['nb_greffe'] - result_df['deces_j30']
    result_df['vivants_j100'] = result_df['nb_greffe'] - result_df['deces_j100']
    result_df['vivants_j365'] = result_df['nb_greffe'] - result_df['deces_j365']

    result_df['30'] = round(result_df['vivants_j30'] / result_df['nb_greffe'] * 100, 1)
    result_df['100'] = round(result_df['vivants_j100'] / result_df['nb_greffe'] * 100, 1)
    result_df['365'] = round(result_df['vivants_j365'] / result_df['nb_greffe'] * 100, 1)
    result_df['0'] = 100.0  # Ajout de J0 à 100%

    # Format long
    result_long = result_df[['Year', '0', '30', '100', '365']].melt(
        id_vars=['Year'],
        value_vars=['0', '30', '100', '365'],
        var_name='j',
        value_name='pourcentage_survie'
    )
    result_long['j'] = result_long['j'].astype(int)

    return result_long, result_df

def create_survie_visualization(df, selected_year):
    """
    Crée la visualisation complète pour l'indicateur Survie Globale
    """
    try:
        result_long, result_df = process_survie_data(df)
        analysis_year = int(selected_year) - 2
        result_df['Year'] = result_df['Year'].astype(int)

        return dbc.Row([
            dbc.Col([
                dcc.Graph(
                    figure=create_survie_curves_plot(result_long),
                    style={'height': '600px'}
                )
            ], width=7),
            dbc.Col([
                create_survie_datatable(result_df),
                html.Hr(className='my-3'),
                html.H6(f"Indicateurs pour l'année {analysis_year}", className='text-center mb-3'),
                create_survie_gauges(result_df, analysis_year)
            ], width=5)
        ])
    except Exception as e:
        return dbc.Alert(f"Erreur lors du calcul des indicateurs de Survie Globale: {str(e)}", color="danger")

def create_survie_curves_plot(result_long):
    """
    Crée le graphique des courbes de survie
    """
    fig = go.Figure()
    years = sorted(result_long['Year'].unique())
    colors = ['#3498db', '#2ecc71', '#e74c3c', '#9b59b6', '#f1c40f', '#1abc9c', '#e67e22']

    for i, year in enumerate(years):
        year_data = result_long[result_long['Year'] == year].sort_values('j')
        fig.add_trace(go.Scatter(
            x=year_data['j'],
            y=year_data['pourcentage_survie'],
            mode='lines+markers',
            name=f'Année {year}',
            line=dict(color=colors[i % len(colors)], width=3),
            marker=dict(size=8),
            customdata=[year] * len(year_data)
        ))

    # Ajout des lignes verticales
    for day in [30, 100, 365]:
        fig.add_vline(
            x=day,
            line_dash="dash",
            line_color="gray",
            opacity=0.5,
            annotation_text=f"J{day}",
            annotation_position="top"
        )

    fig.update_layout(
        title={
            'text': '<b>Évolution de la Survie Globale</b>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='<b>Jours post-greffe</b>',
        yaxis_title='<b>Taux de survie (%)</b>',
        xaxis=dict(
            tickmode='array',
            tickvals=[0, 30, 100, 200, 365],
            ticktext=['J0', 'J30', 'J100', 'J200', 'J365'],
            range=[-10, 380]
        ),
        yaxis=dict(
            range=[50, 105],  # Ajusté pour mieux voir les variations
            tickformat='.1f'
        ),
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        template='plotly_white',
        margin=dict(r=150)
    )
    return fig

def create_survie_datatable(result_df):
    """
    Crée la table des résultats de survie
    """
    table_data = []
    for _, row in result_df.iterrows():
        table_data.append({
            'Année': int(row['Year']),
            'Survivants J30': int(row['vivants_j30']),
            '% J30': f"{row['30']:.1f}%",
            'Survivants J100': int(row['vivants_j100']),
            '% J100': f"{row['100']:.1f}%",
            'Survivants J365': int(row['vivants_j365']),
            '% J365': f"{row['365']:.1f}%"
        })

    return html.Div([
        html.H6("Statistiques par année", className='mb-2'),
        dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Année", "id": "Année"},
                {"name": "Survivants J30", "id": "Survivants J30"},
                {"name": "% J30", "id": "% J30"},
                {"name": "Survivants J100", "id": "Survivants J100"},
                {"name": "% J100", "id": "% J100"},
                {"name": "Survivants J365", "id": "Survivants J365"},
                {"name": "% J365", "id": "% J365"}
            ],
            style_table={'height': '250px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'center', 'padding': '8px', 'fontSize': '12px'},
            style_header={
                'backgroundColor': '#0D3182',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[{
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            }]
        )
    ])

def create_survie_gauges(result_df, analysis_year):
    """
    Crée les jauges de survie (version moderne)
    """
    analysis_year = int(analysis_year)
    year_data = result_df[result_df['Year'] == analysis_year]
    
    if year_data.empty:
        available_years = result_df['Year'].unique()
        return dbc.Alert(
            f"Aucune donnée disponible pour l'année {analysis_year} (années disponibles: {sorted(available_years)})", 
            color="warning"
        )
    
    val_j30 = year_data['30'].iloc[0]
    val_j100 = year_data['100'].iloc[0]
    val_j365 = year_data['365'].iloc[0]

    # Configuration commune
    common_config = {
        'axis': {
            'range': [50, 100],  # Plage ajustée pour la survie
            'tickwidth': 1,
            'tickcolor': 'rgba(0,0,0,0.3)',
            'tickfont': {'size': 10},
            'ticksuffix': '%'
        },
        'bar': {'color': '#2c3e50', 'thickness': 0.25},
        'bgcolor': 'white',
        'borderwidth': 0,
        'bordercolor': 'rgba(0,0,0,0)',
        'threshold': {
            'line': {'color': '#2c3e50', 'width': 2},
            'thickness': 0.75
        }
    }

    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}]],
        subplot_titles=['<b>J30</b>', '<b>J100</b>', '<b>J365</b>'],
        horizontal_spacing=0.15
    )

    # Jauge J30
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=val_j30,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'suffix': '%', 'font': {'size': 24, 'color': '#2c3e50'}, 'valueformat': '.1f'},
        gauge={
            **common_config,
            'steps': [
                {'range': [50, 85], 'color': '#e74c3c'},
                {'range': [85, 95], 'color': '#f39c12'},
                {'range': [95, 100], 'color': '#27ae60'}
            ],
            'threshold': {'value': val_j30}
        },
        title={'text': f"<b>{val_j30:.1f}%</b>", 'font': {'size': 14, 'color': '#2c3e50'}, 'align': 'center'}
    ), row=1, col=1)

    # Jauge J100
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=val_j100,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'suffix': '%', 'font': {'size': 24, 'color': '#2c3e50'}, 'valueformat': '.1f'},
        gauge={
            **common_config,
            'steps': [
                {'range': [50, 75], 'color': '#e74c3c'},
                {'range': [75, 90], 'color': '#f39c12'},
                {'range': [90, 100], 'color': '#27ae60'}
            ],
            'threshold': {'value': val_j100}
        },
        title={'text': f"<b>{val_j100:.1f}%</b>", 'font': {'size': 14, 'color': '#2c3e50'}, 'align': 'center'}
    ), row=1, col=2)

    # Jauge J365
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=val_j365,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'suffix': '%', 'font': {'size': 24, 'color': '#2c3e50'}, 'valueformat': '.1f'},
        gauge={
            **common_config,
            'steps': [
                {'range': [50, 60], 'color': '#e74c3c'},
                {'range': [60, 80], 'color': '#f39c12'},
                {'range': [80, 100], 'color': '#27ae60'}
            ],
            'threshold': {'value': val_j365}
        },
        title={'text': f"<b>{val_j365:.1f}%</b>", 'font': {'size': 14, 'color': '#2c3e50'}, 'align': 'center'}
    ), row=1, col=3)

    # Mise en forme globale
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=80, b=20),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial, sans-serif"),
        annotations=[dict(
            x=0.5, y=1.15,
            showarrow=False,
            text="<b>Taux de Survie Globale</b>",
            xref="paper",
            yref="paper",
            font=dict(size=14, color='#2c3e50')
        )
        ]
    )
    fig.update_annotations(font_size=12, font_color="#7f8c8d")
    
    return dcc.Graph(
        figure=fig,
        config={'displayModeBar': False},
        style={
            'border-radius': '10px',
            'box-shadow': '0 2px 5px rgba(0,0,0,0.1)',
            'background': 'white',
            'padding': '10px'
        }
    )

def process_prise_greffe_data(df):
    """
    Traite les données pour calculer les indicateurs de prise de greffe
    """
    # Créer une copie pour éviter de modifier le DataFrame original
    df = df.copy()
    
    # Vérifier les colonnes nécessaires
    required_cols = ['Year', 'Date Platelet Reconstitution', 'Treatment Date']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Colonnes manquantes pour l'analyse Prise de greffe: {missing_cols}")
    
    # Convertir les colonnes de dates en datetime
    df['Date Platelet Reconstitution'] = pd.to_datetime(df['Date Platelet Reconstitution'], errors='coerce')
    df['Treatment Date'] = pd.to_datetime(df['Treatment Date'], errors='coerce')
    
    # Calculer la durée de prise de greffe
    df['duree_prise_de_greffe'] = (df['Date Platelet Reconstitution'] - df['Treatment Date']).dt.days
    
    # Filtrer les lignes où les dates sont valides (pas NaT/NaN)
    df = df.dropna(subset=['duree_prise_de_greffe'])
    
    # Compter le nombre de greffes par année
    nb_greffe_year = df.groupby('Year').size().reset_index(name='nb_greffe')
    
    # Sélectionner et filtrer les données (prise de greffe <= 100 jours)
    result = df[['Year', 'duree_prise_de_greffe']].copy()
    result = result[result['duree_prise_de_greffe'] <= 100]
    
    # Grouper par année et compter les prises de greffe
    result = result.groupby('Year').size().reset_index(name='nb_prise_greffe')
    
    # Fusionner avec nb_greffe_year pour calculer les pourcentages
    result = pd.merge(result, nb_greffe_year, on='Year', how='left')
    
    # Remplacer les NaN par 0 pour les années sans prise de greffe
    result['nb_prise_greffe'] = result['nb_prise_greffe'].fillna(0).astype(int)
    
    # Calculer le pourcentage de prise de greffe
    result['pourcentage_prise_greffe'] = round(result['nb_prise_greffe'] / result['nb_greffe'] * 100, 1)
    
    # Renommer la colonne nb_greffe en total pour correspondre au résultat R
    result = result.rename(columns={'nb_greffe': 'total'})
    
    return result


def create_prise_greffe_barplot(result):
    """
    Crée le barplot du pourcentage de prise de greffe par année
    """
    fig = go.Figure()
    
    for j in result['Year'].unique():
        fig.add_trace(go.Bar(
            x=result[result['Year'] == j]['Year'],
            y=result[result['Year'] == j]['pourcentage_prise_greffe'],
            name=f'{j}',
            text=result[result['Year'] == j]['pourcentage_prise_greffe'].astype(str),
            textposition='inside'
        ))
    
    fig.update_layout(
        title={
            'text': '<b>Pourcentage de prise de greffe à J100 par année</b>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title="<b>Année</b>",
        yaxis_title="<b>Pourcentage de prise de greffe (%)</b>",
        barmode='group',
        height=500,
        template='plotly_white',
        yaxis=dict(range=[0, 100]),  # Fixer l'axe Y entre 0 et 100%
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Ajouter une ligne horizontale à 80%
    fig.add_shape(
        type="line", 
        x0=result['Year'].min()-0.5, 
        y0=80, 
        x1=result['Year'].max()+0.5, 
        y1=80,
        line=dict(color="red", width=2, dash="dash"), 
        name="80%"
    )
    
    # Afficher le texte des barres au-dessus des barres
    fig.update_traces(
        texttemplate='%{text}%', 
        textposition='inside',
        marker_color='#2c3e50',
    )
    
    return fig

def create_prise_greffe_gauge(result, analysis_year):
    """
    Crée la jauge pour le taux de prise de greffe
    """
    analysis_year = int(analysis_year)
    year_data = result[result['Year'] == analysis_year]
    
    if year_data.empty:
        available_years = result['Year'].unique()
        return dbc.Alert(
            f"Aucune donnée disponible pour l'année {analysis_year} (années disponibles: {sorted(available_years)})", 
            color="warning"
        )
    
    val = year_data['pourcentage_prise_greffe'].iloc[0]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={
            'suffix': '%',
            'font': {'size': 28, 'color': '#2c3e50'},
            'valueformat': '.1f'
        },
        gauge={
            'axis': {
                'range': [0, 100],
                'tickwidth': 1,
                'tickcolor': 'rgba(0,0,0,0.3)',
                'tickfont': {'size': 12},
                'ticksuffix': '%'
            },
            'bar': {'color': "#2c3e50", 'thickness': 0.3},
            'bgcolor': 'white',
            'borderwidth': 0,
            'bordercolor': 'rgba(0,0,0,0)',
            'steps': [
                {'range': [0, 80], 'color': '#e74c3c'},
                {'range': [80, 90], 'color': '#f39c12'},
                {'range': [90, 100], 'color': '#27ae60'}
            ],
            'threshold': {
                'line': {'color': '#2c3e50', 'width': 2},
                'thickness': 0.8,
                'value': val
            }
        },
        title={
            'text': f"<b>Taux de prise de greffe J100<br>{analysis_year}</b>",
            'font': {'size': 16, 'color': '#2c3e50'}
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial, sans-serif")
    )
    
    return dcc.Graph(
        figure=fig,
        config={'displayModeBar': False},
        style={
            'border-radius': '10px',
            'box-shadow': '0 2px 5px rgba(0,0,0,0.1)',
            'background': 'white',
            'padding': '10px'
        }
    )

def create_prise_greffe_datatable(result):
    """
    Crée la table des résultats de prise de greffe
    """
    table_data = []
    for _, row in result.iterrows():
        table_data.append({
            'Année': int(row['Year']),
            'Prise de greffe': int(row['nb_prise_greffe']),
            'Total': int(row['total']),
            'Pourcentage': f"{row['pourcentage_prise_greffe']:.1f}%"
        })
    
    return html.Div([
        html.H6("Statistiques par année", className='mb-2'),
        dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Année", "id": "Année"},
                {"name": "Prise de greffe", "id": "Prise de greffe"},
                {"name": "Total", "id": "Total"},
                {"name": "Pourcentage", "id": "Pourcentage"}
            ],
            style_table={'height': '250px', 'overflowY': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '8px',
                'fontSize': '12px'
            },
            style_header={
                'backgroundColor': '#0D3182',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[{
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            }]
        )
    ])

def create_prise_greffe_visualization(df, selected_year):
    """
    Crée la visualisation complète pour l'indicateur Prise de greffe
    """
    try:
        result = process_prise_greffe_data(df)
        analysis_year = int(selected_year) - 1  # On utilise n-1 pour la prise de greffe
        result['Year'] = result['Year'].astype(int)
        
        return dbc.Row([
            # Colonne gauche : Barplot (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_prise_greffe_barplot(result),
                    style={'height': '600px'}
                )
            ], width=7),
            # Colonne droite : DataTable et jauge (40%)
            dbc.Col([
                create_prise_greffe_datatable(result),
                html.Hr(className='my-3'),
                html.H6(f"Indicateur pour l'année {analysis_year}", className='text-center mb-3'),
                create_prise_greffe_gauge(result, analysis_year)
            ], width=5)
        ])
    except Exception as e:
        return dbc.Alert(f"Erreur lors du calcul des indicateurs de Prise de greffe: {str(e)}", color="danger")

def process_sortie_aplasie_data(df):
    """
    Traite les données pour calculer les indicateurs de sortie d'aplasie
    """
    # Créer une copie pour éviter de modifier le DataFrame original
    df = df.copy()
    
    # Vérifier les colonnes nécessaires
    required_cols = ['Year', 'Date Anc Recovery', 'Treatment Date']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Colonnes manquantes pour l'analyse Sortie d'aplasie: {missing_cols}")
    
    # Convertir les colonnes de dates en datetime
    df['Date Anc Recovery'] = pd.to_datetime(df['Date Anc Recovery'], errors='coerce')
    df['Treatment Date'] = pd.to_datetime(df['Treatment Date'], errors='coerce')
    
    # Créer une colonne Duree_aplasie
    df['duree_aplasie'] = (df['Date Anc Recovery'] - df['Treatment Date']).dt.days
    
    # Filtrer les lignes où les dates sont valides (pas NaT/NaN)
    df = df.dropna(subset=['duree_aplasie'])
    
    # Compter le nombre de greffes par année
    nb_greffe_year = df.groupby('Year').size().reset_index(name='nb_greffe')
    
    # Sélectionner et filtrer les données (sortie d'aplasie <= 28 jours)
    result = df[['Year', 'duree_aplasie']].copy()
    result = result[result['duree_aplasie'] <= 28]
    
    # Grouper par année et compter les sorties d'aplasie
    result = result.groupby('Year').size().reset_index(name='nb_sortie_aplasie')
    
    # Fusionner avec nb_greffe_year pour calculer les pourcentages
    result = pd.merge(result, nb_greffe_year, on='Year', how='left')
    
    # Remplacer les NaN par 0 pour les années sans sortie d'aplasie
    result['nb_sortie_aplasie'] = result['nb_sortie_aplasie'].fillna(0).astype(int)
    
    # Calculer le pourcentage de sortie d'aplasie
    result['pourcentage_sortie_aplasie'] = round(result['nb_sortie_aplasie'] / result['nb_greffe'] * 100, 1)
    
    # Renommer la colonne nb_greffe en total pour correspondre au résultat R
    result = result.rename(columns={'nb_greffe': 'total'})
    
    return result

def create_sortie_aplasie_barplot(result):
    """
    Crée le barplot du pourcentage de sortie d'aplasie par année
    """
    fig = go.Figure()
    
    for j in result['Year'].unique():
        fig.add_trace(go.Bar(
            x=result[result['Year'] == j]['Year'],
            y=result[result['Year'] == j]['pourcentage_sortie_aplasie'],
            name=f'{j}',
            text=result[result['Year'] == j]['pourcentage_sortie_aplasie'].astype(str),
            textposition='inside'
        ))
    
    fig.update_layout(
        title={
            'text': '<b>Pourcentage de sortie d\'aplasie à J28 par année</b>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title="<b>Année</b>",
        yaxis_title="<b>Pourcentage de sortie d'aplasie (%)</b>",
        barmode='group',
        height=500,
        template='plotly_white',
        yaxis=dict(range=[0, 100]),  # Fixer l'axe Y entre 0 et 100%
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Ajouter une ligne horizontale à 80% (seuil de référence)
    fig.add_shape(
        type="line", 
        x0=result['Year'].min()-0.5, 
        y0=80, 
        x1=result['Year'].max()+0.5, 
        y1=80,
        line=dict(color="red", width=2, dash="dash"), 
        name="80%"
    )
    
    # Afficher le texte des barres au-dessus des barres
    fig.update_traces(
        texttemplate='%{text}%', 
        textposition='inside',
        marker_color='#2c3e50',
    )
    
    return fig

def create_sortie_aplasie_gauge(result, analysis_year):
    """
    Crée la jauge pour le taux de sortie d'aplasie
    """
    analysis_year = int(analysis_year)
    year_data = result[result['Year'] == analysis_year]
    
    if year_data.empty:
        available_years = result['Year'].unique()
        return dbc.Alert(
            f"Aucune donnée disponible pour l'année {analysis_year} (années disponibles: {sorted(available_years)})", 
            color="warning"
        )
    
    val = year_data['pourcentage_sortie_aplasie'].iloc[0]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={
            'suffix': '%',
            'font': {'size': 28, 'color': '#2c3e50'},
            'valueformat': '.1f'
        },
        gauge={
            'axis': {
                'range': [0, 100],
                'tickwidth': 1,
                'tickcolor': 'rgba(0,0,0,0.3)',
                'tickfont': {'size': 12},
                'ticksuffix': '%'
            },
            'bar': {'color': "#2c3e50", 'thickness': 0.3},
            'bgcolor': 'white',
            'borderwidth': 0,
            'bordercolor': 'rgba(0,0,0,0)',
            'steps': [
                {'range': [0, 80], 'color': '#e74c3c'},
                {'range': [80, 90], 'color': '#f39c12'},
                {'range': [90, 100], 'color': '#27ae60'}
            ],
            'threshold': {
                'line': {'color': '#2c3e50', 'width': 2},
                'thickness': 0.8,
                'value': val
            }
        },
        title={
            'text': f"<b>Taux de sortie d'aplasie J28<br>{analysis_year}</b>",
            'font': {'size': 16, 'color': '#2c3e50'}
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial, sans-serif")
    )
    
    return dcc.Graph(
        figure=fig,
        config={'displayModeBar': False},
        style={
            'border-radius': '10px',
            'box-shadow': '0 2px 5px rgba(0,0,0,0.1)',
            'background': 'white',
            'padding': '10px'
        }
    )

def create_sortie_aplasie_datatable(result):
    """
    Crée la table des résultats de sortie d'aplasie
    """
    table_data = []
    for _, row in result.iterrows():
        table_data.append({
            'Année': int(row['Year']),
            'Sortie d\'aplasie': int(row['nb_sortie_aplasie']),
            'Total': int(row['total']),
            'Pourcentage': f"{row['pourcentage_sortie_aplasie']:.1f}%"
        })
    
    return html.Div([
        html.H6("Statistiques par année", className='mb-2'),
        dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Année", "id": "Année"},
                {"name": "Sortie d'aplasie", "id": "Sortie d'aplasie"},
                {"name": "Total", "id": "Total"},
                {"name": "Pourcentage", "id": "Pourcentage"}
            ],
            style_table={'height': '250px', 'overflowY': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '8px',
                'fontSize': '12px'
            },
            style_header={
                'backgroundColor': '#0D3182',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[{
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            }]
        )
    ])

def create_sortie_aplasie_visualization(df, selected_year):
    """
    Crée la visualisation complète pour l'indicateur Sortie d'aplasie
    """
    try:
        result = process_sortie_aplasie_data(df)
        analysis_year = int(selected_year) - 1  # On utilise n-1 pour la sortie d'aplasie
        result['Year'] = result['Year'].astype(int)
        
        return dbc.Row([
            # Colonne gauche : Barplot (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_sortie_aplasie_barplot(result),
                    style={'height': '600px'}
                )
            ], width=7),
            # Colonne droite : DataTable et jauge (40%)
            dbc.Col([
                create_sortie_aplasie_datatable(result),
                html.Hr(className='my-3'),
                html.H6(f"Indicateur pour l'année {analysis_year}", className='text-center mb-3'),
                create_sortie_aplasie_gauge(result, analysis_year)
            ], width=5)
        ])
    except Exception as e:
        return dbc.Alert(f"Erreur lors du calcul des indicateurs de Sortie d'aplasie: {str(e)}", color="danger")

def process_rechute_data(df):
    """
    Traite les données pour calculer les indicateurs de Rechute
    
    Args:
        df (pd.DataFrame): DataFrame avec les données
        
    Returns:
        tuple: (result_long, result_df) - DataFrames avec les statistiques de rechute
    """
    # Vérifier les colonnes nécessaires
    required_cols = ['Year', 'First Relapse', 'First Relapse Date', 'Treatment Date']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Colonnes manquantes pour l'analyse Rechute: {missing_cols}")
    
    # Copier le DataFrame pour éviter les modifications
    df = df.copy()
    
    # Créer une colonne delai_rechute
    df['First Relapse Date'] = pd.to_datetime(df['First Relapse Date'], errors='coerce')
    df['Treatment Date'] = pd.to_datetime(df['Treatment Date'], errors='coerce')
    df['delai_rechute'] = (df['First Relapse Date'] - df['Treatment Date']).dt.days
    
    # Calcul du nombre de greffes par année
    nb_greffe_year = df.groupby('Year').size().reset_index(name='nb_greffe')
    
    # Traitement des données de rechute
    # Conversion des valeurs de First Relapse en valeurs numériques
    df['statut_rechute'] = df['First Relapse'].apply(
        lambda x: 1 if x in ["Yes"] else 0
    )
    
    # Filtrage des données et création de nouvelles colonnes
    result = df[~df['delai_rechute'].isna()].copy()
    result = result[['Year', 'delai_rechute', 'statut_rechute']]
    
    # Création des indicateurs de rechute à J100 et J365
    result['rechute_j100'] = np.where(
        (result['statut_rechute'] == 1) & (result['delai_rechute'] <= 100), 1, 0
    )
    result['rechute_j365'] = np.where(
        (result['statut_rechute'] == 1) & (result['delai_rechute'] <= 365), 1, 0
    )
    
    # Groupement par année et calcul des sommes
    rechute_summary = result.groupby('Year').agg({
        'rechute_j100': 'sum',
        'rechute_j365': 'sum'
    }).reset_index()
    
    # Fusion avec nb_greffe_year pour avoir accès au nombre total de greffes
    result_df = pd.merge(rechute_summary, nb_greffe_year, on='Year', how='left')
    
    # Ajouter une colonne pour J0 (toujours 0)
    result_df['rechute_j0'] = 0
    
    # Calcul des pourcentages
    result_df['0'] = 0.0  # Toujours 0% à J0
    result_df['100'] = round(result_df['rechute_j100'] / result_df['nb_greffe'] * 100, 1)
    result_df['365'] = round(result_df['rechute_j365'] / result_df['nb_greffe'] * 100, 1)
    
    # Transformer en format long pour le graphique
    result_long = result_df[['Year', '0', '100', '365']].melt(
        id_vars=['Year'],
        value_vars=['0', '100', '365'],
        var_name='j',
        value_name='pourcentage_rechute'
    )
    
    # Convertir la colonne 'j' en numérique
    result_long['j'] = result_long['j'].astype(int)
    
    return result_long, result_df

def create_rechute_visualization(df, selected_year):
    """
    Crée la visualisation complète pour l'indicateur Rechute
    
    Args:
        df (pd.DataFrame): DataFrame avec les données
        selected_year (int): Année sélectionnée (on affichera l'année n-2)
        
    Returns:
        html.Div: Composant contenant la visualisation complète
    """
    try:
        # Traiter les données
        result_long, result_df = process_rechute_data(df)
        
        # Convertir l'année en int et calculer n-2
        selected_year = int(selected_year)
        analysis_year = selected_year - 2
        
        # S'assurer que la colonne Year est de type int
        result_df['Year'] = result_df['Year'].astype(int)
        
        # Créer le layout avec deux colonnes
        return dbc.Row([
            # Colonne gauche : Graphique des courbes (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_rechute_curves_plot(result_long),
                    style={'height': '600px'},
                    config={'responsive': True}
                )
            ], width=7),
            # Colonne droite : DataTable et jauges (40%)
            dbc.Col([
                # DataTable
                create_rechute_datatable(result_df),
                html.Hr(className='my-3'),
                # Jauges pour l'année sélectionnée
                html.H6(f"Indicateurs {selected_year} pour l'année {analysis_year}", className='text-center mb-3'),
                create_rechute_gauges(result_df, analysis_year)
            ], width=5)
        ])
    except Exception as e:
        return dbc.Alert(f"Erreur lors du calcul des indicateurs Rechute: {str(e)}", color="danger")

def create_rechute_curves_plot(result_long):
    """
    Crée le graphique des courbes Rechute par année
    
    Args:
        result_long (pd.DataFrame): DataFrame en format long avec les données Rechute
        
    Returns:
        plotly.graph_objects.Figure: Figure Plotly
    """
    fig = go.Figure()
    
    # Obtenir les années uniques
    years = sorted(result_long['Year'].unique())
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    
    # Créer une courbe pour chaque année
    for i, year in enumerate(years):
        year_data = result_long[result_long['Year'] == year].sort_values('j')
        
        fig.add_trace(go.Scatter(
            x=year_data['j'],
            y=year_data['pourcentage_rechute'],
            mode='lines+markers',
            name=f'Année {year}',
            line=dict(color=colors[i % len(colors)], width=3),
            marker=dict(size=8),
            customdata=[year] * len(year_data)
        ))
    
    # Ajouter des lignes verticales pour J100 et J365
    for day in [100, 365]:
        fig.add_vline(
            x=day, 
            line_dash="dash", 
            line_color="gray", 
            opacity=0.5,
            annotation_text=f"J{day}",
            annotation_position="top"
        )
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': '<b>Évolution du taux de rechute</b>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='<b>Jours post-greffe</b>',
        yaxis_title='<b>Taux de rechute (%)</b>',
        xaxis=dict(
            tickmode='array',
            tickvals=[0, 100, 200, 365],
            ticktext=['J0', 'J100', 'J200', 'J365'],
            range=[-10, 380]
        ),
        yaxis=dict(
            range=[0, max(result_long['pourcentage_rechute'].max() * 1.1, 10)],
            tickformat='.1f'
        ),
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        template='plotly_white',
        margin=dict(r=150)
    )
    
    return fig

def create_rechute_datatable(result_df):
    """
    Crée la DataTable pour afficher les statistiques Rechute par année
    
    Args:
        result_df (pd.DataFrame): DataFrame avec les statistiques Rechute
        
    Returns:
        html.Div: Composant DataTable
    """
    # Préparer les données pour la table
    table_data = []
    for _, row in result_df.iterrows():
        table_data.append({
            'Année': int(row['Year']),
            'Rechutes J100': int(row['rechute_j100']),
            '% J100': f"{row['100']:.1f}%",
            'Rechutes J365': int(row['rechute_j365']),
            '% J365': f"{row['365']:.1f}%",
            'Total greffes': int(row['nb_greffe'])
        })
    
    return html.Div([
        html.H6("Statistiques par année", className='mb-2'),
        dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Année", "id": "Année"},
                {"name": "Rechutes J100", "id": "Rechutes J100"},
                {"name": "% J100", "id": "% J100"},
                {"name": "Rechutes J365", "id": "Rechutes J365"},
                {"name": "% J365", "id": "% J365"},
                {"name": "Total greffes", "id": "Total greffes"}
            ],
            style_table={'height': '250px', 'overflowY': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '8px',
                'fontSize': '12px'
            },
            style_header={
                'backgroundColor': '#0D3182',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ]
        )
    ])

def create_rechute_gauges(result_df, analysis_year):
    """
    Crée les jauges modernes pour afficher les taux de rechute à J100 et J365
    
    Args:
        result_df (pd.DataFrame): DataFrame avec les statistiques Rechute
        analysis_year (int): Année d'analyse
        
    Returns:
        dcc.Graph: Composant graphique avec les jauges
    """
    # S'assurer que analysis_year est de type int
    analysis_year = int(analysis_year)
    
    # Obtenir les données pour l'année spécifiée
    year_data = result_df[result_df['Year'] == analysis_year]
    
    if year_data.empty:
        available_years = result_df['Year'].unique()
        return dbc.Alert(
            f"Aucune donnée disponible pour l'année {analysis_year} (années disponibles: {sorted(available_years)})", 
            color="warning"
        )
    
    # Extraire les valeurs
    val_j100 = year_data['100'].iloc[0]
    val_j365 = year_data['365'].iloc[0]
    
    # Configuration commune
    common_gauge_config = {
        'axis': {
            'range': [None, 100],
            'tickwidth': 1,
            'tickcolor': 'rgba(0,0,0,0.3)',
            'tickfont': {'size': 10},
            'ticksuffix': '%'
        },
        'bar': {
            'color': '#e74c3c',  # Rouge pour les rechutes
            'thickness': 0.25
        },
        'bgcolor': 'white',
        'borderwidth': 0,
        'bordercolor': 'rgba(0,0,0,0)',
        'threshold': {
            'line': {'color': '#e74c3c', 'width': 2},
            'thickness': 0.75
        }
    }
    
    # Créer les 2 jauges avec un subplot
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}]],
        subplot_titles=['<b>J100</b>', '<b>J365</b>'],
        horizontal_spacing=0.2
    )
    
    # Jauge J100
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=val_j100,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={
            'suffix': '%',
            'font': {'size': 28, 'color': '#2c3e50'},
            'valueformat': '.1f'
        },
        gauge={
            **common_gauge_config,
            'steps': [
                {'range': [0, 10], 'color': '#27ae60'},   # Vert : bon
                {'range': [10, 25], 'color': '#f39c12'},  # Orange : moyen
                {'range': [25, 100], 'color': '#e74c3c'}  # Rouge : élevé
            ],
            'threshold': {'value': val_j100}
        },
        title={
            'text': f"<b>J100</b>",
            'font': {'size': 16, 'color': '#2c3e50'},
            'align': 'center'
        }
    ), row=1, col=1)
    
    # Jauge J365
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=val_j365,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={
            'suffix': '%',
            'font': {'size': 28, 'color': '#2c3e50'},
            'valueformat': '.1f'
        },
        gauge={
            **common_gauge_config,
            'steps': [
                {'range': [0, 20], 'color': '#27ae60'},   # Vert : bon
                {'range': [20, 40], 'color': '#f39c12'},  # Orange : moyen
                {'range': [40, 100], 'color': '#e74c3c'}  # Rouge : élevé
            ],
            'threshold': {'value': val_j365}
        },
        title={
            'text': f"<b>J365</b>",
            'font': {'size': 16, 'color': '#2c3e50'},
            'align': 'center'
        }
    ), row=1, col=2)
    
    # Mise en forme globale
    fig.update_layout(
        height=300,
        margin=dict(l=30, r=30, t=100, b=30),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial, sans-serif"),
        annotations=[
            dict(
                x=0.5,
                y=1.2,
                showarrow=False,
                text="Taux de rechute",
                xref="paper",
                yref="paper",
                font=dict(size=16, color='#2c3e50')
            )
        ]
    )
    
    # Style des sous-titres
    fig.update_annotations(
        font_size=14,
        font_color="#7f8c8d"
    )
    
    return dcc.Graph(
        figure=fig,
        config={'displayModeBar': False},
        style={
            'border-radius': '10px',
            'box-shadow': '0 2px 5px rgba(0,0,0,0.1)',
            'background': 'white',
            'padding': '10px'
        }
    )

def register_callbacks(app):
    """
    Enregistre les callbacks pour la page Indicateurs
    """
    @app.callback(
        [Output('indicator-content', 'children'),
        Output('year-note', 'style')],
        [Input('indicator-selection', 'value'),
        Input('indicator-year-selection', 'value'),
        Input('data-store', 'data'),
        Input('current-page', 'data')],
        prevent_initial_call=True
    )
    def update_indicator_display(indicator, selected_year, data, current_page):
        if current_page != 'Indicateurs' or data is None:
            return html.Div(), {'display': 'none'}
        
        df = pd.DataFrame(data)
        year_note_style = {'display': 'block'} if indicator in ['TRM', 'survie_globale'] else {'display': 'none'}
        
        if indicator == 'TRM':
            content = create_trm_visualization(df, int(selected_year)) if selected_year else dbc.Alert("Veuillez sélectionner une année", color="warning")
        elif indicator == 'survie_globale':
            content = create_survie_visualization(df, int(selected_year)) if selected_year else dbc.Alert("Veuillez sélectionner une année", color="warning")
        elif indicator == 'prise_greffe':
            content = create_prise_greffe_visualization(df, int(selected_year)) if selected_year else dbc.Alert("Veuillez sélectionner une année", color="warning")
        elif indicator == 'sortie_aplasie':
            content = create_sortie_aplasie_visualization(df, int(selected_year)) if selected_year else dbc.Alert("Veuillez sélectionner une année", color="warning")
        elif indicator == 'gvha':
            content = create_gvha_visualization(df, int(selected_year)) if selected_year else dbc.Alert("Veuillez sélectionner une année", color="warning")
        elif indicator == 'gvhc':
            content = create_gvhc_visualization(df, int(selected_year)) if selected_year else dbc.Alert("Veuillez sélectionner une année", color="warning")
        elif indicator == 'rechute':
            content = create_rechute_visualization(df, int(selected_year)) if selected_year else dbc.Alert("Veuillez sélectionner une année", color="warning")
        else:
            titles = {
                'TRM': 'TRM',
                'survie_globale': 'Survie globale',
                'prise_greffe': 'Prise de greffe',
                'sortie_aplasie': "Sortie d'aplasie",
                'gvha': 'GVH aiguë',
                'gvhc': 'GVH chronique',
                'rechute': 'Rechute'
            }
            title = titles.get(indicator, 'Indicateur')
            content = dbc.Alert([
                html.H5("En construction", className="alert-heading"),
                html.P(f"L'indicateur '{title}' sera bientôt disponible.", className="mb-0")
            ], color="info")
        
        return content, year_note_style
    
def create_gvha_datatable(result_combined):
    """
    Crée la DataTable pour afficher les statistiques GVH aiguë par année
    
    Args:
        result_combined (pd.DataFrame): DataFrame avec les statistiques GVHa
        
    Returns:
        html.Div: Composant DataTable
    """
    # Préparer les données pour la table
    table_data = []
    for _, row in result_combined.iterrows():
        table_data.append({
            'Année': int(row['Year']),
            'Nb greffes': int(row['nb_greffe']),
            'GVHa Grade 2': int(row.get('Grade 2', 0)),
            'GVHa Grade 3': int(row.get('Grade 3', 0)),
            'GVHa Grade 4': int(row.get('Grade 4', 0)),
            '% GVHa 2-4': f"{row['pourcentage_gvh_aigue_2_4']:.1f}%",
            'Nb GVHa 3-4': int(row['nb_gvh_aigue_3_4']),
            '% GVHa 3-4': f"{row['pourcentage_gvh_aigue_3_4']:.1f}%"
        })
    
    return html.Div([
        html.H6("Statistiques par année", className='mb-2'),
        dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Année", "id": "Année"},
                {"name": "Nb greffes", "id": "Nb greffes"},
                {"name": "GVHa Grade 2", "id": "GVHa Grade 2"},
                {"name": "GVHa Grade 3", "id": "GVHa Grade 3"},
                {"name": "GVHa Grade 4", "id": "GVHa Grade 4"},
                {"name": "% GVHa 2-4", "id": "% GVHa 2-4"},
                {"name": "Nb GVHa 3-4", "id": "Nb GVHa 3-4"},
                {"name": "% GVHa 3-4", "id": "% GVHa 3-4"}
            ],
            style_table={'height': '250px', 'overflowY': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '8px',
                'fontSize': '11px'
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
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                },
                {
                    'if': {'column_id': ['% GVHa 2-4', '% GVHa 3-4']},
                    'backgroundColor': '#e8f4fd',
                    'fontWeight': 'bold'
                }
            ]
        )
    ])


def create_gvha_badges(result_combined, analysis_year):
    """
    Crée les badges (étiquettes) pour afficher les pourcentages GVHa pour l'année sélectionnée
    
    Args:
        result_combined (pd.DataFrame): DataFrame avec les statistiques GVHa
        analysis_year (int): Année d'analyse
        
    Returns:
        html.Div: Composant avec les badges
    """
    # S'assurer que analysis_year est de type int
    analysis_year = int(analysis_year)
    
    # Obtenir les données pour l'année spécifiée
    year_data = result_combined[result_combined['Year'] == analysis_year]
    
    if year_data.empty:
        available_years = result_combined['Year'].unique()
        return dbc.Alert(
            f"Aucune donnée disponible pour l'année {analysis_year} (années disponibles: {sorted(available_years)})", 
            color="warning"
        )
    
    # Extraire les valeurs
    pct_2_4 = year_data['pourcentage_gvh_aigue_2_4'].iloc[0]
    pct_3_4 = year_data['pourcentage_gvh_aigue_3_4'].iloc[0]
    nb_2_4 = year_data['nb_gvh_aigue_2_4'].iloc[0]
    nb_3_4 = year_data['nb_gvh_aigue_3_4'].iloc[0]
    total_greffes = year_data['nb_greffe'].iloc[0]
    
    return html.Div([
        html.H6(f"Indicateurs GVH aiguë - Année {analysis_year}", className='text-center mb-3'),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{pct_2_4:.1f}%", className="text-center mb-2", style={'color': '#2c3e50'}),
                        html.P("GVH aiguë grades 2-4", className="text-center mb-1", style={'fontSize': '14px'}),
                        html.P(f"({nb_2_4}/{total_greffes})", className="text-center text-muted", style={'fontSize': '12px'})
                    ], className="py-3")
                ], color="primary", outline=True, style={'border-width': '2px'})
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{pct_3_4:.1f}%", className="text-center mb-2", style={'color': '#c0392b'}),
                        html.P("GVH aiguë grades 3-4", className="text-center mb-1", style={'fontSize': '14px'}),
                        html.P(f"({nb_3_4}/{total_greffes})", className="text-center text-muted", style={'fontSize': '12px'})
                    ], className="py-3")
                ], color="danger", outline=True, style={'border-width': '2px'})
            ], width=6)
        ])
    ], className="mb-3")

def process_gvha_data(df):
    """
    Traite les données pour calculer les indicateurs de GVH aiguë
    
    Args:
        df (pd.DataFrame): DataFrame avec les données
        
    Returns:
        tuple: (result_combined, result_grade2_4, result_grade3_4) - DataFrames avec les statistiques GVHa
    """
    # Vérifier les colonnes nécessaires
    required_cols = ['Year', 'First Agvhd Occurrence Date', 'Treatment Date', 'First aGvHD Maximum Score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Colonnes manquantes pour l'analyse GVH aiguë: {missing_cols}")
    
    # Créer une copie et calculer le délai si nécessaire
    df = df.copy()
    
    # Convertir les dates
    df['First Agvhd Occurrence Date'] = pd.to_datetime(df['First Agvhd Occurrence Date'], errors='coerce')
    df['Treatment Date'] = pd.to_datetime(df['Treatment Date'], errors='coerce')
    
    # Calculer le délai GVH aiguë
    df['delai_gvh_aigue'] = (df['First Agvhd Occurrence Date'] - df['Treatment Date']).dt.days
    
    # Compter le nombre de greffes par année
    nb_greffe_year = df.groupby('Year').size().reset_index(name='nb_greffe')
    
    # Traitement pour les grades 2, 3 et 4
    result_grade2_4 = df[['Year', 'delai_gvh_aigue', 'First aGvHD Maximum Score']].copy()
    result_grade2_4 = result_grade2_4[result_grade2_4['delai_gvh_aigue'] <= 100]
    result_grade2_4 = result_grade2_4[result_grade2_4['First aGvHD Maximum Score'].isin(['Grade 2', 'Grade 3', 'Grade 4'])]
    
    # Compter par grade pour le barplot stratifié
    grade_counts = result_grade2_4.groupby(['Year', 'First aGvHD Maximum Score']).size().unstack(fill_value=0)
    grade_counts = grade_counts.reset_index()
    
    # Calculer les totaux pour les grades 2-4
    grade2_4_totals = result_grade2_4.groupby('Year').size().reset_index(name='nb_gvh_aigue_2_4')
    
    # Traitement pour les grades 3 et 4
    result_grade3_4 = df[['Year', 'delai_gvh_aigue', 'First aGvHD Maximum Score']].copy()
    result_grade3_4 = result_grade3_4[result_grade3_4['delai_gvh_aigue'] <= 100]
    result_grade3_4 = result_grade3_4[result_grade3_4['First aGvHD Maximum Score'].isin(['Grade 3', 'Grade 4'])]
    grade3_4_totals = result_grade3_4.groupby('Year').size().reset_index(name='nb_gvh_aigue_3_4')
    
    # Fusionner toutes les données
    result_combined = pd.merge(nb_greffe_year, grade2_4_totals, on='Year', how='left')
    result_combined = pd.merge(result_combined, grade3_4_totals, on='Year', how='left')
    
    # Remplir les NaN par 0
    result_combined['nb_gvh_aigue_2_4'] = result_combined['nb_gvh_aigue_2_4'].fillna(0).astype(int)
    result_combined['nb_gvh_aigue_3_4'] = result_combined['nb_gvh_aigue_3_4'].fillna(0).astype(int)
    
    # Calculer les pourcentages
    result_combined['pourcentage_gvh_aigue_2_4'] = round(
        result_combined['nb_gvh_aigue_2_4'] / result_combined['nb_greffe'] * 100, 1
    )
    result_combined['pourcentage_gvh_aigue_3_4'] = round(
        result_combined['nb_gvh_aigue_3_4'] / result_combined['nb_greffe'] * 100, 1
    )
    
    # Ajouter les détails par grade au dataframe combined
    if not grade_counts.empty:
        # S'assurer que les colonnes de grades existent
        for grade in ['Grade 2', 'Grade 3', 'Grade 4']:
            if grade not in grade_counts.columns:
                grade_counts[grade] = 0
        
        result_combined = pd.merge(result_combined, grade_counts[['Year', 'Grade 2', 'Grade 3', 'Grade 4']], on='Year', how='left')
        
        # Remplir les NaN par 0
        for grade in ['Grade 2', 'Grade 3', 'Grade 4']:
            result_combined[grade] = result_combined[grade].fillna(0).astype(int)
        
        # Calculer les pourcentages par grade
        result_combined['pourcentage_grade_2'] = round(result_combined['Grade 2'] / result_combined['nb_greffe'] * 100, 1)
        result_combined['pourcentage_grade_3'] = round(result_combined['Grade 3'] / result_combined['nb_greffe'] * 100, 1)
        result_combined['pourcentage_grade_4'] = round(result_combined['Grade 4'] / result_combined['nb_greffe'] * 100, 1)
    else:
        # Si pas de données de grades, initialiser avec des 0
        for grade in ['Grade 2', 'Grade 3', 'Grade 4']:
            result_combined[grade] = 0
            result_combined[f'pourcentage_grade_{grade.split()[-1]}'] = 0.0
    
    return result_combined, grade_counts


def create_gvha_barplot(result_combined, grade_counts):
    """
    Crée le barplot stratifié pour la GVH aiguë avec lignes de référence
    
    Args:
        result_combined (pd.DataFrame): DataFrame avec les statistiques combinées
        grade_counts (pd.DataFrame): DataFrame avec les counts par grade
        
    Returns:
        plotly.graph_objects.Figure: Figure Plotly
    """
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Couleurs pour chaque grade
    colors = {
        'Grade 2': '#f39c12',  # Orange
        'Grade 3': '#e67e22',  # Orange foncé
        'Grade 4': '#c0392b'   # Rouge
    }
    
    # Ajouter les barres pour chaque grade
    for grade in ['Grade 2', 'Grade 3', 'Grade 4']:
        if grade in result_combined.columns:
            percentages = []
            for _, row in result_combined.iterrows():
                if row['nb_greffe'] > 0:
                    pct = (row[grade] / row['nb_greffe']) * 100
                    percentages.append(pct)
                else:
                    percentages.append(0)
            
            fig.add_trace(go.Bar(
                name=grade,
                x=result_combined['Year'],
                y=percentages,
                marker_color=colors[grade],
                text=[f"{row[grade]}" for _, row in result_combined.iterrows()],
                textposition='inside',
                hovertemplate=f'<b>{grade}</b><br>' +
                             'Année: %{x}<br>' +
                             'Pourcentage: %{y:.1f}%<br>' +
                             'Nombre: %{text}<br>' +
                             '<extra></extra>'
            ))
    
    # Ajouter les lignes de référence
    years = result_combined['Year'].tolist()
    if years:
        x_min, x_max = min(years) - 0.5, max(years) + 0.5
        
        # Ligne à 20% pour grades 3 et 4
        fig.add_shape(
            type="line",
            x0=x_min, y0=20, x1=x_max, y1=20,
            line=dict(color="red", width=2, dash="dash"),
        )
        
        # Ligne à 40% pour grades 2-4
        fig.add_shape(
            type="line",
            x0=x_min, y0=40, x1=x_max, y1=40,
            line=dict(color="blue", width=2, dash="dash"),
        )
        
        # Annotations pour les lignes
        fig.add_annotation(
            x=x_max - 0.1,
            y=22,
            text="20% (grades 3-4)",
            showarrow=False,
            font=dict(color="red", size=10),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="red",
            borderwidth=1
        )
        
        fig.add_annotation(
            x=x_max - 0.1,
            y=42,
            text="40% (grades 2-4)",
            showarrow=False,
            font=dict(color="blue", size=10),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="blue",
            borderwidth=1
        )
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': '<b>GVH aiguë par grade (J100)</b>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='<b>Année</b>',
        yaxis_title='<b>Pourcentage (%)</b>',
        barmode='stack',
        height=500,
        template='plotly_white',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        yaxis=dict(
            range=[0,100],
            tickformat='.1f'
        ),
        margin=dict(r=150)
    )
    
    return fig


def create_gvha_datatable(result_combined):
    """
    Crée la DataTable pour afficher les statistiques GVH aiguë par année
    
    Args:
        result_combined (pd.DataFrame): DataFrame avec les statistiques GVHa
        
    Returns:
        html.Div: Composant DataTable
    """
    import dash_bootstrap_components as dbc
    from dash import dash_table, html
    
    # Préparer les données pour la table
    table_data = []
    for _, row in result_combined.iterrows():
        table_data.append({
            'Année': int(row['Year']),
            'Nb greffes': int(row['nb_greffe']),
            'GVHa Grade 2': int(row.get('Grade 2', 0)),
            'GVHa Grade 3': int(row.get('Grade 3', 0)),
            'GVHa Grade 4': int(row.get('Grade 4', 0)),
            '% GVHa 2-4': f"{row['pourcentage_gvh_aigue_2_4']:.1f}%",
            'Nb GVHa 3-4': int(row['nb_gvh_aigue_3_4']),
            '% GVHa 3-4': f"{row['pourcentage_gvh_aigue_3_4']:.1f}%"
        })
    
    return html.Div([
        html.H6("Statistiques par année", className='mb-2'),
        dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Année", "id": "Année"},
                {"name": "Nb greffes", "id": "Nb greffes"},
                {"name": "GVHa Grade 2", "id": "GVHa Grade 2"},
                {"name": "GVHa Grade 3", "id": "GVHa Grade 3"},
                {"name": "GVHa Grade 4", "id": "GVHa Grade 4"},
                {"name": "% GVHa 2-4", "id": "% GVHa 2-4"},
                {"name": "Nb GVHa 3-4", "id": "Nb GVHa 3-4"},
                {"name": "% GVHa 3-4", "id": "% GVHa 3-4"}
            ],
            style_table={'height': '250px', 'overflowY': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '8px',
                'fontSize': '11px'
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
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                },
                {
                    'if': {'column_id': ['% GVHa 2-4', '% GVHa 3-4']},
                    'backgroundColor': '#e8f4fd',
                    'fontWeight': 'bold'
                }
            ]
        )
    ])


def create_gvha_badges(result_combined, analysis_year):
    """
    Crée les badges (étiquettes) pour afficher les pourcentages GVHa pour l'année sélectionnée
    
    Args:
        result_combined (pd.DataFrame): DataFrame avec les statistiques GVHa
        analysis_year (int): Année d'analyse
        
    Returns:
        html.Div: Composant avec les badges
    """
    import dash_bootstrap_components as dbc
    from dash import html
    
    # S'assurer que analysis_year est de type int
    analysis_year = int(analysis_year)
    
    # Obtenir les données pour l'année spécifiée
    year_data = result_combined[result_combined['Year'] == analysis_year]
    
    if year_data.empty:
        available_years = result_combined['Year'].unique()
        return dbc.Alert(
            f"Aucune donnée disponible pour l'année {analysis_year} (années disponibles: {sorted(available_years)})", 
            color="warning"
        )
    
    # Extraire les valeurs
    pct_2_4 = year_data['pourcentage_gvh_aigue_2_4'].iloc[0]
    pct_3_4 = year_data['pourcentage_gvh_aigue_3_4'].iloc[0]
    nb_2_4 = year_data['nb_gvh_aigue_2_4'].iloc[0]
    nb_3_4 = year_data['nb_gvh_aigue_3_4'].iloc[0]
    total_greffes = year_data['nb_greffe'].iloc[0]
    
    return html.Div([
        html.H6(f"Indicateurs GVH aiguë - Année {analysis_year}", className='text-center mb-3'),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{pct_2_4:.1f}%", className="text-center mb-2", style={'color': '#2c3e50'}),
                        html.P("GVH aiguë grades 2-4", className="text-center mb-1", style={'fontSize': '14px'}),
                        html.P(f"({nb_2_4}/{total_greffes})", className="text-center text-muted", style={'fontSize': '12px'})
                    ], className="py-3")
                ], color="primary", outline=True, style={'border-width': '2px'})
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{pct_3_4:.1f}%", className="text-center mb-2", style={'color': '#c0392b'}),
                        html.P("GVH aiguë grades 3-4", className="text-center mb-1", style={'fontSize': '14px'}),
                        html.P(f"({nb_3_4}/{total_greffes})", className="text-center text-muted", style={'fontSize': '12px'})
                    ], className="py-3")
                ], color="danger", outline=True, style={'border-width': '2px'})
            ], width=6)
        ])
    ], className="mb-3")


def create_gvha_visualization(df, selected_year):
    """
    Crée la visualisation complète pour l'indicateur GVH aiguë
    
    Args:
        df (pd.DataFrame): DataFrame avec les données
        selected_year (int): Année sélectionnée (on affichera l'année n-2)
        
    Returns:
        html.Div: Composant contenant la visualisation complète
    """
    import dash_bootstrap_components as dbc
    from dash import dcc, html
    
    try:
        # Traiter les données
        result_combined, grade_counts = process_gvha_data(df)
        
        # Convertir l'année en int et calculer n-2
        selected_year = int(selected_year)
        analysis_year = selected_year - 2
        
        # S'assurer que la colonne Year est de type int
        result_combined['Year'] = result_combined['Year'].astype(int)
        
        # Créer le layout avec deux colonnes
        return dbc.Row([
            # Colonne gauche : Graphique (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_gvha_barplot(result_combined, grade_counts),
                    style={'height': '600px'},
                    config={'responsive': True}
                )
            ], width=7),
            # Colonne droite : DataTable et badges (40%)
            dbc.Col([
                # DataTable
                create_gvha_datatable(result_combined),
                html.Hr(className='my-3'),
                # Badges pour l'année sélectionnée
                create_gvha_badges(result_combined, analysis_year)
            ], width=5)
        ])
    except Exception as e:
        return dbc.Alert(f"Erreur lors du calcul des indicateurs GVH aiguë: {str(e)}", color="danger")


def create_gvha_visualization(df, selected_year):
    """
    Crée la visualisation complète pour l'indicateur GVH aiguë
    
    Args:
        df (pd.DataFrame): DataFrame avec les données
        selected_year (int): Année sélectionnée (on affichera l'année n-2)
        
    Returns:
        html.Div: Composant contenant la visualisation complète
    """
    try:
        # Traiter les données
        result_combined, grade_counts = process_gvha_data(df)
        
        # Convertir l'année en int et calculer n-2
        selected_year = int(selected_year)
        analysis_year = selected_year - 2
        
        # S'assurer que la colonne Year est de type int
        result_combined['Year'] = result_combined['Year'].astype(int)
        
        # Créer le layout avec deux colonnes
        return dbc.Row([
            # Colonne gauche : Graphique (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_gvha_barplot(result_combined, grade_counts),
                    style={'height': '600px'},
                    config={'responsive': True}
                )
            ], width=7),
            # Colonne droite : DataTable et badges (40%)
            dbc.Col([
                # DataTable
                create_gvha_datatable(result_combined),
                html.Hr(className='my-3'),
                # Badges pour l'année sélectionnée
                create_gvha_badges(result_combined, analysis_year)
            ], width=5)
        ])
    except Exception as e:
        return dbc.Alert(f"Erreur lors du calcul des indicateurs GVH aiguë: {str(e)}", color="danger")

def process_gvhc_data(df):
    """
    Traite les données pour calculer les indicateurs de GVH chronique
    
    Args:
        df (pd.DataFrame): DataFrame avec les données
        
    Returns:
        tuple: (result_combined, grade_counts) - DataFrames avec les statistiques GVHc
    """
    # Vérifier les colonnes nécessaires
    required_cols = ['Year', 'First Cgvhd Occurrence Date', 'Treatment Date', 'First cGvHD Maximum NIH Score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Colonnes manquantes pour l'analyse GVH chronique: {missing_cols}")
    
    # Créer une copie et calculer le délai si nécessaire
    df = df.copy()
    
    # Convertir les dates
    df['First Cgvhd Occurrence Date'] = pd.to_datetime(df['First Cgvhd Occurrence Date'], errors='coerce')
    df['Treatment Date'] = pd.to_datetime(df['Treatment Date'], errors='coerce')
    
    # Calculer le délai GVH chronique
    df['delai_gvh_chronique'] = (df['First Cgvhd Occurrence Date'] - df['Treatment Date']).dt.days
    
    # Compter le nombre de greffes par année
    nb_greffe_year = df.groupby('Year').size().reset_index(name='nb_greffe')
    
    # Traitement pour tous les grades de GVH chronique
    result_all_grades = df[['Year', 'delai_gvh_chronique', 'First cGvHD Maximum NIH Score']].copy()
    result_all_grades = result_all_grades[result_all_grades['delai_gvh_chronique'] <= 365]  # J365 pour GVHc
    result_all_grades = result_all_grades[result_all_grades['First cGvHD Maximum NIH Score'].isin(['Mild', 'Moderate', 'Severe'])]
    
    # Compter par grade pour le barplot stratifié
    grade_counts = result_all_grades.groupby(['Year', 'First cGvHD Maximum NIH Score']).size().unstack(fill_value=0)
    grade_counts = grade_counts.reset_index()
    
    # Calculer les totaux pour tous les grades
    all_grades_totals = result_all_grades.groupby('Year').size().reset_index(name='nb_gvh_chronique_total')
    
    # Fusionner toutes les données
    result_combined = pd.merge(nb_greffe_year, all_grades_totals, on='Year', how='left')
    
    # Remplir les NaN par 0
    result_combined['nb_gvh_chronique_total'] = result_combined['nb_gvh_chronique_total'].fillna(0).astype(int)
    
    # Calculer le pourcentage total
    result_combined['pourcentage_gvh_chronique_total'] = round(
        result_combined['nb_gvh_chronique_total'] / result_combined['nb_greffe'] * 100, 1
    )
    
    # Ajouter les détails par grade au dataframe combined
    if not grade_counts.empty:
        # S'assurer que les colonnes de grades existent dans l'ordre voulu
        for grade in ['Mild', 'Moderate', 'Severe']:
            if grade not in grade_counts.columns:
                grade_counts[grade] = 0
        
        result_combined = pd.merge(result_combined, grade_counts[['Year', 'Mild', 'Moderate', 'Severe']], on='Year', how='left')
        
        # Remplir les NaN par 0
        for grade in ['Mild', 'Moderate', 'Severe']:
            result_combined[grade] = result_combined[grade].fillna(0).astype(int)
        
        # Calculer les pourcentages par grade
        result_combined['pourcentage_mild'] = round(result_combined['Mild'] / result_combined['nb_greffe'] * 100, 1)
        result_combined['pourcentage_moderate'] = round(result_combined['Moderate'] / result_combined['nb_greffe'] * 100, 1)
        result_combined['pourcentage_severe'] = round(result_combined['Severe'] / result_combined['nb_greffe'] * 100, 1)
    else:
        # Si pas de données de grades, initialiser avec des 0
        for grade in ['Mild', 'Moderate', 'Severe']:
            result_combined[grade] = 0
            grade_name = grade.lower()
            result_combined[f'pourcentage_{grade_name}'] = 0.0
    
    return result_combined, grade_counts


def create_gvhc_barplot(result_combined, grade_counts):
    """
    Crée le barplot stratifié pour la GVH chronique avec ligne de référence
    
    Args:
        result_combined (pd.DataFrame): DataFrame avec les statistiques combinées
        grade_counts (pd.DataFrame): DataFrame avec les counts par grade
        
    Returns:
        plotly.graph_objects.Figure: Figure Plotly
    """
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Couleurs pour chaque grade (du plus clair au plus foncé)
    colors = {
        'Mild': '#3498db',      # Bleu clair
        'Moderate': '#e67e22',  # Orange
        'Severe': '#c0392b'     # Rouge foncé
    }
    
    # Ajouter les barres pour chaque grade dans l'ordre voulu
    for grade in ['Mild', 'Moderate', 'Severe']:
        if grade in result_combined.columns:
            percentages = []
            for _, row in result_combined.iterrows():
                if row['nb_greffe'] > 0:
                    pct = (row[grade] / row['nb_greffe']) * 100
                    percentages.append(pct)
                else:
                    percentages.append(0)
            
            fig.add_trace(go.Bar(
                name=grade,
                x=result_combined['Year'],
                y=percentages,
                marker_color=colors[grade],
                text=[f"{row[grade]}" for _, row in result_combined.iterrows()],
                textposition='inside',
                hovertemplate=f'<b>{grade}</b><br>' +
                             'Année: %{x}<br>' +
                             'Pourcentage: %{y:.1f}%<br>' +
                             'Nombre: %{text}<br>' +
                             '<extra></extra>'
            ))
    
    # Ajouter la ligne de référence à 50%
    years = result_combined['Year'].tolist()
    if years:
        x_min, x_max = min(years) - 0.5, max(years) + 0.5
        
        # Ligne à 50%
        fig.add_shape(
            type="line",
            x0=x_min, y0=50, x1=x_max, y1=50,
            line=dict(color="red", width=2, dash="dash"),
        )
        
        # Annotation pour la ligne
        fig.add_annotation(
            x=x_max - 0.1,
            y=52,
            text="50%",
            showarrow=False,
            font=dict(color="red", size=12),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="red",
            borderwidth=1
        )
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': '<b>GVH chronique par grade (J365)</b>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='<b>Année</b>',
        yaxis_title='<b>Pourcentage (%)</b>',
        barmode='stack',
        height=500,
        template='plotly_white',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        yaxis=dict(
            range=[0, 100],
            tickformat='.1f'
        ),
        margin=dict(r=150)
    )
    
    return fig


def create_gvhc_datatable(result_combined):
    """
    Crée la DataTable pour afficher les statistiques GVH chronique par année
    
    Args:
        result_combined (pd.DataFrame): DataFrame avec les statistiques GVHc
        
    Returns:
        html.Div: Composant DataTable
    """
    # Préparer les données pour la table
    table_data = []
    for _, row in result_combined.iterrows():
        table_data.append({
            'Année': int(row['Year']),
            'Nb greffes': int(row['nb_greffe']),
            'GVHc Mild': int(row.get('Mild', 0)),
            'GVHc Moderate': int(row.get('Moderate', 0)),
            'GVHc Severe': int(row.get('Severe', 0)),
            'Total GVHc': int(row['nb_gvh_chronique_total']),
            '% Total GVHc': f"{row['pourcentage_gvh_chronique_total']:.1f}%"
        })
    
    return html.Div([
        html.H6("Statistiques par année", className='mb-2'),
        dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Année", "id": "Année"},
                {"name": "Nb greffes", "id": "Nb greffes"},
                {"name": "GVHc Mild", "id": "GVHc Mild"},
                {"name": "GVHc Moderate", "id": "GVHc Moderate"},
                {"name": "GVHc Severe", "id": "GVHc Severe"},
                {"name": "Total GVHc", "id": "Total GVHc"},
                {"name": "% Total GVHc", "id": "% Total GVHc"}
            ],
            style_table={'height': '250px', 'overflowY': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '8px',
                'fontSize': '11px'
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
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                },
                {
                    'if': {'column_id': ['Total GVHc', '% Total GVHc']},
                    'backgroundColor': '#e8f4fd',
                    'fontWeight': 'bold'
                }
            ]
        )
    ])


def create_gvhc_badge(result_combined, analysis_year):
    """
    Crée le badge (étiquette) pour afficher le pourcentage GVHc total pour l'année sélectionnée
    
    Args:
        result_combined (pd.DataFrame): DataFrame avec les statistiques GVHc
        analysis_year (int): Année d'analyse
        
    Returns:
        html.Div: Composant avec le badge
    """
    # S'assurer que analysis_year est de type int
    analysis_year = int(analysis_year)
    
    # Obtenir les données pour l'année spécifiée
    year_data = result_combined[result_combined['Year'] == analysis_year]
    
    if year_data.empty:
        available_years = result_combined['Year'].unique()
        return dbc.Alert(
            f"Aucune donnée disponible pour l'année {analysis_year} (années disponibles: {sorted(available_years)})", 
            color="warning"
        )
    
    # Extraire les valeurs
    pct_total = year_data['pourcentage_gvh_chronique_total'].iloc[0]
    nb_total = year_data['nb_gvh_chronique_total'].iloc[0]
    total_greffes = year_data['nb_greffe'].iloc[0]
    
    # Détail par grade
    mild = year_data.get('Mild', pd.Series([0])).iloc[0]
    moderate = year_data.get('Moderate', pd.Series([0])).iloc[0]
    severe = year_data.get('Severe', pd.Series([0])).iloc[0]
    
    return html.Div([
        html.H6(f"Indicateur GVH chronique - Année {analysis_year}", className='text-center mb-3'),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H2(f"{pct_total:.1f}%", className="text-center mb-2", style={'color': '#2c3e50'}),
                        html.P("GVH chronique totale", className="text-center mb-2", style={'fontSize': '16px', 'fontWeight': 'bold'}),
                        html.P(f"({nb_total}/{total_greffes})", className="text-center text-muted mb-2", style={'fontSize': '14px'}),
                        html.Hr(className="my-2"),
                        html.Div([
                            html.P(f"Mild: {mild}", className="text-center mb-1", style={'fontSize': '12px'}),
                            html.P(f"Moderate: {moderate}", className="text-center mb-1", style={'fontSize': '12px'}),
                            html.P(f"Severe: {severe}", className="text-center mb-0", style={'fontSize': '12px'})
                        ])
                    ], className="py-3")
                ], color="info", outline=True, style={'border-width': '2px'})
            ], width=12)
        ])
    ], className="mb-3")


def create_gvhc_visualization(df, selected_year):
    """
    Crée la visualisation complète pour l'indicateur GVH chronique
    
    Args:
        df (pd.DataFrame): DataFrame avec les données
        selected_year (int): Année sélectionnée (on affichera l'année n-2)
        
    Returns:
        html.Div: Composant contenant la visualisation complète
    """
    try:
        # Traiter les données
        result_combined, grade_counts = process_gvhc_data(df)
        
        # Convertir l'année en int et calculer n-2
        selected_year = int(selected_year)
        analysis_year = selected_year - 2
        
        # S'assurer que la colonne Year est de type int
        result_combined['Year'] = result_combined['Year'].astype(int)
        
        # Créer le layout avec deux colonnes
        return dbc.Row([
            # Colonne gauche : Graphique (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_gvhc_barplot(result_combined, grade_counts),
                    style={'height': '600px'},
                    config={'responsive': True}
                )
            ], width=7),
            # Colonne droite : DataTable et badge (40%)
            dbc.Col([
                # DataTable
                create_gvhc_datatable(result_combined),
                html.Hr(className='my-3'),
                # Badge pour l'année sélectionnée
                create_gvhc_badge(result_combined, analysis_year)
            ], width=5)
        ])
    except Exception as e:
        return dbc.Alert(f"Erreur lors du calcul des indicateurs GVH chronique: {str(e)}", color="danger")