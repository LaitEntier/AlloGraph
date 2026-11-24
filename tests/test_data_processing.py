"""Tests pour modules/data_processing.py.

Deux niveaux :
- tests unitaires sur des mini-DataFrames synthétiques (cas limites inclus) ;
- tests d'intégration sur data/test_sample.csv passé par process_data().
"""
import numpy as np
import pandas as pd
import pytest

from modules.data_processing import (
    _to_datetime_fast,
    create_blood_rh_variable,
    create_diagnosis_category,
    create_greffes_variable,
    create_hla_compatibility_variable,
    df_to_store_payload,
    normalize_column_names,
    process_data,
    process_prep_regimen_variables,
    process_prophylaxis_drugs,
    rename_conditioning_regimen_values,
    store_payload_to_df,
    transform_gvhc_scores,
)


# ---------------------------------------------------------------------------
# normalize_column_names
# ---------------------------------------------------------------------------

class TestNormalizeColumnNames:
    def test_case_insensitive_rename(self):
        df = pd.DataFrame({'long id': [1], 'SEX': ['male'], 'Main Diagnosis': ['X']})
        out = normalize_column_names(df)
        assert list(out.columns) == ['Long ID', 'Sex', 'Main Diagnosis']

    def test_known_synonym(self):
        df = pd.DataFrame({'Match Type Related Donor': ['Match']})
        out = normalize_column_names(df)
        assert list(out.columns) == ['Match Type']

    def test_unknown_columns_untouched(self):
        df = pd.DataFrame({'Colonne Inconnue': [1]})
        out = normalize_column_names(df)
        assert list(out.columns) == ['Colonne Inconnue']

    def test_does_not_mutate_input(self):
        df = pd.DataFrame({'sex': ['male']})
        normalize_column_names(df)
        assert list(df.columns) == ['sex']


# ---------------------------------------------------------------------------
# _to_datetime_fast
# ---------------------------------------------------------------------------

class TestToDatetimeFast:
    def test_standard_format(self):
        s = pd.Series(['05/03/2023 00:00', '21/09/1964 00:00'])
        out = _to_datetime_fast(s)
        assert out.iloc[0] == pd.Timestamp(2023, 3, 5)
        assert out.iloc[1] == pd.Timestamp(1964, 9, 21)

    def test_mixed_fallback_iso(self):
        """Les valeurs hors format standard sont repassées en parsing 'mixed'."""
        s = pd.Series(['05/03/2023 00:00', '2023-03-05'])
        out = _to_datetime_fast(s)
        assert out.iloc[1] == pd.Timestamp(2023, 3, 5)

    def test_invalid_becomes_nat(self):
        s = pd.Series(['not a date', None, np.nan])
        out = _to_datetime_fast(s)
        assert out.isna().all()

    def test_dayfirst(self):
        s = pd.Series(['05/03/2023 00:00'])
        out = _to_datetime_fast(s)
        assert out.iloc[0].month == 3 and out.iloc[0].day == 5


# ---------------------------------------------------------------------------
# create_greffes_variable
# ---------------------------------------------------------------------------

class TestGreffes:
    def test_full_combination(self):
        df = pd.DataFrame({
            'Donor Type': ['Related donor'],
            'Source Stem Cells': ['Bone marrow'],
        })
        out = create_greffes_variable(df)
        assert out['Greffes'].iloc[0] == 'Related donor - Bone marrow'

    def test_missing_donor(self):
        df = pd.DataFrame({
            'Donor Type': [np.nan],
            'Source Stem Cells': ['Peripheral blood'],
        })
        out = create_greffes_variable(df)
        assert out['Greffes'].iloc[0] == 'Greffe Peripheral blood'

    def test_missing_source(self):
        df = pd.DataFrame({
            'Donor Type': ['Unrelated donor'],
            'Source Stem Cells': [np.nan],
        })
        out = create_greffes_variable(df)
        assert out['Greffes'].iloc[0] == 'Greffe Unrelated donor'

    def test_both_missing(self):
        df = pd.DataFrame({
            'Donor Type': [np.nan],
            'Source Stem Cells': [''],
        })
        out = create_greffes_variable(df)
        assert out['Greffes'].iloc[0] == 'Non défini'

    def test_missing_columns(self):
        out = create_greffes_variable(pd.DataFrame({'A': [1]}))
        assert out['Greffes'].iloc[0] == 'Non défini'


# ---------------------------------------------------------------------------
# create_blood_rh_variable
# ---------------------------------------------------------------------------

class TestBloodRh:
    def test_positive_and_negative(self):
        df = pd.DataFrame({
            'Blood Group': ['A', 'O'],
            'Rhesus Factor': ['positive', 'negative'],
        })
        out = create_blood_rh_variable(df)
        assert out['Blood + Rh'].tolist() == ['A+', 'O-']

    def test_case_insensitive_rhesus(self):
        df = pd.DataFrame({'Blood Group': ['B'], 'Rhesus Factor': ['POSITIVE']})
        out = create_blood_rh_variable(df)
        assert out['Blood + Rh'].iloc[0] == 'B+'

    def test_both_unknown(self):
        df = pd.DataFrame({'Blood Group': [np.nan], 'Rhesus Factor': ['']})
        out = create_blood_rh_variable(df)
        assert out['Blood + Rh'].iloc[0] == 'unknown'

    def test_rhesus_only_unknown(self):
        """Groupe connu, Rh manquant : la valeur brute 'unknown' est conservée."""
        df = pd.DataFrame({'Blood Group': ['AB'], 'Rhesus Factor': [np.nan]})
        out = create_blood_rh_variable(df)
        assert out['Blood + Rh'].iloc[0] == 'ABunknown'

    def test_missing_columns(self):
        out = create_blood_rh_variable(pd.DataFrame({'A': [1]}))
        assert out['Blood + Rh'].iloc[0] == 'unknown'


# ---------------------------------------------------------------------------
# create_hla_compatibility_variable
# ---------------------------------------------------------------------------

class TestHlaCompatibility:
    @pytest.mark.parametrize("donor,match,expected", [
        ('Related donor', 'Match', 'Genoidentical'),
        ('Related donor', 'Mismatch', 'MRD (Haplo)'),
        ('Unrelated donor', 'Match', 'MUD'),
        ('Unrelated donor', 'Mismatch', 'MMUD'),
    ])
    def test_main_combinations(self, donor, match, expected):
        df = pd.DataFrame({'Donor Type': [donor], 'Match Type': [match]})
        out = create_hla_compatibility_variable(df)
        assert out['Donor Match Category'].iloc[0] == expected

    @pytest.mark.parametrize("donor,expected", [
        ('Related donor', 'Related + Unknown'),
        ('Unrelated donor', 'Unrelated + Unknown'),
    ])
    def test_missing_match(self, donor, expected):
        df = pd.DataFrame({'Donor Type': [donor], 'Match Type': [np.nan]})
        out = create_hla_compatibility_variable(df)
        assert out['Donor Match Category'].iloc[0] == expected

    def test_missing_donor(self):
        df = pd.DataFrame({'Donor Type': [np.nan], 'Match Type': ['Match']})
        out = create_hla_compatibility_variable(df)
        assert out['Donor Match Category'].iloc[0] == 'Unknown + Match'

    def test_both_missing(self):
        df = pd.DataFrame({'Donor Type': [''], 'Match Type': [np.nan]})
        out = create_hla_compatibility_variable(df)
        assert out['Donor Match Category'].iloc[0] == 'Unknown + Unknown'

    def test_missing_columns(self):
        out = create_hla_compatibility_variable(pd.DataFrame({'A': [1]}))
        assert out['Donor Match Category'].iloc[0] == 'Unknown + Unknown'


# ---------------------------------------------------------------------------
# create_diagnosis_category
# ---------------------------------------------------------------------------

class TestDiagnosisCategory:
    @pytest.mark.parametrize("diagnosis,expected", [
        ('Acute leukemia', 'Malignant'),
        ('Lymphoma', 'Malignant'),
        ('Hemoglobinopathy', 'Non-malignant'),
        ('Inborn Errors', 'Non-malignant'),
        ('Diagnostic non répertorié', 'Unknown'),
    ])
    def test_mapping(self, diagnosis, expected):
        df = pd.DataFrame({'Main Diagnosis': [diagnosis]})
        out = create_diagnosis_category(df)
        assert out['Diagnosis Category'].iloc[0] == expected

    def test_missing_column(self):
        out = create_diagnosis_category(pd.DataFrame({'A': [1]}))
        assert out['Diagnosis Category'].iloc[0] == 'Unknown'


# ---------------------------------------------------------------------------
# rename_conditioning_regimen_values
# ---------------------------------------------------------------------------

class TestConditioningRegimen:
    def test_abbreviations(self):
        df = pd.DataFrame({'Conditioning Regimen Type': [
            'Reduced intensity conditioning (RIC)',
            'Myeloablative conditioning regimen',
            'Autre régime',
        ]})
        out = rename_conditioning_regimen_values(df)
        assert out['Conditioning Regimen Type'].tolist() == ['RIC', 'MAC', 'Autre régime']

    def test_missing_column(self):
        df = pd.DataFrame({'A': [1]})
        out = rename_conditioning_regimen_values(df)
        assert 'Conditioning Regimen Type' not in out.columns


# ---------------------------------------------------------------------------
# process_prep_regimen_variables
# ---------------------------------------------------------------------------

class TestPrepRegimen:
    def test_standardization(self):
        df = pd.DataFrame({
            'Prep Regimen Busulfan': ['Yes', 'yes', 'Y', '1', 'true', 'No', '', np.nan, 'maybe'],
        })
        out = process_prep_regimen_variables(df)
        assert out['Prep Regimen Busulfan'].tolist() == [
            'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No']

    def test_missing_column_ignored(self):
        df = pd.DataFrame({'Prep Regimen Busulfan': ['Yes']})
        out = process_prep_regimen_variables(df)
        assert 'Prep Regimen Bendamustine' not in out.columns


# ---------------------------------------------------------------------------
# process_prophylaxis_drugs
# ---------------------------------------------------------------------------

class TestProphylaxisDrugs:
    def _df(self):
        return pd.DataFrame({
            'Prophylaxis Drug 1': ['cyclosporine', 'Lymphocyte immune globulin', np.nan],
            'Prophylaxis Drug 2': ['methotrexate', 'cyclosporine', np.nan],
            'Prophylaxis Drug 3': [np.nan] * 3,
            'Prophylaxis Drug 4': [np.nan] * 3,
            'Prophylaxis Drug 5': [np.nan] * 3,
            'Prophylaxis Drug 6': [np.nan] * 3,
        })

    def test_binary_columns(self):
        out = process_prophylaxis_drugs(self._df())
        assert out['cyclosporine'].tolist() == ['Oui', 'Oui', 'Non']
        assert out['methotrexate'].tolist() == ['Oui', 'Non', 'Non']

    def test_drug_mapping_atg(self):
        """Les synonymes connus sont regroupés sous la même colonne."""
        out = process_prophylaxis_drugs(self._df())
        assert out['ATG'].tolist() == ['Non', 'Oui', 'Non']

    def test_empty_and_nan_ignored(self):
        out = process_prophylaxis_drugs(self._df())
        assert 'nan' not in out.columns
        assert '' not in out.columns

    def test_no_columns_returns_input(self):
        df = pd.DataFrame({'A': [1]})
        out = process_prophylaxis_drugs(df)
        assert list(out.columns) == ['A']


# ---------------------------------------------------------------------------
# transform_gvhc_scores
# ---------------------------------------------------------------------------

class TestGvhcScores:
    def test_limited_extensive_mapping(self):
        df = pd.DataFrame({'First cGvHD Maximum NIH Score': ['Limited', 'Extensive', 'Mild']})
        out = transform_gvhc_scores(df)
        assert out['First cGvHD Maximum NIH Score'].tolist() == ['Mild', 'Severe', 'Mild']

    def test_missing_column(self):
        df = pd.DataFrame({'A': [1]})
        out = transform_gvhc_scores(df)
        assert 'First cGvHD Maximum NIH Score' not in out.columns


# ---------------------------------------------------------------------------
# Codec dcc.Store : df_to_store_payload / store_payload_to_df
# ---------------------------------------------------------------------------

class TestStoreCodec:
    def test_none_payload(self):
        assert store_payload_to_df(None) is None

    def test_codebook_roundtrip_with_missing(self):
        """Colonne texte répétitive avec valeur manquante : encodage codebook."""
        df = pd.DataFrame({'diag': ['A', 'A', None, 'B', 'A']})
        payload = df_to_store_payload(df)
        assert 'diag' in payload['codebook']
        out = store_payload_to_df(payload)
        assert out['diag'].tolist() == ['A', 'A', None, 'B', 'A']

    def test_high_cardinality_column_not_codebooked(self):
        """Un identifiant unique par ligne ne doit pas passer par le codebook."""
        df = pd.DataFrame({'id': [f'P{i}' for i in range(100)]})
        payload = df_to_store_payload(df)
        assert 'id' not in payload['codebook']
        out = store_payload_to_df(payload)
        assert out['id'].tolist() == df['id'].tolist()

    def test_datetime_serialized_as_iso(self):
        df = pd.DataFrame({'date': pd.to_datetime(['2023-03-05', None])})
        payload = df_to_store_payload(df)
        values = [row[0] for row in payload['data']]
        assert values == ['2023-03-05T00:00:00', None]

    def test_numeric_and_missing(self):
        df = pd.DataFrame({'age': [58.0, np.nan, 42.0]})
        out = store_payload_to_df(df_to_store_payload(df))
        assert out['age'].iloc[0] == 58.0
        assert pd.isna(out['age'].iloc[1])

    def test_columns_subset(self):
        df = pd.DataFrame({'a': [1], 'b': [2], 'c': [3]})
        payload = df_to_store_payload(df, columns=['a', 'c'])
        assert payload['columns'] == ['a', 'c']


# ---------------------------------------------------------------------------
# Intégration : process_data sur le fichier d'exemple réel
# ---------------------------------------------------------------------------

class TestProcessDataIntegration:
    DERIVED_COLUMNS = [
        'Year', 'Age At Diagnosis', 'Age Groups', 'Age Group Detailed',
        'Diagnosis Category', 'Greffes', 'Blood + Rh', 'Donor Match Category',
    ]

    def test_derived_columns_created(self, processed_df):
        for col in self.DERIVED_COLUMNS:
            assert col in processed_df.columns, f"Colonne dérivée manquante : {col}"

    def test_no_row_added_or_removed(self, raw_df, processed_df):
        assert len(processed_df) == len(raw_df)

    def test_year_matches_treatment_date(self, processed_df):
        """Year doit correspondre à l'année de Treatment Date pour chaque ligne."""
        expected = processed_df['Treatment Date'].dt.year
        valid = expected.notna()
        actual = pd.to_numeric(processed_df.loc[valid, 'Year'], errors='coerce')
        assert (actual == expected[valid]).all()

    def test_first_row_values(self, processed_df):
        """Valeurs de la première ligne, vérifiées à la main depuis le CSV."""
        row = processed_df.iloc[0]
        assert row['Year'] == '2023'
        assert row['Age At Diagnosis'] == 58
        assert str(row['Age Groups']) == '40-64'
        assert row['Greffes'] == 'Unrelated donor - Peripheral blood'
        assert row['Blood + Rh'] == 'A+'
        assert row['Donor Match Category'] == 'Unrelated + Unknown'
        assert row['Diagnosis Category'] == 'Malignant'
        assert row['Conditioning Regimen Type'] == 'RIC'

    def test_age_groups_ordered_categorical(self, processed_df):
        cats = list(processed_df['Age Groups'].cat.categories)
        assert cats == ['18-', '18-39', '40-64', '65-74', '75+']
        assert processed_df['Age Groups'].cat.ordered

    def test_age_at_diagnosis_coherent(self, processed_df):
        """L'âge recalculé depuis les dates doit correspondre à la colonne."""
        days = (processed_df['Date Diagnosis'] - processed_df['Date Of Birth']).dt.days
        expected = days // 365.25
        both_valid = expected.notna() & processed_df['Age At Diagnosis'].notna()
        assert (processed_df.loc[both_valid, 'Age At Diagnosis'] == expected[both_valid]).all()

    def test_conditioning_values_abbreviated(self, processed_df):
        values = set(processed_df['Conditioning Regimen Type'].dropna().unique())
        assert 'Reduced intensity conditioning (RIC)' not in values
        assert 'Myeloablative conditioning regimen' not in values
        assert 'RIC' in values

    def test_prep_regimen_only_yes_no(self, processed_df):
        col = 'Prep Regimen Busulfan'
        if col in processed_df.columns:
            assert set(processed_df[col].unique()) <= {'Yes', 'No'}

    def test_full_codec_roundtrip(self, processed_df):
        """Le payload store doit être JSON-sérialisable et fidèle à la valeur."""
        import json
        cols = ['Long ID', 'Main Diagnosis', 'Treatment Date', 'Age At Diagnosis']
        payload = df_to_store_payload(processed_df, columns=cols)
        json.dumps(payload)  # lève une exception si non sérialisable
        out = store_payload_to_df(payload)
        assert list(out.columns) == cols
        assert out['Long ID'].tolist() == processed_df['Long ID'].tolist()
        # Les valeurs manquantes reviennent en None (comportement documenté du codec)
        expected_diag = [None if pd.isna(v) else v for v in processed_df['Main Diagnosis']]
        assert out['Main Diagnosis'].tolist() == expected_diag
