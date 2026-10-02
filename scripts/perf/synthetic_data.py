"""
Générateur de jeu de données SYNTHÉTIQUE pour les tests de performance AlloGraph.

Ne contient aucune donnée patient réelle : toutes les valeurs sont tirées
aléatoirement (graine fixe) avec des distributions approximatives déduites du
schéma EBMT attendu par modules/data_processing.py.

Usage CLI :
    python scripts/perf/synthetic_data.py [n_rows] [output_csv]
"""

import sys

import numpy as np
import pandas as pd

# Graine fixe : le jeu généré est strictement reproductible
SEED = 42
DEFAULT_N_ROWS = 16_000

# Ordre exact des colonnes attendu par modules/data_processing.py (EXPECTED_COLUMNS)
COLUMNS = [
    'Long ID', 'Short ID', 'Promise ID', 'Sex', 'Date Of Birth', 'Blood Group',
    'Rhesus Factor', 'Initials First Name', 'Initials Last Name', 'Date Diagnosis',
    'Main Diagnosis', 'Subclass Diagnosis', 'Treatment CIC', 'Treatment Type',
    'Treatment Date', 'Number HCT', 'Number Allo HCT', 'Performance Status At Treatment Scale',
    'Performance Status At Treatment Score', 'Disease Status At Treatment', 'CMV Status Donor',
    'CMV Status Patient', 'Donor Type', 'Source Stem Cells', 'Source Stem Cells 2',
    'Match Type', 'Conditioning Regimen Type', 'Prep Regimen Bendamustine',
    'Prep Regimen Busulfan', 'Prep Regimen Cyclophosphamide', 'Prep Regimen Fludarabine',
    'Prep Regimen Melphalan', 'Prep Regimen Thiotepa', 'Prep Regimen Treosulfan',
    'Prophylaxis', 'Prophylaxis Drug 1', 'Prophylaxis Drug 2', 'Prophylaxis Drug 3',
    'Prophylaxis Drug 4', 'Prophylaxis Drug 5', 'Prophylaxis Drug 6', 'TBI', 'TBI Dose Gray',
    'Date Of Last Follow Up', 'First aGvHD Maximum Score', 'First Agvhd Occurrence',
    'First Agvhd Occurrence Date', 'First cGvHD Maximum NIH Score', 'First Cgvhd Occurrence',
    'First Cgvhd Occurrence Date', 'First Relapse', 'First Relapse Date', 'First Best Response',
    'First Best Response Date', 'Platelet Reconstitution', 'Date Platelet Reconstitution',
    'Anc Recovery', 'Date Anc Recovery', 'Date Subsequent Treatment',
    'Performance Scale At Last FU', 'Performance Score At Last FU',
    'Cgvhd Maximum Nih Score At Last Fu', 'Cgvhd Occurrence At Last Fu',
    'Status Last Follow Up', 'Death Cause', 'Death Date'
]

DATE_FMT = '%d/%m/%Y %H:%M'

# Schémas de prophylaxie plausibles (combinaisons -> probabilités), incluant les
# libellés qui déclenchent le mapping spécial de process_prophylaxis_drugs
PROPHYLAXIS_SCHEMES = [
    (['cyclosporine', 'mycophenolate mofetil'], 0.22),
    (['cyclosporine', 'methotrexate'], 0.18),
    (['Drug Anti-Thymocyte Globulin or Anti-Lymphocyte Globulin', 'cyclosporine', 'methotrexate'], 0.12),
    (['lymphocyte immune globulin, anti-thymocyte globulin', 'cyclosporine', 'mycophenolate mofetil'], 0.10),
    (['cyclophosphamide', 'tacrolimus', 'mycophenolate mofetil'], 0.10),
    (['tacrolimus', 'methotrexate'], 0.08),
    (['cyclosporine'], 0.06),
    (['antilymphocyte immunoglobulin', 'cyclosporine'], 0.05),
    (['cyclophosphamide', 'cyclosporine'], 0.04),
    (['alemtuzumab', 'cyclosporine'], 0.02),
    (['sirolimus', 'tacrolimus'], 0.02),
    ([], 0.01),
]


def _choice(rng, options, weights, n):
    """Tirage vectorisé dans une liste d'options avec poids (None -> valeur manquante)."""
    probs = np.asarray(weights, dtype=float)
    probs = probs / probs.sum()
    idx = rng.choice(len(options), size=n, p=probs)
    return np.array(options, dtype=object)[idx]


def _fmt(dates):
    """Formate une Series de timestamps en chaînes 'dd/mm/yyyy HH:MM' (NaT -> '')."""
    return dates.dt.strftime(DATE_FMT).fillna('')


def generate_synthetic_dataframe(n_rows=DEFAULT_N_ROWS, seed=SEED):
    """
    Génère un DataFrame synthétique de n_rows lignes au schéma EBMT/AlloGraph.

    Les dates sont cohérentes entre elles (diagnostic <= greffe <= événements <= suivi)
    pour exercer les mêmes chemins de code que les vraies données.

    Args:
        n_rows (int): nombre de lignes à générer
        seed (int): graine du générateur aléatoire

    Returns:
        pd.DataFrame: données synthétiques (toutes colonnes en texte, comme un CSV)
    """
    rng = np.random.default_rng(seed)
    n = n_rows

    # --- Dates de référence -------------------------------------------------
    # Greffe uniforme entre fév. 2018 et déc. 2024 (comme l'échantillon de test)
    t0 = pd.Timestamp('2018-02-01').value
    t1 = pd.Timestamp('2024-12-30').value
    treatment_date = pd.Series(pd.to_datetime(rng.integers(t0, t1, size=n))).dt.normalize()

    # Âge au diagnostic : approximation de la distribution clinique (0-80 ans)
    age_at_diag = np.clip(rng.gamma(shape=6.0, scale=8.5, size=n) - 3, 0, 80).round().astype(int)
    diag_gap_days = np.clip(rng.lognormal(mean=4.8, sigma=1.0, size=n), 1, 4000).astype(int)
    date_diagnosis = treatment_date - pd.to_timedelta(diag_gap_days, unit='D')
    date_of_birth = date_diagnosis - pd.to_timedelta((age_at_diag * 365.25).astype(int), unit='D') \
        - pd.to_timedelta(rng.integers(0, 365, size=n), unit='D')

    # Suivi : durée log-normale (médiane ~2 ans), plafonnée fin 2025
    followup_days = np.clip(rng.lognormal(mean=6.6, sigma=1.0, size=n), 10, 2800).astype(int)
    date_last_fu = treatment_date + pd.to_timedelta(followup_days, unit='D')
    date_last_fu = date_last_fu.clip(upper=pd.Timestamp('2025-12-25'))
    followup_days = (date_last_fu - treatment_date).dt.days.to_numpy()

    # Statut au dernier suivi (~26 % de décès, cohérent avec l'échantillon)
    status = _choice(rng, ['Alive', 'Dead', None], [0.72, 0.265, 0.015], n)
    is_dead = status == 'Dead'
    # Date de décès : entre la greffe et le dernier suivi
    death_offset = (followup_days * rng.uniform(0.02, 0.95, size=n)).astype(int)
    death_date = treatment_date + pd.to_timedelta(death_offset, unit='D')
    death_date = death_date.where(is_dead, pd.NaT)

    # --- Colonnes catégorielles (poids déduits du schéma / échantillon) -----
    sex = _choice(rng, ['male', 'female'], [0.584, 0.416], n)
    blood = _choice(rng, ['O', 'A', 'unknown', 'B', 'AB'], [0.381, 0.358, 0.126, 0.082, 0.053], n)
    rhesus = _choice(rng, ['positive', 'unknown', 'negative'], [0.761, 0.128, 0.111], n)

    main_diag = _choice(
        rng,
        ['Acute leukemia', 'Myelodysplastic syndrome', 'Lymphoma', 'Myeloproliferative disorder',
         'Bone Marrow Failure incl. Aplastic Anemia', 'Myelodysplastic/myeloproliferative disease',
         'Inborn Errors', 'Hemoglobinopathy', 'Chronic leukemia', 'Plasma cell neoplasm',
         'Other Diagnosis', None],
        [0.524, 0.115, 0.102, 0.062, 0.051, 0.040, 0.033, 0.027, 0.022, 0.009, 0.007, 0.004], n)

    subclass_pool = {
        'Acute leukemia': ['Acute myeloid leukemia, disease', 'Acute lymphoid leukemia'],
        'Lymphoma': ['T-cell lymphoma (clinical)', "B-cell non-Hodgkin's lymphoma"],
        'Myelodysplastic syndrome': ['Myelodysplastic syndrome with excess blasts-2',
                                     'Myelodysplastic syndrome with excess blasts-1'],
        'Myeloproliferative disorder': ['Primary myelofibrosis'],
        'Bone Marrow Failure incl. Aplastic Anemia': ['Bone marrow Failure Syndromes incl. AA acquired'],
        'Myelodysplastic/myeloproliferative disease': ['Chronic myelomonocytic leukemia'],
        'Inborn Errors': ['Primary immune deficiency disorder'],
    }
    subclass = np.array([
        rng.choice(subclass_pool[d]) if d in subclass_pool and rng.random() > 0.05
        else (None if rng.random() < 0.03 else 'Other')
        for d in main_diag
    ], dtype=object)

    perf_scale = _choice(
        rng,
        ['Karnofsky performance status', 'Lansky performance status',
         'ECOG Performance Status score', None, 'Not assessed'],
        [0.708, 0.153, 0.069, 0.053, 0.018], n)
    perf_score = np.empty(n, dtype=object)
    karno = np.isin(perf_scale, ['Karnofsky performance status', 'Lansky performance status'])
    perf_score[karno] = _choice(rng, ['100', '90', '80', '70', '60', '50'],
                                [0.45, 0.23, 0.20, 0.05, 0.04, 0.03], karno.sum())
    ecog = perf_scale == 'ECOG Performance Status score'
    perf_score[ecog] = _choice(rng, ['0', '1', '2'], [0.55, 0.33, 0.12], ecog.sum())
    rest = ~(karno | ecog)
    perf_score[rest] = _choice(rng, [None, 'Unknown'], [0.75, 0.25], rest.sum())

    disease_status = _choice(
        rng,
        ['First complete haematological remission (CR)', None, 'In full remission',
         'Second complete haematological remission (CR)',
         'Never treated (supportive care or treatment without chemotherapy)',
         'In partial remission', "Patient's condition improved",
         'Primary refractory phase (no change)', 'Progressive disease',
         'Primary induction failure', 'Chronic phase', 'First relapse'],
        [0.325, 0.179, 0.131, 0.100, 0.044, 0.035, 0.024, 0.020, 0.020, 0.018, 0.013, 0.013], n)

    cmv_donor = _choice(
        rng,
        ['Transplant donor cytomegalovirus antibody negative',
         'Transplant donor cytomegalovirus antibody positive', None, 'Not assessed'],
        [0.493, 0.480, 0.022, 0.004], n)
    cmv_patient = _choice(rng, ['Positive', 'Negative', None, 'Not assessed'],
                          [0.533, 0.431, 0.031, 0.004], n)

    donor_type = _choice(rng, ['Unrelated donor', 'Related donor', None],
                         [0.500, 0.476, 0.024], n)
    source_cells = _choice(rng, ['Peripheral blood', 'Bone marrow', 'Cord blood', None],
                           [0.739, 0.210, 0.033, 0.018], n)
    source_cells_2 = _choice(rng, [None, 'Peripheral blood', 'Unknown'],
                             [0.989, 0.009, 0.002], n)
    match_type = _choice(rng, [None, 'Match', 'Mismatch'], [0.522, 0.252, 0.226], n)

    conditioning = _choice(
        rng,
        ['Reduced intensity conditioning (RIC)', 'Myeloablative conditioning regimen', None],
        [0.549, 0.438, 0.013], n)

    # Médicaments du conditionnement (Oui/Non épars)
    prep_probs = {
        'Prep Regimen Bendamustine': 0.01,
        'Prep Regimen Busulfan': 0.25,
        'Prep Regimen Cyclophosphamide': 0.30,
        'Prep Regimen Fludarabine': 0.60,
        'Prep Regimen Melphalan': 0.10,
        'Prep Regimen Thiotepa': 0.03,
        'Prep Regimen Treosulfan': 0.03,
    }
    prep = {col: np.where(rng.random(n) < p, 'Yes', 'No') for col, p in prep_probs.items()}

    # --- Prophylaxie : tirage de schémas complets puis dispatch en colonnes -
    schemes, scheme_w = zip(*PROPHYLAXIS_SCHEMES)
    scheme_idx = rng.choice(len(schemes), size=n, p=np.asarray(scheme_w) / sum(scheme_w))
    prophylaxis = _choice(rng, ['yes', 'no', None, 'unknown'], [0.980, 0.011, 0.007, 0.002], n)
    drug_cols = {f'Prophylaxis Drug {i}': np.full(n, '', dtype=object) for i in range(1, 7)}
    for row_i, sch_i in enumerate(scheme_idx):
        for j, drug in enumerate(schemes[sch_i][:6]):
            drug_cols[f'Prophylaxis Drug {j + 1}'][row_i] = drug

    # --- TBI -----------------------------------------------------------------
    tbi = _choice(rng, ['No', 'Yes', None], [0.759, 0.221, 0.020], n)
    tbi_dose = np.full(n, None, dtype=object)
    has_tbi = tbi == 'Yes'
    tbi_dose[has_tbi] = _choice(rng, [2.0, 12.0, 8.0, 6.0, 10.0, 4.0],
                                [0.37, 0.36, 0.20, 0.03, 0.02, 0.02], has_tbi.sum())

    # --- Événements cliniques -------------------------------------------------
    # GvH aiguë : ~47 % de 'Yes', date entre J+5 et J+120 (<= suivi)
    agvhd_occ = _choice(rng, ['Yes', 'No evidence of', None, 'Unknown', 'Not assessed'],
                        [0.471, 0.347, 0.173, 0.007, 0.002], n)
    has_agvhd = agvhd_occ == 'Yes'
    agvhd_offset = np.minimum(rng.integers(5, 120, size=n), np.maximum(followup_days, 5))
    agvhd_date = (treatment_date + pd.to_timedelta(agvhd_offset, unit='D')).where(has_agvhd, pd.NaT)
    agvhd_score = np.full(n, None, dtype=object)
    agvhd_score[has_agvhd] = _choice(
        rng, ['Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Unknown', 'Grade 0 (none)'],
        [0.385, 0.366, 0.127, 0.089, 0.023, 0.009], has_agvhd.sum())

    # GvH chronique : ~23 % de 'Yes', date entre J+90 et J+450
    cgvhd_occ = _choice(rng, ['No evidence of', 'Yes', None, 'Unknown'],
                        [0.580, 0.228, 0.184, 0.009], n)
    has_cgvhd = cgvhd_occ == 'Yes'
    cgvhd_offset = np.minimum(rng.integers(90, 450, size=n), np.maximum(followup_days, 90))
    cgvhd_date = (treatment_date + pd.to_timedelta(cgvhd_offset, unit='D')).where(has_cgvhd, pd.NaT)
    cgvhd_score = np.full(n, None, dtype=object)
    cgvhd_score[has_cgvhd] = _choice(
        rng, ['Moderate', 'Mild', 'Severe', 'Limited', 'Not done', 'Extensive', 'Unknown'],
        [0.368, 0.300, 0.155, 0.087, 0.049, 0.029, 0.010], has_cgvhd.sum())

    # Rechute : ~17,5 %, date entre J+30 et J+1500 (<= suivi)
    relapse = _choice(rng, ['No', 'Yes', None, 'Unknown', 'Disease progression'],
                      [0.730, 0.175, 0.088, 0.004, 0.002], n)
    has_relapse = relapse == 'Yes'
    relapse_offset = np.minimum(rng.integers(30, 1500, size=n), np.maximum(followup_days, 30))
    relapse_date = (treatment_date + pd.to_timedelta(relapse_offset, unit='D')).where(has_relapse, pd.NaT)

    # Meilleure réponse
    best_resp = _choice(
        rng,
        ['In full remission', None, 'Not assessed', 'Sustained Full Remission', 'Never in CR',
         'Progressive disease', "Patient's condition improved", 'In partial remission',
         'Chronic phase', 'Unknown', 'Other', 'Death'],
        [0.699, 0.104, 0.060, 0.033, 0.029, 0.027, 0.013, 0.013, 0.004, 0.004, 0.002, 0.002], n)
    best_resp_offset = np.minimum(rng.integers(20, 200, size=n), np.maximum(followup_days, 20))
    best_resp_date = (treatment_date + pd.to_timedelta(best_resp_offset, unit='D'))
    best_resp_date = best_resp_date.where(pd.notna(best_resp), pd.NaT)

    # Reconstitutions
    platelets = _choice(rng, ['Yes', None], [0.730, 0.270], n)
    has_platelets = platelets == 'Yes'
    platelets_offset = np.minimum(rng.integers(8, 60, size=n), np.maximum(followup_days, 8))
    platelets_date = (treatment_date + pd.to_timedelta(platelets_offset, unit='D')).where(has_platelets, pd.NaT)

    anc = _choice(rng, ['Yes', None], [0.892, 0.108], n)
    has_anc = anc == 'Yes'
    anc_offset = np.minimum(rng.integers(8, 40, size=n), np.maximum(followup_days, 8))
    anc_date = (treatment_date + pd.to_timedelta(anc_offset, unit='D')).where(has_anc, pd.NaT)

    # Traitement ultérieur : ~5 %
    subsequent = rng.random(n) < 0.053
    subsequent_offset = np.minimum(rng.integers(100, 900, size=n), np.maximum(followup_days, 100))
    subsequent_date = (treatment_date + pd.to_timedelta(subsequent_offset, unit='D')).where(subsequent, pd.NaT)

    # Dernier suivi GvHc
    cgvhd_fu_occ = _choice(rng, [None, 'Yes'], [0.900, 0.100], n)
    has_cgvhd_fu = cgvhd_fu_occ == 'Yes'
    cgvhd_fu_score = np.full(n, None, dtype=object)
    cgvhd_fu_score[has_cgvhd_fu] = _choice(
        rng, ['Mild', 'Moderate', 'Severe', 'Limited', 'Not done', 'Unknown', 'Extensive'],
        [0.378, 0.244, 0.222, 0.067, 0.044, 0.022, 0.022], has_cgvhd_fu.sum())

    death_cause = np.full(n, None, dtype=object)
    death_cause[is_dead] = _choice(
        rng, ['HCT-related cause of death', 'Relapse/progression', 'Other', 'Secondary malignant'],
        [0.454, 0.403, 0.076, 0.042], is_dead.sum())

    # --- Identifiants synthétiques -------------------------------------------
    long_id = np.array([f'SYN-{i:06d}' for i in range(1, n + 1)], dtype=object)
    short_id = np.array([f'S{i:05d}' for i in range(1, n + 1)], dtype=object)
    promise_id = np.full(n, '', dtype=object)
    initials_first = np.array([chr(65 + x) for x in rng.integers(0, 26, size=n)], dtype=object)
    initials_last = np.array([chr(65 + x) for x in rng.integers(0, 26, size=n)], dtype=object)
    treatment_cic = np.array([str(x) for x in rng.integers(100, 900, size=n)], dtype=object)

    number_hct = _choice(rng, [1.0, 2.0, 3.0, None], [0.865, 0.126, 0.007, 0.002], n)
    number_allo = _choice(rng, [1.0, 2.0, 3.0, None], [0.929, 0.064, 0.004, 0.002], n)

    data = {
        'Long ID': long_id,
        'Short ID': short_id,
        'Promise ID': promise_id,
        'Sex': sex,
        'Date Of Birth': _fmt(date_of_birth),
        'Blood Group': blood,
        'Rhesus Factor': rhesus,
        'Initials First Name': initials_first,
        'Initials Last Name': initials_last,
        'Date Diagnosis': _fmt(date_diagnosis),
        'Main Diagnosis': main_diag,
        'Subclass Diagnosis': subclass,
        'Treatment CIC': treatment_cic,
        'Treatment Type': 'Allogeneic HCT',
        'Treatment Date': _fmt(treatment_date),
        'Number HCT': number_hct,
        'Number Allo HCT': number_allo,
        'Performance Status At Treatment Scale': perf_scale,
        'Performance Status At Treatment Score': perf_score,
        'Disease Status At Treatment': disease_status,
        'CMV Status Donor': cmv_donor,
        'CMV Status Patient': cmv_patient,
        'Donor Type': donor_type,
        'Source Stem Cells': source_cells,
        'Source Stem Cells 2': source_cells_2,
        'Match Type': match_type,
        'Conditioning Regimen Type': conditioning,
        **prep,
        'Prophylaxis': prophylaxis,
        **drug_cols,
        'TBI': tbi,
        'TBI Dose Gray': tbi_dose,
        'Date Of Last Follow Up': _fmt(date_last_fu.where(rng.random(n) > 0.015, pd.NaT)),
        'First aGvHD Maximum Score': agvhd_score,
        'First Agvhd Occurrence': agvhd_occ,
        'First Agvhd Occurrence Date': _fmt(agvhd_date),
        'First cGvHD Maximum NIH Score': cgvhd_score,
        'First Cgvhd Occurrence': cgvhd_occ,
        'First Cgvhd Occurrence Date': _fmt(cgvhd_date),
        'First Relapse': relapse,
        'First Relapse Date': _fmt(relapse_date),
        'First Best Response': best_resp,
        'First Best Response Date': _fmt(best_resp_date),
        'Platelet Reconstitution': platelets,
        'Date Platelet Reconstitution': _fmt(platelets_date),
        'Anc Recovery': anc,
        'Date Anc Recovery': _fmt(anc_date),
        'Date Subsequent Treatment': _fmt(subsequent_date),
        'Performance Scale At Last FU': np.full(n, None, dtype=object),
        'Performance Score At Last FU': np.full(n, None, dtype=object),
        'Cgvhd Maximum Nih Score At Last Fu': cgvhd_fu_score,
        'Cgvhd Occurrence At Last Fu': cgvhd_fu_occ,
        'Status Last Follow Up': status,
        'Death Cause': death_cause,
        'Death Date': _fmt(death_date),
    }

    df = pd.DataFrame(data, columns=COLUMNS)
    # Valeurs manquantes -> NaN (comme à la lecture d'un CSV avec cellules vides)
    df = df.replace({None: np.nan, '': np.nan})
    # Promise ID et initiales ne doivent pas devenir NaN
    df['Promise ID'] = df['Promise ID'].fillna('')
    return df


def main():
    n_rows = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_N_ROWS
    output = sys.argv[2] if len(sys.argv) > 2 else 'data/synthetic_16k.csv'
    df = generate_synthetic_dataframe(n_rows)
    df.to_csv(output, index=False)
    print(f"Jeu synthétique écrit : {output} ({len(df)} lignes, {len(df.columns)} colonnes)")


if __name__ == '__main__':
    main()
