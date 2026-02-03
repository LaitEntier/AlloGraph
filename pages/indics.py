import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import plotly.express as px

# Import des modules communs (à adapter selon votre structure)
import modules.dashboard_layout as layouts
import modules.data_processing as data_processing
import visualizations.allogreffes.graphs as gr

def get_layout():
    """Layout SANS store trimestre avec section données manquantes"""
    return dbc.Container([
        # Stores cachés pour communication (SANS selected-quarter-store)
        dcc.Store(id='selected-indicator-store', data='gvha'),
        dcc.Store(id='selected-year-store', data=None),
        
        # Onglets principaux
        dbc.Row([
            dbc.Col([
                dcc.Tabs(id='indicators-main-tabs', value='global-view', children=[
                    dcc.Tab(label='Global View (All Years)', value='global-view'),
                    dcc.Tab(label='Quarterly View', value='quarterly-view')
                ], className='mb-3')
            ], width=12)
        ]),
        
        # Zone principale
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div(
                            id='indicator-content',
                            children=[
                                dcc.Loading(
                                    id="loading-indicator-content",
                                    type="circle",
                                    children=html.P("Select an indicator in the sidebar...")
                                )
                            ],
                            style={'min-height': '400px'}
                        )
                    ])
                ])
            ], width=12)
        ]),

        # Section données manquantes - nouvelle section dynamique
        html.Hr(style={
            'border': '2px solid #d4c4b5',
            'margin': '3rem 0 2rem 0'
        }),
        
        dbc.Row([
            # Tableau 1 - Résumé des colonnes
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Missing data analysis", className='mb-0'),
                        html.Small(id='indicators-missing-subtitle', 
                                 style={'color': '#ffffff'})
                    ]),
                    dbc.CardBody([
                        html.Div(id='indicators-missing-summary-table', children=[
                            dbc.Alert("Select an indicator to analyze missing data", color='info')
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
                                id="export-missing-indicators-button",
                                color="primary",
                                size="sm",
                                disabled=True,  # Désactivé par défaut
                            )
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody([
                        html.Div(id='indicators-missing-detail-table', children=[
                            dbc.Alert("Select an indicator to analyze missing data", color='info')
                        ]),
                        # Composant pour télécharger le fichier CSV (invisible)
                        dcc.Download(id="download-missing-indicators-excel")
                    ])
                ])
            ], width=6)
        ])
    ], fluid=True)

def create_indicators_sidebar_content(data):
    """Sidebar SANS sélecteur de trimestre pour la nouvelle interface"""
    if data is None or len(data) == 0:
        return html.Div([
            html.P('No data available', className='text-warning'),
            html.Hr(),
            html.P('Please load data to access indicators analysis.', className='text-muted')
        ])
    
    try:
        df = pd.DataFrame(data)
        
        # Options d'années disponibles
        years_options = []
        if 'Year' in df.columns:
            available_years = sorted(df['Year'].unique().tolist())
            years_options = [{'label': f'{year}', 'value': year} for year in available_years]
        
        return html.Div([
            # Titre de section
            html.H6("Analysis Parameters", className='mb-3', style={'color': '#021F59'}),
            
            # Sélection d'indicateur
            html.Label('Select Indicator:', className='mb-2 fw-bold', style={'color': '#021F59'}),
            dcc.Dropdown(
                id='indicator-selection-sidebar',
                options=[
                    {'label': 'TRM (Toxicity-Related Mortality)', 'value': 'TRM'},
                    {'label': 'Overall survival', 'value': 'survie_globale'},
                    {'label': 'Acute GVH (aGVH)', 'value': 'gvha'},
                    {'label': 'Chronic GVH (cGVH)', 'value': 'gvhc'},
                    {'label': 'Transplantation success', 'value': 'prise_greffe'},
                    {'label': 'ANC Recovery', 'value': 'sortie_aplasie'},
                    {'label': 'Relapse', 'value': 'rechute'}
                ],
                value='gvha',
                className='mb-3'
            ),
            
            html.Hr(),
            
            # Sélection d'année
            html.Label('Year for analysis:', className='mb-2 fw-bold', style={'color': '#021F59'}),
            html.Small("Year for badges (Global) or quarterly data", className='text-muted d-block mb-2'),
            dcc.Dropdown(
                id='year-selection-sidebar',
                options=years_options,
                value=available_years[-1] if available_years else None,
                className='mb-3',
                placeholder="Select a year..."
            ),
            
            html.Hr(),
            
            # Informations sur le dataset
            html.H6("Dataset Information", className='mb-2 text-primary'),
            dbc.Card([
                dbc.CardBody([
                    html.P([
                        html.Strong("Total patients: "), 
                        html.Span(f"{len(df)}")
                    ], className='mb-2'),
                    html.P([
                        html.Strong("Years range: "), 
                        html.Span(f"{df['Year'].min() if 'Year' in df.columns else 'N/A'} - {df['Year'].max() if 'Year' in df.columns else 'N/A'}")
                    ], className='mb-0')
                ], className="py-2")
            ], color="light", outline=True)
        ])
        
    except Exception as e:
        print(f"ERROR in create_indicators_sidebar_content: {str(e)}")
        return html.Div([
            dbc.Alert(f"Error creating sidebar: {str(e)}", color="danger"),
            html.P('Please check the data format and try again.')
        ])

def create_global_sidebar_content(data):
    """Version simplifiée sans IDs conflictuels"""
    if data is None or len(data) == 0:
        return html.Div([html.P('No data available', className='text-warning')])
    
    df = pd.DataFrame(data)
    
    return html.Div([
        html.H6("Global Analysis", className='mb-2'),
        html.P(f"Total patients: {len(df)}", className='mb-1'),
        html.P(f"Years covered: {df['Year'].min() if 'Year' in df.columns else 'N/A'} - {df['Year'].max() if 'Year' in df.columns else 'N/A'}", className='mb-1'),
        html.Small("Analysis covers all years in the dataset", className='text-muted')
    ])

def create_quarterly_sidebar_content(data):
    """Version simplifiée"""
    if data is None or len(data) == 0:
        return html.Div([html.P('No data available', className='text-warning')])
    
    df = pd.DataFrame(data)
    
    return html.Div([
        html.H6("Quarterly Analysis", className='mb-2'),
        html.P(f"Total patients: {len(df)}", className='mb-1'),
        html.Small("Feature under development", className='text-muted')
    ])
def create_global_visualization(df, indicator):
    """
    Crée la visualisation globale pour toutes les années confondues
    """
    try:
        if indicator == 'gvha':
            return create_gvha_global_visualization(df)
        elif indicator == 'TRM':
            return create_trm_global_visualization(df)
        elif indicator == 'survie_globale':
            return create_survie_global_visualization(df)
        elif indicator == 'prise_greffe':
            return create_prise_greffe_global_visualization(df)
        elif indicator == 'sortie_aplasie':
            return create_sortie_aplasie_global_visualization(df)
        elif indicator == 'gvhc':
            return create_gvhc_global_visualization(df)
        elif indicator == 'rechute':
            return create_rechute_global_visualization(df)
        else:
            return dbc.Alert(f"Global visualization for '{indicator}' under development", color="info")
            
    except Exception as e:
        return dbc.Alert(f"Error creating global visualization: {str(e)}", color="danger")

def create_gvha_quarterly_visualization(year_data, selected_year):
    """
    Visualisation GVH aiguë avec graphique en haut, badges alignés en dessous, tableau à gauche
    """
    try:
        # Traiter les données (même logique que précédemment)
        quarterly_stats = []
        quarterly_grade_counts = []
        
        for quarter in [1, 2, 3, 4]:
            quarter_data = year_data[year_data['Quarter'] == quarter]
            
            if not quarter_data.empty:
                total_patients = len(quarter_data)
                
                # Compter chaque grade individuellement
                grade_2_count = 0
                grade_3_count = 0
                grade_4_count = 0
                
                if 'First aGvHD Maximum Score' in quarter_data.columns:
                    grade_2_count = (quarter_data['First aGvHD Maximum Score'] == 'Grade 2').sum()
                    grade_3_count = (quarter_data['First aGvHD Maximum Score'] == 'Grade 3').sum()
                    grade_4_count = (quarter_data['First aGvHD Maximum Score'] == 'Grade 4').sum()
                
                # Calculer les totaux 2-4 et 3-4
                gvh_2_4_count = grade_2_count + grade_3_count + grade_4_count
                gvh_3_4_count = grade_3_count + grade_4_count
                
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': total_patients,
                    'Grade_2': grade_2_count,
                    'Grade_3': grade_3_count,
                    'Grade_4': grade_4_count,
                    'GVH_2_4': gvh_2_4_count,
                    'GVH_3_4': gvh_3_4_count,
                    'Pct_GVH_2_4': (gvh_2_4_count / total_patients * 100) if total_patients > 0 else 0,
                    'Pct_GVH_3_4': (gvh_3_4_count / total_patients * 100) if total_patients > 0 else 0
                })
                
                quarterly_grade_counts.append({
                    'Quarter': f'Q{quarter}',
                    'Grade 2': grade_2_count,
                    'Grade 3': grade_3_count,
                    'Grade 4': grade_4_count
                })
            else:
                # Données vides pour ce trimestre
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': 0,
                    'Grade_2': 0,
                    'Grade_3': 0,
                    'Grade_4': 0,
                    'GVH_2_4': 0,
                    'GVH_3_4': 0,
                    'Pct_GVH_2_4': 0,
                    'Pct_GVH_3_4': 0
                })
                
                quarterly_grade_counts.append({
                    'Quarter': f'Q{quarter}',
                    'Grade 2': 0,
                    'Grade 3': 0,
                    'Grade 4': 0
                })
        
        quarterly_df = pd.DataFrame(quarterly_stats)
        quarterly_grades_df = pd.DataFrame(quarterly_grade_counts)
        
        # Créer le graphique empilé
        fig = create_quarterly_stacked_barplot(quarterly_grades_df, selected_year)
        
        # NOUVEAU LAYOUT: 
        # - Ligne 1: Graphique pleine largeur + Tableau compact à droite
        # - Ligne 2: Badges alignés avec les barres du graphique
        
        return html.Div([
            # Ligne 1: Graphique pleine largeur
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        figure=fig,
                        style={'height': '450px'},
                        config={'responsive': True}
                    )
                ], width=12)
            ], className='mb-3'),
            
            # Ligne 2: Badges pleine largeur (4 colonnes égales)
            dbc.Row([
                dbc.Col([
                    create_quarter_badges_column(quarterly_df, 1, selected_year)
                ], width=3),
                dbc.Col([
                    create_quarter_badges_column(quarterly_df, 2, selected_year)
                ], width=3),
                dbc.Col([
                    create_quarter_badges_column(quarterly_df, 3, selected_year)
                ], width=3),
                dbc.Col([
                    create_quarter_badges_column(quarterly_df, 4, selected_year)
                ], width=3)
            ], className='mb-3'),
            
            # Ligne 3: Tableau pleine largeur
            dbc.Row([
                dbc.Col([
                    html.H6("Quarterly Statistics", className='mb-3 text-center'),
                    create_wide_quarterly_table(quarterly_df)
                ], width=12)
            ])
        ])
        
    except Exception as e:
        print(f"ERROR in create_gvha_quarterly_new_layout: {str(e)}")
        return dbc.Alert(f"Error in new quarterly GVH layout: {str(e)}", color="danger")
    
def create_gvha_global_visualization(df):
    """
    Exemple d'adaptation de la visualisation GVH aiguë pour toutes les années
    """
    # Adapté de votre fonction existante create_gvha_visualization
    # mais sans limitation à une année spécifique
    
    try:
        # Traiter les données pour toutes les années
        result_combined, grade_counts = process_gvha_data(df)  # Votre fonction existante
        
        # Calculer les indicateurs globaux
        total_patients = result_combined['nb_greffe'].sum()
        total_gvh_2_4 = result_combined['nb_gvh_aigue_2_4'].sum()
        total_gvh_3_4 = result_combined['nb_gvh_aigue_3_4'].sum()
        
        pct_global_2_4 = (total_gvh_2_4 / total_patients * 100) if total_patients > 0 else 0
        pct_global_3_4 = (total_gvh_3_4 / total_patients * 100) if total_patients > 0 else 0
        
        return dbc.Row([
            # Colonne gauche : Graphique global (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_gvha_barplot(result_combined, grade_counts),  # Votre fonction existante
                    style={'height': '600px'},
                    config={'responsive': True}
                )
            ], width=7),
            # Colonne droite : DataTable et badges globaux (40%)
            dbc.Col([
                # DataTable pour toutes les années
                create_gvha_datatable(result_combined),  # Votre fonction existante
                html.Hr(className='my-3'),
                # Badges globaux
                html.Div([
                    html.H6("Global Acute GVH Indicators", className='text-center mb-3'),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H3(f"{pct_global_2_4:.1f}%", className="text-center mb-2", style={'color': '#2c3e50'}),
                                    html.P("Acute GVH grades 2-4", className="text-center mb-1", style={'fontSize': '14px'}),
                                    html.P(f"({total_gvh_2_4}/{total_patients})", className="text-center text-muted", style={'fontSize': '12px'})
                                ], className="py-3")
                            ], color="primary", outline=True, style={'border-width': '2px'})
                        ], width=12, className="mb-2"),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H3(f"{pct_global_3_4:.1f}%", className="text-center mb-2", style={'color': '#c0392b'}),
                                    html.P("Acute GVH grades 3-4", className="text-center mb-1", style={'fontSize': '14px'}),
                                    html.P(f"({total_gvh_3_4}/{total_patients})", className="text-center text-muted", style={'fontSize': '12px'})
                                ], className="py-3")
                            ], color="danger", outline=True, style={'border-width': '2px'})
                        ], width=12)
                    ])
                ])
            ], width=5)
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error in global GVH visualization: {str(e)}", color="danger")

def create_gvha_quarterly_visualization(year_data, selected_year):
    """
    Visualisation GVH aiguë avec graphique en haut, badges alignés en dessous, tableau à gauche
    """
    try:
        # Traiter les données (même logique que précédemment)
        quarterly_stats = []
        quarterly_grade_counts = []
        
        for quarter in [1, 2, 3, 4]:
            quarter_data = year_data[year_data['Quarter'] == quarter]
            
            if not quarter_data.empty:
                total_patients = len(quarter_data)
                
                # Compter chaque grade individuellement
                grade_2_count = 0
                grade_3_count = 0
                grade_4_count = 0
                
                if 'First aGvHD Maximum Score' in quarter_data.columns:
                    grade_2_count = (quarter_data['First aGvHD Maximum Score'] == 'Grade 2').sum()
                    grade_3_count = (quarter_data['First aGvHD Maximum Score'] == 'Grade 3').sum()
                    grade_4_count = (quarter_data['First aGvHD Maximum Score'] == 'Grade 4').sum()
                
                # Calculer les totaux 2-4 et 3-4
                gvh_2_4_count = grade_2_count + grade_3_count + grade_4_count
                gvh_3_4_count = grade_3_count + grade_4_count
                
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': total_patients,
                    'Grade_2': grade_2_count,
                    'Grade_3': grade_3_count,
                    'Grade_4': grade_4_count,
                    'GVH_2_4': gvh_2_4_count,
                    'GVH_3_4': gvh_3_4_count,
                    'Pct_GVH_2_4': (gvh_2_4_count / total_patients * 100) if total_patients > 0 else 0,
                    'Pct_GVH_3_4': (gvh_3_4_count / total_patients * 100) if total_patients > 0 else 0
                })
                
                quarterly_grade_counts.append({
                    'Quarter': f'Q{quarter}',
                    'Grade 2': grade_2_count,
                    'Grade 3': grade_3_count,
                    'Grade 4': grade_4_count
                })
            else:
                # Données vides pour ce trimestre
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': 0,
                    'Grade_2': 0,
                    'Grade_3': 0,
                    'Grade_4': 0,
                    'GVH_2_4': 0,
                    'GVH_3_4': 0,
                    'Pct_GVH_2_4': 0,
                    'Pct_GVH_3_4': 0
                })
                
                quarterly_grade_counts.append({
                    'Quarter': f'Q{quarter}',
                    'Grade 2': 0,
                    'Grade 3': 0,
                    'Grade 4': 0
                })
        
        quarterly_df = pd.DataFrame(quarterly_stats)
        quarterly_grades_df = pd.DataFrame(quarterly_grade_counts)
        
        # Créer le graphique empilé
        fig = create_quarterly_stacked_barplot(quarterly_grades_df, selected_year)
        
        # NOUVEAU LAYOUT: 
        # - Ligne 1: Graphique pleine largeur + Tableau compact à droite
        # - Ligne 2: Badges alignés avec les barres du graphique
        
        return html.Div([
            # Ligne 1: Graphique pleine largeur
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        figure=fig,
                        style={'height': '450px'},
                        config={'responsive': True}
                    )
                ], width=12)
            ], className='mb-3'),
            
            # Ligne 2: Badges pleine largeur (4 colonnes égales)
            dbc.Row([
                dbc.Col([
                    create_quarter_badges_column(quarterly_df, 1, selected_year)
                ], width=3),
                dbc.Col([
                    create_quarter_badges_column(quarterly_df, 2, selected_year)
                ], width=3),
                dbc.Col([
                    create_quarter_badges_column(quarterly_df, 3, selected_year)
                ], width=3),
                dbc.Col([
                    create_quarter_badges_column(quarterly_df, 4, selected_year)
                ], width=3)
            ], className='mb-3'),
            
            # Ligne 3: Tableau pleine largeur
            dbc.Row([
                dbc.Col([
                    html.H6("Quarterly Statistics", className='mb-3 text-center'),
                    create_wide_quarterly_table(quarterly_df)
                ], width=12)
            ])
        ])
        
    except Exception as e:
        print(f"ERROR in create_gvha_quarterly_new_layout: {str(e)}")
        return dbc.Alert(f"Error in new quarterly GVH layout: {str(e)}", color="danger")

# =============================================================================
# TRM (Toxicity-Related Mortality) - Global et Quarterly
# =============================================================================

def create_trm_global_visualization(df, analysis_year):
    """
    Visualisation globale pour TRM (toutes années confondues) avec badges pour année spécifique
    """
    try:
        # Traiter les données pour toutes les années (nouveau format tuple)
        result_long, result_df = process_trm_data(df)
        
        # Calculer les indicateurs globaux en utilisant TRM à 365 jours
        total_patients = result_df['nb_greffe'].sum()
        total_trm_365 = result_df['trm_j365'].sum()
        pct_global_trm = (total_trm_365 / total_patients * 100) if total_patients > 0 else 0
        
        return dbc.Row([
            # Colonne gauche : Graphique global (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_trm_curves_plot(result_long),
                    style={'height': '600px'},
                    config={'responsive': True}
                )
            ], width=7),
            # Colonne droite : DataTable et badge pour année spécifique (40%)
            dbc.Col([
                # DataTable pour toutes les années
                create_trm_datatable(result_df),
                html.Hr(className='my-3'),
                # Badge pour l'année spécifique
                create_trm_badges(result_df, analysis_year)
            ], width=5)
        ])
        
    except Exception as e:
        print(f"ERROR in create_trm_global_visualization: {str(e)}")
        return dbc.Alert(f"Error in global TRM visualization: {str(e)}", color="danger")

def create_trm_quarterly_visualization(year_data, selected_year):
    """
    Visualisation trimestrielle TRM avec courbes par trimestre et 3 badges par trimestre
    """
    try:
        # Calculer Follow_up_days si nécessaire pour les données trimestrielles
        if 'Follow_up_days' not in year_data.columns:
            year_data = year_data.copy()
            year_data['Treatment Date'] = pd.to_datetime(year_data['Treatment Date'])
            year_data['Date Of Last Follow Up'] = pd.to_datetime(year_data['Date Of Last Follow Up'])
            year_data['Follow_up_days'] = (year_data['Date Of Last Follow Up'] - year_data['Treatment Date']).dt.days
        
        quarterly_stats = []
        quarterly_long = []
        
        for quarter in [1, 2, 3, 4]:
            quarter_data = year_data[year_data['Quarter'] == quarter]
            
            if not quarter_data.empty:
                total_patients = len(quarter_data)
                
                # Appliquer la nouvelle logique TRM
                # Filtrer les causes de décès spécifiques (TRM)
                trm_data = quarter_data[quarter_data['Death Cause'].isin([
                    'Cellular therapy-related cause of death', 
                    'HCT-related cause of death'
                ])]
                
                # Appliquer les filtres pour le statut de décès et le suivi
                trm_filtered = trm_data[
                    (trm_data['Status Last Follow Up'] == 'Dead') | 
                    ((trm_data['Status Last Follow Up'] == 'Alive') & (trm_data['Follow_up_days'] >= 365))
                ]
                
                # Calculer TRM à différents points temporels
                trm_j30 = len(trm_filtered[
                    (trm_filtered['Status Last Follow Up'] == 'Dead') & 
                    (trm_filtered['Follow_up_days'] <= 30)
                ])
                
                trm_j100 = len(trm_filtered[
                    (trm_filtered['Status Last Follow Up'] == 'Dead') & 
                    (trm_filtered['Follow_up_days'] <= 100)
                ])
                
                trm_j365 = len(trm_filtered[
                    (trm_filtered['Status Last Follow Up'] == 'Dead') & 
                    (trm_filtered['Follow_up_days'] <= 365)
                ])
                
                # Calculer les pourcentages
                trm_pct_30 = (trm_j30 / total_patients * 100) if total_patients > 0 else 0
                trm_pct_100 = (trm_j100 / total_patients * 100) if total_patients > 0 else 0
                trm_pct_365 = (trm_j365 / total_patients * 100) if total_patients > 0 else 0
                
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': total_patients,
                    'TRM_D30': trm_j30,
                    'TRM_D100': trm_j100,
                    'TRM_D365': trm_j365,
                    'TRM_D30_%': trm_pct_30,
                    'TRM_D100_%': trm_pct_100,
                    'TRM_D365_%': trm_pct_365
                })
                
                # Créer les données pour les courbes (format long)
                for day, pct in [(0, 0.0), (30, trm_pct_30), (100, trm_pct_100), (365, trm_pct_365)]:
                    quarterly_long.append({
                        'Quarter': f'Q{quarter}',
                        'Quarter_Num': quarter,
                        'Day': day,
                        'TRM_Percentage': pct
                    })
                
            else:
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': 0,
                    'TRM_D30': 0,
                    'TRM_D100': 0,
                    'TRM_D365': 0,
                    'TRM_D30_%': 0,
                    'TRM_D100_%': 0,
                    'TRM_D365_%': 0
                })
                
                # Données vides pour les courbes
                for day in [0, 30, 100, 365]:
                    quarterly_long.append({
                        'Quarter': f'Q{quarter}',
                        'Quarter_Num': quarter,
                        'Day': day,
                        'TRM_Percentage': 0
                    })
        
        quarterly_df = pd.DataFrame(quarterly_stats)
        quarterly_long_df = pd.DataFrame(quarterly_long)
        
        # Graphique TRM courbes trimestrielles
        fig = go.Figure()
        
        quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        colors = ['#e74c3c', '#c0392b', '#a93226', '#922b21']  # Nuances de rouge
        
        for i, quarter in enumerate(quarters):
            quarter_data = quarterly_long_df[quarterly_long_df['Quarter'] == quarter]
            
            fig.add_trace(go.Scatter(
                x=quarter_data['Day'],
                y=quarter_data['TRM_Percentage'],
                mode='lines+markers',
                name=quarter,
                line=dict(width=3, color=colors[i]),
                marker=dict(size=8),
                connectgaps=True
            ))
        
        fig.update_layout(
            title=f'TRM Curves by Quarter - {selected_year}',
            xaxis_title='Days after transplantation',
            yaxis_title='TRM Percentage (%)',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(
                tickvals=[0, 30, 100, 365], 
                ticktext=['D0', 'D30', 'D100', 'D365'],
                range=[-10, 375]
            ),
            yaxis=dict(range=[0, None]),
            template='plotly_white'
        )
        
        return html.Div([
            # Ligne 1: Graphique pleine largeur
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig, style={'height': '450px'}, config={'responsive': True})
                ], width=12)
            ], className='mb-3'),
            
            # Ligne 2: 3 badges TRM par trimestre (4 trimestres × 3 badges = 12 badges)
            html.H6("TRM Indicators by Quarter", className='text-center mb-3'),
            dbc.Row([
                dbc.Col([
                    create_trm_quarter_badges_column(quarterly_df, q)
                ], width=3) for q in [1, 2, 3, 4]
            ], className='mb-3'),
            
            # Ligne 3: Tableau pleine largeur
            dbc.Row([
                dbc.Col([
                    html.H6("Quarterly TRM Statistics", className='mb-3 text-center'),
                    create_wide_trm_table(quarterly_df)
                ], width=12)
            ])
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error in TRM quarterly layout: {str(e)}", color="danger")

def process_trm_data(df):
    """
    Traite les données pour calculer les indicateurs TRM
    
    Args:
        df (pd.DataFrame): DataFrame avec les données
        
    Returns:
        tuple: (result_long, result_df) - Format long pour graphiques et DataFrame complet
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

def create_trm_curves_plot(result_long):
    """
    Graphique des courbes TRM par année avec points à J0, J30, J100, J365
    """
    try:
        fig = go.Figure()
        
        # Obtenir les années uniques
        years = sorted(result_long['Year'].unique())
        colors = px.colors.qualitative.Set1[:len(years)]
        
        for i, year in enumerate(years):
            year_data = result_long[result_long['Year'] == year].sort_values('j')
            
            fig.add_trace(go.Scatter(
                x=year_data['j'],
                y=year_data['pourcentage_deces'],
                mode='lines+markers',
                name=f'{int(year)}',
                line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=8),
                connectgaps=True
            ))
        
        fig.update_layout(
            title='TRM Curves by Year',
            xaxis_title='Days after transplantation',
            yaxis_title='TRM Percentage (%)',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            xaxis=dict(
                tickvals=[0, 30, 100, 365], 
                ticktext=['J0', 'J30', 'J100', 'J365'],
                range=[-10, 375]  # Ajouter un peu d'espace
            ),
            yaxis=dict(range=[0, None]),  # Commencer à 0%
            template='plotly_white'
        )
        
        return fig
    except Exception as e:
        print(f"ERROR in create_trm_curves_plot: {str(e)}")
        return go.Figure()  # Retourner une figure vide en cas d'erreur

def create_trm_datatable(result_df):
    """DataTable pour TRM - adapté au nouveau format avec pourcentages"""
    try:
        table_data = []
        for _, row in result_df.iterrows():
            table_data.append({
                'Year': int(row['Year']),
                'Transplants': int(row['nb_greffe']),
                'TRM_D30': int(row['trm_j30']),
                'TRM_D30_%': f"{row['30']:.1f}%",
                'TRM_D100': int(row['trm_j100']),
                'TRM_D100_%': f"{row['100']:.1f}%",
                'TRM_D365': int(row['trm_j365']),
                'TRM_D365_%': f"{row['365']:.1f}%"
            })
        
        return html.Div([
            html.H6("TRM Statistics by year", className='mb-2'),
            dash_table.DataTable(
                data=table_data,
                columns=[
                    {"name": "Year", "id": "Year"},
                    {"name": "Transplants", "id": "Transplants"},
                    {"name": "TRM D30", "id": "TRM_D30"},
                    {"name": "TRM D30 (%)", "id": "TRM_D30_%"},
                    {"name": "TRM D100", "id": "TRM_D100"},
                    {"name": "TRM D100 (%)", "id": "TRM_D100_%"},
                    {"name": "TRM D365", "id": "TRM_D365"},
                    {"name": "TRM D365 (%)", "id": "TRM_D365_%"}
                ],
                style_cell={'textAlign': 'center', 'fontSize': '11px', 'padding': '6px', 'color': '#021F59'},
                style_header={'backgroundColor': '#021F59', 'color': 'white', 'fontWeight': 'bold', 'fontSize': '10px'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
                    {'if': {'column_id': ['TRM_D30_%', 'TRM_D100_%', 'TRM_D365_%']}, 'backgroundColor': '#F2A594', 'fontWeight': 'bold'}
                ]
            )
        ])
    except Exception as e:
        print(f"ERROR in create_trm_datatable: {str(e)}")
        return html.Div([dbc.Alert(f"Error creating TRM table: {str(e)}", color="danger")])

def create_trm_badges(result_df, analysis_year):
    """Badges TRM pour année spécifique - 3 badges séparés (D30, D100, D365)"""
    try:
        analysis_year = int(analysis_year)
        result_df = result_df.copy()
        result_df['Year'] = result_df['Year'].astype(int)
        
        year_data = result_df[result_df['Year'] == analysis_year]
        
        if year_data.empty:
            available_years = sorted(result_df['Year'].unique())
            if available_years:
                fallback_year = available_years[-1]
                year_data = result_df[result_df['Year'] == fallback_year]
                if not year_data.empty:
                    return create_trm_badges_content(year_data, fallback_year, f"Using latest available year")
            
            return dbc.Alert(f"No data available for year {analysis_year}", color="warning")
        
        return create_trm_badges_content(year_data, analysis_year)
        
    except Exception as e:
        return dbc.Alert(f"Error creating TRM badges: {str(e)}", color="danger")

def create_trm_badges_content(year_data, analysis_year, subtitle=None):
    """Contenu des 3 badges TRM - D30, D100, D365"""
    try:
        # Extraire les données pour l'année
        row = year_data.iloc[0]
        
        # Données pour chaque point temporel
        badges_data = [
            {
                'period': 'D30',
                'percentage': row['30'],
                'count': int(row['trm_j30']),
                'color': '#f39c12'  # Orange
            },
            {
                'period': 'D100', 
                'percentage': row['100'],
                'count': int(row['trm_j100']),
                'color': '#e67e22'  # Orange foncé
            },
            {
                'period': 'D365',
                'percentage': row['365'], 
                'count': int(row['trm_j365']),
                'color': '#e74c3c'  # Rouge
            }
        ]
        
        total_greffes = int(row['nb_greffe'])
        
        title = f"Toxicity-Related Mortality - {analysis_year}"
        if subtitle:
            title += f" ({subtitle})"
        
        # Créer les 3 badges
        badges = []
        for badge_data in badges_data:
            badge = dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{badge_data['percentage']:.1f}%", 
                                className="text-center mb-1", 
                                style={'color': badge_data['color'], 'fontSize': '20px'}),
                        html.P(f"TRM {badge_data['period']}", 
                               className="text-center mb-1", 
                               style={'fontSize': '12px', 'fontWeight': 'bold'}),
                        html.P(f"({badge_data['count']}/{total_greffes})", 
                               className="text-center text-muted", 
                               style={'fontSize': '10px'})
                    ], className="py-2")
                ], color="danger", outline=True, style={'border-width': '1px'})
            ], width=4)
            badges.append(badge)
        
        return html.Div([
            html.H6(title, className='text-center mb-3'),
            dbc.Row(badges, className='g-2')  # g-2 pour un petit espacement entre les badges
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error creating TRM badge content: {str(e)}", color="danger")

def create_compact_trm_table(quarterly_df):
    """Table compacte pour TRM"""
    return dash_table.DataTable(
        data=quarterly_df.to_dict('records'),
        columns=[
            {"name": "Q", "id": "Quarter"},
            {"name": "Pat.", "id": "Total_Patients"},
            {"name": "TRM", "id": "TRM_Count"},
            {"name": "TRM%", "id": "TRM_Percentage", "type": "numeric", "format": {"specifier": ".1f"}}
        ],
        style_cell={'textAlign': 'center', 'fontSize': '9px', 'padding': '3px', 'color': '#021F59'},
        style_header={'backgroundColor': '#021F59', 'color': 'white', 'fontWeight': 'bold', 'fontSize': '8px'}
    )

def create_wide_trm_table(quarterly_df):
    """Table TRM pleine largeur avec tous les détails"""
    return dash_table.DataTable(
        data=quarterly_df.to_dict('records'),
        columns=[
            {"name": "Quarter", "id": "Quarter"},
            {"name": "Total Patients", "id": "Total_Patients"},
            {"name": "TRM D30", "id": "TRM_D30"},
            {"name": "TRM D30 (%)", "id": "TRM_D30_%", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "TRM D100", "id": "TRM_D100"},
            {"name": "TRM D100 (%)", "id": "TRM_D100_%", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "TRM D365", "id": "TRM_D365"},
            {"name": "TRM D365 (%)", "id": "TRM_D365_%", "type": "numeric", "format": {"specifier": ".1f"}}
        ],
        style_cell={
            'textAlign': 'center', 
            'fontSize': '11px', 
            'padding': '8px',
            'minWidth': '100px',
            'color': '#021F59'
        },
        style_header={
            'backgroundColor': '#021F59', 
            'color': 'white', 
            'fontWeight': 'bold',
            'fontSize': '10px',
            'padding': '8px'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
            {'if': {'column_id': ['TRM_D30_%']}, 'backgroundColor': '#fdeaa7', 'fontWeight': 'bold'},
            {'if': {'column_id': ['TRM_D100_%']}, 'backgroundColor': '#fadbd8', 'fontWeight': 'bold'},
            {'if': {'column_id': ['TRM_D365_%']}, 'backgroundColor': '#F2A594', 'fontWeight': 'bold'}
        ]
    )

def create_trm_quarter_badge(quarterly_df, quarter_num, selected_year):
    """Badge unique TRM pour un trimestre - adapté au nouveau format"""
    quarter_data = quarterly_df[quarterly_df['Quarter_Num'] == quarter_num]
    
    if quarter_data.empty:
        return html.Div([
            html.H6(f"Q{quarter_num}", className='text-center mb-2'),
            dbc.Alert("No data", color="light")
        ])
    
    quarter_info = quarter_data.iloc[0]
    trm_pct = quarter_info['TRM_Percentage']
    trm_count = quarter_info['TRM_J365']  # Utilise TRM à J365
    total_patients = quarter_info['Total_Patients']
    
    return html.Div([
        html.H6(f"Q{quarter_num}", className='text-center mb-2', style={'color': '#021F59', 'fontWeight': 'bold'}),
        dbc.Card([
            dbc.CardBody([
                html.H4(f"{trm_pct:.1f}%", className="text-center mb-1", style={'color': '#e74c3c'}),
                html.P("TRM (1Y)", className="text-center mb-1", style={'fontSize': '12px', 'fontWeight': 'bold'}),
                html.P(f"({int(trm_count)}/{int(total_patients)})", className="text-center text-muted", style={'fontSize': '10px'})
            ], className="py-3")
        ], color="danger", outline=True, style={'border-width': '1px'})
    ])

def create_trm_quarter_badges_column(quarterly_df, quarter_num):
    """Colonne avec 3 badges TRM pour un trimestre (D30, D100, D365)"""
    quarter_data = quarterly_df[quarterly_df['Quarter_Num'] == quarter_num]
    
    if quarter_data.empty:
        return html.Div([
            html.H6(f"Q{quarter_num}", className='text-center mb-2', style={'color': '#021F59', 'fontWeight': 'bold'}),
            dbc.Alert("No data", color="light")
        ])
    
    quarter_info = quarter_data.iloc[0]
    total_patients = quarter_info['Total_Patients']
    
    # Données pour les 3 badges
    badges_data = [
        {
            'period': 'D30',
            'percentage': quarter_info['TRM_D30_%'],
            'count': quarter_info['TRM_D30'],
            'color': '#f39c12'  # Orange
        },
        {
            'period': 'D100',
            'percentage': quarter_info['TRM_D100_%'],
            'count': quarter_info['TRM_D100'],
            'color': '#e67e22'  # Orange foncé
        },
        {
            'period': 'D365',
            'percentage': quarter_info['TRM_D365_%'],
            'count': quarter_info['TRM_D365'],
            'color': '#e74c3c'  # Rouge
        }
    ]
    
    badges = []
    for badge_data in badges_data:
        badge = dbc.Card([
            dbc.CardBody([
                html.H5(f"{badge_data['percentage']:.1f}%", 
                        className="text-center mb-1", 
                        style={'color': badge_data['color'], 'fontSize': '14px'}),
                html.P(f"TRM {badge_data['period']}", 
                       className="text-center mb-1", 
                       style={'fontSize': '10px', 'fontWeight': 'bold'}),
                html.P(f"({int(badge_data['count'])}/{int(total_patients)})", 
                       className="text-center text-muted", 
                       style={'fontSize': '8px'})
            ], className="py-1")
        ], color="danger", outline=True, style={'border-width': '1px'}, className='mb-1')
        badges.append(badge)
    
    return html.Div([
        html.H6(f"Q{quarter_num}", className='text-center mb-2', style={'color': '#021F59', 'fontWeight': 'bold'}),
        html.Div(badges)
    ])

# =============================================================================
# Survie Globale - Global et Quarterly
# =============================================================================

def create_survie_global_visualization(df, analysis_year):
    """
    Visualisation globale pour la survie globale avec badges pour année spécifique
    """
    try:
        result_long, result_df = process_survie_data(df)
        
        # Calculer les indicateurs globaux
        total_patients = result_df['nb_greffe'].sum()
        total_vivants_365 = result_df['vivants_j365'].sum()
        pct_global_1an = (total_vivants_365 / total_patients * 100) if total_patients > 0 else 0
        
        return dbc.Row([
            # Colonne gauche : Graphique des courbes de survie
            dbc.Col([
                dcc.Graph(
                    figure=create_survie_curves_plot(result_long),
                    style={'height': '600px'},
                    config={'responsive': True}
                )
            ], width=7),
            # Colonne droite : DataTable et badges pour année spécifique
            dbc.Col([
                create_survie_datatable(result_df),
                html.Hr(className='my-3'),
                create_survie_badges(result_df, analysis_year)
            ], width=5)
        ])
        
    except Exception as e:
        print(f"ERROR in create_survie_global_visualization: {str(e)}")
        return dbc.Alert(f"Error in overall survival visualization: {str(e)}", color="danger")

def create_survie_quarterly_visualization(year_data, selected_year):
    """
    Visualisation trimestrielle survie avec courbes par trimestre et 3 badges par trimestre
    """
    try:
        # Calculer Follow_up_days si nécessaire pour les données trimestrielles
        if 'Follow_up_days' not in year_data.columns:
            year_data = year_data.copy()
            year_data['Treatment Date'] = pd.to_datetime(year_data['Treatment Date'])
            year_data['Date Of Last Follow Up'] = pd.to_datetime(year_data['Date Of Last Follow Up'])
            year_data['Follow_up_days'] = (year_data['Date Of Last Follow Up'] - year_data['Treatment Date']).dt.days
        
        quarterly_stats = []
        quarterly_long = []
        
        for quarter in [1, 2, 3, 4]:
            quarter_data = year_data[year_data['Quarter'] == quarter]
            
            if not quarter_data.empty:
                total_patients = len(quarter_data)
                
                # Appliquer la nouvelle logique survie
                # Appliquer les filtres pour le statut de décès et le suivi
                filtered_data = quarter_data[
                    (quarter_data['Status Last Follow Up'].isin(['Dead', 'Died after conditioning but before main treatment'])) |
                    ((quarter_data['Status Last Follow Up'] == 'Alive') & (quarter_data['Follow_up_days'] >= 365))
                ]
                
                # Calculer les décès à différents points temporels
                deces_j30 = len(filtered_data[
                    (filtered_data['Status Last Follow Up'].isin(['Dead', 'Died after conditioning but before main treatment'])) & 
                    (filtered_data['Follow_up_days'] <= 30)
                ])
                
                deces_j100 = len(filtered_data[
                    (filtered_data['Status Last Follow Up'].isin(['Dead', 'Died after conditioning but before main treatment'])) & 
                    (filtered_data['Follow_up_days'] <= 100)
                ])
                
                deces_j365 = len(filtered_data[
                    (filtered_data['Status Last Follow Up'].isin(['Dead', 'Died after conditioning but before main treatment'])) & 
                    (filtered_data['Follow_up_days'] <= 365)
                ])
                
                # Calculer les survivants et pourcentages
                vivants_j30 = total_patients - deces_j30
                vivants_j100 = total_patients - deces_j100
                vivants_j365 = total_patients - deces_j365
                
                survie_pct_30 = (vivants_j30 / total_patients * 100) if total_patients > 0 else 0
                survie_pct_100 = (vivants_j100 / total_patients * 100) if total_patients > 0 else 0
                survie_pct_365 = (vivants_j365 / total_patients * 100) if total_patients > 0 else 0
                
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': total_patients,
                    'Deaths_D30': deces_j30,
                    'Deaths_D100': deces_j100,
                    'Deaths_D365': deces_j365,
                    'Alive_D30': vivants_j30,
                    'Alive_D100': vivants_j100,
                    'Alive_D365': vivants_j365,
                    'Survival_D30_%': survie_pct_30,
                    'Survival_D100_%': survie_pct_100,
                    'Survival_D365_%': survie_pct_365
                })
                
                # Créer les données pour les courbes (format long)
                for day, pct in [(0, 100.0), (30, survie_pct_30), (100, survie_pct_100), (365, survie_pct_365)]:
                    quarterly_long.append({
                        'Quarter': f'Q{quarter}',
                        'Quarter_Num': quarter,
                        'Day': day,
                        'Survival_Percentage': pct
                    })
                
            else:
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': 0,
                    'Deaths_D30': 0,
                    'Deaths_D100': 0,
                    'Deaths_D365': 0,
                    'Alive_D30': 0,
                    'Alive_D100': 0,
                    'Alive_D365': 0,
                    'Survival_D30_%': 0,
                    'Survival_D100_%': 0,
                    'Survival_D365_%': 0
                })
                
                # Données vides pour les courbes
                for day, pct in [(0, 100.0), (30, 0), (100, 0), (365, 0)]:
                    quarterly_long.append({
                        'Quarter': f'Q{quarter}',
                        'Quarter_Num': quarter,
                        'Day': day,
                        'Survival_Percentage': pct
                    })
        
        quarterly_df = pd.DataFrame(quarterly_stats)
        quarterly_long_df = pd.DataFrame(quarterly_long)
        
        # Graphique survie courbes trimestrielles
        fig = go.Figure()
        
        quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        colors = ['#27ae60', '#2ecc71', '#58d68d', '#82e0aa']  # Nuances de vert
        
        for i, quarter in enumerate(quarters):
            quarter_data = quarterly_long_df[quarterly_long_df['Quarter'] == quarter]
            
            fig.add_trace(go.Scatter(
                x=quarter_data['Day'],
                y=quarter_data['Survival_Percentage'],
                mode='lines+markers',
                name=quarter,
                line=dict(width=3, color=colors[i]),
                marker=dict(size=8),
                connectgaps=True
            ))
        
        fig.update_layout(
            title=f'Overall Survival Curves by Quarter - {selected_year}',
            xaxis_title='Days after transplantation',
            yaxis_title='Overall Survival (%)',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(
                tickvals=[0, 30, 100, 365], 
                ticktext=['D0', 'D30', 'D100', 'D365'],
                range=[-10, 375]
            ),
            yaxis=dict(range=[0, 105]),  # 0-105% pour la survie
            template='plotly_white'
        )
        
        return html.Div([
            # Ligne 1: Graphique pleine largeur
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig, style={'height': '450px'}, config={'responsive': True})
                ], width=12)
            ], className='mb-3'),
            
            # Ligne 2: 3 badges survie par trimestre (4 trimestres × 3 badges = 12 badges)
            html.H6("Overall Survival Indicators by Quarter", className='text-center mb-3'),
            dbc.Row([
                dbc.Col([
                    create_survie_quarter_badges_column(quarterly_df, q)
                ], width=3) for q in [1, 2, 3, 4]
            ], className='mb-3'),
            
            # Ligne 3: Tableau pleine largeur
            dbc.Row([
                dbc.Col([
                    html.H6("Quarterly Overall Survival Statistics", className='mb-3 text-center'),
                    create_wide_survie_table(quarterly_df)
                ], width=12)
            ])
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error in survival quarterly layout: {str(e)}", color="danger")

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
    if filtered_df.empty:
        # Si filtered_df est vide, créer death_summary avec des zéros
        death_summary = nb_greffe_year[['Year']].copy()
        death_summary['deces_j30'] = 0
        death_summary['deces_j100'] = 0  
        death_summary['deces_j365'] = 0
    else:
        death_summary = filtered_df.groupby('Year').agg({
            'deces_j30': 'sum',
            'deces_j100': 'sum',
            'deces_j365': 'sum'
        }).reset_index()

    # Fusion avec le nombre total de greffes
    result_df = pd.merge(nb_greffe_year, death_summary, on='Year', how='left')
    
    # Remplacer les NaN par 0
    result_df = result_df.fillna(0)
    
    # Calcul des survivants et pourcentages
    result_df['vivants_j30'] = result_df['nb_greffe'] - result_df['deces_j30']
    result_df['vivants_j100'] = result_df['nb_greffe'] - result_df['deces_j100']
    result_df['vivants_j365'] = result_df['nb_greffe'] - result_df['deces_j365']
    
    result_df['30'] = round(result_df['vivants_j30'] / result_df['nb_greffe'] * 100, 1)
    result_df['100'] = round(result_df['vivants_j100'] / result_df['nb_greffe'] * 100, 1)
    result_df['365'] = round(result_df['vivants_j365'] / result_df['nb_greffe'] * 100, 1)
    result_df['0'] = 100.0  # Ajout de D0 à 100%
    
    # Format long
    result_long = result_df[['Year', '0', '30', '100', '365']].melt(
        id_vars=['Year'],
        value_vars=['0', '30', '100', '365'],
        var_name='j',
        value_name='pourcentage_survie'
    )
    result_long['j'] = result_long['j'].astype(int)
    
    return result_long, result_df

def create_survie_curves_plot(result_long):
    """
    Graphique des courbes de survie par année avec points à D0, D30, D100, D365
    """
    try:
        fig = go.Figure()
        
        # Obtenir les années uniques
        years = sorted(result_long['Year'].unique())
        colors = px.colors.qualitative.Set2[:len(years)]  # Utiliser Set2 pour des couleurs plus "vie"
        
        for i, year in enumerate(years):
            year_data = result_long[result_long['Year'] == year].sort_values('j')
            
            fig.add_trace(go.Scatter(
                x=year_data['j'],
                y=year_data['pourcentage_survie'],
                mode='lines+markers',
                name=f'{int(year)}',
                line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=8),
                connectgaps=True
            ))
        
        fig.update_layout(
            title='Overall Survival Curves by Year',
            xaxis_title='Days after transplantation',
            yaxis_title='Overall Survival (%)',
            height=500,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            xaxis=dict(
                tickvals=[0, 30, 100, 365], 
                ticktext=['D0', 'D30', 'D100', 'D365'],
                range=[-10, 375]
            ),
            yaxis=dict(range=[0, 105]),  # 0-105% pour la survie
            template='plotly_white'
        )
        
        return fig
    except Exception as e:
        print(f"ERROR in create_survie_curves_plot: {str(e)}")
        return go.Figure()

def create_survie_datatable(result_df):
    """DataTable pour survie - adapté au nouveau format avec pourcentages"""
    try:
        table_data = []
        for _, row in result_df.iterrows():
            table_data.append({
                'Year': int(row['Year']),
                'Transplants': int(row['nb_greffe']),
                'Alive_D30': int(row['vivants_j30']),
                'Surv_D30_%': f"{row['30']:.1f}%",
                'Alive_D100': int(row['vivants_j100']),
                'Surv_D100_%': f"{row['100']:.1f}%",
                'Alive_D365': int(row['vivants_j365']),
                'Surv_D365_%': f"{row['365']:.1f}%"
            })
        
        return html.Div([
            html.H6("Overall Survival Statistics by year", className='mb-2'),
            dash_table.DataTable(
                data=table_data,
                columns=[
                    {"name": "Year", "id": "Year"},
                    {"name": "Transplants", "id": "Transplants"},
                    {"name": "Alive D30", "id": "Alive_D30"},
                    {"name": "Surv D30 (%)", "id": "Surv_D30_%"},
                    {"name": "Alive D100", "id": "Alive_D100"},
                    {"name": "Surv D100 (%)", "id": "Surv_D100_%"},
                    {"name": "Alive D365", "id": "Alive_D365"},
                    {"name": "Surv D365 (%)", "id": "Surv_D365_%"}
                ],
                style_cell={'textAlign': 'center', 'fontSize': '11px', 'padding': '6px', 'color': '#021F59'},
                style_header={'backgroundColor': '#021F59', 'color': 'white', 'fontWeight': 'bold', 'fontSize': '10px'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
                    {'if': {'column_id': ['Surv_D30_%', 'Surv_D100_%', 'Surv_D365_%']}, 'backgroundColor': '#e8f5e8', 'fontWeight': 'bold'}
                ]
            )
        ])
    except Exception as e:
        print(f"ERROR in create_survie_datatable: {str(e)}")
        return html.Div([dbc.Alert(f"Error creating survival table: {str(e)}", color="danger")])

def create_survie_badges(result_df, analysis_year):
    """Badges survie pour année spécifique - 3 badges séparés (D30, D100, D365)"""
    try:
        analysis_year = int(analysis_year)
        result_df = result_df.copy()
        result_df['Year'] = result_df['Year'].astype(int)
        
        year_data = result_df[result_df['Year'] == analysis_year]
        
        if year_data.empty:
            available_years = sorted(result_df['Year'].unique())
            if available_years:
                fallback_year = available_years[-1]
                year_data = result_df[result_df['Year'] == fallback_year]
                if not year_data.empty:
                    return create_survie_badges_content(year_data, fallback_year, f"Using latest available year")
            
            return dbc.Alert(f"No data available for year {analysis_year}", color="warning")
        
        return create_survie_badges_content(year_data, analysis_year)
        
    except Exception as e:
        return dbc.Alert(f"Error creating survival badges: {str(e)}", color="danger")

def create_survie_badges_content(year_data, analysis_year, subtitle=None):
    """Contenu des 3 badges survie - D30, D100, D365"""
    try:
        # Extraire les données pour l'année
        row = year_data.iloc[0]
        
        # Données pour chaque point temporel
        badges_data = [
            {
                'period': 'D30',
                'percentage': row['30'],
                'count': int(row['vivants_j30']),
                'color': '#27ae60'  # Vert
            },
            {
                'period': 'D100', 
                'percentage': row['100'],
                'count': int(row['vivants_j100']),
                'color': '#2ecc71'  # Vert clair
            },
            {
                'period': 'D365',
                'percentage': row['365'], 
                'count': int(row['vivants_j365']),
                'color': '#16a085'  # Vert sarcelle
            }
        ]
        
        total_greffes = int(row['nb_greffe'])
        
        title = f"Overall Survival Indicators - {analysis_year}"
        if subtitle:
            title += f" ({subtitle})"
        
        # Créer les 3 badges
        badges = []
        for badge_data in badges_data:
            badge = dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{badge_data['percentage']:.1f}%", 
                                className="text-center mb-1", 
                                style={'color': badge_data['color'], 'fontSize': '20px'}),
                        html.P(f"Survival {badge_data['period']}", 
                               className="text-center mb-1", 
                               style={'fontSize': '12px', 'fontWeight': 'bold'}),
                        html.P(f"({badge_data['count']}/{total_greffes})", 
                               className="text-center text-muted", 
                               style={'fontSize': '10px'})
                    ], className="py-2")
                ], color="success", outline=True, style={'border-width': '1px'})
            ], width=4)
            badges.append(badge)
        
        return html.Div([
            html.H6(title, className='text-center mb-3'),
            dbc.Row(badges, className='g-2')
        ])
        
    except Exception as e:
        print(f"ERROR in create_survie_badges_content: {str(e)}")
        return dbc.Alert(f"Error creating survival badge content: {str(e)}", color="danger")

def create_wide_survie_table(quarterly_df):
    """Table survie pleine largeur - adaptée au nouveau format"""
    return dash_table.DataTable(
        data=quarterly_df.to_dict('records'),
        columns=[
            {"name": "Quarter", "id": "Quarter"},
            {"name": "Total Patients", "id": "Total_Patients"},
            {"name": "Deaths D30", "id": "Deaths_D30"},
            {"name": "Deaths D100", "id": "Deaths_D100"},
            {"name": "Deaths D365", "id": "Deaths_D365"},
            {"name": "Alive D365", "id": "Alive_D365"},
            {"name": "Survival % (1Y)", "id": "Survival_Percentage", "type": "numeric", "format": {"specifier": ".1f"}}
        ],
        style_cell={
            'textAlign': 'center', 
            'fontSize': '12px', 
            'padding': '12px',
            'minWidth': '120px',
            'color': '#021F59'
        },
        style_header={
            'backgroundColor': '#021F59', 
            'color': 'white', 
            'fontWeight': 'bold',
            'fontSize': '12px',
            'padding': '12px'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
            {'if': {'column_id': ['Survival_Percentage']}, 'backgroundColor': '#e8f5e8', 'fontWeight': 'bold'}
        ]
    )

def create_survie_quarter_badge(quarterly_df, quarter_num, selected_year):
    """Badge unique survie pour un trimestre - adapté au nouveau format"""
    quarter_data = quarterly_df[quarterly_df['Quarter_Num'] == quarter_num]
    
    if quarter_data.empty:
        return html.Div([
            html.H6(f"Q{quarter_num}", className='text-center mb-2'),
            dbc.Alert("No data", color="light")
        ])
    
    quarter_info = quarter_data.iloc[0]
    survival_pct = quarter_info['Survival_Percentage']
    alive_count = quarter_info['Alive_D365']
    total_patients = quarter_info['Total_Patients']
    
    return html.Div([
        html.H6(f"Q{quarter_num}", className='text-center mb-2', style={'color': '#021F59', 'fontWeight': 'bold'}),
        dbc.Card([
            dbc.CardBody([
                html.H4(f"{survival_pct:.1f}%", className="text-center mb-1", style={'color': '#27ae60'}),
                html.P("Survival (1Y)", className="text-center mb-1", style={'fontSize': '12px', 'fontWeight': 'bold'}),
                html.P(f"({int(alive_count)}/{int(total_patients)})", className="text-center text-muted", style={'fontSize': '10px'})
            ], className="py-3")
        ], color="success", outline=True, style={'border-width': '1px'})
    ])

def create_survie_quarter_badges_column(quarterly_df, quarter_num):
    """Colonne avec 3 badges survie pour un trimestre (D30, D100, D365)"""
    quarter_data = quarterly_df[quarterly_df['Quarter_Num'] == quarter_num]
    
    if quarter_data.empty:
        return html.Div([
            html.H6(f"Q{quarter_num}", className='text-center mb-2', style={'color': '#021F59', 'fontWeight': 'bold'}),
            dbc.Alert("No data", color="light")
        ])
    
    quarter_info = quarter_data.iloc[0]
    total_patients = quarter_info['Total_Patients']
    
    # Données pour les 3 badges
    badges_data = [
        {
            'period': 'D30',
            'percentage': quarter_info['Survival_D30_%'],
            'count': quarter_info['Alive_D30'],
            'color': '#27ae60'  # Vert foncé
        },
        {
            'period': 'D100',
            'percentage': quarter_info['Survival_D100_%'],
            'count': quarter_info['Alive_D100'],
            'color': '#2ecc71'  # Vert
        },
        {
            'period': 'D365',
            'percentage': quarter_info['Survival_D365_%'],
            'count': quarter_info['Alive_D365'],
            'color': '#58d68d'  # Vert clair
        }
    ]
    
    badges = []
    for badge_data in badges_data:
        badge = dbc.Card([
            dbc.CardBody([
                html.H5(f"{badge_data['percentage']:.1f}%", 
                        className="text-center mb-1", 
                        style={'color': badge_data['color'], 'fontSize': '14px'}),
                html.P(f"Survival {badge_data['period']}", 
                       className="text-center mb-1", 
                       style={'fontSize': '10px', 'fontWeight': 'bold'}),
                html.P(f"({int(badge_data['count'])}/{int(total_patients)})", 
                       className="text-center text-muted", 
                       style={'fontSize': '8px'})
            ], className="py-1")
        ], color="success", outline=True, style={'border-width': '1px'}, className='mb-1')
        badges.append(badge)
    
    return html.Div([
        html.H6(f"Q{quarter_num}", className='text-center mb-2', style={'color': '#021F59', 'fontWeight': 'bold'}),
        html.Div(badges)
    ])

def create_wide_survie_table(quarterly_df):
    """Table survie pleine largeur avec tous les détails"""
    return dash_table.DataTable(
        data=quarterly_df.to_dict('records'),
        columns=[
            {"name": "Quarter", "id": "Quarter"},
            {"name": "Total Patients", "id": "Total_Patients"},
            {"name": "Alive D30", "id": "Alive_D30"},
            {"name": "Survival D30 (%)", "id": "Survival_D30_%", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Alive D100", "id": "Alive_D100"},
            {"name": "Survival D100 (%)", "id": "Survival_D100_%", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Alive D365", "id": "Alive_D365"},
            {"name": "Survival D365 (%)", "id": "Survival_D365_%", "type": "numeric", "format": {"specifier": ".1f"}}
        ],
        style_cell={
            'textAlign': 'center', 
            'fontSize': '11px', 
            'padding': '8px',
            'minWidth': '100px',
            'color': '#021F59'
        },
        style_header={
            'backgroundColor': '#021F59', 
            'color': 'white', 
            'fontWeight': 'bold',
            'fontSize': '10px',
            'padding': '8px'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
            {'if': {'column_id': ['Survival_D30_%']}, 'backgroundColor': '#d5f4e6', 'fontWeight': 'bold'},
            {'if': {'column_id': ['Survival_D100_%']}, 'backgroundColor': '#a9dfbf', 'fontWeight': 'bold'},
            {'if': {'column_id': ['Survival_D365_%']}, 'backgroundColor': '#e8f5e8', 'fontWeight': 'bold'}
        ]
    )

# =============================================================================
# Prise de Greffe - Global et Quarterly
# =============================================================================

def create_prise_greffe_global_visualization(df, analysis_year):
    """
    Visualisation globale pour la prise de greffe avec badges pour année spécifique
    """
    try:
        # Traiter les données
        result_df = process_prise_greffe_data(df)
        
        # Calculer les indicateurs globaux
        total_patients = result_df['total'].sum()
        total_prise_greffe = result_df['nb_prise_greffe'].sum()
        pct_global_prise = (total_prise_greffe / total_patients * 100) if total_patients > 0 else 0
        
        return dbc.Row([
            # Colonne gauche : Graphique barplot avec ligne horizontale (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_prise_greffe_barplot(result_df),
                    style={'height': '600px'},
                    config={'responsive': True}
                )
            ], width=7),
            # Colonne droite : DataTable et badge pour année spécifique (40%)
            dbc.Col([
                # DataTable pour toutes les années
                create_prise_greffe_datatable(result_df),
                html.Hr(className='my-3'),
                # Badge pour l'année spécifique
                create_prise_greffe_badges(result_df, analysis_year)
            ], width=5)
        ])
        
    except Exception as e:
        print(f"ERROR in create_prise_greffe_global_visualization: {str(e)}")
        return dbc.Alert(f"Error in transplant success visualization: {str(e)}", color="danger")

def create_prise_greffe_quarterly_visualization(year_data, selected_year):
    """
    Visualisation trimestrielle prise de greffe
    """
    try:
        quarterly_stats = []
        
        for quarter in [1, 2, 3, 4]:
            quarter_data = year_data[year_data['Quarter'] == quarter]
            
            if not quarter_data.empty:
                # Appliquer la même logique que la fonction globale
                quarter_data = quarter_data.copy()
                quarter_data['Date Platelet Reconstitution'] = pd.to_datetime(quarter_data['Date Platelet Reconstitution'], errors='coerce')
                quarter_data['Treatment Date'] = pd.to_datetime(quarter_data['Treatment Date'], errors='coerce')
                quarter_data['duree_prise_de_greffe'] = (quarter_data['Date Platelet Reconstitution'] - quarter_data['Treatment Date']).dt.days
                
                # Filtrer les données valides
                valid_data = quarter_data.dropna(subset=['duree_prise_de_greffe'])
                total_patients = len(valid_data)
                
                # Compter les prises de greffe <= 100 jours
                prise_greffe_count = len(valid_data[valid_data['duree_prise_de_greffe'] <= 100])
                prise_greffe_pct = (prise_greffe_count / total_patients * 100) if total_patients > 0 else 0
                
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': total_patients,
                    'Graft_Uptake_Count': prise_greffe_count,
                    'Graft_Uptake_Percentage': prise_greffe_pct
                })
            else:
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': 0,
                    'Graft_Uptake_Count': 0,
                    'Graft_Uptake_Percentage': 0
                })
        
        quarterly_df = pd.DataFrame(quarterly_stats)
        
        # Graphique prise de greffe trimestriel
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=quarterly_df['Quarter'],
            y=quarterly_df['Graft_Uptake_Percentage'],
            marker_color='#3498db',
            text=[f"{val:.1f}%" for val in quarterly_df['Graft_Uptake_Percentage']],
            textposition='auto'
        ))
        
        # Ajouter la ligne horizontale rouge à 80%
        fig.add_hline(
            y=80,
            line_dash="dash",
            line_color="red",
            line_width=3,
            annotation_text="Target: 80%",
            annotation_position="top right",
            annotation=dict(
                font_size=12,
                font_color="red",
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="red",
                borderwidth=1
            )
        )
        
        fig.update_layout(
            title=f'Platelet Transplant Success by Quarter - {selected_year} (≤100 days)',
            xaxis_title='Quarter',
            yaxis_title='Percentage (%)',
            height=450,
            yaxis=dict(range=[0, 105]),
            template='plotly_white'
        )
        
        return html.Div([
            # Ligne 1: Graphique pleine largeur
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig, style={'height': '450px'}, config={'responsive': True})
                ], width=12)
            ], className='mb-3'),
            
            # Ligne 2: Badges prise de greffe (1 badge par trimestre)
            dbc.Row([
                dbc.Col([
                    create_prise_greffe_quarter_badge(quarterly_df, q, selected_year)
                ], width=3) for q in [1, 2, 3, 4]
            ], className='mb-3'),
            
            # Ligne 3: Tableau pleine largeur
            dbc.Row([
                dbc.Col([
                    html.H6("Quarterly Transplant Success Statistics", className='mb-3 text-center'),
                    create_wide_prise_greffe_table(quarterly_df)
                ], width=12)
            ])
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error in transplant success quarterly layout: {str(e)}", color="danger")

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

def create_prise_greffe_barplot(result_df):
    """Graphique en barres pour prise de greffe avec ligne horizontale à 80%"""
    try:
        fig = go.Figure()
        
        # Ajouter les barres
        fig.add_trace(go.Bar(
            x=result_df['Year'],
            y=result_df['pourcentage_prise_greffe'],
            marker_color='#3498db',  # Bleu
            name='Transplant Success (%)',
            text=[f"{val:.1f}%" for val in result_df['pourcentage_prise_greffe']],
            textposition='auto'
        ))
        
        # Ajouter la ligne horizontale rouge à 80%
        fig.add_hline(
            y=80,
            line_dash="dash",
            line_color="red",
            line_width=3,
            annotation_text="Target: 80%",
            annotation_position="top right",
            annotation=dict(
                font_size=12,
                font_color="red",
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="red",
                borderwidth=1
            )
        )
        
        fig.update_layout(
            title='Transplant Success by Year (≤100 days)',
            yaxis_title='Percentage (%)',
            yaxis=dict(range=[0, 105]),  # 0-105% pour bien voir la ligne à 80%
            template="plotly_white"
        )
        
        return fig
    except Exception as e:
        print(f"ERROR in create_prise_greffe_barplot: {str(e)}")
        return go.Figure()  # Retourner une figure vide en cas d'erreur

def create_prise_greffe_datatable(result_df):
    """DataTable pour prise de greffe"""
    try:
        table_data = []
        for _, row in result_df.iterrows():

            table_data.append({
                'Year': int(row['Year']),
                'Transplants': int(row['total']),
                'Success_(D100)': int(row['nb_prise_greffe']),
                'Percentage': f"{row['pourcentage_prise_greffe']:.1f}%"
            })
        
        return html.Div([
            html.H6("Transplant Success Statistics by year", className='mb-2'),
            dash_table.DataTable(
                data=table_data,
                columns=[
                    {"name": "Year", "id": "Year"},
                    {"name": "Transplants", "id": "Transplants"},
                    {"name": "Success (≤D100)", "id": "Success_(D100)"},
                    {"name": "Percentage", "id": "Percentage"},
                    {"name": "≥80%", "id": "Target_80%"}
                ],
                style_cell={'textAlign': 'center', 'fontSize': '12px', 'padding': '8px', 'color': '#021F59'},
                style_header={'backgroundColor': '#021F59', 'color': 'white', 'fontWeight': 'bold'}
            )
        ])
    except Exception as e:
        print(f"ERROR in create_prise_greffe_datatable: {str(e)}")
        return html.Div([dbc.Alert(f"Error creating transplant success table: {str(e)}", color="danger")])

def create_prise_greffe_badges(result_df, analysis_year):
    """Badge prise de greffe pour année spécifique"""
    try:
        analysis_year = int(analysis_year)
        result_df = result_df.copy()
        result_df['Year'] = result_df['Year'].astype(int)
        
        year_data = result_df[result_df['Year'] == analysis_year]
        
        if year_data.empty:
            available_years = sorted(result_df['Year'].unique())
            if available_years:
                fallback_year = available_years[-1]
                year_data = result_df[result_df['Year'] == fallback_year]
                if not year_data.empty:
                    return create_prise_greffe_badge_content(year_data, fallback_year, f"Using latest available year")

            return dbc.Alert(f"No data available for year {analysis_year}", color="warning")
        
        return create_prise_greffe_badge_content(year_data, analysis_year)
        
    except Exception as e:
        return dbc.Alert(f"Error creating transplant success badges: {str(e)}", color="danger")

def create_prise_greffe_badge_content(year_data, analysis_year, subtitle=None):
    """Contenu du badge prise de greffe"""
    try:
        row = year_data.iloc[0]
        
        prise_pct = row['pourcentage_prise_greffe']
        prise_count = int(row['nb_prise_greffe'])
        total_greffes = int(row['total'])
        
        # Déterminer la couleur du badge en fonction du seuil 80%
        badge_color = "success" if prise_pct >= 80 else "warning"
        text_color = '#27ae60' if prise_pct >= 80 else '#f39c12'
        
        title = f"Transplant Success Indicator - {analysis_year}"
        if subtitle:
            title += f" ({subtitle})"
        
        return html.Div([
            html.H6(title, className='text-center mb-3'),
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{prise_pct:.1f}%", className="text-center mb-2", style={'color': text_color}),
                    html.P("Transplant Success (≤100 days)", className="text-center mb-2", style={'fontSize': '16px', 'fontWeight': 'bold'}),
                    html.P(f"({prise_count}/{total_greffes})", className="text-center text-muted", style={'fontSize': '14px'}),
                ], className="py-3")
            ], color=badge_color, outline=True, style={'border-width': '2px'})
        ])
        
    except Exception as e:
        print(f"ERROR in create_prise_greffe_badge_content: {str(e)}")
        return dbc.Alert(f"Error creating transplant success badge content: {str(e)}", color="danger")

def create_wide_prise_greffe_table(quarterly_df):
    """Table prise de greffe pleine largeur"""
    return dash_table.DataTable(
        data=quarterly_df.to_dict('records'),
        columns=[
            {"name": "Quarter", "id": "Quarter"},
            {"name": "Total Patients", "id": "Total_Patients"},
            {"name": "Transplant Success", "id": "Graft_Uptake_Count"},
            {"name": "Uptake %", "id": "Graft_Uptake_Percentage", "type": "numeric", "format": {"specifier": ".1f"}}
        ],
        style_cell={
            'textAlign': 'center', 
            'fontSize': '12px', 
            'padding': '12px',
            'minWidth': '120px',
            'color': '#021F59'
        },
        style_header={
            'backgroundColor': '#021F59', 
            'color': 'white', 
            'fontWeight': 'bold',
            'fontSize': '12px',
            'padding': '12px'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
            {'if': {'column_id': ['Graft_Uptake_Percentage']}, 'backgroundColor': '#e3f2fd', 'fontWeight': 'bold'}
        ]
    )

def create_prise_greffe_quarter_badge(quarterly_df, quarter_num, selected_year):
    """Badge unique prise de greffe pour un trimestre"""
    quarter_data = quarterly_df[quarterly_df['Quarter_Num'] == quarter_num]
    
    if quarter_data.empty:
        return html.Div([
            html.H6(f"Q{quarter_num}", className='text-center mb-2'),
            dbc.Alert("No data", color="light")
        ])
    
    quarter_info = quarter_data.iloc[0]
    uptake_pct = quarter_info['Graft_Uptake_Percentage']
    uptake_count = quarter_info['Graft_Uptake_Count']
    total_patients = quarter_info['Total_Patients']
    
    # Couleur en fonction du seuil 80%
    badge_color = "success" if uptake_pct >= 80 else "warning"
    text_color = '#27ae60' if uptake_pct >= 80 else '#f39c12'
    
    return html.Div([
        html.H6(f"Q{quarter_num}", className='text-center mb-2', style={'color': '#021F59', 'fontWeight': 'bold'}),
        dbc.Card([
            dbc.CardBody([
                html.H4(f"{uptake_pct:.1f}%", className="text-center mb-1", style={'color': text_color}),
                html.P("Transplant Success", className="text-center mb-1", style={'fontSize': '12px', 'fontWeight': 'bold'}),
                html.P(f"({int(uptake_count)}/{int(total_patients)})", className="text-center text-muted", style={'fontSize': '10px'})
            ], className="py-3")
        ], color=badge_color, outline=True, style={'border-width': '1px'})
    ])
# =============================================================================
# Sortie d'Aplasie - Global et Quarterly  
# =============================================================================

def create_sortie_aplasie_global_visualization(df, analysis_year):
    """
    Visualisation globale pour la sortie d'aplasie avec badges pour année spécifique
    """
    try:
        # Traiter les données
        result_df = process_sortie_aplasie_data(df)
        
        # Calculer les indicateurs globaux
        total_patients = result_df['total'].sum()
        total_sortie_aplasie = result_df['nb_sortie_aplasie'].sum()
        pct_global_sortie = (total_sortie_aplasie / total_patients * 100) if total_patients > 0 else 0
        
        return dbc.Row([
            # Colonne gauche : Graphique barplot avec ligne horizontale (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_sortie_aplasie_barplot(result_df),
                    style={'height': '600px'},
                    config={'responsive': True}
                )
            ], width=7),
            # Colonne droite : DataTable et badge pour année spécifique (40%)
            dbc.Col([
                # DataTable pour toutes les années
                create_sortie_aplasie_datatable(result_df),
                html.Hr(className='my-3'),
                # Badge pour l'année spécifique
                create_sortie_aplasie_badges(result_df, analysis_year)
            ], width=5)
        ])
        
    except Exception as e:
        print(f"ERROR in create_sortie_aplasie_global_visualization: {str(e)}")
        return dbc.Alert(f"Error in ANC recovery visualization: {str(e)}", color="danger")

def create_sortie_aplasie_quarterly_visualization(year_data, selected_year):
    """
    Visualisation trimestrielle sortie d'aplasie
    """
    try:
        quarterly_stats = []
        
        for quarter in [1, 2, 3, 4]:
            quarter_data = year_data[year_data['Quarter'] == quarter]
            
            if not quarter_data.empty:
                # Appliquer la même logique que la fonction globale
                quarter_data = quarter_data.copy()
                quarter_data['Date Anc Recovery'] = pd.to_datetime(quarter_data['Date Anc Recovery'], errors='coerce')
                quarter_data['Treatment Date'] = pd.to_datetime(quarter_data['Treatment Date'], errors='coerce')
                quarter_data['duree_aplasie'] = (quarter_data['Date Anc Recovery'] - quarter_data['Treatment Date']).dt.days
                
                # Filtrer les données valides
                valid_data = quarter_data.dropna(subset=['duree_aplasie'])
                total_patients = len(valid_data)
                
                # Compter les sorties d'aplasie <= 28 jours
                sortie_aplasie_count = len(valid_data[valid_data['duree_aplasie'] <= 28])
                sortie_aplasie_pct = (sortie_aplasie_count / total_patients * 100) if total_patients > 0 else 0
                
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': total_patients,
                    'ANC_Recovery_Count': sortie_aplasie_count,
                    'ANC_Recovery_Percentage': sortie_aplasie_pct
                })
            else:
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': 0,
                    'ANC_Recovery_Count': 0,
                    'ANC_Recovery_Percentage': 0
                })
        
        quarterly_df = pd.DataFrame(quarterly_stats)
        
        # Graphique sortie d'aplasie trimestriel
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=quarterly_df['Quarter'],
            y=quarterly_df['ANC_Recovery_Percentage'],
            marker_color='#9b59b6',  # Violet
            text=[f"{val:.1f}%" for val in quarterly_df['ANC_Recovery_Percentage']],
            textposition='auto'
        ))
        
        # Ajouter la ligne horizontale rouge à 80%
        fig.add_hline(
            y=80,
            line_dash="dash",
            line_color="red",
            line_width=3,
            annotation_text="Target: 80%",
            annotation_position="top right",
            annotation=dict(
                font_size=12,
                font_color="red",
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="red",
                borderwidth=1
            )
        )
        
        fig.update_layout(
            title=f'ANC Recovery by Quarter - {selected_year} (≤28 days)',
            xaxis_title='Quarter',
            yaxis_title='Percentage (%)',
            yaxis=dict(range=[0, 105]),
            template='plotly_white'
        )
        
        return html.Div([
            # Ligne 1: Graphique pleine largeur
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig, style={'height': '450px'}, config={'responsive': True})
                ], width=12)
            ], className='mb-3'),
            
            # Ligne 2: Badges sortie d'aplasie (1 badge par trimestre)
            dbc.Row([
                dbc.Col([
                    create_sortie_aplasie_quarter_badge(quarterly_df, q, selected_year)
                ], width=3) for q in [1, 2, 3, 4]
            ], className='mb-3'),
            
            # Ligne 3: Tableau pleine largeur
            dbc.Row([
                dbc.Col([
                    html.H6("Quarterly ANC Recovery Statistics", className='mb-3 text-center'),
                    create_wide_sortie_aplasie_table(quarterly_df)
                ], width=12)
            ])
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error in ANC recovery quarterly layout: {str(e)}", color="danger")

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

def create_sortie_aplasie_barplot(result_df):
    """Graphique en barres pour sortie d'aplasie avec ligne horizontale à 80%"""
    try:
        fig = go.Figure()
        
        # Ajouter les barres
        fig.add_trace(go.Bar(
            x=result_df['Year'],
            y=result_df['pourcentage_sortie_aplasie'],
            marker_color='#9b59b6',  # Violet
            name='ANC Recovery (%)',
            text=[f"{val:.1f}%" for val in result_df['pourcentage_sortie_aplasie']],
            textposition='auto'
        ))
        
        # Ajouter la ligne horizontale rouge à 80%
        fig.add_hline(
            y=80,
            line_dash="dash",
            line_color="red",
            line_width=3,
            annotation_text="Target: 80%",
            annotation_position="top right",
            annotation=dict(
                font_size=12,
                font_color="red",
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="red",
                borderwidth=1
            )
        )
        
        fig.update_layout(
            title='ANC Recovery (≤28 days) by Year',
            yaxis_title='Percentage (%)',
            yaxis=dict(range=[0, 105]),  # 0-105% pour bien voir la ligne à 80%
            template='plotly_white'
        )
        
        return fig
    except Exception as e:
        print(f"ERROR in create_sortie_aplasie_barplot: {str(e)}")
        return go.Figure()  # Retourner une figure vide en cas d'erreur

def create_sortie_aplasie_datatable(result_df):
    """DataTable pour sortie d'aplasie"""
    try:
        table_data = []
        for _, row in result_df.iterrows():
            
            table_data.append({
                'Year': int(row['Year']),
                'Transplants': int(row['total']),
                'ANC_Recovery': int(row['nb_sortie_aplasie']),
                'Percentage': f"{row['pourcentage_sortie_aplasie']:.1f}%"
            })
        
        return html.Div([
            html.H6("ANC Recovery Statistics by year", className='mb-2'),
            dash_table.DataTable(
                data=table_data,
                columns=[
                    {"name": "Year", "id": "Year"},
                    {"name": "Transplants", "id": "Transplants"},
                    {"name": "ANC Recovery", "id": "ANC_Recovery"},
                    {"name": "Percentage", "id": "Percentage"}
                ],
                style_cell={'textAlign': 'center', 'fontSize': '12px', 'padding': '8px', 'color': '#021F59'},
                style_header={'backgroundColor': '#021F59', 'color': 'white', 'fontWeight': 'bold'}
            )
        ])
    except Exception as e:
        print(f"ERROR in create_sortie_aplasie_datatable: {str(e)}")
        return html.Div([dbc.Alert(f"Error creating ANC recovery table: {str(e)}", color="danger")])

def create_sortie_aplasie_badges(result_df, analysis_year):
    """Badge sortie d'aplasie pour année spécifique"""
    try:
        analysis_year = int(analysis_year)
        result_df = result_df.copy()
        result_df['Year'] = result_df['Year'].astype(int)
        
        year_data = result_df[result_df['Year'] == analysis_year]
        
        if year_data.empty:
            available_years = sorted(result_df['Year'].unique())
            if available_years:
                fallback_year = available_years[-1]
                year_data = result_df[result_df['Year'] == fallback_year]
                if not year_data.empty:
                    return create_sortie_aplasie_badge_content(year_data, fallback_year, f"Using latest available year")
            
            return dbc.Alert(f"No data available for year {analysis_year}", color="warning")
        
        return create_sortie_aplasie_badge_content(year_data, analysis_year)
        
    except Exception as e:
        return dbc.Alert(f"Error creating ANC recovery badges: {str(e)}", color="danger")

def create_sortie_aplasie_badge_content(year_data, analysis_year, subtitle=None):
    """Contenu du badge sortie d'aplasie"""
    try:
        row = year_data.iloc[0]
        
        sortie_pct = row['pourcentage_sortie_aplasie']
        sortie_count = int(row['nb_sortie_aplasie'])
        total_greffes = int(row['total'])
        
        # Déterminer la couleur du badge en fonction du seuil 80%
        badge_color = "success" if sortie_pct >= 80 else "warning"
        text_color = '#27ae60' if sortie_pct >= 80 else '#f39c12'
        
        title = f"ANC Recovery (≤28 days) - {analysis_year}"
        if subtitle:
            title += f" ({subtitle})"
        
        return html.Div([
            html.H6(title, className='text-center mb-3'),
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{sortie_pct:.1f}%", className="text-center mb-2", style={'color': text_color}),
                    html.P("ANC Recovery (≤28 days)", className="text-center mb-2", style={'fontSize': '16px', 'fontWeight': 'bold'}),
                    html.P(f"({sortie_count}/{total_greffes})", className="text-center text-muted", style={'fontSize': '14px'}),
                ], className="py-3")
            ], color=badge_color, outline=True, style={'border-width': '2px'})
        ])
        
    except Exception as e:
        print(f"ERROR in create_sortie_aplasie_badge_content: {str(e)}")
        return dbc.Alert(f"Error creating ANC recovery badge content: {str(e)}", color="danger")

def create_wide_sortie_aplasie_table(quarterly_df):
    """Table sortie d'aplasie pleine largeur"""
    return dash_table.DataTable(
        data=quarterly_df.to_dict('records'),
        columns=[
            {"name": "Quarter", "id": "Quarter"},
            {"name": "Total Patients", "id": "Total_Patients"},
            {"name": "ANC Recovery", "id": "ANC_Recovery_Count"},
            {"name": "Recovery %", "id": "ANC_Recovery_Percentage", "type": "numeric", "format": {"specifier": ".1f"}}
        ],
        style_cell={
            'textAlign': 'center', 
            'fontSize': '12px', 
            'padding': '12px',
            'minWidth': '120px',
            'color': '#021F59'
        },
        style_header={
            'backgroundColor': '#021F59', 
            'color': 'white', 
            'fontWeight': 'bold',
            'fontSize': '12px',
            'padding': '12px'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
            {'if': {'column_id': ['ANC_Recovery_Percentage']}, 'backgroundColor': '#f3e5f5', 'fontWeight': 'bold'}
        ]
    )

def create_sortie_aplasie_quarter_badge(quarterly_df, quarter_num, selected_year):
    """Badge unique sortie d'aplasie pour un trimestre"""
    quarter_data = quarterly_df[quarterly_df['Quarter_Num'] == quarter_num]
    
    if quarter_data.empty:
        return html.Div([
            html.H6(f"Q{quarter_num}", className='text-center mb-2'),
            dbc.Alert("No data", color="light")
        ])
    
    quarter_info = quarter_data.iloc[0]
    recovery_pct = quarter_info['ANC_Recovery_Percentage']
    recovery_count = quarter_info['ANC_Recovery_Count']
    total_patients = quarter_info['Total_Patients']
    
    # Couleur en fonction du seuil 80%
    badge_color = "success" if recovery_pct >= 80 else "warning"
    text_color = '#27ae60' if recovery_pct >= 80 else '#f39c12'
    
    return html.Div([
        html.H6(f"Q{quarter_num}", className='text-center mb-2', style={'color': '#021F59', 'fontWeight': 'bold'}),
        dbc.Card([
            dbc.CardBody([
                html.H4(f"{recovery_pct:.1f}%", className="text-center mb-1", style={'color': text_color}),
                html.P("ANC Recovery", className="text-center mb-1", style={'fontSize': '12px', 'fontWeight': 'bold'}),
                html.P(f"({int(recovery_count)}/{int(total_patients)})", className="text-center text-muted", style={'fontSize': '10px'})
            ], className="py-3")
        ], color=badge_color, outline=True, style={'border-width': '1px'})
    ])

# =============================================================================
# GVH Chronique - Global et Quarterly
# =============================================================================

def create_gvhc_global_visualization(df, analysis_year):
    """
    Visualisation globale pour la GVH chronique avec badges pour année spécifique
    """
    try:
        # Traiter les données
        result_combined, grade_counts = process_gvhc_data(df)
        
        # Calculer les indicateurs globaux
        total_patients = result_combined['nb_greffe'].sum()
        total_gvhc = result_combined['nb_gvh_chronique_total'].sum()
        pct_global_gvhc = (total_gvhc / total_patients * 100) if total_patients > 0 else 0
        
        return dbc.Row([
            # Colonne gauche : Graphique barplot stratifié (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_gvhc_barplot(result_combined, grade_counts),
                    style={'height': '600px'},
                    config={'responsive': True}
                )
            ], width=7),
            # Colonne droite : DataTable et badges pour année spécifique (40%)
            dbc.Col([
                # DataTable pour toutes les années
                create_gvhc_datatable(result_combined),
                html.Hr(className='my-3'),
                # Badges pour l'année spécifique
                create_gvhc_badges(result_combined, analysis_year)
            ], width=5)
        ])
        
    except Exception as e:
        print(f"ERROR in create_gvhc_global_visualization: {str(e)}")
        return dbc.Alert(f"Error in chronic GVH visualization: {str(e)}", color="danger")

def create_gvhc_quarterly_visualization(year_data, selected_year):
    """
    Visualisation trimestrielle GVH chronique - CORRIGÉE
    """
    try:
        quarterly_stats = []
        
        for quarter in [1, 2, 3, 4]:
            quarter_data = year_data[year_data['Quarter'] == quarter]
            
            if not quarter_data.empty:
                # TOTAL PATIENTS = TOUS les patients du trimestre (pas seulement ceux avec GVHc)
                total_patients = len(quarter_data)
                
                # Maintenant on traite les données GVHc
                quarter_data = quarter_data.copy()
                
                # Appliquer la transformation GVHc AVANT tout traitement
                quarter_data = data_processing.transform_gvhc_scores(quarter_data)
                
                quarter_data['First Cgvhd Occurrence Date'] = pd.to_datetime(quarter_data['First Cgvhd Occurrence Date'], errors='coerce')
                quarter_data['Treatment Date'] = pd.to_datetime(quarter_data['Treatment Date'], errors='coerce')
                quarter_data['delai_gvh_chronique'] = (quarter_data['First Cgvhd Occurrence Date'] - quarter_data['Treatment Date']).dt.days
                
                # Filtrer SEULEMENT pour les calculs de GVHc (pas pour le total des patients)
                # On garde seulement les patients qui ont une GVHc valide
                gvhc_data = quarter_data[~quarter_data['delai_gvh_chronique'].isna()]
                
                # Filtrer pour GVHc <= 365 jours avec grades valides
                gvhc_data = gvhc_data[gvhc_data['delai_gvh_chronique'] <= 365]
                gvhc_data = gvhc_data[gvhc_data['First cGvHD Maximum NIH Score'].isin(['Mild', 'Moderate', 'Severe'])]
                
                # Compter par grade
                mild_count = len(gvhc_data[gvhc_data['First cGvHD Maximum NIH Score'] == 'Mild'])
                moderate_count = len(gvhc_data[gvhc_data['First cGvHD Maximum NIH Score'] == 'Moderate'])
                severe_count = len(gvhc_data[gvhc_data['First cGvHD Maximum NIH Score'] == 'Severe'])
                total_gvhc = len(gvhc_data)
                
                # IMPORTANT : Calculer le pourcentage sur le total de TOUS les patients du trimestre
                total_gvhc_pct = (total_gvhc / total_patients * 100) if total_patients > 0 else 0
                
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': total_patients,  # TOUS les patients du trimestre
                    'Mild': mild_count,
                    'Moderate': moderate_count,
                    'Severe': severe_count,
                    'Total_cGVH': total_gvhc,
                    'cGVH_Percentage': total_gvhc_pct
                })
            else:
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': 0,
                    'Mild': 0,
                    'Moderate': 0,
                    'Severe': 0,
                    'Total_cGVH': 0,
                    'cGVH_Percentage': 0
                })
        
        quarterly_df = pd.DataFrame(quarterly_stats)
        
        # Graphique GVHc trimestriel empilé
        fig = go.Figure()
        
        colors = {
            'Mild': '#2ecc71',      # Vert
            'Moderate': '#f39c12',  # Orange  
            'Severe': '#e74c3c'     # Rouge
        }
        
        grades = ['Mild', 'Moderate', 'Severe']
        for grade in grades:
            # Calculer les pourcentages pour l'affichage
            percentages = (quarterly_df[grade] / quarterly_df['Total_Patients'] * 100).fillna(0)
            
            fig.add_trace(go.Bar(
                x=quarterly_df['Quarter'],
                y=percentages,
                name=f'{grade} cGVH',
                marker_color=colors[grade],
                text=[f"{val:.1f}%" if val > 0 else "" for val in percentages],
                textposition='inside',
                textfont=dict(color='white', size=10)
            ))
        
        fig.update_layout(
            title=f'Chronic GVH by Quarter - {selected_year} (≤365 days)',
            xaxis_title='Quarter',
            yaxis_title='Percentage (%)',
            barmode='stack',
            template='plotly_white'
        )
        
        return html.Div([
            # Ligne 1: Graphique pleine largeur
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig, style={'height': '450px'}, config={'responsive': True})
                ], width=12)
            ], className='mb-3'),
            
            # Ligne 2: Badges GVHc (1 badge par trimestre)
            dbc.Row([
                dbc.Col([
                    create_gvhc_quarter_badge(quarterly_df, q, selected_year)
                ], width=3) for q in [1, 2, 3, 4]
            ], className='mb-3'),
            
            # Ligne 3: Tableau pleine largeur
            dbc.Row([
                dbc.Col([
                    html.H6("Quarterly Chronic GVH Statistics", className='mb-3 text-center'),
                    create_wide_gvhc_table(quarterly_df)
                ], width=12)
            ])
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error in chronic GVH quarterly layout: {str(e)}", color="danger")

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
    
    # Appliquer la transformation GVHc AVANT tout traitement
    df = data_processing.transform_gvhc_scores(df)
    
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
    
    # Calculer les totaux pour GVH chronique
    gvhc_totals = result_all_grades.groupby('Year').size().reset_index(name='nb_gvh_chronique_total')
    
    # Fusionner avec nb_greffe_year pour obtenir le pourcentage
    result_combined = pd.merge(nb_greffe_year, gvhc_totals, on='Year', how='left')
    result_combined['nb_gvh_chronique_total'] = result_combined['nb_gvh_chronique_total'].fillna(0)
    result_combined['pourcentage_gvh_chronique_total'] = (result_combined['nb_gvh_chronique_total'] / result_combined['nb_greffe']) * 100
    
    # Ajouter les colonnes de grade_counts à result_combined
    if not grade_counts.empty:
        result_combined = pd.merge(result_combined, grade_counts, on='Year', how='left')
        # Remplir les NaN par 0 pour les grades manquants
        grade_columns = ['Mild', 'Moderate', 'Severe']
        for col in grade_columns:
            if col in result_combined.columns:
                result_combined[col] = result_combined[col].fillna(0)
            else:
                result_combined[col] = 0
    else:
        # Si grade_counts est vide, ajouter des colonnes vides
        result_combined['Mild'] = 0
        result_combined['Moderate'] = 0
        result_combined['Severe'] = 0
    
    return result_combined, grade_counts

def create_gvhc_barplot(result_combined, grade_counts):
    """Graphique en barres empilées pour GVH chronique par grade en pourcentage"""
    try:
        fig = go.Figure()
        
        # Couleurs pour les différents grades
        colors = {
            'Mild': '#2ecc71',      # Vert
            'Moderate': '#f39c12',  # Orange  
            'Severe': '#e74c3c'     # Rouge
        }
        
        # Créer les barres empilées pour chaque grade en pourcentage
        grades = ['Mild', 'Moderate', 'Severe']
        
        for grade in grades:
            if grade in result_combined.columns:
                # Calculer les pourcentages
                percentages = (result_combined[grade] / result_combined['nb_greffe'] * 100).round(1)
                
                fig.add_trace(go.Bar(
                    x=result_combined['Year'],
                    y=percentages,
                    name=f'{grade} cGVH',
                    marker_color=colors[grade],
                    text=[f"{val:.1f}%" if val > 0 else "" for val in percentages],
                    textposition='inside',
                    textfont=dict(color='white', size=10)
                ))
        
        fig.update_layout(
            title='Chronic GVH by Year and Grade (≤365 days)',
            yaxis_title='Percentage (%)',
            barmode='stack',  # Barres empilées
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            template='plotly_white'
        )
        
        return fig
    except Exception as e:
        print(f"ERROR in create_gvhc_barplot: {str(e)}")
        return go.Figure()  # Retourner une figure vide en cas d'erreur

def create_gvhc_datatable(result_combined):
    """DataTable pour GVH chronique avec stratification par grades"""
    try:
        table_data = []
        for _, row in result_combined.iterrows():
            # Calculer les pourcentages par grade
            total_transplants = row['nb_greffe']
            mild_pct = (row['Mild'] / total_transplants * 100) if total_transplants > 0 else 0
            moderate_pct = (row['Moderate'] / total_transplants * 100) if total_transplants > 0 else 0
            severe_pct = (row['Severe'] / total_transplants * 100) if total_transplants > 0 else 0
            total_pct = row['pourcentage_gvh_chronique_total']
            
            table_data.append({
                'Year': int(row['Year']),
                'Transplants': int(row['nb_greffe']),
                'Mild': int(row['Mild']),
                'Mild_%': f"{mild_pct:.1f}%",
                'Moderate': int(row['Moderate']),
                'Moderate_%': f"{moderate_pct:.1f}%",
                'Severe': int(row['Severe']),
                'Severe_%': f"{severe_pct:.1f}%",
                'Total_cGVH': int(row['nb_gvh_chronique_total']),
                'Total_%': f"{total_pct:.1f}%"
            })
        
        return html.Div([
            html.H6("Chronic GVH Statistics by year", className='mb-2'),
            dash_table.DataTable(
                data=table_data,
                columns=[
                    {"name": "Year", "id": "Year"},
                    {"name": "Transplants", "id": "Transplants"},
                    {"name": "Mild", "id": "Mild"},
                    {"name": "Mild (%)", "id": "Mild_%"},
                    {"name": "Moderate", "id": "Moderate"},
                    {"name": "Mod. (%)", "id": "Moderate_%"},
                    {"name": "Severe", "id": "Severe"},
                    {"name": "Severe (%)", "id": "Severe_%"},
                    {"name": "Total cGVH", "id": "Total_cGVH"},
                    {"name": "Total (%)", "id": "Total_%"}
                ],
                style_cell={'textAlign': 'center', 'fontSize': '10px', 'padding': '4px', 'color': '#021F59'},
                style_header={'backgroundColor': '#021F59', 'color': 'white', 'fontWeight': 'bold', 'fontSize': '9px'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
                    {'if': {'column_id': ['Mild_%']}, 'backgroundColor': '#d5f4e6', 'fontWeight': 'bold'},
                    {'if': {'column_id': ['Moderate_%']}, 'backgroundColor': '#fdeaa7', 'fontWeight': 'bold'},
                    {'if': {'column_id': ['Severe_%']}, 'backgroundColor': '#fadbd8', 'fontWeight': 'bold'},
                    {'if': {'column_id': ['Total_%']}, 'backgroundColor': 'rgba(119, 172, 242, 0.2)', 'fontWeight': 'bold'}
                ]
            )
        ])
    except Exception as e:
        print(f"ERROR in create_gvhc_datatable: {str(e)}")
        return html.Div([dbc.Alert(f"Error creating chronic GVH table: {str(e)}", color="danger")])

def create_gvhc_badges(result_combined, analysis_year):
    """Badges GVH chronique pour année spécifique - 4 badges (Mild, Moderate, Severe, Total)"""
    try:
        analysis_year = int(analysis_year)
        result_combined = result_combined.copy()
        result_combined['Year'] = result_combined['Year'].astype(int)
        
        year_data = result_combined[result_combined['Year'] == analysis_year]
        
        if year_data.empty:
            available_years = sorted(result_combined['Year'].unique())
            if available_years:
                fallback_year = available_years[-1]
                year_data = result_combined[result_combined['Year'] == fallback_year]
                if not year_data.empty:
                    return create_gvhc_badges_content(year_data, fallback_year, f"Using {fallback_year} (latest available)")
            
            return dbc.Alert(f"No data available for year {analysis_year}", color="warning")
        
        return create_gvhc_badges_content(year_data, analysis_year)
        
    except Exception as e:
        return dbc.Alert(f"Error creating chronic GVH badges: {str(e)}", color="danger")

def create_gvhc_badges_content(year_data, analysis_year, subtitle=None):
    """Contenu du badge GVH chronique - 1 seul badge pour le total tous grades confondus"""
    try:
        # Extraire les données pour l'année
        row = year_data.iloc[0]
        
        total_greffes = int(row['nb_greffe'])
        gvhc_total = int(row['nb_gvh_chronique_total'])
        gvhc_pct = row['pourcentage_gvh_chronique_total']
        
        title = f"Chronic GVH Indicator - {analysis_year}"
        if subtitle:
            title += f" ({subtitle})"
        
        return html.Div([
            html.H6(title, className='text-center mb-3'),
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{gvhc_pct:.1f}%", className="text-center mb-2", style={'color': '#8e44ad'}),
                    html.P("Chronic GVH (all grades)", className="text-center mb-2", style={'fontSize': '16px', 'fontWeight': 'bold'}),
                    html.P(f"({gvhc_total}/{total_greffes})", className="text-center text-muted", style={'fontSize': '14px'})
                ], className="py-3")
            ], color="secondary", outline=True, style={'border-width': '2px'})
        ])
        
    except Exception as e:
        print(f"ERROR in create_gvhc_badges_content: {str(e)}")
        return dbc.Alert(f"Error creating chronic GVH badge content: {str(e)}", color="danger")

def create_wide_gvhc_table(quarterly_df):
    """Table GVHc pleine largeur"""
    return dash_table.DataTable(
        data=quarterly_df.to_dict('records'),
        columns=[
            {"name": "Quarter", "id": "Quarter"},
            {"name": "Total Patients", "id": "Total_Patients"},
            {"name": "Mild", "id": "Mild"},
            {"name": "Moderate", "id": "Moderate"},
            {"name": "Severe", "id": "Severe"},
            {"name": "Total cGVH", "id": "Total_cGVH"},
            {"name": "cGVH %", "id": "cGVH_Percentage", "type": "numeric", "format": {"specifier": ".1f"}}
        ],
        style_cell={
            'textAlign': 'center', 
            'fontSize': '12px', 
            'padding': '12px',
            'minWidth': '100px',
            'color': '#021F59'
        },
        style_header={
            'backgroundColor': '#021F59', 
            'color': 'white', 
            'fontWeight': 'bold',
            'fontSize': '12px',
            'padding': '12px'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
            {'if': {'column_id': ['Mild']}, 'backgroundColor': '#d5f4e6'},
            {'if': {'column_id': ['Moderate']}, 'backgroundColor': '#fdeaa7'},
            {'if': {'column_id': ['Severe']}, 'backgroundColor': '#fadbd8'},
            {'if': {'column_id': ['cGVH_Percentage']}, 'backgroundColor': 'rgba(119, 172, 242, 0.2)', 'fontWeight': 'bold'}
        ]
    )

def create_gvhc_quarter_badge(quarterly_df, quarter_num, selected_year):
    """Badge unique GVHc pour un trimestre"""
    quarter_data = quarterly_df[quarterly_df['Quarter_Num'] == quarter_num]
    
    if quarter_data.empty:
        return html.Div([
            html.H6(f"Q{quarter_num}", className='text-center mb-2'),
            dbc.Alert("No data", color="light")
        ])
    
    quarter_info = quarter_data.iloc[0]
    gvhc_pct = quarter_info['cGVH_Percentage']
    gvhc_total = quarter_info['Total_cGVH']
    total_patients = quarter_info['Total_Patients']
    
    return html.Div([
        html.H6(f"Q{quarter_num}", className='text-center mb-2', style={'color': '#021F59', 'fontWeight': 'bold'}),
        dbc.Card([
            dbc.CardBody([
                html.H4(f"{gvhc_pct:.1f}%", className="text-center mb-1", style={'color': '#8e44ad'}),
                html.P("cGVH Total", className="text-center mb-1", style={'fontSize': '12px', 'fontWeight': 'bold'}),
                html.P(f"({int(gvhc_total)}/{int(total_patients)})", className="text-center text-muted", style={'fontSize': '10px'})
            ], className="py-3")
        ], color="secondary", outline=True, style={'border-width': '1px'})
    ])

# =============================================================================
# Rechute - Global et Quarterly
# =============================================================================

def create_rechute_global_visualization(df, analysis_year):
    """
    Visualisation globale pour la rechute avec badges pour année spécifique
    """
    try:
        # Traiter les données
        result_long, result_df = process_rechute_data(df)
        
        # Calculer les indicateurs globaux
        total_patients = result_df['nb_greffe'].sum()
        total_rechute_365 = result_df['rechute_j365'].sum()
        pct_global_rechute = (total_rechute_365 / total_patients * 100) if total_patients > 0 else 0
        
        return dbc.Row([
            # Colonne gauche : Graphique des courbes de rechute (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_rechute_curves_plot(result_long),
                    style={'height': '600px'},
                    config={'responsive': True}
                )
            ], width=7),
            # Colonne droite : DataTable et badges pour année spécifique (40%)
            dbc.Col([
                # DataTable pour toutes les années
                create_rechute_datatable(result_df),
                html.Hr(className='my-3'),
                # Badges pour l'année spécifique
                create_rechute_badges(result_df, analysis_year)
            ], width=5)
        ])
        
    except Exception as e:
        print(f"ERROR in create_rechute_global_visualization: {str(e)}")
        return dbc.Alert(f"Error in relapse visualization: {str(e)}", color="danger")

def create_rechute_quarterly_visualization(year_data, selected_year):
    """
    Visualisation trimestrielle rechute avec courbes par trimestre et 2 badges par trimestre
    """
    try:
        quarterly_stats = []
        quarterly_long = []
        
        for quarter in [1, 2, 3, 4]:
            quarter_data = year_data[year_data['Quarter'] == quarter]
            
            if not quarter_data.empty:
                # Appliquer la même logique que la fonction globale
                quarter_data = quarter_data.copy()
                quarter_data['First Relapse Date'] = pd.to_datetime(quarter_data['First Relapse Date'], errors='coerce')
                quarter_data['Treatment Date'] = pd.to_datetime(quarter_data['Treatment Date'], errors='coerce')
                quarter_data['delai_rechute'] = (quarter_data['First Relapse Date'] - quarter_data['Treatment Date']).dt.days
                
                # Filtrer les données valides
                valid_data = quarter_data[~quarter_data['delai_rechute'].isna()]
                total_patients = len(valid_data)
                
                # Conversion des valeurs de First Relapse
                valid_data['statut_rechute'] = valid_data['First Relapse'].apply(
                    lambda x: 1 if x in ["Yes"] else 0
                )
                
                # Calculer les rechutes à différents points temporels
                rechute_j100 = len(valid_data[
                    (valid_data['statut_rechute'] == 1) & 
                    (valid_data['delai_rechute'] <= 100)
                ])
                
                rechute_j365 = len(valid_data[
                    (valid_data['statut_rechute'] == 1) & 
                    (valid_data['delai_rechute'] <= 365)
                ])
                
                # Calculer les pourcentages
                rechute_pct_100 = (rechute_j100 / total_patients * 100) if total_patients > 0 else 0
                rechute_pct_365 = (rechute_j365 / total_patients * 100) if total_patients > 0 else 0
                
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': total_patients,
                    'Relapse_D100': rechute_j100,
                    'Relapse_D365': rechute_j365,
                    'Relapse_D100_%': rechute_pct_100,
                    'Relapse_D365_%': rechute_pct_365
                })
                
                # Créer les données pour les courbes (format long) - seulement D0, D100, D365
                for day, pct in [(0, 0.0), (100, rechute_pct_100), (365, rechute_pct_365)]:
                    quarterly_long.append({
                        'Quarter': f'Q{quarter}',
                        'Quarter_Num': quarter,
                        'Day': day,
                        'Relapse_Percentage': pct
                    })
                
            else:
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Quarter_Num': quarter,
                    'Total_Patients': 0,
                    'Relapse_D100': 0,
                    'Relapse_D365': 0,
                    'Relapse_D100_%': 0,
                    'Relapse_D365_%': 0
                })
                
                # Données vides pour les courbes
                for day in [0, 100, 365]:
                    quarterly_long.append({
                        'Quarter': f'Q{quarter}',
                        'Quarter_Num': quarter,
                        'Day': day,
                        'Relapse_Percentage': 0
                    })
        
        quarterly_df = pd.DataFrame(quarterly_stats)
        quarterly_long_df = pd.DataFrame(quarterly_long)
        
        # Graphique rechute courbes trimestrielles
        fig = go.Figure()
        
        quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        colors = ['#e74c3c', '#c0392b', '#a93226', '#922b21']  # Nuances de rouge
        
        for i, quarter in enumerate(quarters):
            quarter_data = quarterly_long_df[quarterly_long_df['Quarter'] == quarter]
            
            fig.add_trace(go.Scatter(
                x=quarter_data['Day'],
                y=quarter_data['Relapse_Percentage'],
                mode='lines+markers',
                name=quarter,
                line=dict(width=3, color=colors[i]),
                marker=dict(size=8),
                connectgaps=True
            ))
        
        fig.update_layout(
            title=f'Relapse Rates by Quarter - {selected_year}',
            xaxis_title='Days after transplantation',
            yaxis_title='Relapse Rate (%)',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(
                tickvals=[0, 100, 365], 
                ticktext=['D0', 'D100', 'D365'],
                range=[-10, 375]
            ),
            yaxis=dict(range=[0, None]),  # Commencer à 0%
            template='plotly_white'
        )
        
        return html.Div([
            # Ligne 1: Graphique pleine largeur
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig, style={'height': '450px'}, config={'responsive': True})
                ], width=12)
            ], className='mb-3'),
            
            # Ligne 2: 2 badges rechute par trimestre (4 trimestres × 2 badges = 8 badges)
            html.H6("Relapse Indicators by Quarter", className='text-center mb-3'),
            dbc.Row([
                dbc.Col([
                    create_rechute_quarter_badges_column(quarterly_df, q)
                ], width=3) for q in [1, 2, 3, 4]
            ], className='mb-3'),
            
            # Ligne 3: Tableau pleine largeur
            dbc.Row([
                dbc.Col([
                    html.H6("Quarterly Relapse Statistics", className='mb-3 text-center'),
                    create_wide_rechute_table(quarterly_df)
                ], width=12)
            ])
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error in relapse quarterly layout: {str(e)}", color="danger")

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

def create_rechute_curves_plot(result_long):
    """
    Graphique des courbes de rechute par année avec points à D0, D100, D365
    """
    try:
        fig = go.Figure()
        
        # Obtenir les années uniques
        years = sorted(result_long['Year'].unique())
        colors = px.colors.qualitative.Set1[:len(years)]
        
        for i, year in enumerate(years):
            year_data = result_long[result_long['Year'] == year].sort_values('j')
            
            fig.add_trace(go.Scatter(
                x=year_data['j'],
                y=year_data['pourcentage_rechute'],
                mode='lines+markers',
                name=f'{int(year)}',
                line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=8),
                connectgaps=True
            ))
        
        fig.update_layout(
            title='Relapse Rates by Year',
            xaxis_title='Days after transplantation',
            yaxis_title='Relapse Rate (%)',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            xaxis=dict(
                tickvals=[0, 100, 365], 
                ticktext=['D0', 'D100', 'D365'],
                range=[-10, 375]
            ),
            yaxis=dict(range=[0, None]),  # Commencer à 0%
            template='plotly_white'
        )
        
        return fig
    except Exception as e:
        print(f"ERROR in create_rechute_curves_plot: {str(e)}")
        return go.Figure()

def create_rechute_datatable(result_df):
    """DataTable pour rechute avec pourcentages D100 et D365"""
    try:
        table_data = []
        for _, row in result_df.iterrows():
            table_data.append({
                'Year': int(row['Year']),
                'Transplants': int(row['nb_greffe']),
                'Relapse_D100': int(row['rechute_j100']),
                'Relapse_D100_%': f"{row['100']:.1f}%",
                'Relapse_D365': int(row['rechute_j365']),
                'Relapse_D365_%': f"{row['365']:.1f}%"
            })
        
        return html.Div([
            html.H6("Relapse Statistics by year", className='mb-2'),
            dash_table.DataTable(
                data=table_data,
                columns=[
                    {"name": "Year", "id": "Year"},
                    {"name": "Transplants", "id": "Transplants"},
                    {"name": "Relapse D100", "id": "Relapse_D100"},
                    {"name": "Relapse D100 (%)", "id": "Relapse_D100_%"},
                    {"name": "Relapse D365", "id": "Relapse_D365"},
                    {"name": "Relapse D365 (%)", "id": "Relapse_D365_%"}
                ],
                style_cell={'textAlign': 'center', 'fontSize': '11px', 'padding': '6px', 'color': '#021F59'},
                style_header={'backgroundColor': '#021F59', 'color': 'white', 'fontWeight': 'bold', 'fontSize': '10px'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
                    {'if': {'column_id': ['Relapse_D100_%', 'Relapse_D365_%']}, 'backgroundColor': '#F2A594', 'fontWeight': 'bold'}
                ]
            )
        ])
    except Exception as e:
        print(f"ERROR in create_rechute_datatable: {str(e)}")
        return html.Div([dbc.Alert(f"Error creating relapse table: {str(e)}", color="danger")])

def create_rechute_badges(result_df, analysis_year):
    """Badges rechute pour année spécifique - 2 badges séparés (D100, D365)"""
    try:
        analysis_year = int(analysis_year)
        result_df = result_df.copy()
        result_df['Year'] = result_df['Year'].astype(int)
        
        year_data = result_df[result_df['Year'] == analysis_year]
        
        if year_data.empty:
            available_years = sorted(result_df['Year'].unique())
            if available_years:
                fallback_year = available_years[-1]
                year_data = result_df[result_df['Year'] == fallback_year]
                if not year_data.empty:
                    return create_rechute_badges_content(year_data, fallback_year, f"Using {fallback_year} (latest available)")
            
            return dbc.Alert(f"No data available for year {analysis_year}", color="warning")
        
        return create_rechute_badges_content(year_data, analysis_year)
        
    except Exception as e:
        return dbc.Alert(f"Error creating relapse badges: {str(e)}", color="danger")

def create_rechute_badges_content(year_data, analysis_year, subtitle=None):
    """Contenu des 2 badges rechute - D100, D365"""
    try:
        # Extraire les données pour l'année
        row = year_data.iloc[0]
        
        # Données pour chaque point temporel
        badges_data = [
            {
                'period': 'D100',
                'percentage': row['100'],
                'count': int(row['rechute_j100']),
                'color': '#e67e22'  # Orange foncé
            },
            {
                'period': 'D365',
                'percentage': row['365'], 
                'count': int(row['rechute_j365']),
                'color': '#e74c3c'  # Rouge
            }
        ]
        
        total_greffes = int(row['nb_greffe'])
        
        title = f"Relapse Indicators - {analysis_year}"
        if subtitle:
            title += f" ({subtitle})"
        
        # Créer les 2 badges
        badges = []
        for badge_data in badges_data:
            badge = dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{badge_data['percentage']:.1f}%", 
                                className="text-center mb-1", 
                                style={'color': badge_data['color'], 'fontSize': '20px'}),
                        html.P(f"Relapse {badge_data['period']}", 
                               className="text-center mb-1", 
                               style={'fontSize': '12px', 'fontWeight': 'bold'}),
                        html.P(f"({badge_data['count']}/{total_greffes})", 
                               className="text-center text-muted", 
                               style={'fontSize': '10px'})
                    ], className="py-2")
                ], color="danger", outline=True, style={'border-width': '1px'})
            ], width=6)
            badges.append(badge)
        
        return html.Div([
            html.H6(title, className='text-center mb-3'),
            dbc.Row(badges, className='g-2')
        ])
        
    except Exception as e:
        print(f"ERROR in create_rechute_badges_content: {str(e)}")
        return dbc.Alert(f"Error creating relapse badge content: {str(e)}", color="danger")

def create_wide_rechute_table(quarterly_df):
    """Table rechute pleine largeur"""
    return dash_table.DataTable(
        data=quarterly_df.to_dict('records'),
        columns=[
            {"name": "Quarter", "id": "Quarter"},
            {"name": "Total Patients", "id": "Total_Patients"},
            {"name": "Relapse D100", "id": "Relapse_D100"},
            {"name": "Relapse D365", "id": "Relapse_D365"},
            {"name": "Relapse % (1Y)", "id": "Relapse_Percentage", "type": "numeric", "format": {"specifier": ".1f"}}
        ],
        style_cell={
            'textAlign': 'center', 
            'fontSize': '12px', 
            'padding': '12px',
            'minWidth': '120px',
            'color': '#021F59'
        },
        style_header={
            'backgroundColor': '#021F59', 
            'color': 'white', 
            'fontWeight': 'bold',
            'fontSize': '12px',
            'padding': '12px'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
            {'if': {'column_id': ['Relapse_Percentage']}, 'backgroundColor': '#F2A594', 'fontWeight': 'bold'}
        ]
    )

def create_rechute_quarter_badge(quarterly_df, quarter_num, selected_year):
    """Badge unique rechute pour un trimestre"""
    quarter_data = quarterly_df[quarterly_df['Quarter_Num'] == quarter_num]
    
    if quarter_data.empty:
        return html.Div([
            html.H6(f"Q{quarter_num}", className='text-center mb-2'),
            dbc.Alert("No data", color="light")
        ])
    
    quarter_info = quarter_data.iloc[0]
    relapse_pct = quarter_info['Relapse_Percentage']
    relapse_count = quarter_info['Relapse_D365']
    total_patients = quarter_info['Total_Patients']
    
    return html.Div([
        html.H6(f"Q{quarter_num}", className='text-center mb-2', style={'color': '#021F59', 'fontWeight': 'bold'}),
        dbc.Card([
            dbc.CardBody([
                html.H4(f"{relapse_pct:.1f}%", className="text-center mb-1", style={'color': '#e74c3c'}),
                html.P("Relapse (1Y)", className="text-center mb-1", style={'fontSize': '12px', 'fontWeight': 'bold'}),
                html.P(f"({int(relapse_count)}/{int(total_patients)})", className="text-center text-muted", style={'fontSize': '10px'})
            ], className="py-3")
        ], color="danger", outline=True, style={'border-width': '1px'})
    ])

def create_rechute_quarter_badges_column(quarterly_df, quarter_num):
    """Colonne avec 2 badges rechute pour un trimestre (D100, D365)"""
    quarter_data = quarterly_df[quarterly_df['Quarter_Num'] == quarter_num]
    
    if quarter_data.empty:
        return html.Div([
            html.H6(f"Q{quarter_num}", className='text-center mb-2', style={'color': '#021F59', 'fontWeight': 'bold'}),
            dbc.Alert("No data", color="light")
        ])
    
    quarter_info = quarter_data.iloc[0]
    total_patients = quarter_info['Total_Patients']
    
    # Données pour les 2 badges
    badges_data = [
        {
            'period': 'D100',
            'percentage': quarter_info['Relapse_D100_%'],
            'count': quarter_info['Relapse_D100'],
            'color': '#e67e22'  # Orange foncé
        },
        {
            'period': 'D365',
            'percentage': quarter_info['Relapse_D365_%'],
            'count': quarter_info['Relapse_D365'],
            'color': '#e74c3c'  # Rouge
        }
    ]
    
    badges = []
    for badge_data in badges_data:
        badge = dbc.Card([
            dbc.CardBody([
                html.H5(f"{badge_data['percentage']:.1f}%", 
                        className="text-center mb-1", 
                        style={'color': badge_data['color'], 'fontSize': '14px'}),
                html.P(f"Relapse {badge_data['period']}", 
                       className="text-center mb-1", 
                       style={'fontSize': '10px', 'fontWeight': 'bold'}),
                html.P(f"({int(badge_data['count'])}/{int(total_patients)})", 
                       className="text-center text-muted", 
                       style={'fontSize': '8px'})
            ], className="py-1")
        ], color="danger", outline=True, style={'border-width': '1px'}, className='mb-1')
        badges.append(badge)
    
    return html.Div([
        html.H6(f"Q{quarter_num}", className='text-center mb-2', style={'color': '#021F59', 'fontWeight': 'bold'}),
        html.Div(badges)
    ])

def create_wide_rechute_table(quarterly_df):
    """Table rechute pleine largeur avec tous les détails"""
    return dash_table.DataTable(
        data=quarterly_df.to_dict('records'),
        columns=[
            {"name": "Quarter", "id": "Quarter"},
            {"name": "Total Patients", "id": "Total_Patients"},
            {"name": "Relapse D100", "id": "Relapse_D100"},
            {"name": "Relapse D100 (%)", "id": "Relapse_D100_%", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Relapse D365", "id": "Relapse_D365"},
            {"name": "Relapse D365 (%)", "id": "Relapse_D365_%", "type": "numeric", "format": {"specifier": ".1f"}}
        ],
        style_cell={
            'textAlign': 'center', 
            'fontSize': '11px', 
            'padding': '8px',
            'minWidth': '120px',
            'color': '#021F59'
        },
        style_header={
            'backgroundColor': '#021F59', 
            'color': 'white', 
            'fontWeight': 'bold',
            'fontSize': '10px',
            'padding': '8px'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
            {'if': {'column_id': ['Relapse_D100_%']}, 'backgroundColor': '#fadbd8', 'fontWeight': 'bold'},
            {'if': {'column_id': ['Relapse_D365_%']}, 'backgroundColor': '#F2A594', 'fontWeight': 'bold'}
        ]
    )

# =============================================================================
# Fonctions utilitaires
# =============================================================================

def get_variables_for_indicator(indicator):
    """
    Retourne les variables à analyser pour chaque indicateur
    
    Args:
        indicator (str): Code de l'indicateur sélectionné
        
    Returns:
        tuple: (variables_list, indicator_name)
    """
    variables_config = {
        'TRM': {
            'variables': [
                'Year',
                'Status Last Follow Up',
                'Death Cause',
                'Date Of Last Follow Up',
                'Treatment Date'
            ],
            'name': 'TRM (Toxicity-related mortality)'
        },
        'survie_globale': {
            'variables': [
                'Year',
                'Status Last Follow Up',
                'Date Of Last Follow Up',
                'Treatment Date',
            ],
            'name': 'Overall survival'
        },
        'prise_greffe': {
            'variables': [
                'Year',
                'Platelet Reconstitution',
                'Date Platelet Reconstitution',
                'Treatment Date'
            ],
            'name': 'Transplantation success'
        },
        'sortie_aplasie': {
            'variables': [
                'Year',
                'Anc Recovery',
                'Date Anc Recovery',
                'Treatment Date'
            ],
            'name': 'ANC Recovery'
        },
        'gvha': {
            'variables': [
                'Year',
                'First Agvhd Occurrence',
                'First aGvHD Maximum Score',
                'First Agvhd Occurrence Date',
                'Treatment Date'
            ],
            'name': 'Acute GVH'
        },
        'gvhc': {
            'variables': [
                'Year',
                'First Cgvhd Occurrence', 
                'First cGvHD Maximum NIH Score',
                'First Cgvhd Occurrence Date',
                'Treatment Date'
            ],
            'name': 'Chronic GVH'
        },
        'rechute': {
            'variables': [
                'Year',
                'First Relapse',
                'First Relapse Date',
                'Treatment Date'
            ],
            'name': 'Relapse'
        }
    }
    
    config = variables_config.get(indicator, {})
    return config.get('variables', []), config.get('name', 'Unknown indicator')

def analyze_missing_data(df, columns_to_check, patient_id_col='Long ID'):
    """
    Analyse les données manquantes pour les colonnes spécifiées
    
    Args:
        df (pd.DataFrame): Dataset des patients
        columns_to_check (list): Liste des colonnes à analyser
        patient_id_col (str): Nom de la colonne ID patient
        
    Returns:
        tuple: (missing_summary_df, detailed_missing_df)
    """
    # Vérifier que les colonnes existent
    existing_columns = [col for col in columns_to_check if col in df.columns]
    
    if not existing_columns:
        return pd.DataFrame(), pd.DataFrame()
    
    analysis_df = df[existing_columns + [patient_id_col]].copy()
    
    # Résumé par colonne
    missing_summary = []
    total_patients = len(analysis_df)
    
    for col in existing_columns:
        missing_count = analysis_df[col].isna().sum()
        missing_percentage = (missing_count / total_patients) * 100
        
        missing_summary.append({
            'Colonne': col,
            'Total patients': total_patients,
            'Données manquantes': missing_count,
            'Pourcentage manquant': round(missing_percentage, 2)
        })
    
    # Détail des patients avec données manquantes
    detailed_missing = []
    
    for _, row in analysis_df.iterrows():
        patient_id = row[patient_id_col]
        missing_columns = []
        
        for col in existing_columns:
            if pd.isna(row[col]):
                missing_columns.append(col)
        
        if missing_columns:
            detailed_missing.append({
                patient_id_col: patient_id,
                'Colonnes avec données manquantes': ', '.join(missing_columns),
                'Nombre de colonnes manquantes': len(missing_columns)
            })
    
    return pd.DataFrame(missing_summary), pd.DataFrame(detailed_missing)

def register_callbacks(app):

    # Callback pour mettre à jour le Store d'indicateur
    @app.callback(
        Output('selected-indicator-store', 'data'),
        Input('indicator-selection-sidebar', 'value'),
        prevent_initial_call=True
    )
    def update_indicator_store(indicator):
        return indicator
    
    # Callback pour mettre à jour le Store d'année
    @app.callback(
        Output('selected-year-store', 'data'),
        Input('year-selection-sidebar', 'value'),
        prevent_initial_call=True
    )
    def update_year_store(year):
        return year
    
    # Callback principal SANS écoute du trimestre
    @app.callback(
        Output('indicator-content', 'children'),
        [Input('current-page', 'data'),
         Input('data-store', 'data'),
         Input('indicators-main-tabs', 'value'),
         Input('selected-indicator-store', 'data'),
         Input('selected-year-store', 'data')],  # SUPPRIMÉ: selected-quarter-store
        prevent_initial_call=False
    )
    def update_indicator_content(current_page, data, active_tab, selected_indicator, selected_year):
        
        if current_page != 'Indicators':
            return dash.no_update
            
        if data is None:
            return dbc.Alert("Please load data to access indicators analysis.", color="warning")
        
        if not selected_indicator:
            return html.P("Select an indicator in the sidebar...")
        
        try:
            df = pd.DataFrame(data)
            
            if active_tab == 'global-view':
                return create_global_visualization_with_year(df, selected_indicator, selected_year)
            elif active_tab == 'quarterly-view':
                return create_quarterly_visualization(df, selected_indicator, selected_year)
            else:
                return dbc.Alert("Unknown tab selected", color="warning")
                
        except Exception as e:
            print(f"ERROR in update_indicator_content: {str(e)}")
            return dbc.Alert(f"Error processing indicator: {str(e)}", color="danger")

    @app.callback(
        Output('indicators-missing-subtitle', 'children'),
        [Input('selected-indicator-store', 'data'),
         Input('current-page', 'data')],
        prevent_initial_call=False
    )
    def update_missing_subtitle(selected_indicator, current_page):
        """Met à jour le sous-titre de la section données manquantes"""
        if current_page != 'Indicators' or not selected_indicator:
            return ""
        
        _, indicator_name = get_variables_for_indicator(selected_indicator)
        return f"for {indicator_name}"
    
    @app.callback(
        Output('indicators-missing-summary-table', 'children'),
        [Input('data-store', 'data'), 
         Input('current-page', 'data'),
         Input('selected-indicator-store', 'data'),
         Input('year-selection-sidebar', 'value')],
        prevent_initial_call=False
    )
    def indicators_missing_summary_callback(data, current_page, selected_indicator, selected_year):
        """Gère le tableau de résumé des données manquantes pour Indicators"""
        
        if current_page != 'Indicators' or not data:
            return html.Div("Waiting...", className='text-muted')
        
        if not selected_indicator:
            return dbc.Alert("Select an indicator to analyze missing data", color='info')
        
        try:
            df = pd.DataFrame(data)
            
            # Filtrer par année si spécifié (single year dropdown)
            if selected_year and 'Year' in df.columns:
                df = df[df['Year'] == selected_year]
            
            if df.empty:
                return html.Div('No data for the selected year', className='text-warning text-center')
            
            # Obtenir les variables spécifiques à l'indicateur sélectionné
            columns_to_analyze, indicator_name = get_variables_for_indicator(selected_indicator)
            
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert(f"No variables found for {indicator_name}", color='warning')
            
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
        [Output('indicators-missing-detail-table', 'children'),
         Output('export-missing-indicators-button', 'disabled')],
        [Input('data-store', 'data'), 
         Input('current-page', 'data'),
         Input('selected-indicator-store', 'data'),
         Input('year-selection-sidebar', 'value')],
        prevent_initial_call=False
    )
    def indicators_missing_detail_callback(data, current_page, selected_indicator, selected_year):
        """Gère le tableau détaillé des patients avec données manquantes pour Indicators"""
        
        if current_page != 'Indicators' or not data:
            return html.Div("Waiting...", className='text-muted'), True
        
        if not selected_indicator:
            return dbc.Alert("Select an indicator to analyze missing data", color='info'), True
        
        try:
            df = pd.DataFrame(data)
            
            # Filtrer par année si spécifié (single year dropdown)
            if selected_year and 'Year' in df.columns:
                df = df[df['Year'] == selected_year]
            
            if df.empty:
                return html.Div('No data for the selected year', className='text-warning text-center'), True
            
            # Obtenir les variables spécifiques à l'indicateur sélectionné
            columns_to_analyze, indicator_name = get_variables_for_indicator(selected_indicator)
            
            existing_columns = [col for col in columns_to_analyze if col in df.columns]
            
            if not existing_columns:
                return dbc.Alert(f"No variables found for {indicator_name}", color='warning'), True
            
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
                    'Nb missing': row['Nb missing'],
                    'Indicator': indicator_name  # Ajouter l'indicateur pour l'export
                })
            
            # Sauvegarder les données pour l'export
            app.server.missing_indicators_data = detailed_data
            app.server.current_indicator_name = indicator_name
            
            table_content = html.Div([
                dash_table.DataTable(
                    data=detailed_data,
                    columns=[
                        {"name": "Long ID", "id": "Long ID"},
                        {"name": "Missing variables", "id": "Missing columns"},
                        {"name": "Nb", "id": "Nb missing", "type": "numeric"}
                        # Ne pas afficher la colonne Indicator dans la table
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
        Output("download-missing-indicators-excel", "data"),
        Input("export-missing-indicators-button", "n_clicks"),
        prevent_initial_call=True
    )
    def export_missing_indicators_excel(n_clicks):
        """Gère l'export csv des patients avec données manquantes pour Indicators"""
        if n_clicks is None:
            return dash.no_update
        
        try:
            # Récupérer les données stockées
            if hasattr(app.server, 'missing_indicators_data') and app.server.missing_indicators_data:
                missing_df = pd.DataFrame(app.server.missing_indicators_data)
                
                # Récupérer le nom de l'indicateur
                indicator_name = getattr(app.server, 'current_indicator_name', 'unknown_indicator')
                indicator_slug = indicator_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
                
                # Générer un nom de fichier avec la date et l'indicateur
                from datetime import datetime
                current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"indicators_{indicator_slug}_missing_data_{current_date}.xlsx"
                
                return dcc.send_data_frame(
                    missing_df.to_excel, 
                    filename=filename,
                    index=False
                )
            else:
                return dash.no_update
                
        except Exception as e:
            print(f"Error during Excel export Indicators: {e}")
            return dash.no_update
        
def process_gvha_data(df):
    """
    Traite les données pour calculer les indicateurs de GVH aiguë
    """
    # Vérifier les colonnes nécessaires
    required_cols = ['Year', 'First Agvhd Occurrence Date', 'Treatment Date', 'First aGvHD Maximum Score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing columns for acute GVH analysis: {missing_cols}")
    
    # Créer une copie et calculer le délai
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
    result_combined = result_combined.fillna(0)
    
    # Calculer les pourcentages
    result_combined['pourcentage_gvh_aigue_2_4'] = (result_combined['nb_gvh_aigue_2_4'] / result_combined['nb_greffe']) * 100
    result_combined['pourcentage_gvh_aigue_3_4'] = (result_combined['nb_gvh_aigue_3_4'] / result_combined['nb_greffe']) * 100
    
    return result_combined, grade_counts

def create_gvha_barplot(result_combined, grade_counts):
    """
    Crée le barplot pour afficher les statistiques GVH aiguë par année
    """
    fig = go.Figure()
    
    # Couleurs pour chaque grade
    colors = {
        'Grade 2': '#3498db',  # Bleu
        'Grade 3': '#f39c12',  # Orange
        'Grade 4': '#e74c3c'   # Rouge
    }
    
    # Ajouter une barre pour chaque grade
    for grade in ['Grade 2', 'Grade 3', 'Grade 4']:
        if grade in grade_counts.columns:
            fig.add_trace(go.Bar(
                name=grade,
                x=grade_counts['Year'],
                y=grade_counts[grade],
                marker_color=colors.get(grade, '#95a5a6')
            ))
    
    fig.update_layout(
        title='Distribution of Acute GVH Grades by Year',
        xaxis_title='Year',
        yaxis_title='Number of patients',
        barmode='stack',
        height=500,
        font=dict(family='Arial, sans-serif', size=12),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Améliorer l'apparence
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.2)')
    
    return fig

def create_gvha_datatable(result_combined):
    """
    Crée la DataTable pour afficher les statistiques GVH aiguë par année
    """
    from dash import dash_table
    
    # Préparer les données pour la table
    table_data = []
    for _, row in result_combined.iterrows():
        table_data.append({
            'Year': int(row['Year']),
            'Nb transplants': int(row['nb_greffe']),
            'aGVH 2-4 (n)': int(row['nb_gvh_aigue_2_4']),
            'aGVH 2-4 (%)': f"{row['pourcentage_gvh_aigue_2_4']:.1f}%",
            'aGVH 3-4 (n)': int(row['nb_gvh_aigue_3_4']),
            'aGVH 3-4 (%)': f"{row['pourcentage_gvh_aigue_3_4']:.1f}%"
        })
    
    return html.Div([
        html.H6("Statistics by year", className='mb-2'),
        dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Year", "id": "Year"},
                {"name": "Transplants", "id": "Nb transplants"},
                {"name": "aGVH 2-4 (n)", "id": "aGVH 2-4 (n)"},
                {"name": "aGVH 2-4 (%)", "id": "aGVH 2-4 (%)"},
                {"name": "aGVH 3-4 (n)", "id": "aGVH 3-4 (n)"},
                {"name": "aGVH 3-4 (%)", "id": "aGVH 3-4 (%)"}
            ],
            style_table={'height': '250px', 'overflowY': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '8px',
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

def create_gvha_badges(result_combined, analysis_year):
    try:
        # S'assurer que analysis_year est de type int
        analysis_year = int(analysis_year)
        
        # S'assurer que la colonne Year est de type int
        result_combined = result_combined.copy()
        result_combined['Year'] = result_combined['Year'].astype(int)
        
        # Obtenir les données pour l'année spécifiée
        year_data = result_combined[result_combined['Year'] == analysis_year]
        
        if year_data.empty:
            available_years = sorted(result_combined['Year'].unique())
            print(f"ERROR Badges: No data for year {analysis_year}, available: {available_years}")
            
            # Essayer avec la dernière année disponible
            if available_years:
                fallback_year = available_years[-1]
                year_data = result_combined[result_combined['Year'] == fallback_year]
                if not year_data.empty:
                    return create_gvha_badges_content(year_data, fallback_year, f"Using {fallback_year} (latest available)")
            
            return dbc.Alert(
                f"No data available for year {analysis_year}. Available years: {available_years}", 
                color="warning"
            )
        
        return create_gvha_badges_content(year_data, analysis_year)
        
    except Exception as e:
        print(f"ERROR in create_gvha_badges: {str(e)}")
        return dbc.Alert(f"Error creating badges: {str(e)}", color="danger")

def create_gvha_badges_content(year_data, analysis_year, subtitle=None):
    """
    Crée le contenu des badges à partir des données d'une année
    """
    # Extraire les valeurs
    pct_2_4 = year_data['pourcentage_gvh_aigue_2_4'].iloc[0]
    pct_3_4 = year_data['pourcentage_gvh_aigue_3_4'].iloc[0]
    nb_2_4 = int(year_data['nb_gvh_aigue_2_4'].iloc[0])
    nb_3_4 = int(year_data['nb_gvh_aigue_3_4'].iloc[0])
    total_greffes = int(year_data['nb_greffe'].iloc[0])
    
    title = f"Acute GVH indicators - {analysis_year}"
    if subtitle:
        title += f" ({subtitle})"
    
    return html.Div([
        html.H6(title, className='text-center mb-3'),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{pct_2_4:.1f}%", className="text-center mb-2", style={'color': '#2c3e50'}),
                        html.P("Acute GVH grades 2-4", className="text-center mb-1", style={'fontSize': '14px'}),
                        html.P(f"({nb_2_4}/{total_greffes})", className="text-center text-muted", style={'fontSize': '12px'})
                    ], className="py-3")
                ], color="primary", outline=True, style={'border-width': '2px'})
            ], width=12, className="mb-2"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{pct_3_4:.1f}%", className="text-center mb-2", style={'color': '#c0392b'}),
                        html.P("Acute GVH grades 3-4", className="text-center mb-1", style={'fontSize': '14px'}),
                        html.P(f"({nb_3_4}/{total_greffes})", className="text-center text-muted", style={'fontSize': '12px'})
                    ], className="py-3")
                ], color="danger", outline=True, style={'border-width': '2px'})
            ], width=12)
        ])
    ], className="mb-3")

def create_gvha_visualization(result_combined, grade_counts, selected_year):
    """Visualisation GVH aiguë avec année sélectionnée pour les badges"""
    
    # Utiliser l'année sélectionnée ou la dernière disponible
    analysis_year = selected_year if selected_year else result_combined['Year'].max()
    
    return dbc.Row([
        # Colonne gauche : Graphique
        dbc.Col([
            dcc.Graph(
                figure=create_gvha_barplot(result_combined, grade_counts),
                config={'responsive': True}
            )
        ], width=7),
        
        # Colonne droite : DataTable et badges
        dbc.Col([
            create_gvha_datatable(result_combined),
            html.Hr(className='my-3'),
            create_gvha_badges(result_combined, analysis_year)
        ], width=5)
    ])
    
def create_global_visualization_with_year(df, indicator, selected_year):
    """
    Crée la visualisation globale en passant l'année sélectionnée pour les badges
    """
    try:
        # Déterminer l'année à utiliser pour les badges
        if selected_year is None:
            # Si pas d'année sélectionnée, utiliser la dernière année disponible
            if 'Year' in df.columns:
                analysis_year = df['Year'].max()
            else:
                analysis_year = 2024  # Année par défaut
        else:
            analysis_year = int(selected_year)
        
        if indicator == 'gvha':
            return create_gvha_global_visualization(df, analysis_year)
        elif indicator == 'TRM':
            return create_trm_global_visualization(df, analysis_year)
        elif indicator == 'survie_globale':
            return create_survie_global_visualization(df, analysis_year)
        elif indicator == 'prise_greffe':
            return create_prise_greffe_global_visualization(df, analysis_year)
        elif indicator == 'sortie_aplasie':
            return create_sortie_aplasie_global_visualization(df, analysis_year)
        elif indicator == 'gvhc':
            return create_gvhc_global_visualization(df, analysis_year)
        elif indicator == 'rechute':
            return create_rechute_global_visualization(df, analysis_year)
        else:
            return dbc.Alert(f"Global visualization for '{indicator}' under development", color="info")
            
    except Exception as e:
        print(f"ERROR in create_global_visualization_with_year: {str(e)}")
        return dbc.Alert(f"Error creating global visualization: {str(e)}", color="danger")

def create_gvha_global_visualization(df, analysis_year):
    try:
        # Traiter les données pour toutes les années
        result_combined, grade_counts = process_gvha_data(df)

        available_years = result_combined['Year'].unique()
        
        # S'assurer que les types correspondent
        result_combined['Year'] = result_combined['Year'].astype(int)
        analysis_year = int(analysis_year)
        
        # Vérifier que l'année existe
        if analysis_year not in result_combined['Year'].values:
            print(f"WARNING: Year {analysis_year} not found, using {available_years.max()}")
            analysis_year = int(available_years.max())
        
        # Calculer les indicateurs globaux
        total_patients = result_combined['nb_greffe'].sum()
        total_gvh_2_4 = result_combined['nb_gvh_aigue_2_4'].sum()
        total_gvh_3_4 = result_combined['nb_gvh_aigue_3_4'].sum()
        
        pct_global_2_4 = (total_gvh_2_4 / total_patients * 100) if total_patients > 0 else 0
        pct_global_3_4 = (total_gvh_3_4 / total_patients * 100) if total_patients > 0 else 0
        
        return dbc.Row([
            # Colonne gauche : Graphique global (60%)
            dbc.Col([
                dcc.Graph(
                    figure=create_gvha_barplot(result_combined, grade_counts),
                    style={'height': '600px'},
                    config={'responsive': True}
                )
            ], width=7),
            # Colonne droite : DataTable et badges pour année spécifique (40%)
            dbc.Col([
                # DataTable pour toutes les années
                create_gvha_datatable(result_combined),
                html.Hr(className='my-3'),
                # Badges pour l'année spécifique (CORRECTION ICI)
                create_gvha_badges(result_combined, analysis_year)
            ], width=5)
        ])
        
    except Exception as e:
        print(f"ERROR in create_gvha_global_visualization: {str(e)}")
        return dbc.Alert(f"Error in global GVH visualization: {str(e)}", color="danger")

def create_quarterly_visualization(df, indicator, selected_year):
    """
    Visualisation trimestrielle complète pour tous les indicateurs
    """
    try:
        if not selected_year:
            return dbc.Alert("Please select a year for quarterly analysis", color="warning")
        
        # Ajouter la colonne trimestre si elle n'existe pas
        df_with_quarters = add_quarter_column(df)
        
        # Filtrer les données pour l'année sélectionnée
        year_data = df_with_quarters[df_with_quarters['Year'] == selected_year].copy()
        
        if year_data.empty:
            return dbc.Alert(f"No data available for year {selected_year}", color="warning")
        
        # Dispatcher vers la fonction appropriée selon l'indicateur
        if indicator == 'gvha':
            return create_gvha_quarterly_visualization(year_data, selected_year)
        elif indicator == 'TRM':
            return create_trm_quarterly_visualization(year_data, selected_year)
        elif indicator == 'survie_globale':
            return create_survie_quarterly_visualization(year_data, selected_year)
        elif indicator == 'prise_greffe':
            return create_prise_greffe_quarterly_visualization(year_data, selected_year)
        elif indicator == 'sortie_aplasie':
            return create_sortie_aplasie_quarterly_visualization(year_data, selected_year)
        elif indicator == 'gvhc':
            return create_gvhc_quarterly_visualization(year_data, selected_year)
        elif indicator == 'rechute':
            return create_rechute_quarterly_visualization(year_data, selected_year)
        else:
            return dbc.Alert(f"Quarterly visualization for '{indicator}' not yet implemented", color="info")
            
    except Exception as e:
        print(f"ERROR in create_quarterly_visualization: {str(e)}")
        return dbc.Alert(f"Error creating quarterly visualization: {str(e)}", color="danger")

def add_quarter_column(df):
    """
    Ajoute une colonne Quarter basée sur la date de traitement
    """
    df = df.copy()
    
    if 'Treatment Date' in df.columns:
        # Convertir en datetime
        df['Treatment Date'] = pd.to_datetime(df['Treatment Date'], errors='coerce')
        # Extraire le trimestre
        df['Quarter'] = df['Treatment Date'].dt.quarter
    else:
        # Si pas de Treatment Date, distribuer aléatoirement (pour test)
        print("WARNING: No Treatment Date column found, using random quarters for testing")
        df['Quarter'] = np.random.randint(1, 5, size=len(df))
    
    return df

def create_quarterly_badges_gvha(quarterly_df, selected_quarter, selected_year):
    """
    Crée les badges pour le trimestre sélectionné
    """
    try:
        # Filtrer les données pour le trimestre sélectionné
        quarter_data = quarterly_df[quarterly_df['Quarter_Num'] == selected_quarter]
        
        if quarter_data.empty:
            return dbc.Alert(f"No data for Q{selected_quarter}", color="warning")
        
        # Extraire les valeurs
        quarter_info = quarter_data.iloc[0]
        pct_2_4 = quarter_info['Pct_GVH_2_4']
        pct_3_4 = quarter_info['Pct_GVH_3_4']
        nb_2_4 = quarter_info['GVH_2_4']
        nb_3_4 = quarter_info['GVH_3_4']
        total_patients = quarter_info['Total_Patients']
        
        return html.Div([
            html.H6(f"Q{selected_quarter} {selected_year} - Acute GVH Indicators", className='text-center mb-3'),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3(f"{pct_2_4:.1f}%", className="text-center mb-2", style={'color': '#2c3e50'}),
                            html.P("Acute GVH grades 2-4", className="text-center mb-1", style={'fontSize': '14px'}),
                            html.P(f"({int(nb_2_4)}/{int(total_patients)})", className="text-center text-muted", style={'fontSize': '12px'})
                        ], className="py-3")
                    ], color="primary", outline=True, style={'border-width': '2px'})
                ], width=12, className="mb-2"),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3(f"{pct_3_4:.1f}%", className="text-center mb-2", style={'color': '#c0392b'}),
                            html.P("Acute GVH grades 3-4", className="text-center mb-1", style={'fontSize': '14px'}),
                            html.P(f"({int(nb_3_4)}/{int(total_patients)})", className="text-center text-muted", style={'fontSize': '12px'})
                        ], className="py-3")
                    ], color="danger", outline=True, style={'border-width': '2px'})
                ], width=12)
            ])
        ], className="mb-3")
        
    except Exception as e:
        print(f"ERROR in create_quarterly_badges_gvha: {str(e)}")
        return dbc.Alert(f"Error creating quarterly badges: {str(e)}", color="danger")

def create_quarterly_stacked_barplot(quarterly_grades_df, selected_year):
    """
    Crée le barplot empilé par grade pour la vue trimestrielle
    """
    fig = go.Figure()
    
    # Couleurs pour chaque grade (mêmes que la vue globale)
    colors = {
        'Grade 2': '#3498db',  # Bleu
        'Grade 3': '#f39c12',  # Orange
        'Grade 4': '#e74c3c'   # Rouge
    }
    
    # Ajouter une barre empilée pour chaque grade
    for grade in ['Grade 2', 'Grade 3', 'Grade 4']:
        fig.add_trace(go.Bar(
            name=grade,
            x=quarterly_grades_df['Quarter'],
            y=quarterly_grades_df[grade],
            marker_color=colors[grade],
            # Ajouter les valeurs sur les barres si > 0
            text=[str(val) if val > 0 else '' for val in quarterly_grades_df[grade]],
            textposition='inside',
            textfont=dict(color='white', size=10)
        ))
    
    fig.update_layout(
        title=f'Distribution of Acute GVH Grades by Quarter - {selected_year}',
        xaxis_title='Quarter',
        yaxis_title='Number of patients',
        barmode='stack',  # IMPORTANT: Mode empilé
        height=500,
        font=dict(family='Arial, sans-serif', size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    # Améliorer l'apparence
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.2)')
    
    return fig

def create_wide_quarterly_table(quarterly_df):
    """
    Crée un tableau pleine largeur pour les statistiques trimestrielles
    """
    return dash_table.DataTable(
        data=quarterly_df.to_dict('records'),
        columns=[
            {"name": "Quarter", "id": "Quarter"},
            {"name": "Total Patients", "id": "Total_Patients"},
            {"name": "Grade 2", "id": "Grade_2"},
            {"name": "Grade 3", "id": "Grade_3"}, 
            {"name": "Grade 4", "id": "Grade_4"},
            {"name": "Total aGVH 2-4", "id": "GVH_2_4"},
            {"name": "aGVH 2-4 (%)", "id": "Pct_GVH_2_4", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Total aGVH 3-4", "id": "GVH_3_4"},
            {"name": "aGVH 3-4 (%)", "id": "Pct_GVH_3_4", "type": "numeric", "format": {"specifier": ".1f"}}
        ],
        style_cell={
            'textAlign': 'center', 
            'fontSize': '12px', 
            'padding': '12px',
            'minWidth': '100px',
            'color': '#021F59'
        },
        style_header={
            'backgroundColor': '#021F59', 
            'color': 'white', 
            'fontWeight': 'bold',
            'fontSize': '12px',
            'padding': '12px'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#F2E9DF'},
            {'if': {'column_id': ['Grade_2', 'Grade_3', 'Grade_4']}, 'backgroundColor': '#fff3cd'},
            {'if': {'column_id': ['Pct_GVH_2_4', 'Pct_GVH_3_4']}, 'backgroundColor': 'rgba(119, 172, 242, 0.2)', 'fontWeight': 'bold'}
        ],
        style_table={
            'overflowX': 'auto'  # Scroll horizontal si nécessaire
        }
    )

def create_quarter_badges_column(quarterly_df, quarter_num, selected_year):
    """
    Crée une colonne de 2 badges pour un trimestre donné
    """
    try:
        # Filtrer les données pour ce trimestre
        quarter_data = quarterly_df[quarterly_df['Quarter_Num'] == quarter_num]
        
        if quarter_data.empty:
            return html.Div([
                html.H6(f"Q{quarter_num}", className='text-center mb-2'),
                dbc.Alert("No data", color="light", className='text-center')
            ])
        
        # Extraire les valeurs
        quarter_info = quarter_data.iloc[0]
        pct_2_4 = quarter_info['Pct_GVH_2_4']
        pct_3_4 = quarter_info['Pct_GVH_3_4']
        nb_2_4 = quarter_info['GVH_2_4']
        nb_3_4 = quarter_info['GVH_3_4']
        total_patients = quarter_info['Total_Patients']
        
        return html.Div([
            # Titre du trimestre
            html.H6(f"Q{quarter_num}", className='text-center mb-2', style={'color': '#021F59', 'fontWeight': 'bold'}),
            
            # Badge GVH 2-4
            dbc.Card([
                dbc.CardBody([
                    html.H5(f"{pct_2_4:.1f}%", className="text-center mb-1", style={'color': '#2c3e50', 'fontSize': '16px'}),
                    html.P("aGVH 2-4", className="text-center mb-1", style={'fontSize': '11px', 'margin': '0'}),
                    html.P(f"({int(nb_2_4)}/{int(total_patients)})", className="text-center text-muted", style={'fontSize': '9px', 'margin': '0'})
                ], className="py-2")
            ], color="primary", outline=True, style={'border-width': '1px'}, className='mb-2'),
            
            # Badge GVH 3-4
            dbc.Card([
                dbc.CardBody([
                    html.H5(f"{pct_3_4:.1f}%", className="text-center mb-1", style={'color': '#c0392b', 'fontSize': '16px'}),
                    html.P("aGVH 3-4", className="text-center mb-1", style={'fontSize': '11px', 'margin': '0'}),
                    html.P(f"({int(nb_3_4)}/{int(total_patients)})", className="text-center text-muted", style={'fontSize': '9px', 'margin': '0'})
                ], className="py-2")
            ], color="danger", outline=True, style={'border-width': '1px'})
        ])
        
    except Exception as e:
        print(f"ERROR in create_quarter_badges_column Q{quarter_num}: {str(e)}")
        return html.Div([
            html.H6(f"Q{quarter_num}", className='text-center mb-2'),
            dbc.Alert(f"Error: {str(e)}", color="danger")
        ])