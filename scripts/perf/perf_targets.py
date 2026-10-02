"""
Registre des fonctions de calcul pures à mesurer / figer (phase 0 du plan perf).

Partagé entre capture_golden.py, benchmark.py et tests/test_golden_master.py
pour garantir que golden masters et benchmarks portent exactement sur les
mêmes appels.

Aucune donnée patient réelle : tout repose sur synthetic_data.py.
"""

import contextlib
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from synthetic_data import generate_synthetic_dataframe, SEED, DEFAULT_N_ROWS  # noqa: E402

from modules.data_processing import (  # noqa: E402
    process_data,
    process_upset_plot,
    process_prophylaxis_drugs,
    process_prep_regimen_variables,
    create_greffes_variable,
    create_blood_rh_variable,
    create_hla_compatibility_variable,
    transform_gvhc_scores,
)
from modules.competing_risks import CompetingRisksAnalyzer  # noqa: E402

# Configuration de risques compétitifs : GvH aiguë vs décès à 100 jours
# (mêmes colonnes que pages/gvh.py)
AGVHD_EVENTS_CONFIG = {
    'agvhd': {
        'occurrence_col': 'First Agvhd Occurrence',
        'date_col': 'First Agvhd Occurrence Date',
        'label': 'GvH aiguë',
    }
}
FOLLOWUP_CONFIG = {
    'status_col': 'Status Last Follow Up',
    'date_col': 'Date Of Last Follow Up',
    'death_value': 'Dead',
}
CR_MAX_DAYS = 100

# Cache de processus (script jetable uniquement — interdit dans l'app serveur)
_raw_df = None
_processed_df = None


def get_raw_df():
    """DataFrame synthétique brut (schéma CSV, tout en texte)."""
    global _raw_df
    if _raw_df is None:
        _raw_df = generate_synthetic_dataframe(DEFAULT_N_ROWS, SEED)
    return _raw_df.copy()


def get_processed_df():
    """DataFrame après process_data (base des calculs des pages)."""
    global _processed_df
    if _processed_df is None:
        with contextlib.redirect_stdout(io.StringIO()):
            _processed_df = process_data(get_raw_df())
    return _processed_df.copy()


def run_quiet(func, *args, **kwargs):
    """Exécute en avalant les prints de debug (ils restent comptés dans le temps)."""
    with contextlib.redirect_stdout(io.StringIO()):
        return func(*args, **kwargs)


# --- Cibles -----------------------------------------------------------------

def target_process_data(df_raw):
    return run_quiet(process_data, df_raw)


def target_create_greffes(df_raw):
    return create_greffes_variable(df_raw)


def target_create_blood_rh(df_raw):
    return create_blood_rh_variable(df_raw)


def target_create_hla(df_raw):
    return create_hla_compatibility_variable(df_raw)


def target_prep_regimen(df_raw):
    return process_prep_regimen_variables(df_raw)


def target_prophylaxis_drugs(df_raw):
    return run_quiet(process_prophylaxis_drugs, df_raw)


def target_upset_plot(df_raw):
    return run_quiet(process_upset_plot, df_raw)


def target_competing_risks_agvhd(df_processed):
    analyzer = CompetingRisksAnalyzer(df_processed, 'Treatment Date')
    results_df, _ = run_quiet(
        analyzer.calculate_cumulative_incidence,
        AGVHD_EVENTS_CONFIG, FOLLOWUP_CONFIG,
        max_days=CR_MAX_DAYS, death_as_competing=True,
    )
    return results_df


def target_km_survival(df_processed):
    """Ajustement Kaplan-Meier global (lifelines), comme pages/survival.py."""
    from lifelines import KaplanMeierFitter
    treatment = pd.to_datetime(df_processed['Treatment Date'], format='mixed', dayfirst=True, errors='coerce')
    last_fu = pd.to_datetime(df_processed['Date Of Last Follow Up'], format='mixed', dayfirst=True, errors='coerce')
    durations = (last_fu - treatment).dt.days
    mask = durations.notna() & (durations >= 0)
    kmf = KaplanMeierFitter()
    kmf.fit(durations[mask], (df_processed.loc[mask, 'Status Last Follow Up'] == 'Dead'))
    return kmf.survival_function_


def target_json_roundtrip(df_processed):
    """Sérialisation/désérialisation du Store (hypothèse H4)."""
    payload = df_processed.to_json(orient='split', date_format='iso')
    pd.read_json(io.StringIO(payload), orient='split')
    return len(payload)


# (nom, fonction, source de données) — source: 'raw' ou 'processed'
TARGETS = [
    ('process_data', target_process_data, 'raw'),
    ('create_greffes_variable', target_create_greffes, 'raw'),
    ('create_blood_rh_variable', target_create_blood_rh, 'raw'),
    ('create_hla_compatibility_variable', target_create_hla, 'raw'),
    ('process_prep_regimen_variables', target_prep_regimen, 'raw'),
    ('process_prophylaxis_drugs', target_prophylaxis_drugs, 'raw'),
    ('process_upset_plot', target_upset_plot, 'raw'),
    ('competing_risks_agvhd_100d', target_competing_risks_agvhd, 'processed'),
    ('km_survival_lifelines', target_km_survival, 'processed'),
    ('json_store_roundtrip', target_json_roundtrip, 'processed'),
]
