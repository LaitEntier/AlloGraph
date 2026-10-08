"""
Tests du codec compact des dcc.Store (phase 4 perf).

Référence d'équivalence : le chemin de sérialisation ACTUEL
(df.to_dict('records') + encodeur JSON de Dash, puis pd.DataFrame(records)).
Le codec doit produire, après aller-retour JSON, un DataFrame équivalent
à ce que les pages reçoivent aujourd'hui.
"""
import json

import pandas as pd
import pytest
from plotly.utils import PlotlyJSONEncoder

from modules.data_processing import (
    df_to_store_payload,
    process_data,
    store_payload_to_df,
)
from scripts.perf.synthetic_data import generate_synthetic_dataframe


def _current_path_df(df):
    """Ce que les pages reçoivent aujourd'hui : records -> JSON -> DataFrame."""
    records = df.to_dict('records')
    round_tripped = json.loads(json.dumps(records, cls=PlotlyJSONEncoder))
    return pd.DataFrame(round_tripped)


def _codec_path_df(df, columns=None):
    """Ce que les pages recevront : payload compact -> JSON -> DataFrame."""
    payload = df_to_store_payload(df, columns)
    round_tripped = json.loads(json.dumps(payload, cls=PlotlyJSONEncoder))
    return store_payload_to_df(round_tripped)


@pytest.fixture(scope='module')
def processed_df():
    raw = generate_synthetic_dataframe(n_rows=2000, seed=123)
    return process_data(raw)


def test_roundtrip_none():
    assert store_payload_to_df(None) is None


def test_payload_is_json_serializable(processed_df):
    payload = df_to_store_payload(processed_df)
    # Ne doit pas lever d'exception (NaN, Timestamps, numpy scalars...)
    json.dumps(payload, cls=PlotlyJSONEncoder)


def test_equivalence_full_df(processed_df):
    expected = _current_path_df(processed_df)
    actual = _codec_path_df(processed_df)
    assert list(actual.columns) == list(expected.columns)
    pd.testing.assert_frame_equal(
        actual, expected, check_dtype=False, check_categorical=False
    )


def test_equivalence_column_subset(processed_df):
    cols = ['Long ID', 'Year', 'Treatment Date', 'Age At Diagnosis', 'Sex']
    expected = _current_path_df(processed_df[[c for c in cols if c in processed_df.columns]])
    actual = _codec_path_df(processed_df, cols)
    pd.testing.assert_frame_equal(
        actual, expected, check_dtype=False, check_categorical=False
    )


def test_codebook_used_for_repetitive_text(processed_df):
    payload = df_to_store_payload(processed_df)
    # 'Sex' a une cardinalité très faible : encodée en codebook
    assert 'Sex' in payload['codebook']
    # Un identifiant quasi unique ne doit PAS être encodé (codebook inutile)
    if 'Long ID' in processed_df.columns:
        assert 'Long ID' not in payload['codebook']


def test_payload_smaller_than_records(processed_df):
    records_size = len(json.dumps(processed_df.to_dict('records'), cls=PlotlyJSONEncoder))
    payload_size = len(json.dumps(df_to_store_payload(processed_df), cls=PlotlyJSONEncoder))
    assert payload_size < records_size
