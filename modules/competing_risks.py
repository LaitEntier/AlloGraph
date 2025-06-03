import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

class CompetingRisksAnalyzer:
    """
    Classe pour l'analyse des risques compétitifs avec événements personnalisables
    """
    
    def __init__(self, data, reference_date_col):
        """
        Initialise l'analyseur
        
        Parameters:
        - data: DataFrame avec les données
        - reference_date_col: nom de la colonne de date de référence (ex: 'Treatment Date')
        """
        self.data = data.copy()
        self.reference_date_col = reference_date_col
        self.data[reference_date_col] = pd.to_datetime(self.data[reference_date_col])
        
    def calculate_cumulative_incidence(self, 
                                     events_config, 
                                     followup_config,
                                     max_days=100,
                                     death_as_competing=True):
        """
        Calcule l'incidence cumulée avec analyse de risques compétitifs généralisée
        
        Parameters:
        - events_config: dict des événements d'intérêt
          Format: {
              'event_name': {
                  'occurrence_col': 'nom_colonne_occurrence',  # colonne Yes/No
                  'date_col': 'nom_colonne_date',              # colonne date événement
                  'label': 'Label pour affichage',             # optionnel
                  'color': 'couleur'                           # optionnel
              }
          }
        - followup_config: dict pour le suivi
          Format: {
              'status_col': 'nom_colonne_statut',       # colonne statut (Dead/Alive)
              'date_col': 'nom_colonne_date_followup',  # colonne date dernier suivi
              'death_value': 'Dead'                     # valeur indiquant décès
          }
        - max_days: nombre maximum de jours à analyser
        - death_as_competing: si True, inclut le décès comme risque compétitif
        
        Returns:
        - DataFrame avec les incidences cumulées par jour
        - DataFrame des données traitées
        """
        
        df = self.data.copy()
        
        # Convertir les dates
        df[followup_config['date_col']] = pd.to_datetime(df[followup_config['date_col']])
        
        for event_name, config in events_config.items():
            df[config['date_col']] = pd.to_datetime(df[config['date_col']])
        
        # Calculer les temps d'événement
        df['time_to_last_followup'] = (df[followup_config['date_col']] - df[self.reference_date_col]).dt.days
        
        for event_name, config in events_config.items():
            time_col = f'time_to_{event_name}'
            df[time_col] = (df[config['date_col']] - df[self.reference_date_col]).dt.days
        
        # Déterminer l'événement et le temps pour chaque patient
        events = []
        times = []
        
        for idx, row in df.iterrows():
            patient_events = []
            
            # Vérifier chaque événement d'intérêt
            for event_name, config in events_config.items():
                time_col = f'time_to_{event_name}'
                if (pd.notna(row[time_col]) and 
                    row[config['occurrence_col']] == 'Yes' and 
                    row[time_col] <= max_days):
                    patient_events.append((event_name, row[time_col]))
            
            # Vérifier le décès si configuré comme risque compétitif
            if death_as_competing:
                if (row[followup_config['status_col']] == followup_config['death_value'] and 
                    row['time_to_last_followup'] <= max_days):
                    # Vérifier si décès avant tout autre événement
                    death_before_events = True
                    for event_name, config in events_config.items():
                        time_col = f'time_to_{event_name}'
                        if (pd.notna(row[time_col]) and 
                            row[time_col] <= row['time_to_last_followup']):
                            death_before_events = False
                            break
                    
                    if death_before_events:
                        patient_events.append(('Décès', row['time_to_last_followup']))
            
            # Prendre le premier événement (temps le plus court)
            if patient_events:
                first_event = min(patient_events, key=lambda x: x[1])
                events.append(first_event[0])
                times.append(first_event[1])
            else:
                # Censuré
                events.append('Censuré')
                times.append(min(row['time_to_last_followup'], max_days))
        
        df['event_type'] = events
        df['event_time'] = times
        
        # Calculer les incidences cumulées
        days = np.arange(0, max_days + 1)
        n_at_risk = []
        event_counts = {event_name: [] for event_name in events_config.keys()}
        if death_as_competing:
            event_counts['Décès'] = []
        event_counts['Censuré'] = []
        
        for day in days:
            # Patients encore à risque au début du jour
            at_risk = df[df['event_time'] >= day].shape[0]
            n_at_risk.append(at_risk)
            
            # Événements ce jour-là
            day_events = df[df['event_time'] == day]
            
            for event_name in event_counts.keys():
                count = day_events[day_events['event_type'] == event_name].shape[0]
                event_counts[event_name].append(count)
        
        # Calculer les incidences cumulées selon Kalbfleisch-Prentice
        cum_incidences = {event_name: np.zeros(len(days)) for event_name in events_config.keys()}
        if death_as_competing:
            cum_incidences['Décès'] = np.zeros(len(days))
        
        survival = np.ones(len(days))  # Probabilité de survie sans événement
        
        for i in range(1, len(days)):
            if n_at_risk[i-1] > 0:
                # Calculer le total des événements ce jour
                total_events = sum(event_counts[event][i-1] for event in event_counts.keys() 
                                 if event != 'Censuré')
                
                # Probabilité de survie sans événement ce jour
                daily_survival = (n_at_risk[i-1] - total_events) / n_at_risk[i-1]
                
                # Hazard spécifique pour chaque événement
                for event_name in cum_incidences.keys():
                    hazard = event_counts[event_name][i-1] / n_at_risk[i-1] if n_at_risk[i-1] > 0 else 0
                    cum_incidences[event_name][i] = cum_incidences[event_name][i-1] + survival[i-1] * hazard
                
                # Mise à jour de la survie
                survival[i] = survival[i-1] * daily_survival
            else:
                for event_name in cum_incidences.keys():
                    cum_incidences[event_name][i] = cum_incidences[event_name][i-1]
                survival[i] = survival[i-1]
        
        # Créer le DataFrame de résultats
        results_data = {
            'jour': days,
            'n_at_risk': n_at_risk,
            'survie_sans_evenement': survival
        }
        
        # Ajouter les incidences cumulées
        for event_name in cum_incidences.keys():
            results_data[f'incidence_cumulative_{event_name.lower()}'] = cum_incidences[event_name]
        
        # Ajouter les comptes d'événements
        for event_name in event_counts.keys():
            results_data[f'{event_name.lower()}_events'] = event_counts[event_name]
        
        results_df = pd.DataFrame(results_data)
        
        return results_df, df
    
    def create_competing_risks_plot(self, results_df, patient_data, events_config, 
                                   title="Analyse de Risques Compétitifs", 
                                   colors=None):
        """
        Crée un graphique d'incidences cumulées avec risques compétitifs (style ggcompetingrisks)
        
        Parameters:
        - results_df: DataFrame des résultats
        - patient_data: DataFrame des données patients traitées
        - events_config: configuration des événements
        - title: titre du graphique
        - colors: dict des couleurs par événement
        """
        
        if colors is None:
            default_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
            colors = {}
            all_events = list(events_config.keys()) + ['Décès']
            for i, event in enumerate(all_events):
                colors[event] = default_colors[i % len(default_colors)]
        
        # Créer les sous-graphiques
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Incidences Cumulées (Empilées)', 'Nombre de Patients à Risque', 
                           'Événements par Jour', 'Répartition des Événements'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"type": "pie"}]]
        )
        
        # Préparer les données pour l'empilement
        event_names = []
        cumulative_data = []
        
        # Collecter tous les événements
        for event_name in events_config.keys():
            col_name = f'incidence_cumulative_{event_name.lower()}'
            if col_name in results_df.columns:
                event_names.append(event_name)
                cumulative_data.append(results_df[col_name] * 100)
        
        # Ajouter le décès si présent
        if 'incidence_cumulative_décès' in results_df.columns:
            event_names.append('Décès')
            cumulative_data.append(results_df['incidence_cumulative_décès'] * 100)
        
        # Créer les courbes empilées (style area plot)
        y_lower = np.zeros(len(results_df))
        
        for i, (event_name, y_data) in enumerate(zip(event_names, cumulative_data)):
            y_upper = y_lower + y_data
            
            # Obtenir la configuration et couleur
            if event_name in events_config:
                label = events_config[event_name].get('label', event_name)
                color = colors.get(event_name, events_config[event_name].get('color', 'blue'))
            else:
                label = event_name
                color = colors.get(event_name, 'black')
            
            # Ajouter l'aire empilée
            fig.add_trace(
                go.Scatter(
                    x=results_df['jour'],
                    y=y_upper,
                    fill='tonexty' if i > 0 else 'tozeroy',
                    mode='lines',
                    name=label,
                    line=dict(color=color, width=2),
                    fillcolor=color,
                    opacity=0.7,
                    hovertemplate=f'Jour %{{x}}<br>Incidence {label}: %{{customdata:.1f}}%<br>Total cumulé: %{{y:.1f}}%<extra></extra>',
                    customdata=y_data
                ),
                row=1, col=1
            )
            
            y_lower = y_upper
        
        # Ajouter la ligne de survie sans événement (optionnel)
        survival_pct = results_df['survie_sans_evenement'] * 100
        total_events = y_lower  # somme de tous les événements
        
        fig.add_trace(
            go.Scatter(
                x=results_df['jour'],
                y=survival_pct + total_events,  # pour atteindre 100%
                fill='tonexty',
                mode='lines',
                name='Sans événement',
                line=dict(color='lightgray', width=1),
                fillcolor='lightgray',
                opacity=0.3,
                hovertemplate='Jour %{x}<br>Sans événement: %{customdata:.1f}%<br>Total: 100%<extra></extra>',
                customdata=survival_pct
            ),
            row=1, col=1
        )
        
        # Mise en forme du graphique principal
        fig.update_xaxes(title_text="Jours post-référence", row=1, col=1)
        fig.update_yaxes(title_text="Incidence Cumulative (%)", row=1, col=1, range=[0, 100])
        
        # Ajouter une ligne à 100% pour référence
        fig.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.3, row=1, col=1)
        
        # Graphique : Patients à risque
        fig.add_trace(
            go.Scatter(
                x=results_df['jour'],
                y=results_df['n_at_risk'],
                mode='lines+markers',
                name='Patients à risque',
                line=dict(color='green'),
                marker=dict(size=4),
                showlegend=False,
                hovertemplate='Jour %{x}<br>Patients à risque: %{y}<extra></extra>'
            ),
            row=1, col=2
        )
        
        # Graphique : Événements par jour (empilé)
        for event_name in events_config.keys():
            event_col = f'{event_name.lower()}_events'
            if event_col in results_df.columns:
                fig.add_trace(
                    go.Bar(
                        x=results_df['jour'],
                        y=results_df[event_col],
                        name=f'{event_name}/jour',
                        marker_color=colors.get(event_name, 'blue'),
                        opacity=0.7,
                        showlegend=False
                    ),
                    row=2, col=1
                )
        
        if 'décès_events' in results_df.columns:
            fig.add_trace(
                go.Bar(
                    x=results_df['jour'],
                    y=results_df['décès_events'],
                    name='Décès/jour',
                    marker_color=colors.get('Décès', 'black'),
                    opacity=0.7,
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Graphique circulaire : Répartition des événements
        event_counts = patient_data['event_type'].value_counts()
        pie_colors = [colors.get(event, 'gray') for event in event_counts.index]
        
        fig.add_trace(
            go.Pie(
                labels=event_counts.index,
                values=event_counts.values,
                name="Répartition",
                showlegend=False,
                marker_colors=pie_colors
            ),
            row=2, col=2
        )
        
        # Mise en forme
        fig.update_xaxes(title_text="Jours post-référence", row=1, col=1)
        fig.update_yaxes(title_text="Incidence Cumulative (%)", row=1, col=1)
        fig.update_xaxes(title_text="Jours post-référence", row=1, col=2)
        fig.update_yaxes(title_text="Nombre de patients", row=1, col=2)
        fig.update_xaxes(title_text="Jours post-référence", row=2, col=1)
        fig.update_yaxes(title_text="Nombre d'événements", row=2, col=1)
        
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                font=dict(size=16)
            ),
            height=800,
            showlegend=True,
            legend=dict(x=0.02, y=0.98)
        )
        
        return fig