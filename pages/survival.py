# pages/survival.py
import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy.interpolate import interp1d
import traceback

# Import des modules nécessaires
import modules.dashboard_layout as layouts
from modules.dashboard_layout import apply_malignancy_filter
import modules.data_processing as data_processing
import visualizations.allogreffes.graphs as gr

# Imports pour les analyses de survie
try:
    from lifelines import KaplanMeierFitter
    LIFELINES_AVAILABLE = True
except ImportError:
    print("Warning: lifelines not available. Survival analyses will not work.")
    LIFELINES_AVAILABLE = False

KM_INFO_TEXT = """Event = Death
Censored = Alive at last follow-up"""

GRFS_INFO_TEXT = """Event = Relapse or GvHD
Censored = No relapse and no GvHD"""


def get_layout():
    """
    Retourne le layout de la page Survie avec graphiques empilés verticalement
    Chaque carte contient des onglets dcc.Tabs liés permettant de basculer
    entre Overall Survival et GRFS (comme dans Procedures)
    """
    return dbc.Container([
        dcc.Store(id='survival-missing-store'),
        dcc.Store(id='survival-tab-store', data='tab-os'),
        
        # ====== Card 1 : Global curve ======
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Survival curve')),
                    dbc.CardBody([
                        dcc.Tabs(
                            id='survival-tabs-0',
                            value='tab-os',
                            children=[
                                dcc.Tab(label='Overall Survival', value='tab-os', children=[
                                    html.Div(id='survival-global-curve')
                                ]),
                                dcc.Tab(label='GRFS', value='tab-grfs', children=[
                                    html.Div(id='survival-grfs-graph')
                                ])
                            ]
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # ====== Card 2 : Curves by year ======
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Survival by year')),
                    dbc.CardBody([
                        dcc.Tabs(
                            id='survival-tabs-1',
                            value='tab-os',
                            children=[
                                dcc.Tab(label='Overall Survival', value='tab-os', children=[
                                    html.Div(id='survival-curves-by-year')
                                ]),
                                dcc.Tab(label='GRFS', value='tab-grfs', children=[
                                    html.Div(id='survival-grfs-curves-by-year')
                                ])
                            ]
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # ====== Card 3 : Statistics table ======
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Statistics')),
                    dbc.CardBody([
                        dcc.Tabs(
                            id='survival-tabs-2',
                            value='tab-os',
                            children=[
                                dcc.Tab(label='Overall Survival', value='tab-os', children=[
                                    html.Div(
                                        id='survival-stats-table',
                                        style={'height': '400px', 'overflow': 'auto'}
                                    )
                                ]),
                                dcc.Tab(label='GRFS', value='tab-grfs', children=[
                                    html.Div(
                                        id='survival-grfs-stats-table',
                                        style={'height': '400px', 'overflow': 'auto'}
                                    )
                                ])
                            ]
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
                        html.Div(id='survival-missing-summary-table', children=[
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
                                id="export-missing-survival-button",
                                color="primary",
                                size="sm",
                                disabled=True,
                            )
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody([
                        html.Div(id='survival-missing-detail-table', children=[
                            dbc.Alert("Initial content - will be replaced by the callback", color='warning')
                        ]),
                        dcc.Download(id="download-missing-survival-excel")
                    ])
                ])
            ], width=6)
        ])

    ], fluid=True)

def create_survival_sidebar_content(data, pediatric_view=False):
    """
    Crée le contenu de la sidebar spécifique à la page Survie.
    
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
        available_years = sorted(df['Year'].unique().tolist(), reverse=True)  # Descending order
        years_options = [{'label': f'{year}', 'value': year} for year in available_years]
        # Select only the last 3 years by default
        default_years = [year['value'] for year in years_options[:3]] if len(years_options) >= 3 else [year['value'] for year in years_options]
    
    controls = [
        layouts.create_pediatric_switch_component(pediatric_view),
        
        # Paramètres d'analyse - RadioItems pour la durée
        html.Label('Maximum analysis duration:', className='mb-2', style={'color': '#021F59'}),
        dcc.RadioItems(
            id='survival-max-duration',
            options=[
                {'label': 'Max. 10 years', 'value': 'limited'},
                {'label': 'No limit (if follow-up > 10 years existing)', 'value': 'unlimited'}
            ],
            value='limited',
            className='mb-3',
            inline=False
        ),
        
        html.Hr(),
        
        # Filtres par année
        html.H5('Year filters', className='mb-2'),
        dcc.Checklist(
            id='survival-year-filter',
            options=years_options,
            value=default_years,
            inline=False,
            className='mb-3'
        ),
        
        html.Hr(),
        # Filtre d'âge toujours présent dans le DOM mais caché en vue normale
        layouts.create_age_filter_component(
            component_id='survival-age-filter',
            title='Age groups',
            pediatric_only=pediatric_view,
            hidden=not pediatric_view
        ),
        
        html.Hr(),
        
        # Filtres par type de diagnostic
        layouts.create_malignancy_filter_component(component_id='survival-malignancy-filter', title='Diagnosis type'),
        
        html.Hr(),
        
        # Filtres GvHD (affichés dynamiquement quand l'onglet GRFS est actif)
        html.Div(id='survival-gvh-filters-container'),
        
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

def prepare_survival_data(df):
    """
    Prépare les données pour l'analyse de survie Kaplan-Meier
    
    Args:
        df (pd.DataFrame): DataFrame avec les données brutes
        
    Returns:
        pd.DataFrame: DataFrame avec les colonnes 'follow_up_days', 'follow_up_years', 'statut_deces', 'Year'
    """
    # Vérifier les colonnes nécessaires
    required_cols = ['Treatment Date', 'Date Of Last Follow Up', 'Status Last Follow Up']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing columns for survival analysis: {missing_cols}")
    
    # Copier les données
    processed_data = df.copy()
    
    # Convertir les dates (format européen dd-mm-yyyy ou ISO8601)
    # Utiliser format='mixed' avec dayfirst pour gérer les différents formats
    processed_data['Treatment Date'] = pd.to_datetime(processed_data['Treatment Date'], dayfirst=True, format='mixed')
    processed_data['Date Of Last Follow Up'] = pd.to_datetime(processed_data['Date Of Last Follow Up'], dayfirst=True, format='mixed')
    
    # Calculer la durée de suivi en jours et en années
    processed_data['follow_up_days'] = (
        processed_data['Date Of Last Follow Up'] - processed_data['Treatment Date']
    ).dt.days
    
    # Convertir en années (365.25 jours par an pour tenir compte des années bissextiles)
    processed_data['follow_up_years'] = processed_data['follow_up_days'] / 365.25
    
    # Créer le statut de décès (1 = décès, 0 = censuré)
    processed_data['statut_deces'] = (
        processed_data['Status Last Follow Up'] == 'Dead'
    ).astype(int)
    
    # Nettoyer les données (supprimer les valeurs négatives ou nulles)
    processed_data = processed_data[
        (processed_data['follow_up_days'] >= 0) & 
        (processed_data['follow_up_days'].notna())
    ]
    
    return processed_data

def create_interactive_single_km_curve(processed_data, max_years=None, title="Kaplan-Meier survival curve"):
    """
    Crée une courbe Kaplan-Meier interactive simple avec axe X en années
    """
    if not LIFELINES_AVAILABLE:
        raise ImportError("lifelines is not available")
    
    # Filtrer si nécessaire (conversion en jours pour lifelines)
    if max_years:
        max_days = max_years * 365.25
        processed_data_filtered = processed_data.copy()
        # Convertir en float pour éviter l'incompatibilité de dtype
        processed_data_filtered['follow_up_days'] = processed_data_filtered['follow_up_days'].astype(float)
        processed_data_filtered['statut_deces'] = processed_data_filtered['statut_deces'].astype(float)
        mask_over_max = processed_data_filtered['follow_up_days'] > max_days
        processed_data_filtered.loc[mask_over_max, 'follow_up_days'] = max_days
        processed_data_filtered.loc[mask_over_max, 'statut_deces'] = 0
        display_max = max_years
    else:
        processed_data_filtered = processed_data
        display_max = processed_data['follow_up_years'].max()
    
    # Ajuster le modèle (lifelines utilise les jours)
    kmf = KaplanMeierFitter()
    kmf.fit(
        durations=processed_data_filtered['follow_up_days'],
        event_observed=processed_data_filtered['statut_deces']
    )
    
    # Obtenir les données et convertir en années pour l'affichage
    survival_function = kmf.survival_function_
    timeline_days = survival_function.index.values
    timeline_years = timeline_days / 365.25  # Convertir en années
    survival_probs = survival_function.iloc[:, 0].values
    confidence_interval = kmf.confidence_interval_
    ci_lower = confidence_interval.iloc[:, 0].values
    ci_upper = confidence_interval.iloc[:, 1].values
    
    # Texte de survol
    hover_text = [
        f"Time: {t:.1f} years ({t*365.25:.0f} days)<br>" +
        f"Survival probability: {p:.3f} ({p*100:.1f}%)<br>" +
        f"95% CI: [{ci_l:.3f} - {ci_u:.3f}]"
        for t, p, ci_l, ci_u in zip(timeline_years, survival_probs, ci_lower, ci_upper)
    ]
    
    # Identifier les temps de censure (où des patients sont censurés)
    event_table = kmf.event_table
    censoring_times_days = event_table[event_table['censored'] > 0].index.values
    censoring_times_years = censoring_times_days / 365.25
    
    # Obtenir les probabilités de survie aux temps de censure
    # Utiliser la survie juste avant la censure (à l'index le plus proche)
    censoring_surv_probs = []
    for ct_day in censoring_times_days:
        # Trouver l'index dans timeline_days le plus proche mais <= ct_day
        valid_indices = timeline_days <= ct_day
        if valid_indices.any():
            closest_idx = np.where(valid_indices)[0][-1]  # Dernier index valide
            censoring_surv_probs.append(survival_probs[closest_idx])
        else:
            censoring_surv_probs.append(1.0)  # Valeur par défaut au début
    
    # Calculer le nombre de sujets à risque aux temps spécifiés
    time_points = np.arange(0, int(display_max) + 1)
    at_risk_counts = []
    for t in time_points:
        t_days = t * 365.25
        at_risk = len(processed_data_filtered[processed_data_filtered['follow_up_days'] >= t_days])
        at_risk_counts.append(at_risk)
    
    # Créer la figure avec subplots pour la table "Number at risk"
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.82, 0.18],
        vertical_spacing=0.05,
        subplot_titles=(None, None)
    )
    
    # Courbe principale (row 1)
    fig.add_trace(go.Scatter(
        x=timeline_years,
        y=survival_probs,
        mode='lines',
        name='Survival curve',
        line=dict(color='#2E86AB', width=4, dash='solid'),
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=hover_text,
        opacity=0.9
    ), row=1, col=1)
    
    # Marqueurs uniquement aux temps de censure (row 1)
    if len(censoring_times_years) > 0:
        censoring_hover = [
            f"Censoring<br>Time: {t:.1f} years<br>Survival: {p:.3f}"
            for t, p in zip(censoring_times_years, censoring_surv_probs)
        ]
        fig.add_trace(go.Scatter(
            x=censoring_times_years,
            y=censoring_surv_probs,
            mode='markers',
            name='Censored',
            marker=dict(symbol='line-ns', size=12, color='#2E86AB', line=dict(width=2)),
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=censoring_hover,
            showlegend=False,
            opacity=0.7
        ), row=1, col=1)
    
    # Intervalle de confiance (row 1)
    fig.add_trace(go.Scatter(
        x=np.concatenate([timeline_years, timeline_years[::-1]]),
        y=np.concatenate([ci_upper, ci_lower[::-1]]),
        fill='toself',
        fillcolor='rgba(46, 134, 171, 0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=False,
        name='IC 95%',
        opacity=0.6
    ), row=1, col=1)
    
    # Ligne médiane avec style amélioré
    median_survival_days = kmf.median_survival_time_
    if not np.isnan(median_survival_days):
        median_survival_years = median_survival_days / 365.25
        fig.add_hline(
            y=0.5, 
            line_dash="dash", 
            line_color="#e74c3c", 
            line_width=2,
            opacity=0.8,
            row=1, col=1
        )
        fig.add_vline(
            x=median_survival_years, 
            line_dash="dash", 
            line_color="#e74c3c", 
            line_width=2,
            opacity=0.8,
            row=1, col=1
        )
        fig.add_annotation(
            x=median_survival_years + display_max*0.05,
            y=0.55,
            text=f"<b>Median: {median_survival_years:.1f} years</b>",
            showarrow=False,
            font=dict(color="#e74c3c", size=12, family='Arial, sans-serif'),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="#e74c3c",
            borderwidth=1,
            row=1, col=1
        )
    
    # Table "Number at risk" dans la deuxième rangée
    # Titre
    fig.add_annotation(
        x=0, y=0.7,
        xref='x2 domain', yref='y2 domain',
        text='<b>Number at risk</b>',
        showarrow=False,
        font=dict(size=11, family='Arial, sans-serif', color='#2c3e50'),
        xanchor='left',
        row=2, col=1
    )
    
    # Nombres à risque
    for t, count in zip(time_points, at_risk_counts):
        if t <= display_max:
            fig.add_annotation(
                x=t, y=0.2,
                xref='x2', yref='y2 domain',
                text=str(count),
                showarrow=False,
                font=dict(size=11, family='Arial, sans-serif', color='#2c3e50'),
                xanchor='center',
                row=2, col=1
            )
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': f'<b>{title}</b>', 
            'x': 0.5, 
            'y': 0.97,
            'font': {'size': 18, 'family': 'Arial, sans-serif', 'color': '#2c3e50'}
        },
        showlegend=False,
        plot_bgcolor='rgba(248, 249, 250, 0.8)',
        paper_bgcolor='white',
        height=520,
        margin=dict(l=80, r=60, t=60, b=40),
        font=dict(family='Arial, sans-serif', color='#2c3e50')
    )
    
    # Axe X du graphique principal
    fig.update_xaxes(
        range=[0, display_max],
        title_text='<b>Time (years)</b>',
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        showline=True,
        linewidth=2,
        linecolor='#bdc3c7',
        mirror=True,
        dtick=1 if display_max <= 10 else 2,
        row=1, col=1
    )
    
    # Axe Y du graphique principal
    fig.update_yaxes(
        range=[0, 1.05],
        title_text='<b>Survival probability</b>',
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        showline=True,
        linewidth=2,
        linecolor='#bdc3c7',
        mirror=True,
        tickformat='.2f',
        row=1, col=1
    )
    
    # Axe X de la table (même échelle, pas de titre, pas de grille)
    fig.update_xaxes(
        range=[0, display_max],
        showgrid=False,
        showline=False,
        showticklabels=False,
        zeroline=False,
        row=2, col=1
    )
    
    # Axe Y de la table (caché)
    fig.update_yaxes(
        range=[0, 1],
        showgrid=False,
        showline=False,
        showticklabels=False,
        zeroline=False,
        row=2, col=1
    )
    
    # Fond blanc pour la zone de la table (row 2)
    fig.add_shape(
        type="rect",
        xref="paper", yref="paper",
        x0=0, y0=0, x1=1, y1=0.18,
        fillcolor="white",
        line=dict(width=0),
        layer="below"
    )
    
    return fig

def create_interactive_km_curves_by_year(processed_data, max_years=None):
    """
    Crée des courbes Kaplan-Meier interactives par année avec Plotly et axe X en années
    
    Args:
        processed_data: DataFrame avec colonnes 'follow_up_days', 'statut_deces', 'Year'
        max_years: Limite maximale en années (None = pas de limite)
    """
    if not LIFELINES_AVAILABLE:
        raise ImportError("lifelines is not available")
    
    # Filtrer les données si limite spécifiée
    if max_years:
        max_days = max_years * 365.25
        processed_data_filtered = processed_data.copy()
        # Convertir en float pour éviter l'incompatibilité de dtype
        processed_data_filtered['follow_up_days'] = processed_data_filtered['follow_up_days'].astype(float)
        processed_data_filtered['statut_deces'] = processed_data_filtered['statut_deces'].astype(float)
        mask_over_max = processed_data_filtered['follow_up_days'] > max_days
        processed_data_filtered.loc[mask_over_max, 'follow_up_days'] = max_days
        processed_data_filtered.loc[mask_over_max, 'statut_deces'] = 0
        display_max = max_years
        title_suffix = f"(0-{max_years} years)"
    else:
        processed_data_filtered = processed_data
        display_max = processed_data['follow_up_years'].max()
        title_suffix = "(all duration)"
    
    # Créer la figure
    fig = go.Figure()
    
    # Obtenir les années uniques et les couleurs
    years = sorted(processed_data_filtered['Year'].unique())
    # Utiliser une palette étendue ou cyclique pour supporter beaucoup d'années
    extended_palette = (px.colors.qualitative.Set1 + 
                        px.colors.qualitative.Set2 + 
                        px.colors.qualitative.Set3 +
                        px.colors.qualitative.Dark24 +
                        px.colors.qualitative.Light24)
    # Cycle through colors if there are more years than colors
    colors = [extended_palette[i % len(extended_palette)] for i in range(len(years))]
    
    # Stocker les statistiques
    stats_summary = []
    
    # Créer une courbe pour chaque année
    for i, year in enumerate(years):
        year_data = processed_data_filtered[processed_data_filtered['Year'] == year]
        
        if len(year_data) > 0:
            # Ajuster le modèle Kaplan-Meier (utilise les jours)
            kmf = KaplanMeierFitter()
            kmf.fit(
                durations=year_data['follow_up_days'],
                event_observed=year_data['statut_deces']
            )
            
            # Obtenir les données de survie et convertir en années
            survival_function = kmf.survival_function_
            timeline_days = survival_function.index.values
            timeline_years = timeline_days / 365.25  # Convertir en années
            survival_probs = survival_function.iloc[:, 0].values
            
            # Calculer les intervalles de confiance - MÊME MÉTHODE QUE LES COURBES
            confidence_interval = kmf.confidence_interval_
            ci_lower = confidence_interval.iloc[:, 0].values
            ci_upper = confidence_interval.iloc[:, 1].values
            
            # Créer le texte de survol personnalisé
            hover_text = [
                f"<b>Year {year}</b><br>" +
                f"Time: {t:.1f} years ({t*365.25:.0f} days)<br>" +
                f"Survival probability: {p:.3f} ({p*100:.1f}%)<br>" +
                f"95% CI: [{ci_l:.3f} - {ci_u:.3f}]<br>" +
                f"Patients: {len(year_data)}"
                for t, p, ci_l, ci_u in zip(timeline_years, survival_probs, ci_lower, ci_upper)
            ]
            
            # Identifier les temps de censure (où des patients sont censurés)
            event_table = kmf.event_table
            censoring_times_days = event_table[event_table['censored'] > 0].index.values
            censoring_times_years = censoring_times_days / 365.25
            
            # Obtenir les probabilités de survie aux temps de censure
            censoring_surv_probs = []
            for ct_day in censoring_times_days:
                valid_indices = timeline_days <= ct_day
                if valid_indices.any():
                    closest_idx = np.where(valid_indices)[0][-1]
                    censoring_surv_probs.append(survival_probs[closest_idx])
                else:
                    censoring_surv_probs.append(1.0)
            
            # Ajouter la courbe principale (ligne uniquement)
            fig.add_trace(go.Scatter(
                x=timeline_years,
                y=survival_probs,
                mode='lines',
                name=f'Year {year}',
                line=dict(color=colors[i], width=3, dash='solid'),
                hovertemplate='%{hovertext}<extra></extra>',
                hovertext=hover_text,
                showlegend=True,
                opacity=0.9
            ))
            
            # Marqueurs uniquement aux temps de censure
            if len(censoring_times_years) > 0:
                censoring_hover = [
                    f"Censoring<br>Time: {t:.1f} years<br>Survival: {p:.3f}"
                    for t, p in zip(censoring_times_years, censoring_surv_probs)
                ]
                fig.add_trace(go.Scatter(
                    x=censoring_times_years,
                    y=censoring_surv_probs,
                    mode='markers',
                    name=f'Censored - Year {year}',
                    marker=dict(symbol='line-ns', size=11, color=colors[i], line=dict(width=2)),
                    hovertemplate='%{hovertext}<extra></extra>',
                    hovertext=censoring_hover,
                    showlegend=False,
                    opacity=0.7
                ))
            
            # Ajouter l'intervalle de confiance seulement si peu d'années (sinon c'est trop chargé)
            if len(years) <= 10:
                # Convertir la couleur en rgba avec transparence
                color = colors[i]
                if color.startswith('rgb'):
                    fill_color = color.replace('rgb', 'rgba').replace(')', ', 0.15)')
                elif color.startswith('#'):
                    # Convertir hex en rgba
                    fill_color = f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15)'
                else:
                    fill_color = 'rgba(128, 128, 128, 0.15)'
                
                fig.add_trace(go.Scatter(
                    x=np.concatenate([timeline_years, timeline_years[::-1]]),
                    y=np.concatenate([ci_upper, ci_lower[::-1]]),
                    fill='toself',
                    fillcolor=fill_color,
                    line=dict(color='rgba(255,255,255,0)'),
                    hoverinfo="skip",
                    showlegend=False,
                    name=f'95% CI - Year {year}',
                    opacity=0.6
                ))
            
            # Calculer les statistiques
            median_survival_days = kmf.median_survival_time_
            median_survival_years = median_survival_days / 365.25 if not np.isnan(median_survival_days) else np.nan
            
            # Fonction helper pour extraire les IC aux temps spécifiques
            # UTILISE LA MÊME MÉTHODE QUE LES COURBES POUR LA COHÉRENCE
            def get_survival_with_ci_exact(target_days):
                """Extrait la survie et ses IC aux temps spécifiques de manière cohérente avec les courbes"""
                if (not max_years or target_days/365.25 <= max_years):
                    try:
                        # Obtenir la survie à cette durée - MÊME MÉTHODE QUE L'ORIGINAL
                        surv = kmf.survival_function_at_times(target_days).iloc[0]
                        
                        # Pour les IC, trouver l'index le plus proche dans la timeline des IC
                        timeline_days_ic = confidence_interval.index.values
                        
                        # Trouver l'index le plus proche du temps cible
                        closest_idx = np.argmin(np.abs(timeline_days_ic - target_days))
                        closest_time = timeline_days_ic[closest_idx]
                        
                        # Si le temps le plus proche est dans une tolérance raisonnable (±30 jours)
                        if abs(closest_time - target_days) <= 30:
                            # Utiliser les valeurs exactes de l'index le plus proche
                            ci_lower_val = confidence_interval.iloc[closest_idx, 0]
                            ci_upper_val = confidence_interval.iloc[closest_idx, 1]
                        else:
                            # Si pas de point proche, interpoler entre les deux points les plus proches
                            if target_days < timeline_days_ic.min():
                                ci_lower_val = confidence_interval.iloc[0, 0]
                                ci_upper_val = confidence_interval.iloc[0, 1]
                            elif target_days > timeline_days_ic.max():
                                ci_lower_val = confidence_interval.iloc[-1, 0]
                                ci_upper_val = confidence_interval.iloc[-1, 1]
                            else:
                                # Interpolation simple avec numpy
                                ci_lower_vals = confidence_interval.iloc[:, 0].values
                                ci_upper_vals = confidence_interval.iloc[:, 1].values
                                ci_lower_val = np.interp(target_days, timeline_days_ic, ci_lower_vals)
                                ci_upper_val = np.interp(target_days, timeline_days_ic, ci_upper_vals)
                        
                        # Calculer la marge d'erreur de la même façon que dans les courbes
                        margin_error = (ci_upper_val - ci_lower_val) / 2
                        
                        return surv, margin_error, ci_lower_val, ci_upper_val
                        
                    except Exception as e:
                        # En cas d'erreur, retourner au minimum la survie si possible
                        try:
                            surv = kmf.survival_function_at_times(target_days).iloc[0]
                            return surv, np.nan, np.nan, np.nan
                        except:
                            return np.nan, np.nan, np.nan, np.nan
                else:
                    return np.nan, np.nan, np.nan, np.nan
            
            # Calculer survie et IC à 1, 2, 5 et 10 ans avec la méthode cohérente
            surv_1yr, me_1yr, ci_l_1yr, ci_u_1yr = get_survival_with_ci_exact(365.25)
            surv_2yr, me_2yr, ci_l_2yr, ci_u_2yr = get_survival_with_ci_exact(730.5)
            surv_5yr, me_5yr, ci_l_5yr, ci_u_5yr = get_survival_with_ci_exact(1826.25)
            surv_10yr, me_10yr, ci_l_10yr, ci_u_10yr = get_survival_with_ci_exact(3652.5)
            
            # Fonction pour formater avec intervalle de confiance
            def format_survival_with_ci(survival, margin_error):
                """Formate la survie avec IC sous forme 72.9±2.5"""
                if not np.isnan(survival) and not np.isnan(margin_error):
                    return f"{survival*100:.1f}±{margin_error*100:.1f}"
                elif not np.isnan(survival):
                    # Si on a la survie mais pas la marge d'erreur, afficher juste la survie
                    return f"{survival*100:.1f}"
                else:
                    return "N/A"
            
            stats_summary.append({
                'Année': year,
                'N patients': len(year_data),
                'Événements': year_data['statut_deces'].sum(),
                'Taux censure (%)': f"{(1 - year_data['statut_deces'].mean())*100:.1f}",
                'Survie médiane (ans)': f"{median_survival_years:.1f}" if not np.isnan(median_survival_years) else "Non atteinte",
                'Survie 1 an (%)': format_survival_with_ci(surv_1yr, me_1yr),
                'Survie 2 ans (%)': format_survival_with_ci(surv_2yr, me_2yr),
                'Survie 5 ans (%)': format_survival_with_ci(surv_5yr, me_5yr),
                'Survie 10 ans (%)': format_survival_with_ci(surv_10yr, me_10yr)
            })
    
    # Calculer le nombre de sujets à risque pour chaque année
    time_points = np.arange(0, int(display_max) + 1)
    at_risk_by_year = {}
    for year in years:
        year_data = processed_data_filtered[processed_data_filtered['Year'] == year]
        at_risk_counts = []
        for t in time_points:
            t_days = t * 365.25
            at_risk = len(year_data[year_data['follow_up_days'] >= t_days])
            at_risk_counts.append(at_risk)
        at_risk_by_year[year] = at_risk_counts
    
    # Créer les annotations pour le tableau "Number at risk"
    annotations = []
    
    # Titre du tableau
    annotations.append(dict(
        x=0, y=-0.12,
        xref='paper', yref='paper',
        text='<b>Number at risk</b>',
        showarrow=False,
        font=dict(size=12, family='Arial, sans-serif', color='#2c3e50'),
        xanchor='left'
    ))
    
    # Pour chaque année, ajouter une ligne
    y_offset = -0.17
    for i, year in enumerate(years):
        color = colors[i] if i < len(colors) else '#2c3e50'
        # Label de l'année (positionné à gauche de la colonne t=0)
        annotations.append(dict(
            x=-0.02, y=y_offset,
            xref='paper', yref='paper',
            text=f'{year}',
            showarrow=False,
            font=dict(size=10, family='Arial, sans-serif', color=color),
            xanchor='right'
        ))
        # Nombres à risque (commençant à t=0)
        for t, count in zip(time_points, at_risk_by_year[year]):
            if t <= display_max:
                x_pos = t / display_max if display_max > 0 else 0
                annotations.append(dict(
                    x=x_pos, y=y_offset,
                    xref='paper', yref='paper',
                    text=str(count),
                    showarrow=False,
                    font=dict(size=10, family='Arial, sans-serif', color='#2c3e50'),
                    xanchor='center'
                ))
        y_offset -= 0.04
    
    # Mise en forme du graphique avec style élégant
    fig.update_layout(
        title={
            'text': f'<b>Kaplan-Meier survival curves by year {title_suffix}</b>',
            'x': 0.5,
            'y': 0.95,
            'font': {'size': 18, 'family': 'Arial, sans-serif', 'color': '#2c3e50'}
        },
        xaxis_title='<b>Time (years)</b>',
        yaxis_title='<b>Survival probability</b>',
        xaxis=dict(
            range=[0, display_max],
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='rgba(128, 128, 128, 0.5)',
            tickfont=dict(size=12, family='Arial, sans-serif', color='#34495e'),
            titlefont=dict(size=14, family='Arial, sans-serif', color='#2c3e50'),
            showline=True,
            linewidth=2,
            linecolor='#bdc3c7',
            mirror=True,
            dtick=1 if display_max <= 10 else 2  # Graduations tous les 1 ou 2 ans
        ),
        yaxis=dict(
            range=[0, 1.05],
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='rgba(128, 128, 128, 0.5)',
            tickfont=dict(size=12, family='Arial, sans-serif', color='#34495e'),
            titlefont=dict(size=14, family='Arial, sans-serif', color='#2c3e50'),
            showline=True,
            linewidth=2,
            linecolor='#bdc3c7',
            mirror=True,
            tickformat='.2f'
        ),
        legend=dict(
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.98,
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='#bdc3c7',
            borderwidth=1,
            font=dict(size=11, family='Arial, sans-serif', color='#2c3e50')
        ),
        annotations=annotations,
        hovermode='closest',
        plot_bgcolor='rgba(248, 249, 250, 0.8)',
        paper_bgcolor='white',
        height=450 + len(years) * 25,
        margin=dict(l=80, r=80, t=60, b=60 + len(years) * 20),
        font=dict(family='Arial, sans-serif', color='#2c3e50')
    )
    
    return fig, pd.DataFrame(stats_summary)

def prepare_grfs_data(df):
    """
    Prépare les données pour l'analyse de survie GRFS
    (GvH & Relapse Free Survival)
    
    Event = première occurrence de GvHD aiguë, GvHD chronique, ou rechute
    Censure = pas d'event à la date de dernier suivi
    """
    required_cols = ['Treatment Date', 'Date Of Last Follow Up']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns for GRFS analysis: {missing_cols}")
    
    processed_data = df.copy()
    
    # Convertir les dates
    processed_data['Treatment Date'] = pd.to_datetime(
        processed_data['Treatment Date'], dayfirst=True, format='mixed'
    )
    processed_data['Date Of Last Follow Up'] = pd.to_datetime(
        processed_data['Date Of Last Follow Up'], dayfirst=True, format='mixed'
    )
    
    # Convertir les dates d'event si elles existent
    date_cols = [
        'First Agvhd Occurrence Date', 
        'First Cgvhd Occurrence Date',
        'First Relapse Date'
    ]
    for col in date_cols:
        if col in processed_data.columns:
            processed_data[col] = pd.to_datetime(
                processed_data[col], dayfirst=True, format='mixed', errors='coerce'
            )
    
    # Calculer le temps de suivi de base
    processed_data['follow_up_days'] = (
        processed_data['Date Of Last Follow Up'] - processed_data['Treatment Date']
    ).dt.days
    
    # Collecter les dates candidates pour chaque type d'event
    candidate_dates = pd.DataFrame(index=processed_data.index)
    
    if 'First Agvhd Occurrence' in processed_data.columns and 'First Agvhd Occurrence Date' in processed_data.columns:
        mask = processed_data['First Agvhd Occurrence'] == 'Yes'
        candidate_dates['agvhd'] = processed_data['First Agvhd Occurrence Date'].where(mask, pd.NaT)
    
    if 'First Cgvhd Occurrence' in processed_data.columns and 'First Cgvhd Occurrence Date' in processed_data.columns:
        mask = processed_data['First Cgvhd Occurrence'] == 'Yes'
        candidate_dates['cgvhd'] = processed_data['First Cgvhd Occurrence Date'].where(mask, pd.NaT)
    
    if 'First Relapse' in processed_data.columns and 'First Relapse Date' in processed_data.columns:
        mask = processed_data['First Relapse'] == 'Yes'
        candidate_dates['relapse'] = processed_data['First Relapse Date'].where(mask, pd.NaT)
    
    if not candidate_dates.empty:
        processed_data['event_date'] = candidate_dates.min(axis=1)
    else:
        processed_data['event_date'] = pd.NaT
    
    # Déterminer le temps et le statut d'event
    event_valid = processed_data['event_date'].notna()
    event_before_censor = event_valid & (
        processed_data['event_date'] <= processed_data['Date Of Last Follow Up']
    )
    
    processed_data['grfs_event'] = event_before_censor.astype(int)
    processed_data['grfs_days'] = processed_data['follow_up_days'].copy()
    
    event_times = (processed_data.loc[event_before_censor, 'event_date'] - 
                   processed_data.loc[event_before_censor, 'Treatment Date']).dt.days
    processed_data.loc[event_before_censor, 'grfs_days'] = event_times
    
    # Nettoyer les données (supprimer les valeurs négatives ou nulles)
    processed_data = processed_data[
        (processed_data['grfs_days'] >= 0) & 
        (processed_data['grfs_days'].notna())
    ]
    
    return processed_data


def create_grfs_km_curve(processed_data, max_years=None, title="GvH & Relapse Free Survival"):
    """
    Crée une courbe Kaplan-Meier interactive pour la GRFS avec axe X en années
    """
    if not LIFELINES_AVAILABLE:
        raise ImportError("lifelines is not available")
    
    # Filtrer si nécessaire (conversion en jours pour lifelines)
    if max_years:
        max_days = max_years * 365.25
        processed_data_filtered = processed_data.copy()
        processed_data_filtered['grfs_days'] = processed_data_filtered['grfs_days'].astype(float)
        processed_data_filtered['grfs_event'] = processed_data_filtered['grfs_event'].astype(float)
        mask_over_max = processed_data_filtered['grfs_days'] > max_days
        processed_data_filtered.loc[mask_over_max, 'grfs_days'] = max_days
        processed_data_filtered.loc[mask_over_max, 'grfs_event'] = 0
        display_max = max_years
    else:
        processed_data_filtered = processed_data
        display_max = processed_data['grfs_days'].max() / 365.25
    
    # Ajuster le modèle (lifelines utilise les jours)
    kmf = KaplanMeierFitter()
    kmf.fit(
        durations=processed_data_filtered['grfs_days'],
        event_observed=processed_data_filtered['grfs_event']
    )
    
    # Obtenir les données et convertir en années pour l'affichage
    survival_function = kmf.survival_function_
    timeline_days = survival_function.index.values
    timeline_years = timeline_days / 365.25
    survival_probs = survival_function.iloc[:, 0].values
    confidence_interval = kmf.confidence_interval_
    ci_lower = confidence_interval.iloc[:, 0].values
    ci_upper = confidence_interval.iloc[:, 1].values
    
    # Texte de survol
    hover_text = [
        f"Time: {t:.1f} years ({t*365.25:.0f} days)<br>" +
        f"GRFS probability: {p:.3f} ({p*100:.1f}%)<br>" +
        f"95% CI: [{ci_l:.3f} - {ci_u:.3f}]"
        for t, p, ci_l, ci_u in zip(timeline_years, survival_probs, ci_lower, ci_upper)
    ]
    
    # Identifier les temps de censure
    event_table = kmf.event_table
    censoring_times_days = event_table[event_table['censored'] > 0].index.values
    censoring_times_years = censoring_times_days / 365.25
    
    censoring_surv_probs = []
    for ct_day in censoring_times_days:
        valid_indices = timeline_days <= ct_day
        if valid_indices.any():
            closest_idx = np.where(valid_indices)[0][-1]
            censoring_surv_probs.append(survival_probs[closest_idx])
        else:
            censoring_surv_probs.append(1.0)
    
    # Calculer le nombre de sujets à risque aux temps spécifiés
    time_points = np.arange(0, int(display_max) + 1)
    at_risk_counts = []
    for t in time_points:
        t_days = t * 365.25
        at_risk = len(processed_data_filtered[processed_data_filtered['grfs_days'] >= t_days])
        at_risk_counts.append(at_risk)
    
    # Créer la figure avec subplots pour la table "Number at risk"
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.82, 0.18],
        vertical_spacing=0.05,
        subplot_titles=(None, None)
    )
    
    # Courbe principale
    fig.add_trace(go.Scatter(
        x=timeline_years,
        y=survival_probs,
        mode='lines',
        name='GRFS curve',
        line=dict(color='#2E86AB', width=4, dash='solid'),
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=hover_text,
        opacity=0.9
    ), row=1, col=1)
    
    # Marqueurs de censure
    if len(censoring_times_years) > 0:
        censoring_hover = [
            f"Censoring<br>Time: {t:.1f} years<br>GRFS: {p:.3f}"
            for t, p in zip(censoring_times_years, censoring_surv_probs)
        ]
        fig.add_trace(go.Scatter(
            x=censoring_times_years,
            y=censoring_surv_probs,
            mode='markers',
            name='Censored',
            marker=dict(symbol='line-ns', size=12, color='#2E86AB', line=dict(width=2)),
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=censoring_hover,
            showlegend=False,
            opacity=0.7
        ), row=1, col=1)
    
    # Intervalle de confiance
    fig.add_trace(go.Scatter(
        x=np.concatenate([timeline_years, timeline_years[::-1]]),
        y=np.concatenate([ci_upper, ci_lower[::-1]]),
        fill='toself',
        fillcolor='rgba(46, 134, 171, 0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=False,
        name='IC 95%',
        opacity=0.6
    ), row=1, col=1)
    
    # Ligne médiane
    median_survival_days = kmf.median_survival_time_
    if not np.isnan(median_survival_days):
        median_survival_years = median_survival_days / 365.25
        fig.add_hline(
            y=0.5, 
            line_dash="dash", 
            line_color="#e74c3c", 
            line_width=2,
            opacity=0.8,
            row=1, col=1
        )
        fig.add_vline(
            x=median_survival_years, 
            line_dash="dash", 
            line_color="#e74c3c", 
            line_width=2,
            opacity=0.8,
            row=1, col=1
        )
        fig.add_annotation(
            x=median_survival_years + display_max*0.05,
            y=0.55,
            text=f"<b>Median: {median_survival_years:.1f} years</b>",
            showarrow=False,
            font=dict(color="#e74c3c", size=12, family='Arial, sans-serif'),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="#e74c3c",
            borderwidth=1,
            row=1, col=1
        )
    
    # Table "Number at risk"
    fig.add_annotation(
        x=0, y=0.7,
        xref='x2 domain', yref='y2 domain',
        text='<b>Number at risk</b>',
        showarrow=False,
        font=dict(size=11, family='Arial, sans-serif', color='#2c3e50'),
        xanchor='left',
        row=2, col=1
    )
    
    for t, count in zip(time_points, at_risk_counts):
        if t <= display_max:
            fig.add_annotation(
                x=t, y=0.2,
                xref='x2', yref='y2 domain',
                text=str(count),
                showarrow=False,
                font=dict(size=11, family='Arial, sans-serif', color='#2c3e50'),
                xanchor='center',
                row=2, col=1
            )
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': f'<b>{title}</b>', 
            'x': 0.5, 
            'y': 0.97,
            'font': {'size': 18, 'family': 'Arial, sans-serif', 'color': '#2c3e50'}
        },
        showlegend=False,
        plot_bgcolor='rgba(248, 249, 250, 0.8)',
        paper_bgcolor='white',
        height=520,
        margin=dict(l=80, r=60, t=60, b=40),
        font=dict(family='Arial, sans-serif', color='#2c3e50')
    )
    
    fig.update_xaxes(
        range=[0, display_max],
        title_text='<b>Time (years)</b>',
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        showline=True,
        linewidth=2,
        linecolor='#bdc3c7',
        mirror=True,
        dtick=1 if display_max <= 10 else 2,
        row=1, col=1
    )
    
    fig.update_yaxes(
        range=[0, 1.05],
        title_text='<b>GRFS probability</b>',
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        showline=True,
        linewidth=2,
        linecolor='#bdc3c7',
        mirror=True,
        tickformat='.2f',
        row=1, col=1
    )
    
    fig.update_xaxes(
        range=[0, display_max],
        showgrid=False,
        showline=False,
        showticklabels=False,
        zeroline=False,
        row=2, col=1
    )
    
    fig.update_yaxes(
        range=[0, 1],
        showgrid=False,
        showline=False,
        showticklabels=False,
        zeroline=False,
        row=2, col=1
    )
    
    fig.add_shape(
        type="rect",
        xref="paper", yref="paper",
        x0=0, y0=0, x1=1, y1=0.18,
        fillcolor="white",
        line=dict(width=0),
        layer="below"
    )
    
    return fig

def create_interactive_grfs_curves_by_year(processed_data, max_years=None):
    """
    Crée des courbes GRFS interactives par année avec Plotly et axe X en années
    
    Args:
        processed_data: DataFrame avec colonnes 'grfs_days', 'grfs_event', 'Year'
        max_years: Limite maximale en années (None = pas de limite)
    """
    if not LIFELINES_AVAILABLE:
        raise ImportError("lifelines is not available")
    
    # Filtrer les données si limite spécifiée
    if max_years:
        max_days = max_years * 365.25
        processed_data_filtered = processed_data.copy()
        processed_data_filtered['grfs_days'] = processed_data_filtered['grfs_days'].astype(float)
        processed_data_filtered['grfs_event'] = processed_data_filtered['grfs_event'].astype(float)
        mask_over_max = processed_data_filtered['grfs_days'] > max_days
        processed_data_filtered.loc[mask_over_max, 'grfs_days'] = max_days
        processed_data_filtered.loc[mask_over_max, 'grfs_event'] = 0
        display_max = max_years
        title_suffix = f"(0-{max_years} years)"
    else:
        processed_data_filtered = processed_data
        display_max = processed_data['grfs_days'].max() / 365.25
        title_suffix = "(all duration)"
    
    # Créer la figure
    fig = go.Figure()
    
    # Obtenir les années uniques et les couleurs
    years = sorted(processed_data_filtered['Year'].unique())
    extended_palette = (px.colors.qualitative.Set1 + 
                        px.colors.qualitative.Set2 + 
                        px.colors.qualitative.Set3 +
                        px.colors.qualitative.Dark24 +
                        px.colors.qualitative.Light24)
    colors = [extended_palette[i % len(extended_palette)] for i in range(len(years))]
    
    # Stocker les statistiques
    stats_summary = []
    
    # Créer une courbe pour chaque année
    for i, year in enumerate(years):
        year_data = processed_data_filtered[processed_data_filtered['Year'] == year]
        
        if len(year_data) > 0:
            kmf = KaplanMeierFitter()
            kmf.fit(
                durations=year_data['grfs_days'],
                event_observed=year_data['grfs_event']
            )
            
            survival_function = kmf.survival_function_
            timeline_days = survival_function.index.values
            timeline_years = timeline_days / 365.25
            survival_probs = survival_function.iloc[:, 0].values
            
            confidence_interval = kmf.confidence_interval_
            ci_lower = confidence_interval.iloc[:, 0].values
            ci_upper = confidence_interval.iloc[:, 1].values
            
            hover_text = [
                f"<b>Year {year}</b><br>" +
                f"Time: {t:.1f} years ({t*365.25:.0f} days)<br>" +
                f"GRFS probability: {p:.3f} ({p*100:.1f}%)<br>" +
                f"95% CI: [{ci_l:.3f} - {ci_u:.3f}]<br>" +
                f"Patients: {len(year_data)}"
                for t, p, ci_l, ci_u in zip(timeline_years, survival_probs, ci_lower, ci_upper)
            ]
            
            event_table = kmf.event_table
            censoring_times_days = event_table[event_table['censored'] > 0].index.values
            censoring_times_years = censoring_times_days / 365.25
            
            censoring_surv_probs = []
            for ct_day in censoring_times_days:
                valid_indices = timeline_days <= ct_day
                if valid_indices.any():
                    closest_idx = np.where(valid_indices)[0][-1]
                    censoring_surv_probs.append(survival_probs[closest_idx])
                else:
                    censoring_surv_probs.append(1.0)
            
            fig.add_trace(go.Scatter(
                x=timeline_years,
                y=survival_probs,
                mode='lines',
                name=f'Year {year}',
                line=dict(color=colors[i], width=3, dash='solid'),
                hovertemplate='%{hovertext}<extra></extra>',
                hovertext=hover_text,
                showlegend=True,
                opacity=0.9
            ))
            
            if len(censoring_times_years) > 0:
                censoring_hover = [
                    f"Censoring<br>Time: {t:.1f} years<br>GRFS: {p:.3f}"
                    for t, p in zip(censoring_times_years, censoring_surv_probs)
                ]
                fig.add_trace(go.Scatter(
                    x=censoring_times_years,
                    y=censoring_surv_probs,
                    mode='markers',
                    name=f'Censored - Year {year}',
                    marker=dict(symbol='line-ns', size=11, color=colors[i], line=dict(width=2)),
                    hovertemplate='%{hovertext}<extra></extra>',
                    hovertext=censoring_hover,
                    showlegend=False,
                    opacity=0.7
                ))
            
            if len(years) <= 10:
                color = colors[i]
                if color.startswith('rgb'):
                    fill_color = color.replace('rgb', 'rgba').replace(')', ', 0.15)')
                elif color.startswith('#'):
                    fill_color = f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15)'
                else:
                    fill_color = 'rgba(128, 128, 128, 0.15)'
                
                fig.add_trace(go.Scatter(
                    x=np.concatenate([timeline_years, timeline_years[::-1]]),
                    y=np.concatenate([ci_upper, ci_lower[::-1]]),
                    fill='toself',
                    fillcolor=fill_color,
                    line=dict(color='rgba(255,255,255,0)'),
                    hoverinfo="skip",
                    showlegend=False,
                    name=f'95% CI - Year {year}',
                    opacity=0.6
                ))
            
            median_survival_days = kmf.median_survival_time_
            median_survival_years = median_survival_days / 365.25 if not np.isnan(median_survival_days) else np.nan
            
            def get_grfs_with_ci_exact(target_days):
                """Extrait la GRFS et ses IC aux temps spécifiques"""
                if (not max_years or target_days/365.25 <= max_years):
                    try:
                        surv = kmf.survival_function_at_times(target_days).iloc[0]
                        timeline_days_ic = confidence_interval.index.values
                        closest_idx = np.argmin(np.abs(timeline_days_ic - target_days))
                        closest_time = timeline_days_ic[closest_idx]
                        
                        if abs(closest_time - target_days) <= 30:
                            ci_lower_val = confidence_interval.iloc[closest_idx, 0]
                            ci_upper_val = confidence_interval.iloc[closest_idx, 1]
                        else:
                            if target_days < timeline_days_ic.min():
                                ci_lower_val = confidence_interval.iloc[0, 0]
                                ci_upper_val = confidence_interval.iloc[0, 1]
                            elif target_days > timeline_days_ic.max():
                                ci_lower_val = confidence_interval.iloc[-1, 0]
                                ci_upper_val = confidence_interval.iloc[-1, 1]
                            else:
                                ci_lower_vals = confidence_interval.iloc[:, 0].values
                                ci_upper_vals = confidence_interval.iloc[:, 1].values
                                ci_lower_val = np.interp(target_days, timeline_days_ic, ci_lower_vals)
                                ci_upper_val = np.interp(target_days, timeline_days_ic, ci_upper_vals)
                        
                        margin_error = (ci_upper_val - ci_lower_val) / 2
                        return surv, margin_error, ci_lower_val, ci_upper_val
                        
                    except Exception:
                        try:
                            surv = kmf.survival_function_at_times(target_days).iloc[0]
                            return surv, np.nan, np.nan, np.nan
                        except:
                            return np.nan, np.nan, np.nan, np.nan
                else:
                    return np.nan, np.nan, np.nan, np.nan
            
            grfs_1yr, me_1yr, ci_l_1yr, ci_u_1yr = get_grfs_with_ci_exact(365.25)
            grfs_2yr, me_2yr, ci_l_2yr, ci_u_2yr = get_grfs_with_ci_exact(730.5)
            grfs_5yr, me_5yr, ci_l_5yr, ci_u_5yr = get_grfs_with_ci_exact(1826.25)
            grfs_10yr, me_10yr, ci_l_10yr, ci_u_10yr = get_grfs_with_ci_exact(3652.5)
            
            def format_grfs_with_ci(survival, margin_error):
                if not np.isnan(survival) and not np.isnan(margin_error):
                    return f"{survival*100:.1f}±{margin_error*100:.1f}"
                elif not np.isnan(survival):
                    return f"{survival*100:.1f}"
                else:
                    return "N/A"
            
            stats_summary.append({
                'Année': year,
                'N patients': len(year_data),
                'Événements': year_data['grfs_event'].sum(),
                'Taux censure (%)': f"{(1 - year_data['grfs_event'].mean())*100:.1f}",
                'GRFS médiane (ans)': f"{median_survival_years:.1f}" if not np.isnan(median_survival_years) else "Non atteinte",
                'GRFS 1 an (%)': format_grfs_with_ci(grfs_1yr, me_1yr),
                'GRFS 2 ans (%)': format_grfs_with_ci(grfs_2yr, me_2yr),
                'GRFS 5 ans (%)': format_grfs_with_ci(grfs_5yr, me_5yr),
                'GRFS 10 ans (%)': format_grfs_with_ci(grfs_10yr, me_10yr)
            })
    
    # Calculer le nombre de sujets à risque pour chaque année
    time_points = np.arange(0, int(display_max) + 1)
    at_risk_by_year = {}
    for year in years:
        year_data = processed_data_filtered[processed_data_filtered['Year'] == year]
        at_risk_counts = []
        for t in time_points:
            t_days = t * 365.25
            at_risk = len(year_data[year_data['grfs_days'] >= t_days])
            at_risk_counts.append(at_risk)
        at_risk_by_year[year] = at_risk_counts
    
    # Créer les annotations pour le tableau "Number at risk"
    annotations = []
    
    annotations.append(dict(
        x=0, y=-0.12,
        xref='paper', yref='paper',
        text='<b>Number at risk</b>',
        showarrow=False,
        font=dict(size=12, family='Arial, sans-serif', color='#2c3e50'),
        xanchor='left'
    ))
    
    y_offset = -0.17
    for i, year in enumerate(years):
        color = colors[i] if i < len(colors) else '#2c3e50'
        annotations.append(dict(
            x=-0.02, y=y_offset,
            xref='paper', yref='paper',
            text=f'{year}',
            showarrow=False,
            font=dict(size=10, family='Arial, sans-serif', color=color),
            xanchor='right'
        ))
        for t, count in zip(time_points, at_risk_by_year[year]):
            if t <= display_max:
                x_pos = t / display_max if display_max > 0 else 0
                annotations.append(dict(
                    x=x_pos, y=y_offset,
                    xref='paper', yref='paper',
                    text=str(count),
                    showarrow=False,
                    font=dict(size=10, family='Arial, sans-serif', color='#2c3e50'),
                    xanchor='center'
                ))
        y_offset -= 0.04
    
    fig.update_layout(
        title={
            'text': f'<b>GRFS curves by year {title_suffix}</b>',
            'x': 0.5,
            'y': 0.95,
            'font': {'size': 18, 'family': 'Arial, sans-serif', 'color': '#2c3e50'}
        },
        xaxis_title='<b>Time (years)</b>',
        yaxis_title='<b>GRFS probability</b>',
        xaxis=dict(
            range=[0, display_max],
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='rgba(128, 128, 128, 0.5)',
            tickfont=dict(size=12, family='Arial, sans-serif', color='#34495e'),
            titlefont=dict(size=14, family='Arial, sans-serif', color='#2c3e50'),
            showline=True,
            linewidth=2,
            linecolor='#bdc3c7',
            mirror=True,
            dtick=1 if display_max <= 10 else 2
        ),
        yaxis=dict(
            range=[0, 1.05],
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='rgba(128, 128, 128, 0.5)',
            tickfont=dict(size=12, family='Arial, sans-serif', color='#34495e'),
            titlefont=dict(size=14, family='Arial, sans-serif', color='#2c3e50'),
            showline=True,
            linewidth=2,
            linecolor='#bdc3c7',
            mirror=True,
            tickformat='.2f'
        ),
        legend=dict(
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.98,
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='#bdc3c7',
            borderwidth=1,
            font=dict(size=11, family='Arial, sans-serif', color='#2c3e50')
        ),
        annotations=annotations,
        hovermode='closest',
        plot_bgcolor='rgba(248, 249, 250, 0.8)',
        paper_bgcolor='white',
        height=450 + len(years) * 25,
        margin=dict(l=80, r=80, t=60, b=60 + len(years) * 20),
        font=dict(family='Arial, sans-serif', color='#2c3e50')
    )
    
    return fig, pd.DataFrame(stats_summary)

def register_callbacks(app):
    """
    Enregistre tous les callbacks spécifiques à la page Survie
    """
    
    # Import caching utility
    from modules.cache_utils import cache_survival_result
    
    # ------------------------------------------------------------------
    # Linked tabs sync using dash.set_props (avoids circular callbacks)
    # ------------------------------------------------------------------
    from dash import set_props
    
    @app.callback(
        Output('survival-tab-store', 'data', allow_duplicate=True),
        Input('survival-tabs-0', 'value'),
        State('survival-tab-store', 'data'),
        prevent_initial_call=True
    )
    def sync_from_tab_0(value, current_store):
        if value == current_store:
            return dash.no_update
        set_props('survival-tabs-1', {'value': value})
        set_props('survival-tabs-2', {'value': value})
        return value
    
    @app.callback(
        Output('survival-tab-store', 'data', allow_duplicate=True),
        Input('survival-tabs-1', 'value'),
        State('survival-tab-store', 'data'),
        prevent_initial_call=True
    )
    def sync_from_tab_1(value, current_store):
        if value == current_store:
            return dash.no_update
        set_props('survival-tabs-0', {'value': value})
        set_props('survival-tabs-2', {'value': value})
        return value
    
    @app.callback(
        Output('survival-tab-store', 'data', allow_duplicate=True),
        Input('survival-tabs-2', 'value'),
        State('survival-tab-store', 'data'),
        prevent_initial_call=True
    )
    def sync_from_tab_2(value, current_store):
        if value == current_store:
            return dash.no_update
        set_props('survival-tabs-0', {'value': value})
        set_props('survival-tabs-1', {'value': value})
        return value
    
    # ------------------------------------------------------------------
    # Dynamic GvHD grade filters in sidebar (visible only for GRFS)
    # ------------------------------------------------------------------
    @app.callback(
        Output('survival-gvh-filters-container', 'children'),
        [Input('survival-tab-store', 'data'),
         Input('data-store', 'data')]
    )
    def update_gvh_filters_container(active_tab, data):
        """Affiche les filtres de grade GvHD quand l'onglet GRFS est actif"""
        if active_tab != 'tab-grfs' or data is None:
            return html.Div()
        
        df = pd.DataFrame(data)
        
        # Filtre pour grades aGvH
        acute_col = 'First aGvHD Maximum Score'
        acute_filter = []
        if acute_col in df.columns:
            available = df[acute_col].dropna().unique().tolist()
            available = [g for g in available if g != 'Grade 0 (none)']
            grade_order = ['Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Unknown']
            options = []
            for g in grade_order:
                if g in available:
                    options.append({'label': g, 'value': g})
            for g in available:
                if g not in grade_order:
                    options.append({'label': g, 'value': g})
            if options:
                acute_filter = [
                    html.H6('Acute GvHD grades', className='mb-2'),
                    dcc.Checklist(
                        id='survival-agvh-grade-filter',
                        options=options,
                        value=[o['value'] for o in options],
                        inline=False,
                        className='mb-3',
                        style={'fontSize': '12px'}
                    )
                ]
        
        # Filtre pour scores cGvH
        chronic_col = 'First cGvHD Maximum NIH Score'
        chronic_filter = []
        if chronic_col in df.columns:
            import modules.data_processing as data_processing
            df = data_processing.transform_gvhc_scores(df)
            available = df[chronic_col].dropna().unique().tolist()
            score_order = ['Mild', 'Moderate', 'Severe', 'Not done', 'Unknown']
            options = []
            for s in score_order:
                if s in available:
                    options.append({'label': s, 'value': s})
            for s in available:
                if s not in score_order:
                    options.append({'label': s, 'value': s})
            if options:
                chronic_filter = [
                    html.H6('Chronic GvHD scores', className='mb-2'),
                    dcc.Checklist(
                        id='survival-cgvh-grade-filter',
                        options=options,
                        value=[o['value'] for o in options],
                        inline=False,
                        className='mb-3',
                        style={'fontSize': '12px'}
                    )
                ]
        
        if not acute_filter and not chronic_filter:
            return html.Div([
                html.P('No GvHD grade data available', className='text-muted small')
            ])
        
        return html.Div([
            html.H5('GvHD filters', className='mb-2'),
            html.P('Filter patients by GvHD grade', className='text-muted small mb-2'),
        ] + acute_filter + chronic_filter)
    
    # Create cached versions of expensive lifelines calculations
    @cache_survival_result
    def _cached_prepare_survival_data(data_json_str, max_duration, selected_years_tuple):
        """Cached version of survival data preparation + curve generation"""
        import json
        # Convert JSON string back to DataFrame
        data_list = json.loads(data_json_str)
        df = pd.DataFrame(data_list)
        
        print(f"DEBUG _cached_prepare_survival_data: Columns in cached df: {list(df.columns)}")
        
        # Filtrer par années
        if selected_years_tuple and 'Year' in df.columns:
            df = df[df['Year'].isin(list(selected_years_tuple))]
        
        if df.empty:
            return None
        
        processed_data = prepare_survival_data(df)
        if len(processed_data) == 0:
            return None
            
        max_years = 10 if max_duration == 'limited' else None
        
        fig = create_interactive_single_km_curve(
            processed_data,
            max_years=max_years,
            title=f"Kaplan-Meier overall survival curve (N={len(processed_data)})"
        )
        return fig
    
    @app.callback(
        Output('survival-global-curve', 'children'),
        [Input('data-store-survival', 'data'),  # Use slim store
         Input('current-page', 'data'),
         Input('survival-max-duration', 'value'),
         Input('survival-year-filter', 'value'),
         Input('survival-age-filter', 'value'),
         Input('survival-malignancy-filter', 'value')]
        # Note: No prevent_initial_call - must run when page loads with data
    )
    def update_global_survival_curve(data, current_page, max_duration, selected_years, selected_age_groups, malignancy_filter):
        """Met à jour la courbe de survie globale"""
        if current_page != 'Survival' or data is None:
            return html.Div()
        
        if not LIFELINES_AVAILABLE:
            return dbc.Alert([
                html.H6("Module 'lifelines' required", className="mb-2"),
                html.P("To use survival analyses, install the lifelines module:", className="mb-1"),
                html.Code("pip install lifelines", className="d-block mb-2"),
                html.P("Restart the application.", className="mb-0")
            ], color="warning")
        
        try:
            # Filtrer les données par âge et malignité avant de les passer au cache
            import json
            df = pd.DataFrame(data)
            if selected_age_groups and 'Age Group Detailed' in df.columns:
                df = df[df['Age Group Detailed'].isin(selected_age_groups)]
            
            # Filtrer par type de diagnostic
            df = apply_malignancy_filter(df, malignancy_filter)
            
            # Convert data to JSON string for caching (preserves structure)
            data_json = json.dumps(df.to_dict('records')) if len(df) > 0 else '[]'
            years_tuple = tuple(selected_years) if selected_years else tuple()
            
            fig = _cached_prepare_survival_data(data_json, max_duration, years_tuple)
            
            if fig is None:
                return dbc.Alert('No valid data for survival analysis', color='warning')
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True}
            )
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return dbc.Alert(f'Error during survival curve creation: {str(e)}', color='danger')
    
    # Cached version for multi-year survival curves
    @cache_survival_result
    def _cached_survival_by_year(data_json_str, max_duration, selected_years_tuple):
        """Cached version of multi-year survival calculation"""
        import json
        # Convert JSON string back to DataFrame
        data_list = json.loads(data_json_str)
        df = pd.DataFrame(data_list)
        
        if selected_years_tuple and 'Year' in df.columns:
            df = df[df['Year'].isin(list(selected_years_tuple))]
        
        if df.empty:
            return None, None
        
        processed_data = prepare_survival_data(df)
        if len(processed_data) == 0:
            return None, None
        
        max_years = 10 if max_duration == 'limited' else None
        
        fig, stats_df = create_interactive_km_curves_by_year(
            processed_data,
            max_years=max_years
        )
        
        # Convert fig to dict for caching
        return fig.to_dict() if fig else None, stats_df.to_dict('records') if not stats_df.empty else []
    
    @app.callback(
        [Output('survival-curves-by-year', 'children'),
         Output('survival-stats-table', 'children')],
        [Input('data-store-survival', 'data'),  # Use slim store
         Input('current-page', 'data'),
         Input('survival-max-duration', 'value'),
         Input('survival-year-filter', 'value'),
         Input('survival-age-filter', 'value'),
         Input('survival-malignancy-filter', 'value')]
        # Note: No prevent_initial_call - must run when page loads with data
    )
    def update_survival_curves_by_year(data, current_page, max_duration, selected_years, selected_age_groups, malignancy_filter):
        """Met à jour les courbes de survie par année et le tableau des statistiques"""
        if current_page != 'Survival' or data is None:
            return html.Div(), html.Div()
        
        if not LIFELINES_AVAILABLE:
            warning_alert = dbc.Alert([
                html.H6("Module 'lifelines' required", className="mb-2"),
                html.P("To use survival analyses, install the lifelines module:", className="mb-1"),
                html.Code("pip install lifelines", className="d-block mb-2"),
                html.P("Restart the application.", className="mb-0")
            ], color="warning")
            return warning_alert, warning_alert
        
        try:
            # Filtrer les données par âge et malignité avant de les passer au cache
            import json
            df = pd.DataFrame(data)
            if selected_age_groups and 'Age Group Detailed' in df.columns:
                df = df[df['Age Group Detailed'].isin(selected_age_groups)]
            
            # Filtrer par type de diagnostic
            df = apply_malignancy_filter(df, malignancy_filter)
            
            data_json = json.dumps(df.to_dict('records')) if len(df) > 0 else '[]'
            years_tuple = tuple(selected_years) if selected_years else tuple()
            
            fig_dict, stats_records = _cached_survival_by_year(data_json, max_duration, years_tuple)
            
            if fig_dict is None:
                no_data_alert = dbc.Alert('No valid data for survival analysis', color='warning')
                return no_data_alert, no_data_alert
            
            # Reconstruct figure from dict
            import plotly.graph_objects as go
            fig = go.Figure(fig_dict)
            stats_df = pd.DataFrame(stats_records) if stats_records else pd.DataFrame()
            
            # Graphique
            graph_component = html.Div([dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True}
            )])
            
            # Tableau des statistiques
            if not stats_df.empty:
                
                table_component = html.Div([
                    html.P(f"Survival statistics for {len(stats_df)} years analyzed", 
                           className="text-muted mb-3"),
                    dash_table.DataTable(
                        data=stats_df.to_dict('records'),
                        columns=[
                            {"name": col, "id": col, "type": "text" if col == "Year" else "text"}
                            for col in stats_df.columns
                        ],
                        style_table={'height': '350px', 'overflowY': 'auto'},
                        style_cell={
                            'textAlign': 'center',
                            'padding': '10px',
                            'fontFamily': 'Arial, sans-serif',
                            'fontSize': '12px',
                            'color': '#021F59'
                        },
                        style_header={
                            'backgroundColor': '#021F59', 
                            'color': 'white',
                            'fontWeight': 'bold',
                            'textAlign': 'center'
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': '#F2E9DF'
                            }
                        ]
                    )
                ])
            else:
                table_component = dbc.Alert('No statistics calculated', color='warning')
            
            return graph_component, table_component
        
        except Exception as e:
            error_msg = f'Error during survival analysis: {str(e)}'
            print(f"\n{'='*60}")
            print(error_msg)
            print(traceback.format_exc())
            print(f"{'='*60}\n")
            error_alert = dbc.Alert([
                html.H6('Error during survival analysis', className='mb-2'),
                html.Pre(str(e), style={'whiteSpace': 'pre-wrap', 'fontSize': '11px'})
            ], color='danger')
            return error_alert, error_alert
    
    # Cached version of GRFS by year calculation
    @cache_survival_result
    def _cached_grfs_by_year(data_json_str, max_duration, selected_years_tuple):
        """Cached version of multi-year GRFS calculation"""
        import json
        data_list = json.loads(data_json_str)
        df = pd.DataFrame(data_list)
        
        if selected_years_tuple and 'Year' in df.columns:
            df = df[df['Year'].isin(list(selected_years_tuple))]
        
        if df.empty:
            return None, None
        
        processed_data = prepare_grfs_data(df)
        if processed_data.empty:
            return None, None
        
        max_years = 10 if max_duration == 'limited' else None
        
        fig, stats_df = create_interactive_grfs_curves_by_year(
            processed_data,
            max_years=max_years
        )
        
        return fig.to_dict() if fig else None, stats_df.to_dict('records') if not stats_df.empty else []
    
    # Cached version of GRFS calculation
    @cache_survival_result
    def _cached_grfs_km(data_json_str, selected_years_tuple, max_years):
        """Cached version of GRFS Kaplan-Meier calculation"""
        import json
        data_list = json.loads(data_json_str)
        df = pd.DataFrame(data_list)
        
        # Filter by years
        if selected_years_tuple and 'Year' in df.columns:
            df = df[df['Year'].isin(list(selected_years_tuple))]
        
        if df.empty:
            return None
        
        # Prepare GRFS data and create KM curve
        processed_data = prepare_grfs_data(df)
        
        if processed_data.empty:
            return None
        
        fig = create_grfs_km_curve(processed_data, max_years=max_years)
        return fig.to_dict() if fig else None
    
    
    @app.callback(
        [Output('survival-grfs-graph', 'children'),
         Output('survival-grfs-curves-by-year', 'children'),
         Output('survival-grfs-stats-table', 'children')],
        [Input('data-store-survival', 'data'),
         Input('current-page', 'data'),
         Input('survival-max-duration', 'value'),
         Input('survival-year-filter', 'value'),
         Input('survival-age-filter', 'value'),
         Input('survival-malignancy-filter', 'value'),
         Input('survival-agvh-grade-filter', 'value'),
         Input('survival-cgvh-grade-filter', 'value')]
    )
    def update_survival_grfs_graph(data, current_page, max_duration, selected_years, selected_age_groups, malignancy_filter, selected_agvh_grades, selected_cgvh_scores):
        """Met à jour le graphique GRFS (Kaplan-Meier), les courbes par année et le tableau"""
        if current_page != 'Survival' or data is None:
            return html.Div(), html.Div(), html.Div()
        
        if not LIFELINES_AVAILABLE:
            warning_alert = dbc.Alert([
                html.H6("Module 'lifelines' required", className="mb-2"),
                html.P("To use GRFS analysis, install the lifelines module:", className="mb-1"),
                html.Code("pip install lifelines", className="d-block mb-2"),
                html.P("Restart the application.", className="mb-0")
            ], color="warning")
            return warning_alert, warning_alert, warning_alert
        
        try:
            import json
            df = pd.DataFrame(data)
            if selected_age_groups and 'Age Group Detailed' in df.columns:
                df = df[df['Age Group Detailed'].isin(selected_age_groups)]
            
            df = apply_malignancy_filter(df, malignancy_filter)
            
            # Appliquer les filtres de grade GvHD
            if selected_agvh_grades and 'First aGvHD Maximum Score' in df.columns:
                df = df[df['First aGvHD Maximum Score'].isin(selected_agvh_grades)]
            
            if selected_cgvh_scores and 'First cGvHD Maximum NIH Score' in df.columns:
                df = data_processing.transform_gvhc_scores(df)
                df = df[df['First cGvHD Maximum NIH Score'].isin(selected_cgvh_scores)]
            
            data_json = json.dumps(df.to_dict('records')) if len(df) > 0 else '[]'
            years_tuple = tuple(selected_years) if selected_years else tuple()
            
            # Global GRFS curve (no artificial limit)
            max_years = None
            fig_dict_global = _cached_grfs_km(data_json, years_tuple, max_years)
            
            if fig_dict_global is None:
                no_data = dbc.Alert('No valid data for GRFS analysis', color='warning')
                return no_data, no_data, no_data
            
            import plotly.graph_objects as go
            fig_global = go.Figure(fig_dict_global)
            global_component = dcc.Graph(
                figure=fig_global,
                style={'height': '100%'},
                config={'responsive': True}
            )
            
            # GRFS by year
            fig_dict_by_year, stats_records = _cached_grfs_by_year(data_json, max_duration, years_tuple)
            
            if fig_dict_by_year is None:
                no_data = dbc.Alert('No valid data for GRFS by year analysis', color='warning')
                return global_component, no_data, no_data
            
            fig_by_year = go.Figure(fig_dict_by_year)
            by_year_component = html.Div([dcc.Graph(
                figure=fig_by_year,
                style={'height': '100%'},
                config={'responsive': True}
            )])
            
            stats_df = pd.DataFrame(stats_records) if stats_records else pd.DataFrame()
            
            if not stats_df.empty:
                table_component = html.Div([
                    html.P(f"GRFS statistics for {len(stats_df)} years analyzed", 
                           className="text-muted mb-3"),
                    dash_table.DataTable(
                        data=stats_df.to_dict('records'),
                        columns=[
                            {"name": col, "id": col, "type": "text" if col == "Year" else "text"}
                            for col in stats_df.columns
                        ],
                        style_table={'height': '350px', 'overflowY': 'auto'},
                        style_cell={
                            'textAlign': 'center',
                            'padding': '10px',
                            'fontFamily': 'Arial, sans-serif',
                            'fontSize': '12px',
                            'color': '#021F59'
                        },
                        style_header={
                            'backgroundColor': '#021F59', 
                            'color': 'white',
                            'fontWeight': 'bold',
                            'textAlign': 'center'
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': '#F2E9DF'
                            }
                        ]
                    )
                ])
            else:
                table_component = dbc.Alert('No statistics calculated', color='warning')
            
            return global_component, by_year_component, table_component
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_alert = dbc.Alert([
                html.H6('Error during GRFS analysis', className='mb-2'),
                html.Pre(str(e), style={'whiteSpace': 'pre-wrap', 'fontSize': '11px'})
            ], color='danger')
            return error_alert, error_alert, error_alert
    
    @app.callback(
        Output('survival-missing-summary-table', 'children'),
        [Input('data-store', 'data'), 
         Input('current-page', 'data'),
         Input('survival-year-filter', 'value'),
         Input('survival-age-filter', 'value'),
         Input('survival-malignancy-filter', 'value')],
        prevent_initial_call=False
    )
    def survival_missing_summary_callback(data, current_page, selected_years, selected_age_groups, malignancy_filter):
        """Gère le tableau de résumé des données manquantes pour Survie"""
        
        if current_page != 'Survival' or not data:
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
            
            # Variables spécifiques à analyser pour Survie
            columns_to_analyze = [
                # Variables principales pour l'analyse de survie
                'Treatment Date',
                'Date Of Last Follow Up',
                'Status Last Follow Up',
                
                # Variable pour stratification
                'Year'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert("No survival variable found", color='warning')
            
            # Utiliser la fonction existante de graphs.py
            missing_summary, _ = gr.analyze_missing_data(df, existing_columns, 'Long ID')
            
            return dash_table.DataTable(
                data=missing_summary.to_dict('records'),
                columns=[
                    {"name": "Column", "id": "Column"},
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
        [Output('survival-missing-detail-table', 'children'),
         Output('export-missing-survival-button', 'disabled'),
         Output('survival-missing-store', 'data')],
        [Input('data-store', 'data'), 
         Input('current-page', 'data'),
         Input('survival-year-filter', 'value'),
         Input('survival-age-filter', 'value'),
         Input('survival-malignancy-filter', 'value')],
        prevent_initial_call=False
    )
    def survival_missing_detail_callback(data, current_page, selected_years, selected_age_groups, malignancy_filter):
        """Gère le tableau détaillé des patients avec données manquantes pour Survie"""
        
        if current_page != 'Survival' or not data:
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
            
            # Variables spécifiques à analyser pour Survie
            columns_to_analyze = [
                # Variables principales pour l'analyse de survie
                'Treatment Date',
                'Date Of Last Follow Up',
                'Status Last Follow Up',
                
                # Variable pour stratification
                'Year'
            ]
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert("No survival variable found", color='warning'), True, None
            
            # Utiliser la fonction existante de graphs.py
            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
            
            if detailed_missing.empty:
                return dbc.Alert("No missing data found !", color='success'), True, None
            
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
            
            return table_content, False, detailed_data  # Activer le bouton d'export
            
        except Exception as e:
            return dbc.Alert(f"Error during analysis: {str(e)}", color='danger'), True, None

    @app.callback(
        Output("download-missing-survival-excel", "data"),
        Input("export-missing-survival-button", "n_clicks"),
        State('survival-missing-store', 'data'),
        prevent_initial_call=True
    )
    def export_missing_survival_excel(n_clicks, missing_data):
        """Gère l'export Excel des patients avec données manquantes pour Survie"""
        if n_clicks is None:
            return dash.no_update
        
        try:
            # Récupérer les données stockées
            if missing_data:
                missing_df = pd.DataFrame(missing_data)
                
                # Générer un nom de fichier avec la date
                from datetime import datetime
                current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"survival_missing_data_{current_date}.xlsx"
                
                return dcc.send_data_frame(
                    missing_df.to_excel, 
                    filename=filename,
                    index=False
                )
            else:
                return dash.no_update
                
        except Exception as e:
            print(f"Error during Excel export Survival: {e}")
            return dash.no_update
