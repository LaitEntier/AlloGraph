"""Fixtures partagées pour la suite de tests.

Les fixtures de données sont en scope 'session' : le chargement et le
traitement du fichier d'exemple ne sont faits qu'une fois par run.
"""
from pathlib import Path

import pandas as pd
import pytest

from modules.data_processing import detect_csv_separator, process_data

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SAMPLE_CSV = DATA_DIR / "test_sample.csv"


@pytest.fixture(scope="session")
def raw_df():
    """DataFrame brut tel que lu depuis le fichier d'exemple."""
    separator = detect_csv_separator(str(SAMPLE_CSV), is_file_path=True)
    return pd.read_csv(SAMPLE_CSV, sep=separator)


@pytest.fixture(scope="session")
def processed_df(raw_df):
    """DataFrame d'exemple passé par process_data()."""
    return process_data(raw_df)
