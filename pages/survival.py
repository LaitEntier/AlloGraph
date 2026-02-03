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
import visualizations.allogreffes.graphs as gr

# Imports pour les analyses de survie
try:
    from lifelines import KaplanMeierFitter
    LIFELINES_AVAILABLE = True
except ImportError:
    print("Warning: lifelines not available. Survival analyses will not work.")
    LIFELINES_AVAILABLE = False

def get_layout():
    """
    Retourne le layout de la page Survie avec graphiques empilés verticalement
    """
    return dbc.Container([
        # Premier graphique - Courbe de survie globale
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Kaplan-Meier overall survival curve')),
                    dbc.CardBody([
                        html.Div(
                            id='survival-global-curve'
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Deuxième graphique - Courbes de survie par année
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Kaplan-Meier survival curves by year')),
                    dbc.CardBody([
                        html.Div(
                            id='survival-curves-by-year'
                        )  
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Troisième section - Tableau des statistiques
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Survival statistics by year')),
                    dbc.CardBody([
                        html.Div(
                            id='survival-stats-table',
                            style={'height': '400px', 'overflow': 'auto'}
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
                                disabled=True,  # Désactivé par défaut
                            )
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody([
                        html.Div(id='survival-missing-detail-table', children=[
                            dbc.Alert("Initial content - will be replaced by the callback", color='warning')
                        ]),
                        # Composant pour télécharger le fichier CSV (invisible)
                        dcc.Download(id="download-missing-survival-excel")
                    ])
                ])
            ], width=6)
        ])

    ], fluid=True)

def create_survival_sidebar_content(data):
    """
    Crée le contenu de la sidebar spécifique à la page Survie.
    
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
        available_years = sorted(df['Year'].unique().tolist(), reverse=True)  # Descending order
        years_options = [{'label': f'{year}', 'value': year} for year in available_years]
        # Select only the last 3 years by default
        default_years = [year['value'] for year in years_options[:3]] if len(years_options) >= 3 else [year['value'] for year in years_options]
    
    return html.Div([
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
            marker=dict(symbol='cross', size=10, color='#2E86AB'),
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
                    marker=dict(symbol='cross', size=9, color=colors[i]),
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
def register_callbacks(app):
    """
    Enregistre tous les callbacks spécifiques à la page Survie
    """
    
    @app.callback(
        Output('survival-global-curve', 'children'),
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('survival-max-duration', 'value'),  # Changé de 'survival-max-days'
         Input('survival-year-filter', 'value')]
    )
    def update_global_survival_curve(data, current_page, max_duration, selected_years):
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
        
        df = pd.DataFrame(data)
        
        # Filtrer par années sélectionnées
        if selected_years and 'Year' in df.columns:
            df = df[df['Year'].isin(selected_years)]
        
        if df.empty:
            return dbc.Alert('No data available with the selected filters', color='warning')
        
        try:
            # Préparer les données pour l'analyse de survie
            processed_data = prepare_survival_data(df)
            
            if len(processed_data) == 0:
                return dbc.Alert('No valid data for survival analysis', color='warning')
            
            # Déterminer la limite maximale
            max_years = 10 if max_duration == 'limited' else None
            
            # Créer la courbe de survie globale
            fig = create_interactive_single_km_curve(
                processed_data,
                max_years=max_years,
                title=f"Kaplan-Meier overall survival curve (N={len(processed_data)})"
            )
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True}
            )
        
        except Exception as e:
            return dbc.Alert(f'Error during survival curve creation: {str(e)}', color='danger')
    
    @app.callback(
        [Output('survival-curves-by-year', 'children'),
         Output('survival-stats-table', 'children')],
        [Input('data-store', 'data'),
         Input('current-page', 'data'),
         Input('survival-max-duration', 'value'),  # Changé de 'survival-max-days'
         Input('survival-year-filter', 'value')]
    )
    def update_survival_curves_by_year(data, current_page, max_duration, selected_years):
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
        
        df = pd.DataFrame(data)
        
        # Filtrer par années sélectionnées
        if selected_years and 'Year' in df.columns:
            df = df[df['Year'].isin(selected_years)]
        
        if df.empty:
            empty_alert = dbc.Alert('No data available with the selected filters', color='warning')
            return empty_alert, empty_alert
        
        try:
            # Préparer les données pour l'analyse de survie
            processed_data = prepare_survival_data(df)
            
            if len(processed_data) == 0:
                no_data_alert = dbc.Alert('No valid data for survival analysis', color='warning')
                return no_data_alert, no_data_alert
            
            # Vérifier qu'on a plusieurs années
            if 'Year' not in processed_data.columns:
                single_year_alert = dbc.Alert(
                    'At least 2 years of data are necessary for the comparison by year', 
                    color='info'
                )
                return single_year_alert, single_year_alert
            
            # Limiter le nombre d'années affichées si trop nombreuses
            years = sorted(processed_data['Year'].unique(), reverse=True)  # Descending order
            year_limit_warning = None
            if len(years) > 20:
                # Garder seulement les 15 dernières années
                recent_years = years[:15]
                processed_data = processed_data[processed_data['Year'].isin(recent_years)]
                year_limit_warning = dbc.Alert(
                    f"Too many years selected. Showing only the 15 most recent years.",
                    color='info',
                    className='mb-3'
                )
            
            # Déterminer la limite maximale
            max_years = 10 if max_duration == 'limited' else None
            
            # Créer les courbes de survie par année
            fig, stats_df = create_interactive_km_curves_by_year(
                processed_data,
                max_years=max_years
            )
            
            # Graphique (avec avertissement si années limitées)
            graph_children = [dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True}
            )]
            if year_limit_warning:
                graph_children.insert(0, year_limit_warning)
            graph_component = html.Div(graph_children)
            
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
    
    @app.callback(
        Output('survival-missing-summary-table', 'children'),
        [Input('data-store', 'data'), 
         Input('current-page', 'data'),
         Input('survival-year-filter', 'value')],
        prevent_initial_call=False
    )
    def survival_missing_summary_callback(data, current_page, selected_years):
        """Gère le tableau de résumé des données manquantes pour Survie"""
        
        if current_page != 'Survival' or not data:
            return html.Div("Waiting...", className='text-muted')
        
        try:
            df = pd.DataFrame(data)
            
            # Filtrer par années si spécifié
            if selected_years and 'Year' in df.columns:
                df = df[df['Year'].isin(selected_years)]
            
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
         Output('export-missing-survival-button', 'disabled')],
        [Input('data-store', 'data'), 
         Input('current-page', 'data'),
         Input('survival-year-filter', 'value')],
        prevent_initial_call=False
    )
    def survival_missing_detail_callback(data, current_page, selected_years):
        """Gère le tableau détaillé des patients avec données manquantes pour Survie"""
        
        if current_page != 'Survival' or not data:
            return html.Div("Waiting...", className='text-muted'), True
        
        try:
            df = pd.DataFrame(data)
            
            # Filtrer par années si spécifié
            if selected_years and 'Year' in df.columns:
                df = df[df['Year'].isin(selected_years)]
            
            if df.empty:
                return html.Div('No data for the selected years', className='text-warning text-center'), True
            
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
                return dbc.Alert("No survival variable found", color='warning'), True
            
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
            app.server.missing_survival_data = detailed_data
            
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

    @app.callback(
        Output("download-missing-survival-excel", "data"),
        Input("export-missing-survival-button", "n_clicks"),
        prevent_initial_call=True
    )
    def export_missing_survival_excel(n_clicks):
        """Gère l'export Excel des patients avec données manquantes pour Survie"""
        if n_clicks is None:
            return dash.no_update
        
        try:
            # Récupérer les données stockées
            if hasattr(app.server, 'missing_survival_data') and app.server.missing_survival_data:
                missing_df = pd.DataFrame(app.server.missing_survival_data)
                
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
