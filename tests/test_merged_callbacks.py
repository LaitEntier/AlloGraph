"""
Équivalence des callbacks fusionnés (phase 4 perf).

Les callbacks fusionnés doivent produire exactement les mêmes sorties que
les callbacks individuels capturés AVANT fusion dans
tests/golden/callback_outputs.json.gz (jeu synthétique, 2 combos de filtres).
"""
import gzip
import json

import pytest
from plotly.utils import PlotlyJSONEncoder

import app as app_module
from modules.data_processing import df_to_store_payload
from scripts.perf.perf_targets import get_processed_df
from tests.test_page_stores import _FILTER_VALUES, _value_for

# {merged_out_id: (page, [(golden_out_id, slice_ou_index), ...])}
MERGED = {
    '..relapse-main-graph.children...relapse-missing-summary-table.children...relapse-missing-detail-table.children...export-missing-relapse-button.disabled...relapse-missing-store.data..': (
        'Relapse', [
            ('relapse-main-graph.children', 0),
            ('relapse-missing-summary-table.children', 1),
            ('..relapse-missing-detail-table.children...export-missing-relapse-button.disabled...relapse-missing-store.data..', slice(2, 5)),
        ]),
    '..toxicity-nrm-graph.children...toxicity-missing-summary-table.children...toxicity-missing-detail-table.children...export-missing-toxicity-button.disabled...toxicity-missing-store.data..': (
        'Toxicity', [
            ('toxicity-nrm-graph.children', 0),
            ('toxicity-missing-summary-table.children', 1),
            ('..toxicity-missing-detail-table.children...export-missing-toxicity-button.disabled...toxicity-missing-store.data..', slice(2, 5)),
        ]),
    '..patients-normalized-chart.children...patients-distribution-chart.children..': (
        'Patients', [
            ('patients-normalized-chart.children', 0),
            ('patients-distribution-chart.children', 1),
        ]),
    '..hemopathies-barplot-simple.children...hemopathies-barplot-normalized.children..': (
        'Indications', [
            ('hemopathies-barplot-simple.children', 0),
            ('hemopathies-barplot-normalized.children', 1),
        ]),
    '..gvh-missing-summary-table.children...gvh-missing-detail-table.children...export-missing-gvh-button.disabled...gvh-missing-store.data..': (
        'GvH', [
            ('gvh-missing-summary-table.children', 0),
            ('..gvh-missing-detail-table.children...export-missing-gvh-button.disabled...gvh-missing-store.data..', slice(1, 4)),
        ]),
    '..survival-global-curve.children...survival-curves-by-year.children...survival-stats-table.children..': (
        'Survival', [
            ('survival-global-curve.children', 0),
            ('..survival-curves-by-year.children...survival-stats-table.children..', slice(1, 3)),
        ]),
    '..survival-missing-summary-table.children...survival-missing-detail-table.children...export-missing-survival-button.disabled...survival-missing-store.data..': (
        'Survival', [
            ('survival-missing-summary-table.children', 0),
            ('..survival-missing-detail-table.children...export-missing-survival-button.disabled...survival-missing-store.data..', slice(1, 4)),
        ]),
    '..indicators-missing-summary-table.children...indicators-missing-detail-table.children...export-missing-indicators-button.disabled...indicators-missing-store.data...indicators-name-store.data..': (
        'Indicators', [
            ('indicators-missing-summary-table.children', 0),
            ('..indicators-missing-detail-table.children...export-missing-indicators-button.disabled...indicators-missing-store.data...indicators-name-store.data..', slice(1, 5)),
        ]),
}


def _serialize(output):
    return json.dumps(output, cls=PlotlyJSONEncoder, sort_keys=True, default=str)


@pytest.fixture(scope='module')
def golden():
    with gzip.open('tests/golden/callback_outputs.json.gz', 'rt', encoding='utf-8') as fh:
        return json.load(fh)


@pytest.fixture(scope='module')
def store_payloads():
    df = get_processed_df()
    payloads = {'data-store': df_to_store_payload(df)}
    s, g, v = app_module._create_slim_stores(df)
    payloads['data-store-survival'] = s
    payloads['data-store-gvh'] = g
    payloads['data-store-viz'] = v
    payloads.update(
        {f'data-store-{k}': p for k, p in app_module._build_page_stores(df).items()}
    )
    return json.loads(json.dumps(payloads, cls=PlotlyJSONEncoder))


@pytest.mark.parametrize('merged_id', sorted(MERGED.keys()))
def test_merged_callback_matches_golden(golden, store_payloads, merged_id):
    page, golden_map = MERGED[merged_id]
    spec = app_module.app.callback_map.get(merged_id)
    assert spec is not None, f'callback fusionné introuvable: {merged_id}'
    store_id = next(i['id'] for i in spec['inputs'] if i['id'].startswith('data-store'))
    cb = getattr(spec['callback'], '__wrapped__', spec['callback'])

    for ci, combo in enumerate(_FILTER_VALUES):
        args = [
            _value_for(i['id'], page, combo, store_payloads, store_id)
            for i in spec['inputs']
        ] + [
            _value_for(s['id'], page, combo, store_payloads, store_id)
            for s in spec.get('state', [])
        ]
        out = cb(*args)
        if not isinstance(out, tuple):
            out = (out,)
        for golden_out_id, pos in golden_map:
            expected = golden[golden_out_id][ci]
            actual = out[pos]
            if isinstance(pos, slice):
                actual = list(actual)
            assert _serialize(actual) == expected, (
                f'{golden_out_id} diffère après fusion (combo={combo})'
            )
