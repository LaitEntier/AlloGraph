"""
Benchmark des fonctions de calcul pures (phase 0 du plan perf).

Chronomètre chaque cible avec time.perf_counter, plusieurs répétitions,
et rapporte la médiane. Écrit le tableau dans docs/perf/phase0_benchmark.md.

Usage : python scripts/perf/benchmark.py [repetitions]
"""

import json
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np

from perf_targets import TARGETS, get_raw_df, get_processed_df, REPO_ROOT

REPORT_PATH = REPO_ROOT / 'docs' / 'perf' / 'phase0_benchmark.md'


def bench(func, df, repetitions):
    times = []
    result = None
    for _ in range(repetitions):
        t0 = time.perf_counter()
        result = func(df)
        times.append(time.perf_counter() - t0)
    return float(np.median(times)), min(times), max(times), result


def main():
    repetitions = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    df_raw = get_raw_df()
    df_processed = get_processed_df()

    rows = []
    extra = {}
    for name, func, source in TARGETS:
        df = df_raw if source == 'raw' else df_processed
        reps = repetitions if name != 'competing_risks_agvhd_100d' else max(3, repetitions // 2)
        median, tmin, tmax, result = bench(func, df, reps)
        rows.append((name, source, reps, median, tmin, tmax))
        print(f"{name:35s} médiane={median * 1000:9.1f} ms  (min={tmin * 1000:9.1f}, max={tmax * 1000:9.1f})")
        if name == 'json_store_roundtrip':
            extra['json_payload_bytes'] = result

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 0 — temps de référence des fonctions pures",
        "",
        f"Date : {date.today().isoformat()} — jeu synthétique {len(df_raw)} lignes (graine fixe).",
        "Machine : poste de développement (Windows). Médiane sur N répétitions, `time.perf_counter`.",
        "",
        "| Fonction | Entrée | Rép. | Médiane (ms) | Min (ms) | Max (ms) |",
        "|---|---|---|---|---|---|",
    ]
    for name, source, reps, median, tmin, tmax in rows:
        lines.append(f"| `{name}` | {source} | {reps} | {median * 1000:.1f} | {tmin * 1000:.1f} | {tmax * 1000:.1f} |")
    if extra:
        lines += [
            "",
            f"Taille de la sérialisation JSON `orient='split'` du DataFrame traité : "
            f"{extra['json_payload_bytes'] / 1e6:.1f} Mo (hypothèse H4).",
        ]
    REPORT_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f"\nRapport écrit : {REPORT_PATH}")


if __name__ == '__main__':
    main()
