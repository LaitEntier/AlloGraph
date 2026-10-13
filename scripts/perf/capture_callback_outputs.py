"""
Capture les sorties sérialisées des callbacks candidats à la fusion
(phase 4 perf) AVANT fusion, comme référence (« golden »).

Jeu synthétique uniquement. Sortie : tests/golden/callback_outputs.json.gz

Usage : .venv/Scripts/python.exe scripts/perf/capture_callback_outputs.py
"""
import gzip
import json

from plotly.utils import PlotlyJSONEncoder

import app as app_module
from modules.data_processing import df_to_store_payload
from scripts.perf.perf_targets import get_processed_df
from tests.test_page_stores import _FILTER_VALUES, _PAGE_OF_STORE, _value_for

# Groupes de callbacks fusionnables (Inputs identiques), inventoriés via
# app.callback_map : {nom_de_groupe: [out_ids dans l'ordre]}
MERGE_GROUPS = {
    'relapse': [
        'relapse-main-graph.children',
        'relapse-missing-summary-table.children',
        '..relapse-missing-detail-table.children...export-missing-relapse-button.disabled...relapse-missing-store.data..',
    ],
    'toxicity': [
        'toxicity-nrm-graph.children',
        'toxicity-missing-summary-table.children',
        '..toxicity-missing-detail-table.children...export-missing-toxicity-button.disabled...toxicity-missing-store.data..',
    ],
    'patients': [
        'patients-normalized-chart.children',
        'patients-distribution-chart.children',
    ],
    'hemopathies': [
        'hemopathies-barplot-simple.children',
        'hemopathies-barplot-normalized.children',
    ],
    'gvh_missing': [
        'gvh-missing-summary-table.children',
        '..gvh-missing-detail-table.children...export-missing-gvh-button.disabled...gvh-missing-store.data..',
    ],
    'survival_curves': [
        'survival-global-curve.children',
        '..survival-curves-by-year.children...survival-stats-table.children..',
    ],
    'survival_missing': [
        'survival-missing-summary-table.children',
        '..survival-missing-detail-table.children...export-missing-survival-button.disabled...survival-missing-store.data..',
    ],
    'indics_missing': [
        'indicators-missing-summary-table.children',
        '..indicators-missing-detail-table.children...export-missing-indicators-button.disabled...indicators-missing-store.data...indicators-name-store.data..',
    ],
}


def _serialize(output):
    return json.dumps(output, cls=PlotlyJSONEncoder, sort_keys=True, default=str)


def main():
    df = get_processed_df()
    payloads = {'data-store': df_to_store_payload(df)}
    s, g, v = app_module._create_slim_stores(df)
    payloads['data-store-survival'] = s
    payloads['data-store-gvh'] = g
    payloads['data-store-viz'] = v
    payloads.update(
        {f'data-store-{k}': p for k, p in app_module._build_page_stores(df).items()}
    )
    payloads = json.loads(json.dumps(payloads, cls=PlotlyJSONEncoder))

    golden = {}
    for group, out_ids in MERGE_GROUPS.items():
        for out_id in out_ids:
            spec = app_module.app.callback_map.get(out_id)
            if spec is None:
                raise SystemExit(f'callback introuvable: {out_id}')
            store_id = next(
                i['id'] for i in spec['inputs'] if i['id'].startswith('data-store')
            )
            page = _PAGE_OF_STORE[store_id]
            cb = getattr(spec['callback'], '__wrapped__', spec['callback'])
            results = []
            for combo in _FILTER_VALUES:
                args = [
                    _value_for(i['id'], page, combo, payloads, store_id)
                    for i in spec['inputs']
                ] + [
                    _value_for(st['id'], page, combo, payloads, store_id)
                    for st in spec.get('state', [])
                ]
                results.append(_serialize(cb(*args)))
            golden[out_id] = results
            print(f'capturé: {out_id[:80]} ({len(results)} combos)')

    with gzip.open('tests/golden/callback_outputs.json.gz', 'wt', encoding='utf-8') as fh:
        json.dump(golden, fh)
    print('-> tests/golden/callback_outputs.json.gz')


if __name__ == '__main__':
    main()
