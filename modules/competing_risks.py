import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

from modules.data_processing import _to_datetime_fast

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
        self.data[reference_date_col] = _to_datetime_fast(self.data[reference_date_col])
        
    def create_competing_risks_plot_original(self, results_df, patient_data, events_config, 
                                           title="Analyse de Risques Compétitifs", 
                                           colors=None):
        """
        Version originale de create_competing_risks_plot pour maintenir la compatibilité
        """
        if colors is None:
            default_colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
            colors = {}
            all_events = list(events_config.keys()) + ['Décès']
            for i, event in enumerate(all_events):
                colors[event] = default_colors[i % len(default_colors)]
        
        # Créer la figure principale
        fig = go.Figure()
        
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
                color = colors.get(event_name, events_config[event_name].get('color', '#3498db'))
            else:
                label = event_name
                color = colors.get(event_name, '#2c3e50')
            
            # Ajouter l'aire empilée
            fig.add_trace(
                go.Scatter(
                    x=results_df['jour'],  # Utiliser 'jour' au lieu de 'Day'
                    y=y_upper,
                    fill='tonexty' if i > 0 else 'tozeroy',
                    mode='lines',
                    name=label,
                    line=dict(color=color, width=2),
                    fillcolor=color,
                    opacity=0.7,
                    hovertemplate=f'Jour %{{x}}<br>Incidence {label}: %{{customdata:.1f}}%<br>Total cumulé: %{{y:.1f}}%<extra></extra>',
                    customdata=y_data
                )
            )
            
            y_lower = y_upper
        
        # Ajouter la zone "Sans événement" pour atteindre 100%
        survival_pct = results_df['survie_sans_evenement'] * 100
        total_events = y_lower  # somme de tous les événements
        
        fig.add_trace(
            go.Scatter(
                x=results_df['jour'],  # Utiliser 'jour' au lieu de 'Day'
                y=survival_pct + total_events,  # pour atteindre 100%
                fill='tonexty',
                mode='lines',
                name='Sans événement',
                line=dict(color='lightgray', width=1),
                fillcolor='lightgray',
                opacity=0.3,
                hovertemplate='Jour %{x}<br>Sans événement: %{customdata:.1f}%<br>Total: 100%<extra></extra>',
                customdata=survival_pct
            )
        )
        
        # Mise en forme du graphique
        fig.update_layout(
            title=dict(
                text=f'<b>{title}</b>',
                x=0.5,
                font=dict(size=16, family='Arial, sans-serif', color='#2c3e50')
            ),
            xaxis_title='<b>Jours après greffe</b>',
            yaxis_title='<b>Incidence cumulative (%)</b>',
            template='plotly_white',
            height=600,
            showlegend=True,
            hovermode='x unified',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='rgba(0,0,0,0.2)',
                borderwidth=1
            ),
            xaxis=dict(
                range=[0, results_df['jour'].max()],
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128, 128, 128, 0.2)',
                showline=True,
                linewidth=2,
                linecolor='#bdc3c7',
                mirror=True
            ),
            yaxis=dict(
                range=[0, 105],
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128, 128, 128, 0.2)',
                showline=True,
                linewidth=2,
                linecolor='#bdc3c7',
                mirror=True,
                tickformat='.1f'
            ),
            plot_bgcolor='rgba(248, 249, 250, 0.8)',
            paper_bgcolor='white',
            margin=dict(l=80, r=120, t=80, b=60)
        )
        
        return fig

    def create_competing_risks_plot(self, results_df, processed_data, events_config, 
                                  title="Analyse de Risques Compétitifs", 
                                  initial_display_days=None):
        """
        Crée le graphique des risques compétitifs avec support pour affichage initial limité
        
        Args:
            results_df: DataFrame avec les résultats d'incidence cumulative (structure existante)
            processed_data: DataFrame des données traitées  
            events_config: Configuration des événements
            title: Titre du graphique
            initial_display_days: Si spécifié, limite l'affichage initial à ce nombre de jours
        """
        import plotly.graph_objects as go
        
        # Utiliser la méthode existante mais avec modification pour l'affichage initial
        # Appeler la méthode create_competing_risks_plot existante d'abord
        fig = self.create_competing_risks_plot_original(results_df, processed_data, events_config, title)
        
        # Modifier le layout pour l'affichage initial limité si demandé
        if initial_display_days:
            max_days = results_df['jour'].max()
            
            if max_days > initial_display_days:
                # Modifier l'axe X pour l'affichage initial limité
                fig.update_xaxes(range=[0, initial_display_days])
                
                # Ajouter une annotation explicative
                fig.add_annotation(
                    x=0.02, y=0.98,
                    xref='paper', yref='paper',
                    text=f"<b>Affichage initial: {initial_display_days} jours</b><br>" +
                         f"Données disponibles jusqu'à {max_days} jours<br>" +
                         "<i>Utilisez les contrôles de zoom pour voir au-delà</i>",
                    showarrow=False,
                    font=dict(size=10, color='#34495e'),
                    bgcolor="rgba(255, 255, 255, 0.9)",
                    bordercolor="#3498db",
                    borderwidth=1,
                    align="left"
                )
        
        return fig

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
        df[followup_config['date_col']] = _to_datetime_fast(df[followup_config['date_col']])

        for event_name, config in events_config.items():
            df[config['date_col']] = _to_datetime_fast(df[config['date_col']])

        # Calculer les temps d'événement avec validation
        df['time_to_last_followup'] = (df[followup_config['date_col']] - df[self.reference_date_col]).dt.days
        
        for event_name, config in events_config.items():
            time_col = f'time_to_{event_name}'
            df[time_col] = (df[config['date_col']] - df[self.reference_date_col]).dt.days
            
        # Nettoyer les temps négatifs ou invalides
        df['time_to_last_followup'] = df['time_to_last_followup'].fillna(-1)
        
        for event_name, config in events_config.items():
            time_col = f'time_to_{event_name}'
            df[time_col] = df[time_col].fillna(-1)
        
        # Déterminer l'événement et le temps pour chaque patient (vectorisé)
        n = len(df)
        event_names = list(events_config.keys())

        # Occurrence 'yes' par événement (strip + casse insensible, comme avant)
        occ_yes = {
            name: (df[cfg['occurrence_col']].fillna('').astype(str)
                   .str.strip().str.lower() == 'yes').to_numpy()
            for name, cfg in events_config.items()
        }
        times_np = {name: df[f'time_to_{name}'].to_numpy() for name in event_names}
        time_fu = df['time_to_last_followup'].to_numpy()

        # Premier événement par patient : parcours dans l'ordre de la config, le
        # décès en dernier ; égalité de temps -> priorité au premier de la liste
        # (même comportement que min() sur la liste chaînée d'avant)
        best_time = np.full(n, np.inf)
        event_type = np.full(n, 'Censuré', dtype=object)
        for name in event_names:
            t = times_np[name]
            valid = occ_yes[name] & (t >= 0) & (t <= max_days)
            take = valid & (t < best_time)
            best_time[take] = t[take]
            event_type[take] = name

        if death_as_competing:
            death_value = followup_config['death_value'].lower()
            dead = (df[followup_config['status_col']].fillna('').astype(str)
                    .str.strip().str.lower() == death_value).to_numpy()
            # Un événement strictement avant le décès (sans borne max_days,
            # comme avant) empêche le décès d'être compté comme premier événement
            event_before_death = np.zeros(n, dtype=bool)
            for name in event_names:
                t = times_np[name]
                event_before_death |= occ_yes[name] & (t >= 0) & (t < time_fu)
            death_mask = (dead & (time_fu >= 0) & (time_fu <= max_days)
                          & ~event_before_death & (time_fu < best_time))
            best_time[death_mask] = time_fu[death_mask]
            event_type[death_mask] = 'Décès'

        # Patients censurés : temps de suivi borné à max_days (comme avant)
        censored = event_type == 'Censuré'
        censor_time = np.where(time_fu < 0, max_days, np.minimum(time_fu, max_days))
        event_time = np.where(censored, censor_time, best_time)

        df['event_type'] = event_type
        df['event_time'] = event_time

        # Comptages par jour (vectorisés) — int Python pour rester en int64
        days = np.arange(0, max_days + 1)
        n_at_risk = [int((event_time >= day).sum()) for day in days]

        count_names = event_names + (['Décès'] if death_as_competing else []) + ['Censuré']
        event_counts = {
            name: [int(((event_time == day) & (event_type == name)).sum()) for day in days]
            for name in count_names
        }

        # Calculer les incidences cumulées selon la méthode des risques compétitifs
        cum_incidences = {event_name: np.zeros(len(days)) for event_name in events_config.keys()}
        if death_as_competing:
            cum_incidences['Décès'] = np.zeros(len(days))

        survival = np.ones(len(days))  # Probabilité de survie sans événement

        for i in range(1, len(days)):
            if n_at_risk[i-1] > 0:
                # Total des événements du jour précédent
                total_events_today = sum(event_counts[event][i-1] for event in event_counts.keys()
                                       if event != 'Censuré')

                # Probabilité de survie sans événement ce jour
                daily_survival = (n_at_risk[i-1] - total_events_today) / n_at_risk[i-1]

                # Hazard spécifique pour chaque événement et incidence cumulative
                for event_name in cum_incidences.keys():
                    if event_name in event_counts:
                        hazard = event_counts[event_name][i-1] / n_at_risk[i-1] if n_at_risk[i-1] > 0 else 0
                        # Formule de Gray pour les risques compétitifs
                        cum_incidences[event_name][i] = cum_incidences[event_name][i-1] + survival[i-1] * hazard

                # Mise à jour de la survie globale
                survival[i] = survival[i-1] * daily_survival

            else:
                # Pas de patients à risque : maintenir les valeurs précédentes
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
    
