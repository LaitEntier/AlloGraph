"""
Capture les sorties de référence (« golden masters ») des fonctions pures
sur le jeu synthétique, dans tests/golden/.

À rejouer uniquement si le schéma synthétique change volontairement.
Les tests (tests/test_golden_master.py) comparent le code actuel à ces sorties.
"""

import gzip
import json
import pickle
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from perf_targets import (
    get_raw_df,
    target_process_data,
    target_upset_plot,
    target_competing_risks_agvhd,
    target_km_survival,
    SEED,
    DEFAULT_N_ROWS,
)

GOLDEN_DIR = Path(__file__).resolve().parents[2] / 'tests' / 'golden'


def _dump(obj, name):
    path = GOLDEN_DIR / f'{name}.pkl.gz'
    with gzip.open(path, 'wb') as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"  {path.name}: {path.stat().st_size / 1e6:.1f} Mo")


def main():
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    df_raw = get_raw_df()
    print(f"Jeu synthétique : {len(df_raw)} lignes (graine {SEED})")

    print("Capture des golden masters...")
    _dump(target_process_data(df_raw), 'process_data')
    _dump(target_upset_plot(df_raw), 'process_upset_plot')
    df_processed = target_process_data(df_raw)
    _dump(target_competing_risks_agvhd(df_processed), 'competing_risks_agvhd_100d')
    _dump(target_km_survival(df_processed), 'km_survival_lifelines')

    manifest = {
        'description': 'Sorties de référence phase 0 (données 100 % synthétiques)',
        'captured_on': date.today().isoformat(),
        'n_rows': DEFAULT_N_ROWS,
        'seed': SEED,
        'pandas': pd.__version__,
        'numpy': np.__version__,
    }
    (GOLDEN_DIR / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print("Manifest écrit.")


if __name__ == '__main__':
    main()
