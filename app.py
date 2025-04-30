import streamlit as st
import plotly.express as px
import numpy as np
from io import StringIO
import pandas as pd
import os
from visualizations.allogreffes.graphs import (
    create_barplot as barplot,
    create_cumulative_barplot as cum_barplot,
)

# Configuration de la page
st.set_page_config(layout="wide", page_title="Rapport d'Analyse")


# Initialisation des variables de session si elles n'existent pas déjà
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'data' not in st.session_state:
    st.session_state.data = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Accueil"

# Sidebar pour l'upload de fichier
with st.sidebar:
    st.title("Chargement des données")
    uploaded_file = st.file_uploader("Choisir un fichier CSV", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.session_state.data = df
            st.session_state.data_loaded = True
            st.success(f"Données chargées avec succès! {df.shape[0]} lignes et {df.shape[1]} colonnes.")

        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier: {e}")

# Navigation bar (en haut)
st.markdown("""
<style>
    .navbar {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .navbar-button {
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Container pour la navbar
navbar = st.container()
with navbar:
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    
    with col1:
        if st.button("Accueil", key="nav_accueil"):
            st.session_state.current_page = "Accueil"
            st.experimental_rerun()
    
    # Afficher les autres boutons de navigation seulement si les données sont chargées
    if st.session_state.data_loaded:
        with col2:
            if st.button("Page 1", key="nav_page1"):
                st.session_state.current_page = "WIP"
                st.experimental_rerun()
        
        with col3:
            if st.button("Page 2", key="nav_page2"):
                st.session_state.current_page = "WIP"
                st.experimental_rerun()

# Contenu principal
st.title(f"Dashboard - {st.session_state.current_page}")

# Affichage en fonction de la page sélectionnée
if st.session_state.current_page == "Accueil":
    if st.session_state.data_loaded:
        # utiliser la fonction create_cumulative_graph de la bibliothèque allogreffes

    #df['Year'] = df['Treatment Date'].dt.year
    #df['Year'] = df['Year'].astype(str)

#        fig = create_cumulative_barplot(
#            data=df,
#            category_column='Year',
#            title="Nombre de greffes par an",
#            x_axis_title="Année",
#            bar_y_axis_title="Nombre de greffes",
#            line_y_axis_title="Effectif cumulé"
#    )
#    fig.show()
        df['Year'] = df['Treatment Date'].dt.year
        df['Year'] = df['Year'].astype(str)
        
        fig = cum_barplot(
            data=df,
            category_column='Year',
            title="Nombre de greffes par an",
            x_axis_title="Année",
            bar_y_axis_title="Nombre de greffes",
            line_y_axis_title="Effectif cumulé",
            custom_order = df['Year'].unique().tolist()
        )
        # Afficher le graphique
        fig.show()
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Veuillez charger un fichier de données pour commencer l'analyse.")
        
        # Création d'un message d'accueil avec des instructions
        st.markdown("""
        ## Bienvenue dans AlloGraph
        
        Cette application vous permet d'analyser des données de patients depuis le modèle de données EBMT.
        
        ### Instructions:
        1. Utilisez le bouton dans la barre latérale pour télécharger votre fichier CSV ou Excel.
        2. Une fois les données chargées, vous pourrez naviguer entre différentes pages d'analyse.

        """)

elif st.session_state.current_page == "Page 1":
    st.write("Contenu de la Page 1 - En cours de développement")
    # Ici vous pouvez ajouter le contenu spécifique à la Page 1
    
elif st.session_state.current_page == "Page 2":
    st.write("Contenu de la Page 2 - En cours de développement")
    # Ici vous pouvez ajouter le contenu spécifique à la Page 2

# Ajout d'un pied de page
st.markdown("---")
st.markdown("© 2025 - CHRU de Tours - Tous droits réservés")