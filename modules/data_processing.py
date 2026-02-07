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
    
    # Créer la variable combinée
    def combine_hla_compatibility(row):
        donor_type_raw = row.get('Donor Type', '')
        match_type_raw = row.get('Match Type', '')
        
        # Nettoyer et standardiser les valeurs
        if pd.isna(donor_type_raw) or str(donor_type_raw).strip() == '':
            donor_type = None
        else:
            donor_type = str(donor_type_raw).strip()
        
        if pd.isna(match_type_raw) or str(match_type_raw).strip() == '':
            match_type = None
        else:
            match_type = str(match_type_raw).strip()
        
        # Cas où les deux colonnes sont vides/manquantes
        if donor_type is None and match_type is None:
            return 'Unknown + Unknown'
        
        # Cas où seulement Donor Type est vide/manquant
        if donor_type is None:
            return f'Unknown + {match_type}'
        
        # Cas où seulement Match Type est vide/manquant
        if match_type is None:
            # Extraire le type de base (Related ou Unrelated) pour un affichage plus propre
            donor_lower = donor_type.lower()
            if 'related' in donor_lower and 'un' not in donor_lower:
                return 'Related + Unknown'
            elif 'unrelated' in donor_lower or ('un' in donor_lower and 'related' in donor_lower):
                return 'Unrelated + Unknown'
            else:
                return f'{donor_type} + Unknown'
        
        # Normaliser le donor_type (accepter 'Related', 'Related donor', 'Unrelated', 'Unrelated donor')
        donor_lower = donor_type.lower()
        if 'related' in donor_lower and 'un' not in donor_lower:
            donor_normalized = 'Related donor'
        elif 'unrelated' in donor_lower or ('un' in donor_lower and 'related' in donor_lower):
            donor_normalized = 'Unrelated donor'
        else:
            donor_normalized = donor_type  # Garder la valeur originale si non reconnue
        
        # Logique de combinaison selon les spécifications
        if donor_normalized == 'Related donor' and match_type == 'Match':
            return 'Genoidentical'
        elif donor_normalized == 'Related donor' and match_type == 'Mismatch':
            return 'MRD (Haplo)'
        elif donor_normalized == 'Unrelated donor' and match_type == 'Match':
            return 'MUD'
        elif donor_normalized == 'Unrelated donor' and match_type == 'Mismatch':
            return 'MMUD'
        else:
            # Pour toute autre combinaison non prévue (valeurs inattendues)
            return f'{donor_normalized} + {match_type}'
    
    df['Donor Match Category'] = df.apply(combine_hla_compatibility, axis=1)
    
    return df


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
    df['Treatment Date'] = pd.to_datetime(df['Treatment Date'], dayfirst=True, format='mixed', errors='coerce')
    df['Year'] = df['Treatment Date'].dt.year.astype(str)

    df['Date Diagnosis'] = pd.to_datetime(df['Date Diagnosis'], dayfirst=True, format='mixed', errors='coerce')
    df['Date Of Birth'] = pd.to_datetime(df['Date Of Birth'], dayfirst=True, format='mixed', errors='coerce')
    # Calculer l'age au diagnostic en années
    df['Age At Diagnosis'] = (df['Date Diagnosis'] - df['Date Of Birth']).dt.days // 365.25

    # Créer une colone Age Groups regroupant les patients par tranche d'âge (<18, 18-39, 40-64, 65-74, 75+)
    df['Age Groups'] = pd.cut(df['Age At Diagnosis'], bins=[-1, 17, 39, 64, 74, np.inf], labels=['18-', '18-39', '40-64', '65-74', '75+'], right=True)
    # order the categories for display in barplot
    df['Age Groups'] = pd.Categorical(df['Age Groups'], categories=['18-', '18-39', '40-64', '65-74', '75+'], ordered=True)

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
    
    # Créer la variable combinée
    def combine_greffe_info(row):
        donor_type = row.get('Donor Type', '')
        stem_cells = row.get('Source Stem Cells', '')
        
        # Gérer les valeurs nulles ou vides
        if pd.isna(donor_type) or donor_type == '':
            donor_type = 'Inconnu'
        if pd.isna(stem_cells) or stem_cells == '':
            stem_cells = 'Inconnu'
        
        # Combinaison intelligente
        if donor_type == 'Inconnu' and stem_cells == 'Inconnu':
            return 'Non défini'
        elif donor_type == 'Inconnu':
            return f"Greffe {stem_cells}"
        elif stem_cells == 'Inconnu':
            return f"Greffe {donor_type}"
        else:
            return f"{donor_type} - {stem_cells}"
    
    df['Greffes'] = df.apply(combine_greffe_info, axis=1)
    
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
    
    # Créer la variable combinée
    def combine_blood_rh(row):
        blood_group = row.get('Blood Group', '')
        rhesus_factor = row.get('Rhesus Factor', '')
        
        # Nettoyer et standardiser les valeurs
        if pd.isna(blood_group) or str(blood_group).strip() == '':
            blood_group = 'unknown'
        else:
            blood_group = str(blood_group).strip()
        
        if pd.isna(rhesus_factor) or str(rhesus_factor).strip() == '':
            rhesus_factor = 'unknown'
        else:
            rhesus_factor = str(rhesus_factor).strip().lower()
        
        # Exception spéciale : si les deux sont unknown
        if blood_group.lower() == 'unknown' and rhesus_factor == 'unknown':
            return 'unknown'
        
        # Mapper les valeurs de Rhesus Factor
        if rhesus_factor == 'positive':
            rh_symbol = '+'
        elif rhesus_factor == 'negative':
            rh_symbol = '-'
        else:
            # Pour 'unknown' ou toute autre valeur
            rh_symbol = rhesus_factor
        
        # Concaténer Blood Group + Rhesus Factor
        return f"{blood_group}{rh_symbol}"
    
    df['Blood + Rh'] = df.apply(combine_blood_rh, axis=1)
    
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
            df[col] = df[col].astype(str).str.strip().str.lower()
            df[col] = df[col].apply(lambda x: 'Yes' if x in ['yes', 'y', '1', 'true'] else 'No')
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
    
    # Collecter tous les traitements uniques
    all_drugs = set()
    
    for col in existing_cols:
        # Remplacer les valeurs NaN/None par des chaînes vides
        drugs_in_col = df[col].fillna('').astype(str)
        
        # Appliquer le mapping et collecter les traitements non vides
        for drug in drugs_in_col:
            if drug and drug.lower() != 'nan' and drug.strip():
                # Appliquer le mapping si nécessaire (insensible à la casse)
                mapped_drug = None
                for original, mapped in drug_mapping.items():
                    if original.lower() in drug.lower():
                        mapped_drug = mapped
                        break
                
                if mapped_drug is None:
                    mapped_drug = drug
                
                all_drugs.add(mapped_drug)
    
    # Supprimer les valeurs vides
    all_drugs = {drug for drug in all_drugs if drug.strip()}
    
    # Créer les nouvelles colonnes binaires
    for drug in sorted(all_drugs):
        df[drug] = 'Non'
    
    # Remplir les colonnes binaires
    for idx, row in df.iterrows():
        patient_drugs = []
        
        # Collecter tous les traitements du patient
        for col in existing_cols:
            drug_value = row[col]
            if pd.notna(drug_value) and str(drug_value).strip():
                # Appliquer le mapping si nécessaire (insensible à la casse)
                mapped_drug = None
                drug_str = str(drug_value)
                
                for original, mapped in drug_mapping.items():
                    if original.lower() in drug_str.lower():
                        mapped_drug = mapped
                        break
                
                if mapped_drug is None:
                    mapped_drug = drug_str
                
                patient_drugs.append(mapped_drug)
        
        # Marquer 'Oui' pour tous les traitements du patient
        for drug in patient_drugs:
            if drug in df.columns:
                df.at[idx, drug] = 'Oui'

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
    
    # Collecter tous les traitements uniques
    all_drugs = set()
    
    for col in existing_cols:
        # Remplacer les valeurs NaN/None par des chaînes vides
        drugs_in_col = df[col].fillna('').astype(str)
        
        # Appliquer le mapping et collecter les traitements non vides
        for drug in drugs_in_col:
            if drug and drug.lower() != 'nan' and drug.strip():
                # Appliquer le mapping si nécessaire (insensible à la casse)
                mapped_drug = None
                for original, mapped in drug_mapping.items():
                    if original.lower() in drug.lower():
                        mapped_drug = mapped
                        break
                
                if mapped_drug is None:
                    mapped_drug = drug
                
                all_drugs.add(mapped_drug)
    
    # Supprimer les valeurs vides
    all_drugs = {drug for drug in all_drugs if drug.strip()}
    
    # Créer les nouvelles colonnes binaires
    for drug in sorted(all_drugs):
        df[drug] = 0
    
    # Remplir les colonnes binaires
    for idx, row in df.iterrows():
        patient_drugs = []
        
        # Collecter tous les traitements du patient
        for col in existing_cols:
            drug_value = row[col]
            if pd.notna(drug_value) and str(drug_value).strip():
                # Appliquer le mapping si nécessaire (insensible à la casse)
                mapped_drug = None
                drug_str = str(drug_value)
                
                for original, mapped in drug_mapping.items():
                    if original.lower() in drug_str.lower():
                        mapped_drug = mapped
                        break
                
                if mapped_drug is None:
                    mapped_drug = drug_str
                
                patient_drugs.append(mapped_drug)
        
        # Marquer 'Oui' pour tous les traitements du patient
        for drug in patient_drugs:
            if drug in df.columns:
                df.at[idx, drug] = 1

    # Supprimer les colonnes originales de traitement prophylactique
    df.drop(columns=existing_cols, inplace=True)

    # Réinitialiser l'index pour le plot
    df.reset_index(drop=True, inplace=True)

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
