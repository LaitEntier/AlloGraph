import pandas as pd
import numpy as np

def load_data(file_path):
    """
    Charge et prépare les données à partir d'un fichier CSV exporté de REDCap.

    Args:
        file_path (str): Chemin vers le fichier CSV

    Returns:
        pd.DataFrame: Données nettoyées et formatées
    """
    # Chargement des données
    df = pd.read_csv(file_path)

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
    print("  'Reduced intensity conditioning (RIC)' → 'RIC'")
    print("  'Myeloablative conditioning regimen' → 'MAC'")
    
    return df

def create_hla_compatibility_variable(df):
    """
    Crée une variable 'Compatibilité HLA' basée sur Donor Type et Match Type.
    
    Args:
        df (pd.DataFrame): DataFrame avec les colonnes Donor Type et Match Type
        
    Returns:
        pd.DataFrame: DataFrame avec la nouvelle colonne 'Compatibilité HLA'
    """
    df = df.copy()
    
    # Vérifier si les colonnes existent
    if 'Donor Type' not in df.columns or 'Match Type' not in df.columns:
        print("Attention: Colonnes 'Donor Type' ou 'Match Type' manquantes pour créer la variable 'Compatibilité HLA'")
        df['Compatibilité HLA'] = 'unknown'
        return df
    
    # Créer la variable combinée
    def combine_hla_compatibility(row):
        donor_type = row.get('Donor Type', '')
        match_type = row.get('Match Type', '')
        
        # Nettoyer et standardiser les valeurs
        if pd.isna(donor_type) or str(donor_type).strip() == '':
            donor_type = None
        else:
            donor_type = str(donor_type).strip()
        
        if pd.isna(match_type) or str(match_type).strip() == '':
            match_type = None
        else:
            match_type = str(match_type).strip()
        
        # Si l'une des deux colonnes est vide/manquante
        if donor_type is None or match_type is None:
            return 'unknown'
        
        # Logique de combinaison selon les spécifications
        if donor_type == 'Related donor' and match_type == 'Match':
            return 'Related Match'
        elif donor_type == 'Related donor' and match_type == 'Mismatch':
            return 'Related Mismatch'
        elif donor_type == 'Unrelated donor' and match_type == 'Match':
            return 'Unrelated Match'
        elif donor_type == 'Unrelated donor' and match_type == 'Mismatch':
            return 'Unrelated Mismatch'
        else:
            # Pour toute autre combinaison non prévue
            return 'unknown'
    
    df['Compatibilité HLA'] = df.apply(combine_hla_compatibility, axis=1)
    
    return df


def process_data(df):
    """
    Fonction qui prend en entrée un DataFrame et qui applique un traitement sur les données

    Args:
        df (pd.DataFrame): DataFrame contenant les colonnes de départ

    Returns:
        pd.DataFrame: DataFrame avec les données traitées
    """

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
    
    # Nouvelle variable : Compatibilité HLA (combinaison de Donor Type et Match Type)
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
        'lymphocyte immune globulin': 'Sérum Anti-Lymphocytaire - ATG',
        'anti-thymocyte globulin': 'Sérum Anti-Lymphocytaire - ATG',
        'Drug Anti-Thymocyte Globulin or Anti-Lymphocyte Globulin': 'Sérum Anti-Lymphocytaire - ALTG',
        'antilymphocyte immunoglobulin': 'Sérum Anti-Lymphocytaire - ALTG'
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
        'lymphocyte immune globulin': 'Sérum Anti-Lymphocytaire - ATG',
        'anti-thymocyte globulin': 'Sérum Anti-Lymphocytaire - ATG',
        'Drug Anti-Thymocyte Globulin or Anti-Lymphocyte Globulin': 'Sérum Anti-Lymphocytaire - ALTG',
        'antilymphocyte immunoglobulin': 'Sérum Anti-Lymphocytaire - ALTG'
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
            print(f"Transformation GVHc appliquée: {before_limited} 'Limited' → 'Mild', {before_extensive} 'Extensive' → 'Severe'")
    
    return df_transformed
