"""Tests pour la détection d'encodage des CSV uploadés (decode_csv_bytes)."""
import io

import pandas as pd

from modules.data_processing import decode_csv_bytes, detect_csv_separator

CSV_TEXT = "Long ID;Main Diagnosis\n1;Hématologie ça va\n2;Leucémie aiguë\n"


def _roundtrip(content: bytes) -> pd.DataFrame:
    """Reproduit le pipeline d'upload : décodage -> séparateur -> read_csv."""
    text = decode_csv_bytes(content)
    separator = detect_csv_separator(text, is_file_path=False)
    return pd.read_csv(io.StringIO(text), sep=separator)


def test_utf8_plain():
    assert decode_csv_bytes(CSV_TEXT.encode('utf-8')) == CSV_TEXT


def test_utf8_bom():
    assert decode_csv_bytes(CSV_TEXT.encode('utf-8-sig')) == CSV_TEXT


def test_utf16_with_bom():
    assert decode_csv_bytes(CSV_TEXT.encode('utf-16')) == CSV_TEXT


def test_utf16_le_without_bom():
    assert decode_csv_bytes(CSV_TEXT.encode('utf-16-le')) == CSV_TEXT


def test_utf16_be_without_bom():
    assert decode_csv_bytes(CSV_TEXT.encode('utf-16-be')) == CSV_TEXT


def test_cp1252_fallback():
    assert decode_csv_bytes(CSV_TEXT.encode('cp1252')) == CSV_TEXT


def test_full_pipeline_utf16_tab_separated():
    """Cas réel : export Excel 'texte Unicode' = UTF-16 tabulé."""
    tsv = CSV_TEXT.replace(';', '\t')
    df = _roundtrip(tsv.encode('utf-16'))
    assert list(df.columns) == ['Long ID', 'Main Diagnosis']
    assert df.loc[0, 'Main Diagnosis'] == 'Hématologie ça va'
    assert len(df) == 2


def test_full_pipeline_cp1252_semicolon():
    df = _roundtrip(CSV_TEXT.encode('cp1252'))
    assert list(df.columns) == ['Long ID', 'Main Diagnosis']
    assert df.loc[1, 'Main Diagnosis'] == 'Leucémie aiguë'
