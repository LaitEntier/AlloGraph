# pages/survival.py
import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.interpolate import interp1d

# Import des modules nécessaires
import modules.dashboard_layout as layouts
import visualizations.allogreffes.graphs as gr

# Imports pour les analyses de survie
try:
    from lifelines import KaplanMeierFitter
    LIFELINES_AVAILABLE = True
except ImportError:
    print("Attention: lifelines non disponible. Les analyses de survie ne fonctionneront pas.")
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
                    dbc.CardHeader(html.H5('Courbe de survie Kaplan-Meier globale')),
                    dbc.CardBody([
                        html.Div(
                            id='survival-global-curve',
                            style={'height': '600px', 'overflow': 'hidden'}
                        )
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Deuxième graphique - Courbes de survie par année
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Courbes de survie Kaplan-Meier par année')),
                    dbc.CardBody([
                        html.Div(
                            id='survival-curves-by-year',
                            style={'height': '700px', 'overflow': 'hidden'}
                        )  
                    ], className='p-2')
                ])
            ], width=12)
        ], className='mb-4'),
        
        # Troisième section - Tableau des statistiques
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Statistiques de survie par année')),
                    dbc.CardBody([
                        html.Div(
                            id='survival-stats-table',
                            style={'height': '400px', 'overflow': 'auto'}
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
                        html.Div(id='survival-missing-summary-table', children=[
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
                                id="export-missing-survival-button",
                                color="primary",
                                size="sm",
                                disabled=True,  # Désactivé par défaut
                            )
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody([
                        html.Div(id='survival-missing-detail-table', children=[
                            dbc.Alert("Contenu initial - sera remplacé par le callback", color='warning')
                        ]),
                        # Composant pour télécharger le fichier CSV (invisible)
                        dcc.Download(id="download-missing-survival-csv")
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
        # Paramètres d'analyse - RadioItems pour la durée
        html.Label('Durée maximale d\'analyse:', className='mb-2'),
        dcc.RadioItems(
            id='survival-max-duration',
            options=[
                {'label': 'Max. 10 ans', 'value': 'limited'},
                {'label': 'Pas de limite', 'value': 'unlimited'}
            ],
            value='limited',
            className='mb-3',
            inline=False
        ),
        
        html.Hr(),
        
        # Filtres par année
        html.H5('Filtres par année', className='mb-2'),
        dcc.Checklist(
            id='survival-year-filter',
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
        raise ValueError(f"Colonnes manquantes pour l'analyse de survie: {missing_cols}")
    
    # Copier les données
    processed_data = df.copy()
    
    # Convertir les dates
    processed_data['Treatment Date'] = pd.to_datetime(processed_data['Treatment Date'])
    processed_data['Date Of Last Follow Up'] = pd.to_datetime(processed_data['Date Of Last Follow Up'])
    
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

def create_interactive_single_km_curve(processed_data, max_years=None, title="Courbe de survie Kaplan-Meier"):
    """
    Crée une courbe Kaplan-Meier interactive simple avec axe X en années
    """
    if not LIFELINES_AVAILABLE:
        raise ImportError("lifelines n'est pas disponible")
    
    # Filtrer si nécessaire (conversion en jours pour lifelines)
    if max_years:
        max_days = max_years * 365.25
        processed_data_filtered = processed_data.copy()
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
        f"Temps: {t:.1f} années ({t*365.25:.0f} jours)<br>" +
        f"Probabilité de survie: {p:.3f} ({p*100:.1f}%)<br>" +
        f"IC 95%: [{ci_l:.3f} - {ci_u:.3f}]"
        for t, p, ci_l, ci_u in zip(timeline_years, survival_probs, ci_lower, ci_upper)
    ]
    
    # Créer la figure
    fig = go.Figure()
    
    # Courbe principale avec style amélioré
    fig.add_trace(go.Scatter(
        x=timeline_years,
        y=survival_probs,
        mode='lines',
        name='Courbe de survie',
        line=dict(color='#2E86AB', width=4, dash='solid'),
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=hover_text,
        opacity=0.9
    ))
    
    # Intervalle de confiance avec style élégant
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
    ))
    
    # Ligne médiane avec style amélioré
    median_survival_days = kmf.median_survival_time_
    if not np.isnan(median_survival_days):
        median_survival_years = median_survival_days / 365.25
        fig.add_hline(
            y=0.5, 
            line_dash="dash", 
            line_color="#e74c3c", 
            line_width=2,
            opacity=0.8
        )
        fig.add_vline(
            x=median_survival_years, 
            line_dash="dash", 
            line_color="#e74c3c", 
            line_width=2,
            opacity=0.8
        )
        fig.add_annotation(
            x=median_survival_years + display_max*0.05,
            y=0.55,
            text=f"<b>Médiane: {median_survival_years:.1f}ans</b>",
            showarrow=False,
            font=dict(color="#e74c3c", size=12, family='Arial, sans-serif'),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="#e74c3c",
            borderwidth=1
        )
    
    # Mise en forme avec style professionnel
    fig.update_layout(
        title={
            'text': f'<b>{title}</b>', 
            'x': 0.5, 
            'y': 0.95,
            'font': {'size': 18, 'family': 'Arial, sans-serif', 'color': '#2c3e50'}
        },
        xaxis_title='<b>Temps (années)</b>',
        yaxis_title='<b>Probabilité de survie</b>',
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
        plot_bgcolor='rgba(248, 249, 250, 0.8)',
        paper_bgcolor='white',
        height=550,
        margin=dict(l=80, r=60, t=80, b=60),
        font=dict(family='Arial, sans-serif', color='#2c3e50')
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
        raise ImportError("lifelines n'est pas disponible")
    
    # Filtrer les données si limite spécifiée
    if max_years:
        max_days = max_years * 365.25
        processed_data_filtered = processed_data.copy()
        mask_over_max = processed_data_filtered['follow_up_days'] > max_days
        processed_data_filtered.loc[mask_over_max, 'follow_up_days'] = max_days
        processed_data_filtered.loc[mask_over_max, 'statut_deces'] = 0
        display_max = max_years
        title_suffix = f"(0-{max_years} ans)"
    else:
        processed_data_filtered = processed_data
        display_max = processed_data['follow_up_years'].max()
        title_suffix = "(toute la durée)"
    
    # Créer la figure
    fig = go.Figure()
    
    # Obtenir les années uniques et les couleurs
    years = sorted(processed_data_filtered['Year'].unique())
    colors = px.colors.qualitative.Set1[:len(years)]
    
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
                f"<b>Année {year}</b><br>" +
                f"Temps: {t:.1f} années ({t*365.25:.0f} jours)<br>" +
                f"Probabilité de survie: {p:.3f} ({p*100:.1f}%)<br>" +
                f"IC 95%: [{ci_l:.3f} - {ci_u:.3f}]<br>" +
                f"Patients: {len(year_data)}"
                for t, p, ci_l, ci_u in zip(timeline_years, survival_probs, ci_lower, ci_upper)
            ]
            
            # Ajouter la courbe principale avec style amélioré
            fig.add_trace(go.Scatter(
                x=timeline_years,
                y=survival_probs,
                mode='lines',
                name=f'Année {year}',
                line=dict(color=colors[i], width=3, dash='solid'),
                hovertemplate='%{hovertext}<extra></extra>',
                hovertext=hover_text,
                showlegend=True,
                opacity=0.9
            ))
            
            # Ajouter l'intervalle de confiance avec transparence élégante
            fig.add_trace(go.Scatter(
                x=np.concatenate([timeline_years, timeline_years[::-1]]),
                y=np.concatenate([ci_upper, ci_lower[::-1]]),
                fill='toself',
                fillcolor=colors[i].replace('rgb', 'rgba').replace(')', ', 0.15)'),
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=False,
                name=f'IC 95% - Année {year}',
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
    
    # Mise en forme du graphique avec style élégant
    fig.update_layout(
        title={
            'text': f'<b>Courbes de survie Kaplan-Meier par année {title_suffix}</b>',
            'x': 0.5,
            'y': 0.95,
            'font': {'size': 18, 'family': 'Arial, sans-serif', 'color': '#2c3e50'}
        },
        xaxis_title='<b>Temps (années)</b>',
        yaxis_title='<b>Probabilité de survie</b>',
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
        hovermode='closest',
        plot_bgcolor='rgba(248, 249, 250, 0.8)',
        paper_bgcolor='white',
        height=650,
        margin=dict(l=80, r=80, t=80, b=60),
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
        if current_page != 'Survie' or data is None:
            return html.Div()
        
        if not LIFELINES_AVAILABLE:
            return dbc.Alert([
                html.H6("Module 'lifelines' requis", className="mb-2"),
                html.P("Pour utiliser les analyses de survie, installez le module lifelines :", className="mb-1"),
                html.Code("pip install lifelines", className="d-block mb-2"),
                html.P("Redémarrez ensuite l'application.", className="mb-0")
            ], color="warning")
        
        df = pd.DataFrame(data)
        
        # Filtrer par années sélectionnées
        if selected_years and 'Year' in df.columns:
            df = df[df['Year'].isin(selected_years)]
        
        if df.empty:
            return dbc.Alert('Aucune donnée disponible avec les filtres sélectionnés', color='warning')
        
        try:
            # Préparer les données pour l'analyse de survie
            processed_data = prepare_survival_data(df)
            
            if len(processed_data) == 0:
                return dbc.Alert('Aucune donnée valide pour l\'analyse de survie', color='warning')
            
            # Déterminer la limite maximale
            max_years = 10 if max_duration == 'limited' else None
            
            # Créer la courbe de survie globale
            fig = create_interactive_single_km_curve(
                processed_data,
                max_years=max_years,
                title=f"Courbe de survie Kaplan-Meier globale (N={len(processed_data)})"
            )
            
            return dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True}
            )
        
        except Exception as e:
            return dbc.Alert(f'Erreur lors de la création de la courbe de survie: {str(e)}', color='danger')
    
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
        if current_page != 'Survie' or data is None:
            return html.Div(), html.Div()
        
        if not LIFELINES_AVAILABLE:
            warning_alert = dbc.Alert([
                html.H6("Module 'lifelines' requis", className="mb-2"),
                html.P("Pour utiliser les analyses de survie, installez le module lifelines :", className="mb-1"),
                html.Code("pip install lifelines", className="d-block mb-2"),
                html.P("Redémarrez ensuite l'application.", className="mb-0")
            ], color="warning")
            return warning_alert, warning_alert
        
        df = pd.DataFrame(data)
        
        # Filtrer par années sélectionnées
        if selected_years and 'Year' in df.columns:
            df = df[df['Year'].isin(selected_years)]
        
        if df.empty:
            empty_alert = dbc.Alert('Aucune donnée disponible avec les filtres sélectionnés', color='warning')
            return empty_alert, empty_alert
        
        try:
            # Préparer les données pour l'analyse de survie
            processed_data = prepare_survival_data(df)
            
            if len(processed_data) == 0:
                no_data_alert = dbc.Alert('Aucune donnée valide pour l\'analyse de survie', color='warning')
                return no_data_alert, no_data_alert
            
            # Vérifier qu'on a plusieurs années
            if 'Year' not in processed_data.columns :
                single_year_alert = dbc.Alert(
                    'Au moins 2 années de données sont nécessaires pour la comparaison par année', 
                    color='info'
                )
                return single_year_alert, single_year_alert
            
            # Déterminer la limite maximale
            max_years = 10 if max_duration == 'limited' else None
            
            # Créer les courbes de survie par année
            fig, stats_df = create_interactive_km_curves_by_year(
                processed_data,
                max_years=max_years
            )
            
            # Graphique
            graph_component = dcc.Graph(
                figure=fig,
                style={'height': '100%'},
                config={'responsive': True}
            )
            
            # Tableau des statistiques
            if not stats_df.empty:
                
                table_component = html.Div([
                    html.P(f"Statistiques de survie pour {len(stats_df)} années analysées", 
                           className="text-muted mb-3"),
                    dash_table.DataTable(
                        data=stats_df.to_dict('records'),
                        columns=[
                            {"name": col, "id": col, "type": "text" if col == "Année" else "text"}
                            for col in stats_df.columns
                        ],
                        style_table={'height': '350px', 'overflowY': 'auto'},
                        style_cell={
                            'textAlign': 'center',
                            'padding': '10px',
                            'fontFamily': 'Arial, sans-serif',
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
            else:
                table_component = dbc.Alert('Aucune statistique calculée', color='warning')
            
            return graph_component, table_component
        
        except Exception as e:
            error_alert = dbc.Alert(f'Erreur lors de l\'analyse de survie: {str(e)}', color='danger')
            return error_alert, error_alert
    
    @app.callback(
        Output('survival-missing-summary-table', 'children'),
        [Input('data-store', 'data'), Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def survival_missing_summary_callback(data, current_page):
        """Gère le tableau de résumé des données manquantes pour Survie"""
        
        if current_page != 'Survie' or not data:
            return html.Div("En attente...", className='text-muted')
        
        try:
            df = pd.DataFrame(data)
            
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
                return dbc.Alert("Aucune variable Survie trouvée", color='warning')
            
            # Utiliser la fonction existante de graphs.py
            missing_summary, _ = gr.analyze_missing_data(df, existing_columns, 'Long ID')
            
            return dash_table.DataTable(
                data=missing_summary.to_dict('records'),
                columns=[
                    {"name": "Variable", "id": "Colonne"},
                    {"name": "Total", "id": "Total patients", "type": "numeric"},
                    {"name": "Manquantes", "id": "Données manquantes", "type": "numeric"},
                    {"name": "% Manquant", "id": "Pourcentage manquant", "type": "numeric", 
                     "format": {"specifier": ".1f"}}
                ],
                style_table={'height': '300px', 'overflowY': 'auto'},
                style_cell={
                    'textAlign': 'center',
                    'padding': '8px',
                    'fontSize': '12px',
                    'fontFamily': 'Arial, sans-serif'
                },
                style_header={
                    'backgroundColor': '#0D3182',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'},
                    {
                        'if': {
                            'filter_query': '{Pourcentage manquant} > 20',
                            'column_id': 'Pourcentage manquant'
                        },
                        'backgroundColor': '#ffebee',
                        'color': 'red',
                        'fontWeight': 'bold'
                    }
                ]
            )
            
        except Exception as e:
            return dbc.Alert(f"Erreur lors de l'analyse: {str(e)}", color='danger')

    @app.callback(
        [Output('survival-missing-detail-table', 'children'),
         Output('export-missing-survival-button', 'disabled')],
        [Input('data-store', 'data'), Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def survival_missing_detail_callback(data, current_page):
        """Gère le tableau détaillé des patients avec données manquantes pour Survie"""
        
        if current_page != 'Survie' or not data:
            return html.Div("En attente...", className='text-muted'), True
        
        try:
            df = pd.DataFrame(data)
            
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
                return dbc.Alert("Aucune variable Survie trouvée", color='warning'), True
            
            # Utiliser la fonction existante de graphs.py
            _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
            
            if detailed_missing.empty:
                return dbc.Alert("🎉 Aucune donnée manquante trouvée !", color='success'), True
            
            # Adapter les noms de colonnes pour correspondre au format attendu
            detailed_data = []
            for _, row in detailed_missing.iterrows():
                detailed_data.append({
                    'Long ID': row['Long ID'],
                    'Colonnes manquantes': row['Colonnes avec données manquantes'],
                    'Nb manquant': row['Nombre de colonnes manquantes']
                })
            
            # Sauvegarder les données pour l'export
            app.server.missing_survival_data = detailed_data
            
            table_content = html.Div([
                dash_table.DataTable(
                    data=detailed_data,
                    columns=[
                        {"name": "Long ID", "id": "Long ID"},
                        {"name": "Variables manquantes", "id": "Colonnes manquantes"},
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
            
            return table_content, False  # Activer le bouton d'export
            
        except Exception as e:
            return dbc.Alert(f"Erreur lors de l'analyse: {str(e)}", color='danger'), True

    @app.callback(
        Output("download-missing-survival-csv", "data"),
        Input("export-missing-survival-button", "n_clicks"),
        prevent_initial_call=True
    )
    def export_missing_survival_csv(n_clicks):
        """Gère l'export CSV des patients avec données manquantes pour Survie"""
        if n_clicks is None:
            return dash.no_update
        
        try:
            # Récupérer les données stockées
            if hasattr(app.server, 'missing_survival_data') and app.server.missing_survival_data:
                missing_df = pd.DataFrame(app.server.missing_survival_data)
                
                # Générer un nom de fichier avec la date
                from datetime import datetime
                current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"survie_donnees_manquantes_{current_date}.csv"
                
                return dcc.send_data_frame(
                    missing_df.to_csv, 
                    filename=filename,
                    index=False
                )
            else:
                return dash.no_update
                
        except Exception as e:
            print(f"Erreur lors de l'export CSV Survie: {e}")
            return dash.no_update
