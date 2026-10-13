"""
Harnais d'équivalence pour les stores par page (phase 4 perf).

Pour chaque callback alimenté par un store de page allégé, on exécute le
callback deux fois : une fois avec le store COMPLET (codec) en entrée, une
fois avec le store DE PAGE. Les sorties sérialisées doivent être identiques :
cela prouve que le store de page contient toutes les colonnes nécessaires
(notamment face aux gardes silencieuses du type `'Col' in df.columns`).
"""
import json

import pytest
from plotly.utils import PlotlyJSONEncoder

import app as app_module
from modules.data_processing import df_to_store_payload
from scripts.perf.perf_targets import get_processed_df

# store de page -> nom de page attendu par le filtre 'current-page'
_PAGE_OF_STORE = {
    'data-store-home': 'Home',
    'data-store-hemopathies': 'Indications',
    'data-store-procedures': 'Procedures',
    'data-store-relapse': 'Relapse',
    'data-store-toxicity': 'Toxicity',
    'data-store-survival': 'Survival',
    'data-store-gvh': 'GvH',
    'data-store-viz': 'Patients',
    'data-store-indics': 'Indicators',
}

# Valeurs de filtres réalistes pour exercer les callbacks
_FILTER_VALUES = [
    {},  # défauts
    {'years': ['2018'], 'malignancy': 'Malignant'},  # filtres actifs
]


def _value_for(cid, page, combo, store_payloads, store_id):
    if cid == store_id:
        return store_payloads[store_id]
    if cid == 'current-page':
        return page
    if 'year' in cid and ('filter' in cid or 'checklist' in cid):
        return combo.get('years')
    if cid in ('year-selection-sidebar', 'years-radio-sidebar'):
        return (combo.get('years') or ['2018'])[-1]
    if 'age-filter' in cid:
        return None
    if 'custom-age-switch' in cid:
        return False
    if 'custom-age-slider' in cid:
        return None
    if 'malignancy' in cid:
        return combo.get('malignancy', 'both')
    if 'pediatric' in cid:
        return False
    if 'gvh-type' in cid:
        return 'acute'
    if 'indicator-selection' in cid:
        return 'gvha'
    if 'analysis-mode' in cid:
        return 'yearly'
    if 'max-duration' in cid:
        return 'limited'
    return None


def _serialize(output):
    return json.dumps(output, cls=PlotlyJSONEncoder, sort_keys=True, default=str)


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
    # Aller-retour JSON pour simuler le passage par le navigateur
    return json.loads(json.dumps(payloads, cls=PlotlyJSONEncoder))


def _callbacks_by_store():
    """{store_id: [(out_id, raw_callback, spec)]} pour les callbacks avec un store en Input."""
    by_store = {}
    for out_id, spec in app_module.app.callback_map.items():
        store_ids = [i['id'] for i in spec['inputs'] if i['id'].startswith('data-store')]
        for store_id in store_ids:
            if store_id == 'data-store':
                continue  # plus aucun callback de page ne doit l'utiliser
            cb = getattr(spec['callback'], '__wrapped__', spec['callback'])
            by_store.setdefault(store_id, []).append((out_id, cb, spec))
    return by_store


def test_no_page_callback_uses_full_store():
    """Régression : seuls upload/purge peuvent toucher 'data-store'."""
    offenders = []
    for out_id, spec in app_module.app.callback_map.items():
        if any(i['id'] == 'data-store' for i in spec['inputs']):
            offenders.append(out_id)
    assert offenders == [], f'Callbacks encore sur data-store: {offenders}'


@pytest.mark.parametrize('store_id,page', sorted(_PAGE_OF_STORE.items()))
def test_page_store_equivalence(store_payloads, store_id, page):
    entries = _callbacks_by_store().get(store_id, [])
    assert entries, f'aucun callback trouvé pour {store_id}'

    tested = 0
    for out_id, cb, spec in entries:
        for combo in _FILTER_VALUES:
            def args_for(payload_key):
                overrides = {store_id: store_payloads[payload_key]}
                merged = dict(store_payloads)
                merged.update(overrides)
                return [
                    _value_for(i['id'], page, combo, merged, store_id)
                    for i in spec['inputs']
                ] + [
                    _value_for(s['id'], page, combo, merged, store_id)
                    for s in spec.get('state', [])
                ]

            try:
                ref = cb(*args_for('data-store'))
            except Exception as e:
                if 'callback_context' in str(e):
                    continue  # callbacks nécessitant le contexte Dash : hors harnais
                raise
            got = cb(*args_for(store_id))

            assert _serialize(got) == _serialize(ref), (
                f'{out_id} diffère entre store complet et {store_id} '
                f'(combo={combo})'
            )
            tested += 1

    assert tested > 0, f'aucun callback réellement exécuté pour {store_id}'
