"""
Tests « golden master » (filet de sécurité du plan perf, phase 0).

Vérifie que les fonctions de calcul pures produisent, sur le jeu de données
SYNTHÉTIQUE (graine fixe), des sorties identiques aux références capturées
dans tests/golden/. Toute optimisation (phase 3+) doit garder ces tests verts.
"""

import gzip
import pickle
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'scripts' / 'perf'))

from perf_targets import (  # noqa: E402
    get_raw_df,
    get_processed_df,
    target_process_data,
    target_upset_plot,
    target_competing_risks_agvhd,
    target_km_survival,
)

GOLDEN_DIR = Path(__file__).resolve().parent / 'golden'


def _load_golden(name):
    path = GOLDEN_DIR / f'{name}.pkl.gz'
    if not path.exists():
        pytest.skip(f"golden master absent : {path} (lancer scripts/perf/capture_golden.py)")
    with gzip.open(path, 'rb') as f:
        return pickle.load(f)


def test_process_data_golden():
    expected = _load_golden('process_data')
    result = target_process_data(get_raw_df())
    pd.testing.assert_frame_equal(result, expected)


def test_process_upset_plot_golden():
    expected = _load_golden('process_upset_plot')
    result = target_upset_plot(get_raw_df())
    pd.testing.assert_frame_equal(result, expected)


def test_competing_risks_agvhd_golden():
    expected = _load_golden('competing_risks_agvhd_100d')
    result = target_competing_risks_agvhd(get_processed_df())
    pd.testing.assert_frame_equal(result, expected)


def test_km_survival_golden():
    expected = _load_golden('km_survival_lifelines')
    result = target_km_survival(get_processed_df())
    pd.testing.assert_frame_equal(result, expected)
