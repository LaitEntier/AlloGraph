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


def process_data(df):
    """
    Fonction qui prend en entrée un DataFrame et qui applique un traitement sur les données

    Args:
        df (pd.DataFrame): DataFrame contenant les colonnes de départ

    Returns:
        pd.DataFrame: DataFrame avec les données traitées
    """

    # Créer une colonne 'Year' à partir de 'Date Diagnosis'
    df['Treatment Date'] = pd.to_datetime(df['Treatment Date'], errors='coerce')
    df['Year'] = df['Treatment Date'].dt.year.astype(str)

    # Calculer l'age au diagnostic en années
    df['Age At Diagnosis'] = (df['Date Diagnosis'] - df['Date Of Birth']).dt.days // 365.25

    # Créer une colone Age Groups regroupant les patients par tranche d'âge (<18, 18-39, 40-64, 65-74, 75+)
    df['Age Groups'] = pd.cut(df['Age At Diagnosis'], bins=[-1, 17, 39, 64, 74, np.inf], labels=['<18', '18-39', '40-64', '65-74', '75+'], right=True)
    # order the categories for display in barplot
    df['Age Groups'] = pd.Categorical(df['Age Groups'], categories=['<18', '18-39', '40-64', '65-74', '75+'], ordered=True)

    return df
