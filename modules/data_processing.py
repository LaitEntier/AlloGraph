import pandas as pd


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

    # Calcul de l'âge en années
    df["Age At Diagnosis"] = (df["Date Diagnosis"] - df["Date Of Birth"]).dt.days // 365

    return df
