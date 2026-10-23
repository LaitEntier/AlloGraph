# utils/missing_export.py
"""Génération du classeur Excel des données manquantes (export global).

La logique métier vit ici (et non dans une page) car la feuille 'All'
analyse par nature l'ensemble des colonnes du jeu de données : le callback
global de app.py consomme le store complet et délègue la construction du
classeur à ce module.
"""
from datetime import datetime
from io import BytesIO

import pandas as pd

import visualizations.allogreffes.graphs as gr

# Colonnes du tableau de détail des données manquantes
DETAIL_COLUMNS = ['Long ID', 'Missing columns', 'Nb missing']

# Sections thématiques : nom de la feuille -> colonnes à analyser
SECTION_COLUMNS = {
    'Patient': [
        'Age At Diagnosis',
        'Main Diagnosis',
        'Sex',
        'Blood + Rh',
        'Number HCT',
        'Number Allo HCT',
        'Performance Status At Treatment Scale',
        'Performance Status At Treatment Score'
    ],
    'Indications': [
        'Main Diagnosis',
        'Subclass Diagnosis',
        'Age Groups',
        'Blood Group',
        'Rhesus Factor',
        'Disease Status At Treatment'
    ],
    'Procedures': [
        'Donor Type',
        'Source Stem Cells',
        'Match Type',
        'Conditioning Regimen Type',
        'Donor Match Category',
        'Treatment Date',
        'Anc Recovery',
        'Date Anc Recovery',
        'Platelet Reconstitution',
        'Date Platelet Reconstitution'
    ],
    'GVH': [
        # Variables GvH Aiguë
        'First Agvhd Occurrence',
        'First aGvHD Maximum Score',
        'First Agvhd Occurrence Date',
        # Variables GvH Chronique
        'First Cgvhd Occurrence',
        'First cGvHD Maximum NIH Score',
        'First Cgvhd Occurrence Date',
        # Variables de suivi
        'Status Last Follow Up',
        'Date Of Last Follow Up'
    ],
    'Relapse': [
        # Variables de rechute
        'First Relapse',
        'First Relapse Date',
        # Variables de traitement et suivi
        'Treatment Date',
        'Status Last Follow Up',
        'Date Of Last Follow Up'
    ],
    'Survival': [
        'Treatment Date',
        'Date Of Last Follow Up',
        'Status Last Follow Up',
        'First Agvhd Occurrence',
        'First Agvhd Occurrence Date',
        'First Cgvhd Occurrence',
        'First Cgvhd Occurrence Date',
        'First Relapse',
        'First Relapse Date',
        'First aGvHD Maximum Score',
        'First cGvHD Maximum NIH Score',
        'Year'
    ],
    'Toxicity': [
        'Status Last Follow Up',
        'Date Of Last Follow Up',
        'First Relapse',
        'First Relapse Date',
        'Treatment Date'
    ]
}

INDICATORS = ['prise_greffe', 'sortie_aplasie', 'TRM', 'gvha', 'gvhc', 'rechute', 'survie_globale']


def _detail_dataframe(detailed_missing, indicator_name=None):
    """
    Convertit le résultat de gr.analyze_missing_data en DataFrame d'export.

    Retourne toujours les colonnes attendues, même sans donnée manquante,
    afin d'écrire une feuille vide plutôt que d'interrompre l'export.
    """
    columns = DETAIL_COLUMNS + (['Indicator'] if indicator_name is not None else [])
    rows = []
    for _, row in detailed_missing.iterrows():
        record = {col: row[col] for col in DETAIL_COLUMNS}
        if indicator_name is not None:
            record['Indicator'] = indicator_name
        rows.append(record)
    return pd.DataFrame(rows, columns=columns)


def build_missing_data_workbook(df):
    """
    Construit le classeur Excel des données manquantes et retourne ses bytes.

    Feuilles : All (toutes colonnes), une par section thématique, puis une
    par indicateur clinique.
    """
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Feuille 'All' : toutes les colonnes du jeu de données
    _, detailed_missing = gr.analyze_missing_data(df, list(df.columns), 'Long ID')
    _detail_dataframe(detailed_missing).to_excel(writer, sheet_name='All', index=False)

    # Feuilles par section thématique
    for sheet_name, columns_to_analyze in SECTION_COLUMNS.items():
        existing_columns = [col for col in columns_to_analyze if col in df.columns]
        _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
        _detail_dataframe(detailed_missing).to_excel(writer, sheet_name=sheet_name, index=False)

    # Feuilles par indicateur
    from pages.indics import get_variables_for_indicator
    for selected_indicator in INDICATORS:
        columns_to_analyze, indicator_name = get_variables_for_indicator(selected_indicator)
        existing_columns = [col for col in columns_to_analyze if col in df.columns]
        _, detailed_missing = gr.analyze_missing_data(df, existing_columns, 'Long ID')
        _detail_dataframe(detailed_missing, indicator_name=indicator_name).to_excel(
            writer, sheet_name='Indicators_' + selected_indicator, index=False)

    writer.close()
    return output.getvalue()


def get_missing_export_filename():
    """Retourne le nom de fichier horodaté pour l'export des données manquantes."""
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"donnees_manquantes_{current_date}.xlsx"
