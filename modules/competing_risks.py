import pandas as pd
import numpy as np
import plotly.graph_objects as go
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
        df[followup_config['date_col']] = pd.to_datetime(df[followup_config['date_col']])
        
        for event_name, config in events_config.items():
            df[config['date_col']] = pd.to_datetime(df[config['date_col']])
        
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
        
        # Déterminer l'événement et le temps pour chaque patient
        events = []
        times = []
        
        # Variables de debug
        debug_stats = {
            'total_patients': len(df),
            'gvh_yes_count': 0,
            'gvh_valid_time_count': 0,
            'gvh_invalid_time_count': 0,
            'death_count': 0,
            'censored_count': 0,
            'negative_times': 0,
            'times_over_max': 0
        }
        
        for idx, row in df.iterrows():
            patient_events = []
            
            # Vérifier chaque événement d'intérêt
            for event_name, config in events_config.items():
                time_col = f'time_to_{event_name}'
                occurrence_value = str(row[config['occurrence_col']]).strip() if pd.notna(row[config['occurrence_col']]) else ""
                
                # Debug : compter les "Yes"
                if occurrence_value.lower() == 'yes':
                    debug_stats['gvh_yes_count'] += 1
                    
                    # Vérifier le temps
                    if pd.isna(row[time_col]):
                        debug_stats['gvh_invalid_time_count'] += 1
                        print(f"Patient {idx}: GvH 'Yes' mais temps NaN")
                    elif row[time_col] < 0:
                        debug_stats['negative_times'] += 1
                        print(f"Patient {idx}: GvH 'Yes' mais temps négatif: {row[time_col]}")
                    elif row[time_col] > max_days:
                        debug_stats['times_over_max'] += 1
                        print(f"Patient {idx}: GvH 'Yes' mais temps > {max_days}: {row[time_col]}")
                
                # Vérifier les conditions pour ajouter l'événement
                if (not pd.isna(row[time_col]) and 
                    occurrence_value.lower() == 'yes' and 
                    row[time_col] >= 0 and  # Temps positif ou nul
                    row[time_col] <= max_days):
                    debug_stats['gvh_valid_time_count'] += 1
                    patient_events.append((event_name, row[time_col]))
            
            # Vérifier le décès si configuré comme risque compétitif
            death_added = False
            if death_as_competing:
                death_status = str(row[followup_config['status_col']]).strip() if pd.notna(row[followup_config['status_col']]) else ""
                if (death_status.lower() == followup_config['death_value'].lower() and 
                    not pd.isna(row['time_to_last_followup']) and
                    row['time_to_last_followup'] >= 0 and  # Temps positif ou nul
                    row['time_to_last_followup'] <= max_days):
                    
                    # Vérifier si décès avant tout autre événement GvH
                    death_before_events = True
                    for event_name, config in events_config.items():
                        time_col = f'time_to_{event_name}'
                        occurrence_value = str(row[config['occurrence_col']]).strip() if pd.notna(row[config['occurrence_col']]) else ""
                        # Un événement GvH s'est produit avant le décès
                        if (not pd.isna(row[time_col]) and 
                            occurrence_value.lower() == 'yes' and
                            row[time_col] >= 0 and
                            row[time_col] < row['time_to_last_followup']):  # Strictement avant le décès
                            death_before_events = False
                            break
                    
                    if death_before_events:
                        debug_stats['death_count'] += 1
                        patient_events.append(('Décès', row['time_to_last_followup']))
                        death_added = True
            
            # Prendre le premier événement (temps le plus court)
            if patient_events:
                first_event = min(patient_events, key=lambda x: x[1])
                events.append(first_event[0])
                times.append(first_event[1])
            else:
                # Censuré - utiliser le temps de suivi disponible
                debug_stats['censored_count'] += 1
                censoring_time = row['time_to_last_followup']
                
                # Gestion robuste du temps de censure
                if pd.isna(censoring_time) or censoring_time < 0:
                    censoring_time = max_days  # Si temps invalide, censurer à la fin de la période
                elif censoring_time > max_days:
                    censoring_time = max_days  # Limiter au maximum
                    
                events.append('Censuré')
                times.append(censoring_time)
        
        # Afficher les statistiques de debug
        print(f"\n=== DEBUG COMPETING RISKS ===")
        print(f"Total patients: {debug_stats['total_patients']}")
        print(f"Patients avec GvH 'Yes': {debug_stats['gvh_yes_count']}")
        print(f"Patients avec GvH 'Yes' et temps valide (0-{max_days}j): {debug_stats['gvh_valid_time_count']}")
        print(f"Patients avec GvH 'Yes' mais temps invalide: {debug_stats['gvh_invalid_time_count']}")
        print(f"Patients avec GvH 'Yes' mais temps négatif: {debug_stats['negative_times']}")
        print(f"Patients avec GvH 'Yes' mais temps > {max_days}j: {debug_stats['times_over_max']}")
        print(f"Décès détectés: {debug_stats['death_count']}")
        print(f"Patients censurés: {debug_stats['censored_count']}")
        print(f"Somme vérification: {debug_stats['gvh_valid_time_count'] + debug_stats['death_count'] + debug_stats['censored_count']}")
        
        # Afficher la répartition des événements finaux
        from collections import Counter
        event_counts = Counter(events)
        print(f"Répartition finale des événements: {dict(event_counts)}")
        
        # Calculer les pourcentages attendus
        total = len(events)
        for event, count in event_counts.items():
            percentage = (count / total) * 100 if total > 0 else 0
            print(f"  {event}: {count}/{total} = {percentage:.1f}%")
        print(f"===============================\n")
        
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
        
        # Calculer les incidences cumulées selon la méthode des risques compétitifs
        cum_incidences = {event_name: np.zeros(len(days)) for event_name in events_config.keys()}
        if death_as_competing:
            cum_incidences['Décès'] = np.zeros(len(days))
        
        survival = np.ones(len(days))  # Probabilité de survie sans événement
        
        print(f"\n=== DEBUG CALCUL INCIDENCES ===")
        print(f"Nombre de jours à analyser: {len(days)} (0 à {max_days})")
        
        for i in range(1, len(days)):
            day = days[i]
            
            if n_at_risk[i-1] > 0:
                # Calculer le total des événements ce jour
                total_events_today = sum(event_counts[event][i-1] for event in event_counts.keys() 
                                       if event != 'Censuré')
                
                if total_events_today > 0:
                    print(f"Jour {day}: {n_at_risk[i-1]} à risque, {total_events_today} événements")
                
                # Probabilité de survie sans événement ce jour
                if n_at_risk[i-1] > 0:
                    daily_survival = (n_at_risk[i-1] - total_events_today) / n_at_risk[i-1]
                else:
                    daily_survival = 1.0
                
                # Hazard spécifique pour chaque événement et calcul de l'incidence cumulative
                for event_name in cum_incidences.keys():
                    if event_name in event_counts:
                        hazard = event_counts[event_name][i-1] / n_at_risk[i-1] if n_at_risk[i-1] > 0 else 0
                        # Formule de Gray pour les risques compétitifs
                        cum_incidences[event_name][i] = cum_incidences[event_name][i-1] + survival[i-1] * hazard
                        
                        if hazard > 0:
                            print(f"  {event_name}: hazard={hazard:.4f}, incidence_cum={cum_incidences[event_name][i]:.4f}")
                
                # Mise à jour de la survie globale
                survival[i] = survival[i-1] * daily_survival
                
            else:
                # Pas de patients à risque : maintenir les valeurs précédentes
                for event_name in cum_incidences.keys():
                    cum_incidences[event_name][i] = cum_incidences[event_name][i-1]
                survival[i] = survival[i-1]
        
        # Afficher les incidences finales
        print(f"\nIncidences cumulées finales (à J{max_days}):")
        for event_name in cum_incidences.keys():
            final_incidence = cum_incidences[event_name][-1] * 100
            print(f"  {event_name}: {final_incidence:.1f}%")
        print(f"Survie sans événement: {survival[-1]*100:.1f}%")
        print(f"Total (vérification): {sum(cum_incidences[e][-1] for e in cum_incidences.keys()) + survival[-1]:.3f}")
        print(f"===============================\n")
        
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
    
