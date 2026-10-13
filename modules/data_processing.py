import pandas as pd
import numpy as np

# Column name mapping - defines the standard names we expect
# The processing will accept any case variation of these names
EXPECTED_COLUMNS = [
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

def normalize_column_names(df):
    """
    Normalise les noms de colonnes pour accepter n'importe quelle casse
    et gère les noms de colonnes alternatifs connus.
    
    Args:
        df (pd.DataFrame): DataFrame avec les colonnes originales
        
    Returns:
        pd.DataFrame: DataFrame avec les noms de colonnes normalisés
    """
    df = df.copy()
    
    # Mapping pour les noms de colonnes alternatifs (synonymes connus)
    # Clé: nom alternatif en minuscules -> Valeur: nom standard
    alternate_names = {
        'match type related donor': 'Match Type',
    }
    
    # Créer un mapping des noms en minuscules vers les noms standards
    lower_to_standard = {col.lower(): col for col in EXPECTED_COLUMNS}
    
    # Renommer les colonnes
    new_columns = {}
    for col in df.columns:
        col_lower = col.lower()
        
        # Vérifier d'abord les noms alternatifs
        if col_lower in alternate_names:
            standard_name = alternate_names[col_lower]
            if col != standard_name:
                new_columns[col] = standard_name
                print(f"Colonne renommée (synonyme): '{col}' -> '{standard_name}'")
        # Ensuite vérifier les noms standards (insensible à la casse)
        elif col_lower in lower_to_standard:
            standard_name = lower_to_standard[col_lower]
            if col != standard_name:
                new_columns[col] = standard_name
                print(f"Colonne renommée: '{col}' -> '{standard_name}'")
    
    if new_columns:
        df.rename(columns=new_columns, inplace=True)
    
    return df

def detect_csv_separator(file_path_or_content, is_file_path=True):
    """
    Détecte automatiquement le séparateur CSV en testant les séparateurs courants.
    
    Args:
        file_path_or_content: Chemin vers le fichier ou contenu string/bytes
        is_file_path: True si file_path_or_content est un chemin, False si c'est du contenu
        
    Returns:
        str: Le séparateur détecté (par défaut ',' si aucun n'est clairement meilleur)
    """
    common_separators = [',', ';', '\t', '|']
    
    try:
        # Lire un échantillon des données
        if is_file_path:
            with open(file_path_or_content, 'r', encoding='utf-8', errors='ignore') as f:
                sample = f.read(5000)  # Lire les premiers 5000 caractères
        else:
            # C'est du contenu (string ou bytes)
            content = file_path_or_content
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            sample = content[:5000]
        
        best_separator = ','
        max_cols = 0
        
        for sep in common_separators:
            try:
                # Compter le nombre de colonnes sur les premières lignes
                lines = sample.strip().split('\n')[:5]  # Tester sur 5 lignes max
                if not lines:
                    continue
                    
                col_counts = []
                for line in lines:
                    if line.strip():  # Ignorer les lignes vides
                        col_counts.append(len(line.split(sep)))
                
                if col_counts:
                    # Utiliser le mode (valeur la plus fréquente) pour éviter les lignes malformées
                    from statistics import mode
                    try:
                        most_common_count = mode(col_counts)
                    except:
                        most_common_count = max(col_counts)
                    
                    # On veut au moins 2 colonnes et le maximum de colonnes cohérent
                    if most_common_count > max_cols and most_common_count > 1:
                        max_cols = most_common_count
                        best_separator = sep
            except Exception:
                continue
        
        return best_separator
    except Exception:
        return ','  # Fallback sur la virgule


def load_data(file_path):
    """
    Charge et prépare les données à partir d'un fichier CSV exporté de REDCap.
    Détecte automatiquement le séparateur utilisé.

    Args:
        file_path (str): Chemin vers le fichier CSV

    Returns:
        pd.DataFrame: Données nettoyées et formatées
    """
    # Détection du séparateur
    separator = detect_csv_separator(file_path, is_file_path=True)
    
    # Chargement des données avec le séparateur détecté
    df = pd.read_csv(file_path, sep=separator)

    # Nettoyage et formatage de base
    # df = clean_data(df)

    # Calcul de l'âge au diagnostic
    df = process_data(df)

    # Détection du type de données
    # data_type = detect_data_type(df)

    return df

def rename_conditioning_regimen_values(df):
    """
    Renomme les valeurs dans la colonne 'Conditioning Regimen Type' pour les raccourcir.
    
    Args:
        df (pd.DataFrame): DataFrame avec la colonne Conditioning Regimen Type
        
    Returns:
        pd.DataFrame: DataFrame avec les valeurs renommées
    """
    df = df.copy()
    
    # Vérifier si la colonne existe
    if 'Conditioning Regimen Type' not in df.columns:
        print("Attention: Colonne 'Conditioning Regimen Type' non trouvée - renommage ignoré")
        return df
    
    # Dictionnaire de mapping pour le renommage
    conditioning_mapping = {
        'Reduced intensity conditioning (RIC)': 'RIC',
        'Myeloablative conditioning regimen': 'MAC'
    }
    
    # Appliquer le renommage
    df['Conditioning Regimen Type'] = df['Conditioning Regimen Type'].replace(conditioning_mapping)
    
    print("Renommage effectué dans 'Conditioning Regimen Type':")
    print("  'Reduced intensity conditioning (RIC)' -> 'RIC'")
    print("  'Myeloablative conditioning regimen' -> 'MAC'")
    
    return df

def create_hla_compatibility_variable(df):
    """
    Crée une variable 'Donor Match Category' basée sur Donor Type et Match Type.
    Accepte différents formats de valeurs (avec ou sans 'donor').
    
    Args:
        df (pd.DataFrame): DataFrame avec les colonnes Donor Type et Match Type
        
    Returns:
        pd.DataFrame: DataFrame avec la nouvelle colonne 'Donor Match Category'
    """
    df = df.copy()
    
    # Vérifier si les colonnes existent
    if 'Donor Type' not in df.columns or 'Match Type' not in df.columns:
        print("Attention: Colonnes 'Donor Type' ou 'Match Type' manquantes pour créer la variable 'Donor Match Category'")
        df['Donor Match Category'] = 'Unknown + Unknown'
        return df
    
    # Créer la variable combinée (vectorisé)
    d_raw = df['Donor Type']
    m_raw = df['Match Type']

    d_none = d_raw.isna() | (d_raw.astype(str).str.strip() == '')
    m_none = m_raw.isna() | (m_raw.astype(str).str.strip() == '')

    donor = d_raw.astype(str).str.strip()
    match = m_raw.astype(str).str.strip()

    # Normalisation du type de donneur (mêmes règles qu'avant)
    dl = donor.str.lower()
    is_related = dl.str.contains('related', regex=False) & ~dl.str.contains('un', regex=False)
    is_unrelated = dl.str.contains('unrelated', regex=False) | (
        dl.str.contains('un', regex=False) & dl.str.contains('related', regex=False))
    donor_norm = donor.mask(is_related, 'Related donor').mask(is_unrelated, 'Unrelated donor')

    # Combinaisons quand les deux colonnes sont renseignées
    out = donor_norm + ' + ' + match
    rel = donor_norm == 'Related donor'
    unrel = donor_norm == 'Unrelated donor'
    out = out.mask(rel & (match == 'Match'), 'Genoidentical')
    out = out.mask(rel & (match == 'Mismatch'), 'MRD (Haplo)')
    out = out.mask(unrel & (match == 'Match'), 'MUD')
    out = out.mask(unrel & (match == 'Mismatch'), 'MMUD')

    # Match Type manquant : base Related/Unrelated pour un affichage plus propre
    match_unknown = (donor + ' + Unknown').mask(is_related, 'Related + Unknown') \
        .mask(is_unrelated, 'Unrelated + Unknown')
    out = out.mask(~d_none & m_none, match_unknown)

    # Donor Type manquant
    out = out.where(~(d_none & ~m_none), 'Unknown + ' + match)

    # Les deux manquants
    out = out.where(~(d_none & m_none), 'Unknown + Unknown')

    df['Donor Match Category'] = out

    return df


def _to_datetime_fast(series):
    """
    Parse une colonne de dates de façon vectorisée : tente d'abord le format
    le plus courant ('%d/%m/%Y %H:%M', chemin rapide de pandas), puis repasse
    en 'mixed' (dateutil, élément par élément) sur les valeurs non reconnues.

    Équivalent à pd.to_datetime(dayfirst=True, format='mixed', errors='coerce')
    mais bien plus rapide quand le format est homogène.
    """
    parsed = pd.to_datetime(series, format='%d/%m/%Y %H:%M', errors='coerce')
    mask = parsed.isna() & series.notna()
    if mask.any():
        parsed.loc[mask] = pd.to_datetime(
            series[mask], dayfirst=True, format='mixed', errors='coerce')
    return parsed


def process_data(df):
    """
    Fonction qui prend en entrée un DataFrame et qui applique un traitement sur les données

    Args:
        df (pd.DataFrame): DataFrame contenant les colonnes de départ

    Returns:
        pd.DataFrame: DataFrame avec les données traitées
    """
    # Normaliser les noms de colonnes (insensible à la casse)
    df = normalize_column_names(df)

    # Créer une colonne 'Year' à partir de 'Date Diagnosis'
    df['Treatment Date'] = _to_datetime_fast(df['Treatment Date'])
    df['Year'] = df['Treatment Date'].dt.year.astype(str)

    df['Date Diagnosis'] = _to_datetime_fast(df['Date Diagnosis'])
    df['Date Of Birth'] = _to_datetime_fast(df['Date Of Birth'])
    # Calculer l'age au diagnostic en années
    df['Age At Diagnosis'] = (df['Date Diagnosis'] - df['Date Of Birth']).dt.days // 365.25

    # Créer une colone Age Groups regroupant les patients par tranche d'âge (<18, 18-39, 40-64, 65-74, 75+)
    df['Age Groups'] = pd.cut(df['Age At Diagnosis'], bins=[-1, 17, 39, 64, 74, np.inf], labels=['18-', '18-39', '40-64', '65-74', '75+'], right=True)
    # order the categories for display in barplot
    df['Age Groups'] = pd.Categorical(df['Age Groups'], categories=['18-', '18-39', '40-64', '65-74', '75+'], ordered=True)
    
    # Créer une colonne Age Group Detailed avec des tranches pédiatriques détaillées
    df['Age Group Detailed'] = pd.cut(
        df['Age At Diagnosis'], 
        bins=[-1, 1, 5, 10, 15, 18, np.inf], 
        labels=['<1 year', '1-5 years', '6-10 years', '11-15 years', '16-18 years', '>18 years'], 
        right=False
    )
    # Définir l'ordre des catégories
    df['Age Group Detailed'] = pd.Categorical(
        df['Age Group Detailed'], 
        categories=['<1 year', '1-5 years', '6-10 years', '11-15 years', '16-18 years', '>18 years'], 
        ordered=True
    )
    
    # Créer une colonne Diagnosis Category (Malignant / Non-malignant)
    df = create_diagnosis_category(df)

    # Nouvelle variable : Greffes (combinaison de type de donneur et source des cellules souches)
    df = create_greffes_variable(df)
    
    # Nouvelle variable : Blood + Rh (combinaison de Blood Group et Rhesus Factor)
    df = create_blood_rh_variable(df)
    
    # Nouvelle variable : Donor Match Category (combinaison de Donor Type et Match Type)
    df = create_hla_compatibility_variable(df)
    
    # Renommage des valeurs dans Conditioning Regimen Type
    df = rename_conditioning_regimen_values(df)
    
    # Traitement des variables de préparation de régime pour la page Procedures
    df = process_prep_regimen_variables(df)
    
    # Traitement des variables de prophylaxie
    df = process_prophylaxis_drugs(df)

    return df

def create_greffes_variable(df):
    """
    Crée une variable 'Greffes' basée sur le type de donneur et la source des cellules souches.
    
    Args:
        df (pd.DataFrame): DataFrame avec les colonnes Donor Type et Source Stem Cells
        
    Returns:
        pd.DataFrame: DataFrame avec la nouvelle colonne 'Greffes'
    """
    df = df.copy()
    
    # Vérifier si les colonnes existent
    if 'Donor Type' not in df.columns or 'Source Stem Cells' not in df.columns:
        print("Attention: Colonnes 'Donor Type' ou 'Source Stem Cells' manquantes pour créer la variable 'Greffes'")
        df['Greffes'] = 'Non défini'
        return df
    
    # Créer la variable combinée (vectorisé)
    donor = df['Donor Type'].astype(object)
    stem = df['Source Stem Cells'].astype(object)
    d_unk = donor.isna() | (donor == '')
    s_unk = stem.isna() | (stem == '')

    out = donor + ' - ' + stem
    out = out.where(~(d_unk & ~s_unk), 'Greffe ' + stem)
    out = out.where(~(~d_unk & s_unk), 'Greffe ' + donor)
    out = out.where(~(d_unk & s_unk), 'Non défini')

    df['Greffes'] = out

    return df

def create_blood_rh_variable(df):
    """
    Crée une variable 'Blood + Rh' basée sur Blood Group et Rhesus Factor.
    
    Args:
        df (pd.DataFrame): DataFrame avec les colonnes Blood Group et Rhesus Factor
        
    Returns:
        pd.DataFrame: DataFrame avec la nouvelle colonne 'Blood + Rh'
    """
    df = df.copy()
    
    # Vérifier si les colonnes existent
    if 'Blood Group' not in df.columns or 'Rhesus Factor' not in df.columns:
        print("Attention: Colonnes 'Blood Group' ou 'Rhesus Factor' manquantes pour créer la variable 'Blood + Rh'")
        df['Blood + Rh'] = 'unknown'
        return df
    
    # Créer la variable combinée (vectorisé)
    bg_raw = df['Blood Group']
    rh_raw = df['Rhesus Factor']

    bg_unk = bg_raw.isna() | (bg_raw.astype(str).str.strip() == '')
    rh_unk = rh_raw.isna() | (rh_raw.astype(str).str.strip() == '')

    blood_group = bg_raw.astype(str).str.strip().where(~bg_unk, 'unknown')
    rhesus = rh_raw.astype(str).str.strip().str.lower().where(~rh_unk, 'unknown')

    # Symbole Rhesus : '+'/'-', sinon la valeur brute ('unknown' ou autre)
    rh_symbol = rhesus.mask(rhesus == 'positive', '+').mask(rhesus == 'negative', '-')

    # Exception spéciale : si les deux sont unknown
    both_unknown = (blood_group.str.lower() == 'unknown') & (rhesus == 'unknown')

    df['Blood + Rh'] = (blood_group + rh_symbol).where(~both_unknown, 'unknown')

    return df

def process_prep_regimen_variables(df):
    """
    Traite les variables de préparation de régime pour standardiser les valeurs Yes/No.
    
    Args:
        df (pd.DataFrame): DataFrame avec les colonnes de préparation de régime
        
    Returns:
        pd.DataFrame: DataFrame avec les colonnes traitées
    """
    df = df.copy()
    
    # Liste des colonnes de préparation de régime
    prep_regimen_cols = [
        'Prep Regimen Bendamustine',
        'Prep Regimen Busulfan', 
        'Prep Regimen Cyclophosphamide',
        'Prep Regimen Fludarabine',
        'Prep Regimen Melphalan',
        'Prep Regimen Thiotepa',
        'Prep Regimen Treosulfan'
    ]
    
    # Traiter chaque colonne
    for col in prep_regimen_cols:
        if col in df.columns:
            # Standardiser les valeurs : Yes pour "Yes", "yes", "Y", etc.
            # No pour tout le reste (vide, NaN, "No", etc.)
            normalized = df[col].astype(str).str.strip().str.lower()
            df[col] = np.where(normalized.isin(['yes', 'y', '1', 'true']), 'Yes', 'No')
        else:
            print(f"Attention: Colonne '{col}' non trouvée dans les données")
    
    return df

def process_prophylaxis_drugs(df):
    """
    Parse les colonnes Prophylaxis Drug 1-6 et les transforme en colonnes binaires
    pour chaque traitement unique. Supprime ensuite les colonnes originales.
    
    Args:
        df (pd.DataFrame): DataFrame contenant les colonnes Prophylaxis Drug 1 à 6
        
    Returns:
        pd.DataFrame: DataFrame avec les nouvelles colonnes de traitement (Oui/Non)
                     et sans les colonnes Prophylaxis Drug originales
    """
    df = df.copy()
    
    # Colonnes de traitement prophylactique
    prophylaxis_cols = [f'Prophylaxis Drug {i}' for i in range(1, 7)]
    
    # Vérifier que les colonnes existent
    existing_cols = [col for col in prophylaxis_cols if col in df.columns]
    if not existing_cols:
        print("Aucune colonne Prophylaxis Drug trouvée")
        return df
    
    print(f"Traitement de {len(existing_cols)} colonnes de prophylaxie trouvées")
    
    # Dictionnaire de mapping pour les transformations spéciales
    drug_mapping = {
        'lymphocyte immune globulin': 'ATG',
        'anti-thymocyte globulin': 'ATG',
        'Drug Anti-Thymocyte Globulin or Anti-Lymphocyte Globulin': 'ALTG',
        'antilymphocyte immunoglobulin': 'ALTG'
    }
    
    # --- Version vectorisée (équivalente à l'ancienne boucle iterrows) ---

    # 1. Empiler les colonnes de prophylaxie en format long et filtrer les vides
    stacked = df[existing_cols].stack()
    drug_str = stacked.astype(str)
    keep = stacked.notna() & drug_str.str.strip().ne('') & drug_str.str.lower().ne('nan')
    stacked = stacked[keep]

    # 2. Appliquer le mapping sur les valeurs uniques seulement (insensible à la casse,
    #    première clé du dictionnaire contenue dans la valeur gagne, comme avant)
    def _map_drug(drug):
        drug_lower = drug.lower()
        for original, mapped in drug_mapping.items():
            if original.lower() in drug_lower:
                return mapped
        return drug

    unique_values = stacked.unique()
    value_to_drug = dict(zip(unique_values, [_map_drug(d) for d in unique_values]))

    # Supprimer les valeurs vides (comme avant)
    all_drugs = sorted({d for d in value_to_drug.values() if d.strip()})

    # 3. Paires (ligne, médicament) uniques puis colonnes binaires Oui/Non
    mapped = stacked.map(value_to_drug)
    pairs = pd.DataFrame({
        'row': mapped.index.get_level_values(0),
        'drug': mapped.values,
    }).drop_duplicates()

    for drug in all_drugs:
        column = pd.Series('Non', index=df.index)
        row_idx = pairs.loc[pairs['drug'] == drug, 'row']
        column.loc[row_idx] = 'Oui'
        df[drug] = column

    return df

def process_upset_plot(df):
    """
    Parse les colonnes Prophylaxis Drug 1-6 et les transforme en colonnes binaires
    pour chaque traitement unique. Supprime ensuite les colonnes originales.
    
    Args:
        df (pd.DataFrame): DataFrame contenant les colonnes Prophylaxis Drug 1 à 6
        
    Returns:
        pd.DataFrame: DataFrame avec les nouvelles colonnes de traitement (Oui/Non)
                     et sans les colonnes Prophylaxis Drug originales
    """
    df = df.copy()
    
    # Colonnes de traitement prophylactique
    prophylaxis_cols = [f'Prophylaxis Drug {i}' for i in range(1, 7)]
    # garder uniquement ces colonnes
    df = df[prophylaxis_cols]

    # Vérifier que les colonnes existent
    existing_cols = [col for col in prophylaxis_cols if col in df.columns]
    if not existing_cols:
        print("Aucune colonne Prophylaxis Drug trouvée")
        return df
    
    print(f"Traitement de {len(existing_cols)} colonnes de prophylaxie trouvées")
    
    # Dictionnaire de mapping pour les transformations spéciales
    drug_mapping = {
        'lymphocyte immune globulin': 'ATG',
        'anti-thymocyte globulin': 'ATG',
        'Drug Anti-Thymocyte Globulin or Anti-Lymphocyte Globulin': 'ALTG',
        'antilymphocyte immunoglobulin': 'ALTG'
    }
    
    # --- Version vectorisée (équivalente à l'ancienne boucle iterrows) ---

    # 1. Empiler les colonnes de prophylaxie en format long et filtrer les vides
    stacked = df[existing_cols].stack()
    drug_str = stacked.astype(str)
    keep = stacked.notna() & drug_str.str.strip().ne('') & drug_str.str.lower().ne('nan')
    stacked = stacked[keep]

    # 2. Appliquer le mapping sur les valeurs uniques seulement (mêmes règles qu'avant)
    def _map_drug(drug):
        drug_lower = drug.lower()
        for original, mapped in drug_mapping.items():
            if original.lower() in drug_lower:
                return mapped
        return drug

    unique_values = stacked.unique()
    value_to_drug = dict(zip(unique_values, [_map_drug(d) for d in unique_values]))

    # Supprimer les valeurs vides (comme avant)
    all_drugs = sorted({d for d in value_to_drug.values() if d.strip()})

    # 3. Paires (ligne, médicament) uniques puis colonnes binaires 0/1
    mapped = stacked.map(value_to_drug)
    pairs = pd.DataFrame({
        'row': mapped.index.get_level_values(0),
        'drug': mapped.values,
    }).drop_duplicates()

    for drug in all_drugs:
        column = pd.Series(0, index=df.index)
        row_idx = pairs.loc[pairs['drug'] == drug, 'row']
        column.loc[row_idx] = 1
        df[drug] = column

    # Supprimer les colonnes originales de traitement prophylactique
    df.drop(columns=existing_cols, inplace=True)

    # Réinitialiser l'index pour le plot
    df.reset_index(drop=True, inplace=True)

    return df

def create_diagnosis_category(df):
    """
    Crée une variable 'Diagnosis Category' basée sur Main Diagnosis.
    Catégorise les pathologies en 'Malignant' ou 'Non-malignant'.
    
    Args:
        df (pd.DataFrame): DataFrame avec la colonne 'Main Diagnosis'
        
    Returns:
        pd.DataFrame: DataFrame avec la nouvelle colonne 'Diagnosis Category'
    """
    df = df.copy()
    
    # Mapping des Main Diagnosis vers leur catégorie
    malignancy_mapping = {
        # Malignant
        'Acute leukemia': 'Malignant',
        'Chronic leukemia': 'Malignant',
        'Lymphoma': 'Malignant',
        'Myelodysplastic syndrome': 'Malignant',
        'Myelodysplastic/myeloproliferative disease': 'Malignant',
        'Myeloproliferative disorder': 'Malignant',
        'Plasma cell neoplasm': 'Malignant',
        'Solid tumor configuration': 'Malignant',
        # Non-malignant
        'Autoimmune disease': 'Non-malignant',
        'Bone Marrow Failure incl. Aplastic Anemia': 'Non-malignant',
        'Hemoglobinopathy': 'Non-malignant',
        'Inborn Errors': 'Non-malignant',
        'Other Diagnosis': 'Non-malignant'
    }
    
    if 'Main Diagnosis' in df.columns:
        df['Diagnosis Category'] = df['Main Diagnosis'].map(malignancy_mapping)
        # Pour les diagnostics non reconnus, mettre 'Unknown'
        df['Diagnosis Category'] = df['Diagnosis Category'].fillna('Unknown')
    else:
        df['Diagnosis Category'] = 'Unknown'
    
    return df


def transform_gvhc_scores(df):
    """
    Transforme les scores GVH chronique selon les nouvelles règles:
    - 'Limited' → 'Mild'
    - 'Extensive' → 'Severe'
    
    Args:
        df (pd.DataFrame): DataFrame contenant les données
        
    Returns:
        pd.DataFrame: DataFrame avec les scores transformés
    """
    df_transformed = df.copy()
    
    if 'First cGvHD Maximum NIH Score' in df_transformed.columns:
        # Comptage avant transformation pour logging
        before_limited = (df_transformed['First cGvHD Maximum NIH Score'] == 'Limited').sum()
        before_extensive = (df_transformed['First cGvHD Maximum NIH Score'] == 'Extensive').sum()
        
        # Appliquer les transformations
        df_transformed['First cGvHD Maximum NIH Score'] = df_transformed['First cGvHD Maximum NIH Score'].replace({
            'Limited': 'Mild',
            'Extensive': 'Severe'
        })
        
        # Logging pour suivi
        if before_limited > 0 or before_extensive > 0:
            print(f"Transformation GVHc appliquée: {before_limited} 'Limited' -> 'Mild', {before_extensive} 'Extensive' -> 'Severe'")
    
    return df_transformed


# ---------------------------------------------------------------------------
# Codec compact pour les dcc.Store (phase 4 perf)
# ---------------------------------------------------------------------------
# Format records (to_dict('records')) répète les noms de colonnes et les
# valeurs texte sur chaque ligne : ~43 Mo pour 16 000 lignes. Le payload
# compact utilise l'orientation 'split' et un codebook pour les colonnes
# texte répétitives. Aucune donnée n'est conservée côté serveur : ces
# fonctions ne font que transformer le DataFrame à la volée.

# Au-delà de ce ratio cardinalité/lignes, un codebook ne compresse rien
# (ex : identifiants patients) : la colonne reste en clair.
_CODEBOOK_MAX_RATIO = 0.5


def _json_safe(value):
    """Convertit les scalaires numpy en types Python natifs (JSON-sérialisables)."""
    if isinstance(value, np.generic):
        return value.item()
    return value


def df_to_store_payload(df, columns=None):
    """
    Sérialise un DataFrame en payload JSON compact pour un dcc.Store.

    - orientation 'split' : {'columns', 'data'} (noms de colonnes une seule fois)
    - colonnes texte répétitives encodées en entiers + 'codebook'
    - dates en ISO 8601 (non ambigu ; les pages re-parsent via pd.to_datetime)
    - valeurs manquantes : None (sérialisé null)

    Args:
        df (pd.DataFrame): DataFrame à sérialiser
        columns (list[str] | None): sous-ensemble de colonnes (None = toutes)

    Returns:
        dict: payload JSON-compatible
    """
    if columns is not None:
        cols = list(dict.fromkeys(c for c in columns if c in df.columns))
        df = df[cols]

    n_rows = max(len(df), 1)
    codebook = {}
    encoded_cols = {}

    for col in df.columns:
        series = df[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            # ISO complet pour ne pas perdre une éventuelle composante horaire
            as_str = series.dt.strftime('%Y-%m-%dT%H:%M:%S')
            encoded_cols[col] = as_str.where(series.notna(), None).tolist()
        elif series.dtype == object and 0 < series.nunique(dropna=True) <= _CODEBOOK_MAX_RATIO * n_rows:
            cat = pd.Categorical(series)
            codebook[col] = [_json_safe(v) for v in cat.categories]
            encoded_cols[col] = [None if code < 0 else int(code) for code in cat.codes]
        else:
            encoded_cols[col] = [_json_safe(v) if pd.notna(v) else None for v in series.tolist()]

    columns_list = list(df.columns)
    rows = [list(row) for row in zip(*(encoded_cols[c] for c in columns_list))]

    return {'columns': columns_list, 'data': rows, 'codebook': codebook}


def store_payload_to_df(payload):
    """
    Reconstruit un DataFrame depuis un payload créé par df_to_store_payload.

    Les colonnes encodées (codebook) redeviennent des colonnes texte (object)
    avec None pour les valeurs manquantes, comme après un pd.DataFrame(records).
    Les dates restent des chaînes ISO : les pages les parsent déjà elles-mêmes.

    Args:
        payload (dict | None): payload du store (None si pas de données)

    Returns:
        pd.DataFrame | None
    """
    if payload is None:
        return None

    df = pd.DataFrame(payload['data'], columns=payload['columns'])

    for col, values in (payload.get('codebook') or {}).items():
        if col in df.columns:
            # Après reconstruction, une colonne de codes contenant des None
            # est typée float (NaN) : indexation vectorisée avec masque.
            codes = df[col].to_numpy()
            mask = pd.isna(codes)
            decoded = np.empty(len(codes), dtype=object)
            decoded[mask] = None
            if (~mask).any():
                decoded[~mask] = np.asarray(values, dtype=object)[codes[~mask].astype(np.int64)]
            df[col] = decoded

    return df
