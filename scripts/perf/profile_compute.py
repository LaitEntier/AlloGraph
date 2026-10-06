"""
Profilage cProfile des fonctions de calcul (phase 2 du plan perf).

Scénarios profilés séparément pour isoler les coûts :
1. load_data        : lecture/parsing CSV + process_data (chemin réel d'upload)
2. process_data     : traitements pandas seuls
3. competing_risks  : calculate_cumulative_incidence (GvH aiguë, 100 j)
4. json_roundtrip   : sérialisation/désérialisation du Store (H4)
5. plotly_barplot   : construction d'une figure Plotly représentative

Sortie : docs/perf/phase2_profile.md (top 10 par temps cumulé par scénario).
"""

import cProfile
import io
import pstats
from datetime import date

import pandas as pd

from perf_targets import (
    get_raw_df,
    get_processed_df,
    target_process_data,
    target_competing_risks_agvhd,
    target_json_roundtrip,
    REPO_ROOT,
)
from modules.data_processing import load_data  # noqa: E402
from visualizations.allogreffes.graphs import create_barplot  # noqa: E402

REPORT_PATH = REPO_ROOT / 'docs' / 'perf' / 'phase2_profile.md'
CSV_PATH = REPO_ROOT / 'data' / 'synthetic_16k.csv'


def scenario_plotly_barplot(df_processed):
    """Figure Plotly représentative : barplot du nombre de greffes par année."""
    counts = df_processed['Year'].value_counts().sort_index().reset_index()
    counts.columns = ['Year', 'n']
    return create_barplot(counts, 'Year', 'n', title='Greffes par année')


def profile(func, *args):
    """Profile un appel et retourne le top 10 par temps cumulé."""
    pr = cProfile.Profile()
    pr.enable()
    func(*args)
    pr.disable()
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    rows = []
    for func_key, (cc, nc, tt, ct, callers) in list(stats.stats.items()):
        rows.append((ct, tt, nc, func_key))
    rows.sort(reverse=True)
    return rows[:10], stats.total_tt


def fmt_rows(rows):
    out = ['| Temps cum. (s) | Temps propre (s) | Appels | Fonction |', '|---|---|---|---|']
    for ct, tt, nc, (file, line, name) in rows:
        short_file = file.replace(str(REPO_ROOT), '.').replace('\\', '/')
        out.append(f"| {ct:.3f} | {tt:.3f} | {nc} | `{name}` ({short_file}:{line}) |")
    return '\n'.join(out)


def main():
    if not CSV_PATH.exists():
        from synthetic_data import main as gen_main
        gen_main()

    df_raw = get_raw_df()
    df_processed = get_processed_df()

    scenarios = [
        ('load_data (parsing CSV + process_data)', load_data, (str(CSV_PATH),)),
        ('process_data seul', target_process_data, (df_raw,)),
        ('competing_risks GvH aiguë 100 j', target_competing_risks_agvhd, (df_processed,)),
        ('json_store_roundtrip (H4)', target_json_roundtrip, (df_processed,)),
        ('plotly create_barplot', scenario_plotly_barplot, (df_processed,)),
    ]

    md = [
        '# Phase 2 — Profilage cProfile',
        '',
        f"Date : {date.today().isoformat()}. Jeu synthétique 16 000 lignes. "
        "Top 10 par **temps cumulé** par scénario.",
        '',
    ]
    totals = {}
    for name, func, args in scenarios:
        rows, total = profile(func, *args)
        totals[name] = total
        md.append(f"## {name} — total {total * 1000:.0f} ms")
        md.append('')
        md.append(fmt_rows(rows))
        md.append('')

    md.append('## Synthèse des coûts')
    md.append('')
    md.append('| Scénario | Total (ms) |')
    md.append('|---|---|')
    for name, total in totals.items():
        md.append(f"| {name} | {total * 1000:.0f} |")
    md.append('')

    REPORT_PATH.write_text('\n'.join(md), encoding='utf-8')
    print(f"Rapport écrit : {REPORT_PATH}")
    for name, total in totals.items():
        print(f"  {name}: {total * 1000:.0f} ms")


if __name__ == '__main__':
    main()
