"""Tests pour modules/competing_risks.py (CompetingRisksAnalyzer).

Stratégie :
- petits jeux de données synthétiques dont les résultats sont calculables
  à la main (formule de Gray) ;
- invariants statistiques valables quelles que soient les données
  (incidences bornées, somme incidence + survie = 1).
"""
import numpy as np
import pandas as pd
import pytest

from modules.competing_risks import CompetingRisksAnalyzer

TREATMENT_DATE = '01/01/2023 00:00'

EVENTS_CONFIG = {
    'Rechute': {
        'occurrence_col': 'First Relapse',
        'date_col': 'First Relapse Date',
        'label': 'Rechute',
    }
}

FOLLOWUP_CONFIG = {
    'status_col': 'Status Last Follow Up',
    'date_col': 'Date Of Last Follow Up',
    'death_value': 'Dead',
}


def _date(day):
    """Date au format attendu, `day` jours après la date de greffe."""
    return (pd.Timestamp(2023, 1, 1) + pd.Timedelta(days=day)).strftime('%d/%m/%Y %H:%M')


def make_patient(relapse_day=None, status='Alive', followup_day=200):
    """Construit une ligne patient. relapse_day=None -> pas de rechute."""
    return {
        'Treatment Date': TREATMENT_DATE,
        'First Relapse': 'Yes' if relapse_day is not None else 'No',
        'First Relapse Date': _date(relapse_day) if relapse_day is not None else None,
        'Status Last Follow Up': status,
        'Date Of Last Follow Up': _date(followup_day),
    }


def run_analysis(patients, max_days=100):
    analyzer = CompetingRisksAnalyzer(pd.DataFrame(patients), 'Treatment Date')
    return analyzer.calculate_cumulative_incidence(
        EVENTS_CONFIG, FOLLOWUP_CONFIG, max_days=max_days)


class TestHandComputed:
    def test_no_events_all_censored(self):
        """5 patients vivants suivis 200 jours : aucun événement, survie = 1."""
        patients = [make_patient() for _ in range(5)]
        results, processed = run_analysis(patients)

        assert (results['incidence_cumulative_rechute'] == 0).all()
        assert (results['incidence_cumulative_décès'] == 0).all()
        assert (results['survie_sans_evenement'] == 1.0).all()
        assert (processed['event_type'] == 'Censuré').all()

    def test_single_relapse(self):
        """1 rechute au jour 10 sur 10 patients -> incidence 1/10 = 0.1."""
        patients = [make_patient(relapse_day=10)] + [make_patient() for _ in range(9)]
        results, processed = run_analysis(patients)

        day11 = results[results['jour'] == 11].iloc[0]
        assert day11['incidence_cumulative_rechute'] == pytest.approx(0.1)
        assert day11['survie_sans_evenement'] == pytest.approx(0.9)
        final = results.iloc[-1]
        assert final['incidence_cumulative_rechute'] == pytest.approx(0.1)
        assert final['incidence_cumulative_décès'] == pytest.approx(0.0)

    def test_relapse_then_competing_death(self):
        """10 patients : 1 rechute j10, 1 décès j20, 8 censurés j100.

        Formule de Gray, calculée à la main :
        - j11 : F_rechute = 1 * 1/10 = 0.1 ; S = 0.9
        - j21 : F_décès = 0.9 * 1/9 = 0.1 ; S = 0.9 * 8/9 = 0.8
        """
        patients = (
            [make_patient(relapse_day=10)]
            + [make_patient(status='Dead', followup_day=20)]
            + [make_patient() for _ in range(8)]
        )
        results, _ = run_analysis(patients)

        final = results.iloc[-1]
        assert final['incidence_cumulative_rechute'] == pytest.approx(0.1)
        assert final['incidence_cumulative_décès'] == pytest.approx(0.1)
        assert final['survie_sans_evenement'] == pytest.approx(0.8)

    def test_n_at_risk_day_zero(self):
        patients = [make_patient() for _ in range(7)]
        results, _ = run_analysis(patients)
        assert results.loc[results['jour'] == 0, 'n_at_risk'].iloc[0] == 7


class TestEventAttribution:
    def test_event_before_death_not_counted_as_death(self):
        """Rechute j5 puis décès j50 : le décès ne doit pas être compté."""
        patients = [make_patient(relapse_day=5, status='Dead', followup_day=50)]
        results, processed = run_analysis(patients)

        assert processed['event_type'].iloc[0] == 'Rechute'
        assert (results['incidence_cumulative_décès'] == 0).all()

    def test_death_without_prior_event_is_competing(self):
        patients = [make_patient(status='Dead', followup_day=30)]
        _, processed = run_analysis(patients)
        assert processed['event_type'].iloc[0] == 'Décès'

    def test_event_after_max_days_ignored(self):
        """Rechute au jour 150 avec max_days=100 -> patient censuré."""
        patients = [make_patient(relapse_day=150)]
        results, processed = run_analysis(patients, max_days=100)

        assert processed['event_type'].iloc[0] == 'Censuré'
        assert (results['incidence_cumulative_rechute'] == 0).all()

    def test_negative_time_ignored(self):
        """Date de rechute antérieure à la greffe -> temps négatif ignoré."""
        patients = [{
            'Treatment Date': TREATMENT_DATE,
            'First Relapse': 'Yes',
            'First Relapse Date': _date(-10),
            'Status Last Follow Up': 'Alive',
            'Date Of Last Follow Up': _date(200),
        }]
        results, processed = run_analysis(patients)
        assert processed['event_type'].iloc[0] == 'Censuré'

    @pytest.mark.parametrize("occurrence", ['Yes', 'YES', ' yes ', 'yEs'])
    def test_occurrence_case_and_whitespace_insensitive(self, occurrence):
        patient = make_patient(relapse_day=10)
        patient['First Relapse'] = occurrence
        _, processed = run_analysis([patient])
        assert processed['event_type'].iloc[0] == 'Rechute'

    @pytest.mark.parametrize("occurrence", ['No', '', None, 'Unknown'])
    def test_non_yes_occurrence_not_an_event(self, occurrence):
        patient = make_patient(relapse_day=10)
        patient['First Relapse'] = occurrence
        _, processed = run_analysis([patient])
        assert processed['event_type'].iloc[0] == 'Censuré'


class TestInvariants:
    """Propriétés qui doivent tenir quelles que soient les données."""

    @pytest.fixture
    def mixed_results(self):
        patients = (
            [make_patient(relapse_day=10)]
            + [make_patient(relapse_day=45)]
            + [make_patient(status='Dead', followup_day=20)]
            + [make_patient(status='Dead', followup_day=80)]
            + [make_patient(followup_day=30)]   # censuré tôt
            + [make_patient() for _ in range(5)]
        )
        results, _ = run_analysis(patients, max_days=100)
        return results

    def test_incidence_plus_survival_equals_one(self, mixed_results):
        """Somme des incidences cumulées + survie sans événement = 1 chaque jour."""
        total = (mixed_results['incidence_cumulative_rechute']
                 + mixed_results['incidence_cumulative_décès']
                 + mixed_results['survie_sans_evenement'])
        np.testing.assert_allclose(total, 1.0, atol=1e-12)

    def test_incidences_bounded_and_monotonic(self, mixed_results):
        for col in ['incidence_cumulative_rechute', 'incidence_cumulative_décès']:
            values = mixed_results[col]
            assert ((values >= 0) & (values <= 1)).all()
            assert (values.diff().dropna() >= -1e-12).all(), f"{col} n'est pas croissante"

    def test_survival_bounded_and_decreasing(self, mixed_results):
        survival = mixed_results['survie_sans_evenement']
        assert ((survival >= 0) & (survival <= 1)).all()
        assert (survival.diff().dropna() <= 1e-12).all()

    def test_output_covers_all_days(self, mixed_results):
        assert mixed_results['jour'].tolist() == list(range(0, 101))
