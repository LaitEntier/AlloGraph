import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
import plotly.colors
from dash import html, dash_table, dcc
import dash_bootstrap_components as dbc
from scipy.stats import gaussian_kde
from typing import Optional, List, Tuple
import numpy as np

def create_consistent_color_map(data, color_column):
    """
    Crée un mapping de couleurs cohérent pour une variable donnée.
    Utilise toujours les mêmes couleurs pour les mêmes catégories.
    
    Args:
        data (pd.DataFrame): DataFrame contenant les données
        color_column (str): Nom de la colonne pour laquelle créer le mapping
        
    Returns:
        dict: Mapping {catégorie: couleur}
    """
    if color_column not in data.columns:
        return {}
    
    # Obtenir les catégories uniques en filtrant les valeurs nulles
    categories = data[color_column].dropna().unique()
    # Trier seulement les valeurs non-nulles pour garantir la cohérence
    categories = sorted([cat for cat in categories if pd.notna(cat)])
    
    # Utiliser la palette Plotly standard
    colors = px.colors.qualitative.Safe
    
    # Créer le mapping
    color_map = {}
    for i, category in enumerate(categories):
        color_map[category] = colors[i % len(colors)]
    
    return color_map

def apply_x_axis_rotation(fig, rotation_angle=45):
    """
    Applique une rotation aux labels de l'axe X pour améliorer la lisibilité.
    
    Args:
        fig: Figure Plotly
        rotation_angle (int): Angle de rotation en degrés (défaut: 45)
    
    Returns:
        fig: Figure modifiée
    """
    fig.update_layout(
        xaxis=dict(
            tickangle=rotation_angle,
            tickmode='linear'
        )
    )
def create_prophylaxis_treatments_barplot(data, prophylaxis_columns, title="Proportion de patients par traitement prophylactique",
                                        x_axis_title="Traitement", y_axis_title="Proportion (%)",
                                        height=400, width=None, show_values=True):
    """
    Crée un barplot montrant les proportions Oui/Non pour chaque traitement prophylactique.
    Une barre par traitement.
    
    Args:
        data (pd.DataFrame): DataFrame avec les données
        prophylaxis_columns (list): Liste des colonnes de traitement prophylactique
        title (str): Titre du graphique
        x_axis_title (str): Titre de l'axe X
        y_axis_title (str): Titre de l'axe Y
        height (int): Hauteur du graphique
        width (int): Largeur du graphique
        show_values (bool): Afficher les valeurs sur les barres
        
    Returns:
        plotly.graph_objects.Figure: Figure Plotly
    """
    import plotly.graph_objects as go
    import pandas as pd
    
    # Calculer les proportions pour chaque traitement
    treatment_data = []
    
    for treatment in prophylaxis_columns:
        if treatment in data.columns:
            # Compter les Oui et Non
            value_counts = data[treatment].value_counts()
            total = len(data)
            
            oui_count = value_counts.get('Oui', 0)
            non_count = value_counts.get('Non', 0)
            
            oui_percentage = (oui_count / total) * 100 if total > 0 else 0
            non_percentage = (non_count / total) * 100 if total > 0 else 0
            
            treatment_data.append({
                'Traitement': treatment,
                'Oui_count': oui_count,
                'Non_count': non_count,
                'Oui_percentage': oui_percentage,
                'Non_percentage': non_percentage,
                'Total': total
            })
    
    # Convertir en DataFrame pour faciliter la manipulation
    df_treatments = pd.DataFrame(treatment_data)
    
    if df_treatments.empty:
        # Graphique vide si pas de données
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée de prophylaxie disponible",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            title=title,
            height=height,
            width=width
        )
        return fig
    
    # Trier par pourcentage de "Oui" décroissant
    df_treatments = df_treatments.sort_values('Oui_percentage', ascending=False)
    
    # Créer le graphique
    fig = go.Figure()
    
    # Barres pour "Oui"
    fig.add_trace(go.Bar(
        name='Oui',
        x=df_treatments['Traitement'],
        y=df_treatments['Oui_percentage'],
        text=[f"{row['Oui_count']} ({row['Oui_percentage']:.1f}%)" 
              for _, row in df_treatments.iterrows()] if show_values else None,
        textposition='auto',
        marker_color='#2E86AB',
        hovertemplate='<b>%{x}</b><br>' +
                      'Patients avec traitement: %{text}<br>' +
                      '<extra></extra>'
    ))
    
    # Barres pour "Non"  
    fig.add_trace(go.Bar(
        name='Non',
        x=df_treatments['Traitement'],
        y=df_treatments['Non_percentage'],
        text=[f"{row['Non_count']} ({row['Non_percentage']:.1f}%)" 
              for _, row in df_treatments.iterrows()] if show_values else None,
        textposition='auto',
        marker_color='#A23B72',
        hovertemplate='<b>%{x}</b><br>' +
                      'Patients sans traitement: %{text}<br>' +
                      '<extra></extra>'
    ))
    
    # Configuration du layout
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'family': 'Arial, sans-serif'}
        },
        xaxis_title=x_axis_title,
        yaxis_title=y_axis_title,
        barmode='stack',  # Barres empilées pour montrer le total de 100%
        height=height,
        width=width,
        font={'family': 'Arial, sans-serif', 'size': 12},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1
        },
        margin={'l': 50, 'r': 50, 't': 80, 'b': 100}
    )
    
    # Style des axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray',
        tickangle=45,  # Rotation des labels pour une meilleure lisibilité
        title_font={'size': 14}
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray',
        range=[0, 100],  # Fixer l'échelle à 0-100%
        title_font={'size': 14}
    )
    
    return fig

def truncate_diagnosis_names(text, max_length=25, smart_truncate=True):
    """
    Tronque intelligemment les noms de diagnostics longs.
    
    Args:
        text (str): Texte à tronquer
        max_length (int): Longueur maximale autorisée
        smart_truncate (bool): Si True, essaie de couper aux mots
        
    Returns:
        str: Texte tronqué avec "..." si nécessaire
    """
    if pd.isna(text) or len(str(text)) <= max_length:
        return str(text)
    
    text = str(text)
    
    if smart_truncate:
        # Essayer de couper au dernier espace avant la limite
        if ' ' in text[:max_length]:
            truncated = text[:max_length].rsplit(' ', 1)[0]
            return truncated + "..."
        else:
            # Si pas d'espace, couper brutalement
            return text[:max_length-3] + "..."
    else:
        # Troncature brutale
        return text[:max_length-3] + "..."

def prepare_data_with_truncated_labels(data, x_column, max_length=25):
    """
    Prépare les données en ajoutant une colonne avec les labels tronqués.
    Gère les doublons en ajoutant des suffixes numériques.
    
    Args:
        data (pd.DataFrame): DataFrame original
        x_column (str): Nom de la colonne à traiter
        max_length (int): Longueur maximale des labels
        
    Returns:
        tuple: (DataFrame avec colonne tronquée, nom de la colonne tronquée)
    """
    df = data.copy()
    
    # Obtenir les valeurs uniques originales
    unique_values = df[x_column].unique()
    
    # Créer un mapping des noms originaux vers les noms tronqués
    truncated_mapping = {}
    truncated_counts = {}
    
    for original_name in unique_values:
        if pd.isna(original_name):
            truncated_mapping[original_name] = original_name
            continue
            
        # Tronquer le nom
        truncated = truncate_diagnosis_names(original_name, max_length)
        
        # Gérer les doublons
        if truncated in truncated_counts:
            truncated_counts[truncated] += 1
            # Ajuster la longueur pour faire de la place au suffixe
            suffix = f" ({truncated_counts[truncated]})"
            available_length = max_length - len(suffix)
            
            if available_length > 10:  # Garder au moins 10 caractères
                base_truncated = truncate_diagnosis_names(original_name, available_length)
                # Enlever les "..." à la fin s'ils existent
                if base_truncated.endswith("..."):
                    base_truncated = base_truncated[:-3]
                truncated_mapping[original_name] = base_truncated + suffix
            else:
                # Si pas assez de place, utiliser juste un numéro
                truncated_mapping[original_name] = f"Diagnostic {truncated_counts[truncated]}"
        else:
            truncated_counts[truncated] = 1
            truncated_mapping[original_name] = truncated
    
    # Créer la colonne tronquée
    truncated_col = f"{x_column}_truncated"
    df[truncated_col] = df[x_column].map(truncated_mapping)
    
    return df, truncated_col

def create_safe_custom_order(original_order, truncated_mapping):
    """
    Crée un ordre personnalisé sûr sans doublons.
    
    Args:
        original_order (list): Ordre original des catégories
        truncated_mapping (dict): Mapping original -> tronqué
        
    Returns:
        list: Ordre des catégories tronquées sans doublons
    """
    truncated_order = []
    seen = set()
    
    for original_name in original_order:
        if original_name in truncated_mapping:
            truncated_name = truncated_mapping[original_name]
            if truncated_name not in seen:
                truncated_order.append(truncated_name)
                seen.add(truncated_name)
    
    return truncated_order

def create_barplot(
    data,
    x_column,
    y_column,
    title="",
    x_axis_title=None,
    y_axis_title=None,
    bar_color="#0D3182",
    text_color="white",
    show_values=True,
    value_format=".1f",
    orientation="v",
    text_position="auto",
    height=500,
    width=800,
):
    """
    Crée un barplot simple avec plotly en affichant optionnellement les valeurs à l'intérieur des barres.

    Args:
        data (pd.DataFrame): DataFrame contenant les données
        x_column (str): Nom de la colonne pour l'axe X (catégories)
        y_column (str): Nom de la colonne pour l'axe Y (valeurs)
        title (str, optional): Titre du graphique
        x_axis_title (str, optional): Titre de l'axe X. Si None, utilise x_column
        y_axis_title (str, optional): Titre de l'axe Y. Si None, utilise y_column
        bar_color (str, optional): Couleur des barres en format hex
        text_color (str, optional): Couleur du texte pour les valeurs affichées
        show_values (bool, optional): Afficher les valeurs dans les barres
        value_format (str, optional): Format des valeurs affichées (ex: ".1f" pour 1 décimale)
        orientation (str, optional): Orientation des barres ('v' pour vertical, 'h' pour horizontal)
        text_position (str, optional): Position du texte ('auto', 'inside', 'outside')
        height (int, optional): Hauteur du graphique en pixels
        width (int, optional): Largeur du graphique en pixels

    Returns:
        plotly.graph_objects.Figure: Figure plotly du barplot
    """
    # Définir les titres d'axes s'ils ne sont pas spécifiés
    if x_axis_title is None:
        x_axis_title = x_column
    if y_axis_title is None:
        y_axis_title = y_column

    # Préparation des valeurs pour l'affichage
    if show_values:
        text_values = data[y_column].apply(lambda x: f"{x:{value_format}}")
    else:
        text_values = None

    # Création du graphique selon l'orientation
    if orientation == "v":
        fig = go.Figure(
            go.Bar(
                x=data[x_column],
                y=data[y_column],
                marker_color=bar_color,
                text=text_values,
                textposition=text_position,
                textfont=dict(color=text_color),
                name="",
            )
        )

        # Configuration des axes
        fig.update_layout(xaxis_title=x_axis_title, yaxis_title=y_axis_title)
    else:  # orientation == 'h'
        fig = go.Figure(
            go.Bar(
                y=data[x_column],
                x=data[y_column],
                marker_color=bar_color,
                text=text_values,
                textposition=text_position,
                textfont=dict(color=text_color),
                orientation="h",
                name="",
            )
        )

        # Configuration des axes
        fig.update_layout(yaxis_title=x_axis_title, xaxis_title=y_axis_title)

    # Configuration générale du graphique
    fig.update_layout(
        title=title,
        height=height,
        width=width,
        template="plotly_white",
        showlegend=False,
    )
    
def create_boxplot(
    data,
    x_column,
    y_column,
    title="",
    x_axis_title=None,
    y_axis_title=None,
    color_map=None,
    auto_colors=True,
    color_palette=None,
    height=500,
    width=1500
):
    """
    Crée un boxplot avec Plotly avec assignation automatique de couleurs.

    Args:
        data (pd.DataFrame): DataFrame contenant les données
        x_column (str): Nom de la colonne pour l'axe X
        y_column (str): Nom de la colonne pour l'axe Y
        title (str, optional): Titre du graphique
        x_axis_title (str, optional): Titre de l'axe X
        y_axis_title (str, optional): Titre de l'axe Y
        color_map (dict, optional): Dictionnaire de mapping couleurs pour chaque catégorie
        auto_colors (bool, optional): Si True, assigne automatiquement des couleurs distinctes
        color_palette (list, optional): Liste de couleurs à utiliser. Si None, utilise une palette par défaut
        height (int, optional): Hauteur du graphique
        width (int, optional): Largeur du graphique

    Returns:
        plotly.graph_objects.Figure: Figure Plotly du boxplot
    """
    # Définir les titres par défaut
    x_axis_title = x_axis_title or x_column
    y_axis_title = y_axis_title or y_column
    
    # Cas spécial : si x_column est None, créer un boxplot simple
    if x_column is None:
        fig = px.box(
            data,
            y=y_column,
            title=title,
            height=height,
            width=width
        )
        fig.update_layout(
            xaxis_title="",
            yaxis_title=y_axis_title,
            template='plotly_white',
            showlegend=False
        )
        return fig
    
    # Obtenir les catégories uniques
    categories = data[x_column].unique()
    n_categories = len(categories)
    
    # Gestion des couleurs
    if color_map:
        # Utiliser le color_map fourni
        fig = px.box(
            data,
            x=x_column,
            y=y_column,
            title=title,
            color=x_column,
            color_discrete_map=color_map,
            height=height,
            width=width
        )
    elif auto_colors:
        # Assignation automatique de couleurs
        if color_palette is None:
            # Utiliser une palette par défaut de Plotly
            color_palette = px.colors.qualitative.Safe
        # Limiter la palette à 24 couleurs
        if len(color_palette) > 24:
            color_palette = color_palette[:24]
        # Si plus de 24 catégories, répéter les couleurs
        elif len(color_palette) < n_categories:
            color_palette = color_palette * (n_categories // len(color_palette) + 1)
            color_palette = color_palette[:n_categories]  # Ajuster à la taille exacte

        # Créer un mapping automatique
        auto_color_map = {cat: color_palette[i % len(color_palette)] 
                         for i, cat in enumerate(categories)}

        fig = px.box(
            data,
            x=x_column,
            y=y_column,
            title=title,
            color=x_column,
            color_discrete_map=auto_color_map,
            height=height,
            width=width
        )
    else:
        # Boxplot sans couleurs spécifiques
        fig = px.box(
            data,
            x=x_column,
            y=y_column,
            title=title,
            height=height,
            width=width
        )
    
    # Configuration du layout
    fig.update_layout(
        xaxis_title=x_axis_title,
        yaxis_title=y_axis_title,
        template='plotly_white',
        showlegend=False  # Masquer la légende car elle peut être redondante avec l'axe X
    )

    return fig

def create_enhanced_boxplot(
    data,
    x_column,
    y_column,
    color_column=None,
    title="",
    x_axis_title=None,
    y_axis_title=None,
    height=500,
    width=1500,
    show_points=True,
    point_size=4,
    force_zero_start=False,
    color_map=None,
    sort_by_median=False,  # ← NOUVEAU PARAMÈTRE
    sort_ascending=True    # ← NOUVEAU PARAMÈTRE
):
    """
    Crée un boxplot amélioré avec des points optionnels et coloration cohérente.
    
    Args:
        data (pd.DataFrame): DataFrame contenant les données
        x_column (str): Nom de la colonne pour l'axe X (groupement)
        y_column (str): Nom de la colonne pour l'axe Y (variable continue)
        color_column (str, optional): Colonne pour colorer les points/boxplots
        title (str, optional): Titre du graphique
        x_axis_title (str, optional): Titre de l'axe X
        y_axis_title (str, optional): Titre de l'axe Y
        height (int, optional): Hauteur du graphique
        width (int, optional): Largeur du graphique
        show_points (bool, optional): Afficher les points individuels
        point_size (int, optional): Taille des points
        force_zero_start (bool, optional): Forcer l'axe Y à commencer à 0
        color_map (dict, optional): Mapping de couleurs cohérent
        sort_by_median (bool, optional): Trier les groupes par médiane
        sort_ascending (bool, optional): Ordre croissant (True) ou décroissant (False)
        
    Returns:
        plotly.graph_objects.Figure: Figure Plotly du boxplot amélioré
    """
    # Définir les titres par défaut
    x_axis_title = x_axis_title or x_column
    y_axis_title = y_axis_title or y_column
    
    # Nettoyer les données (supprimer les NaN dans les colonnes importantes)
    clean_data = data.dropna(subset=[x_column, y_column])
    
    # NOUVELLE FONCTIONNALITÉ : Tri par médiane
    category_orders = None
    if sort_by_median:
        # Calculer les médianes pour chaque groupe
        medians = clean_data.groupby(x_column)[y_column].median().sort_values(ascending=sort_ascending)
        # Créer l'ordre personnalisé basé sur les médianes
        ordered_categories = medians.index.tolist()
        category_orders = {x_column: ordered_categories}
    
    # Cas sans coloration
    if color_column is None or color_column not in clean_data.columns:
        if show_points:
            fig = px.box(
                clean_data,
                x=x_column,
                y=y_column,
                title=title,
                height=height,
                width=width,
                points="all",  # Afficher tous les points
                category_orders=category_orders  # ← Appliquer l'ordre personnalisé
            )
        else:
            fig = px.box(
                clean_data,
                x=x_column,
                y=y_column,
                title=title,
                height=height,
                width=width,
                category_orders=category_orders  # ← Appliquer l'ordre personnalisé
            )
    else:
        # Cas avec coloration
        # Utiliser le color_map fourni ou en créer un
        if color_map is None:
            color_map = create_consistent_color_map(clean_data, color_column)
        
        if show_points:
            fig = px.box(
                clean_data,
                x=x_column,
                y=y_column,
                color=color_column,
                color_discrete_map=color_map,
                title=title,
                height=height,
                width=width,
                points="all",  # Afficher tous les points
                category_orders=category_orders  # ← Appliquer l'ordre personnalisé
            )
        else:
            fig = px.box(
                clean_data,
                x=x_column,
                y=y_column,
                color=color_column,
                color_discrete_map=color_map,
                title=title,
                height=height,
                width=width,
                category_orders=category_orders  # ← Appliquer l'ordre personnalisé
            )
        
        # Personnaliser la légende
        fig.update_layout(
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.01
            )
        )
    
    # Personnaliser les points si affichés
    if show_points:
        fig.update_traces(
            marker=dict(size=point_size),
            jitter=0.3,  # Espacement horizontal des points
            pointpos=0   # Position des points (0 = centrés)
        )
    
    # Configuration de l'axe Y
    y_axis_config = {
        'title': y_axis_title
    }
    
    # Forcer l'axe Y à commencer à 0 avec des steps de 1
    if force_zero_start:
        y_max = clean_data[y_column].max()
        if pd.notna(y_max):
            y_axis_config.update({
                'range': [0, y_max + 1],
                'dtick': 1  # Steps de 1
            })
    
    # Configuration du layout
    fig.update_layout(
        xaxis_title=x_axis_title,
        yaxis=y_axis_config,
        template='plotly_white',
        showlegend=False
    )
    
    return fig

def create_simple_barplot(
    data,
    x_column,
    y_column=None,
    title="",
    x_axis_title=None,
    y_axis_title=None,
    bar_color="#0D3182",
    show_values=True,
    height=500,
    width=1500,
    custom_order=None,
    rotate_x_labels=False,  # ← Nouveau paramètre
    x_rotation_angle=45     # ← Nouveau paramètre
):
    """
    Crée un barplot simple (non empilé) basé sur des données.
    Peut traiter soit des données déjà agrégées, soit des données brutes à compter.
    
    Args:
        data (pd.DataFrame): DataFrame contenant les données
        x_column (str): Nom de la colonne pour l'axe X
        y_column (str, optional): Nom de la colonne pour l'axe Y. Si None, compte les occurrences de x_column
        title (str, optional): Titre du graphique
        x_axis_title (str, optional): Titre de l'axe X
        y_axis_title (str, optional): Titre de l'axe Y
        bar_color (str, optional): Couleur des barres
        show_values (bool, optional): Afficher les valeurs dans les barres
        height (int, optional): Hauteur du graphique
        width (int, optional): Largeur du graphique
        custom_order (list, optional): Ordre personnalisé pour les catégories
        rotate_x_labels (bool, optional): Rotation des labels de l'axe X
        x_rotation_angle (int, optional): Angle de rotation des labels
        
    Returns:
        plotly.graph_objects.Figure: Figure Plotly du barplot simple
    """
    # Si y_column est fourni et existe, utiliser ces données agrégées
    if y_column is not None and y_column in data.columns:
        agg_data = data.groupby(x_column)[y_column].sum().reset_index()
        value_column = y_column
    else:
        # Sinon, compter les occurrences de x_column
        agg_data = data[x_column].value_counts().reset_index()
        agg_data.columns = [x_column, 'Count']
        value_column = 'Count'
    
    # Appliquer l'ordre personnalisé si fourni
    if custom_order is not None and len(custom_order) > 0:
        # Filtrer les catégories qui existent réellement dans les données
        valid_categories = [cat for cat in custom_order if cat in agg_data[x_column].values]
        if valid_categories:  # Seulement si des catégories valides existent
            agg_data[x_column] = pd.Categorical(
                agg_data[x_column], 
                categories=valid_categories, 
                ordered=True
            )
            agg_data = agg_data.sort_values(x_column)
    
    # Définir les titres par défaut
    x_axis_title = x_axis_title or x_column
    y_axis_title = y_axis_title or (y_column if y_column else "Nombre d'occurrences")
    
    # Préparation des valeurs pour l'affichage
    text_values = agg_data[value_column].astype(str) if show_values else None
    
    # Création du graphique
    fig = go.Figure(
        go.Bar(
            x=agg_data[x_column],
            y=agg_data[value_column],
            marker_color=bar_color,
            text=text_values,
            textposition='inside',
            textfont=dict(color='white'),
            name=""
        )
    )
    
    # Configuration du layout
    layout_config = {
        'title': title,
        'xaxis_title': x_axis_title,
        'yaxis_title': y_axis_title,
        'height': height,
        'width': width,
        'template': 'plotly_white',
        'showlegend': False
    }
    
    # Ajouter la rotation si demandée
    if rotate_x_labels:
        layout_config['xaxis'] = dict(
            title=x_axis_title,
            tickangle=x_rotation_angle,
            tickmode='linear'
        )
    
    fig.update_layout(**layout_config)
    
    return fig


def create_simple_normalized_barplot(
    data,
    x_column,
    y_column=None,
    title="",
    x_axis_title=None,
    y_axis_title=None,
    bar_color="#0D3182",
    show_values=True,
    height=500,
    width=1500,
    custom_order=None,
    percentage_format=".1f",
    rotate_x_labels=False,  # ← Nouveau paramètre
    x_rotation_angle=45     # ← Nouveau paramètre
):
    """
    Crée un barplot simple normalisé où CHAQUE BARRE = 100%.
    Utile pour indiquer qu'une variable de stratification doit être sélectionnée.
    
    Args:
        data (pd.DataFrame): DataFrame contenant les données
        x_column (str): Nom de la colonne pour l'axe X
        y_column (str, optional): Nom de la colonne pour les valeurs. Si None, compte les occurrences
        title (str, optional): Titre du graphique
        x_axis_title (str, optional): Titre de l'axe X
        y_axis_title (str, optional): Titre de l'axe Y
        bar_color (str, optional): Couleur des barres
        show_values (bool, optional): Afficher les pourcentages dans les barres
        height (int, optional): Hauteur du graphique
        width (int, optional): Largeur du graphique
        custom_order (list, optional): Ordre personnalisé pour les catégories
        percentage_format (str, optional): Format des pourcentages
        rotate_x_labels (bool, optional): Rotation des labels de l'axe X
        x_rotation_angle (int, optional): Angle de rotation des labels
        
    Returns:
        plotly.graph_objects.Figure: Figure Plotly du barplot normalisé simple
    """
    # Si y_column est fourni et existe, utiliser ces données agrégées
    if y_column is not None and y_column in data.columns:
        agg_data = data.groupby(x_column)[y_column].sum().reset_index()
        value_column = y_column
    else:
        # Sinon, compter les occurrences de x_column
        agg_data = data[x_column].value_counts().reset_index()
        agg_data.columns = [x_column, 'Count']
        value_column = 'Count'
    
    # Pour le barplot normalisé simple : chaque barre = 100%
    agg_data['percentage'] = 100.0  # Chaque barre fait 100%
    
    # Appliquer l'ordre personnalisé si fourni
    if custom_order is not None and len(custom_order) > 0:
        # Filtrer les catégories qui existent réellement dans les données
        valid_categories = [cat for cat in custom_order if cat in agg_data[x_column].values]
        if valid_categories:  # Seulement si des catégories valides existent
            agg_data[x_column] = pd.Categorical(
                agg_data[x_column], 
                categories=valid_categories, 
                ordered=True
            )
            agg_data = agg_data.sort_values(x_column)
    
    # Définir les titres par défaut
    x_axis_title = x_axis_title or x_column
    y_axis_title = y_axis_title or "Proportion (%)"
    
    # Préparation des valeurs pour l'affichage
    if show_values:
        text_values = [
            f"100% ({int(val)})" 
            for val in agg_data[value_column]
        ]
    else:
        text_values = None
    
    # Création du graphique
    fig = go.Figure(
        go.Bar(
            x=agg_data[x_column],
            y=agg_data['percentage'],
            marker_color=bar_color,
            text=text_values,
            textposition='inside',
            textfont=dict(color='white', size=10),
            name=""
        )
    )
    
    # Configuration du layout
    layout_config = {
        'title': title,
        'xaxis_title': x_axis_title,
        'yaxis_title': y_axis_title,
        'height': height,
        'width': width,
        'template': 'plotly_white',
        'showlegend': False,
        'yaxis': dict(range=[0, 100])  # Fixer l'échelle de 0 à 100%
    }
    
    # Ajouter la rotation si demandée
    if rotate_x_labels:
        layout_config['xaxis'] = dict(
            title=x_axis_title,
            tickangle=x_rotation_angle,
            tickmode='linear'
        )
    
    fig.update_layout(**layout_config)
    
    return fig


def create_cumulative_barplot(
    data,
    category_column,
    title="Distribution and cumulative count",
    x_axis_title=None,
    bar_y_axis_title="Patient count",
    line_y_axis_title="Cumulative count",
    bar_color='#0D3182',
    line_color='#FF6B6B',
    text_color='white',
    show_bar_values=True,
    show_cumulative_values=True,
    height=500,
    width=1500,
    custom_order=None
):
    """
    Crée un barplot avec une courbe d'effectif cumulé.

    Args:
        data (pd.DataFrame): DataFrame contenant les données
        category_column (str): Nom de la colonne à catégoriser
        title (str, optional): Titre du graphique
        x_axis_title (str, optional): Titre de l'axe X
        bar_y_axis_title (str, optional): Titre de l'axe Y pour les barres
        line_y_axis_title (str, optional): Titre de l'axe Y pour la courbe cumulative
        bar_color (str, optional): Couleur des barres en format hex
        line_color (str, optional): Couleur de la courbe cumulative en format hex
        text_color (str, optional): Couleur du texte des valeurs
        show_bar_values (bool, optional): Afficher les valeurs sur les barres
        show_cumulative_values (bool, optional): Afficher les valeurs de la courbe cumulative
        height (int, optional): Hauteur du graphique en pixels
        width (int, optional): Largeur du graphique en pixels
        custom_order (list, optional): Liste définissant l'ordre personnalisé des catégories

    Returns:
        plotly.graph_objects.Figure: Figure plotly avec barplot et courbe cumulative
    """

    # Calculer le nombre d'occurrences pour chaque catégorie
    count_data = data[category_column].value_counts().reset_index()
    count_data.columns = [category_column, 'Count']
    
    # Appliquer l'ordre personnalisé si fourni
    if custom_order is not None:
        count_data[category_column] = pd.Categorical(
            count_data[category_column], 
            categories=custom_order, 
            ordered=True
        )
        count_data = count_data.sort_values(category_column)
    
    # Calculer l'effectif cumulé
    count_data['Cumulative'] = count_data['Count'].cumsum()
    
    # Définir les titres d'axes s'ils ne sont pas spécifiés
    if x_axis_title is None:
        x_axis_title = category_column

    # Préparation des valeurs texte pour les barres
    bar_text_values = count_data['Count'].astype(str) if show_bar_values else None
    
    # Préparation des valeurs texte pour la courbe cumulative
    line_text_values = count_data['Cumulative'].astype(str) if show_cumulative_values else None

    # Création de la figure
    fig = go.Figure()

    # Ajout du barplot
    fig.add_trace(go.Bar(
        x=count_data[category_column],
        y=count_data['Count'],
        name=bar_y_axis_title,
        marker_color=bar_color,
        text=bar_text_values,
        textposition='inside',
        textfont=dict(color=text_color)
    ))

    # Ajout de la courbe cumulative
    fig.add_trace(go.Scatter(
        x=count_data[category_column],
        y=count_data['Cumulative'],
        name=line_y_axis_title,
        mode='lines+markers+text',
        line=dict(color=line_color, width=3),
        marker=dict(size=10),
        text=line_text_values,
        textposition='top center'
    ))
    
    # Configuration du layout avec deux axes Y
    fig.update_layout(
        title=title,
        xaxis_title=x_axis_title,
        yaxis_title=bar_y_axis_title,
        yaxis2=dict(
            title=line_y_axis_title,
            overlaying='y',
            side='right'
        ),
        height=height,
        width=width,
        template='plotly_white',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )

    return fig

def create_grouped_barplot_with_cumulative(
    data,
    x_column,
    group_column,
    title="Distribution by year with cumulative counts",
    x_axis_title=None,
    bar_y_axis_title="Patient count",
    line_y_axis_title="Cumulative count",
    height=500,
    width=1500,
    custom_x_order=None,
    show_cumulative=True
):
    """
    Crée un barplot groupé (barres côte à côte) avec une courbe d'effectif cumulé.
    
    Args:
        data (pd.DataFrame): DataFrame contenant les données
        x_column (str): Colonne pour l'axe X (ex: Year)
        group_column (str): Colonne pour grouper les barres (ex: Donor Type)
        title (str): Titre du graphique
        x_axis_title (str): Titre de l'axe X
        bar_y_axis_title (str): Titre de l'axe Y pour les barres
        line_y_axis_title (str): Titre de l'axe Y pour la courbe cumulative
        height (int): Hauteur du graphique
        width (int): Largeur du graphique
        custom_x_order (list): Ordre personnalisé pour l'axe X
        show_cumulative (bool): Afficher la courbe cumulative
        
    Returns:
        plotly.graph_objects.Figure: Figure Plotly du barplot groupé avec cumul
    """
    
    # Calculer les données groupées
    grouped_data = data.groupby([x_column, group_column]).size().unstack(fill_value=0)
    
    # Appliquer l'ordre personnalisé si fourni
    if custom_x_order is not None:
        grouped_data = grouped_data.reindex(custom_x_order, fill_value=0)
    
    # Réinitialiser l'index pour avoir x_column comme colonne
    grouped_data = grouped_data.reset_index()
    
    # Obtenir les catégories de groupe
    group_categories = [col for col in grouped_data.columns if col != x_column]
    
    # Créer la figure
    fig = go.Figure()
    
    # Palette de couleurs
    colors = px.colors.qualitative.Safe

    # Ajouter les barres groupées
    for i, category in enumerate(group_categories):
        fig.add_trace(go.Bar(
            name=category,
            x=grouped_data[x_column],
            y=grouped_data[category],
            marker_color=colors[i % len(colors)],
            text=grouped_data[category],
            textposition='outside',
            yaxis='y'
        ))
    
    # Calculer et ajouter la courbe cumulative si demandée
    if show_cumulative:
        # Calculer l'effectif total par année
        yearly_totals = grouped_data[group_categories].sum(axis=1)
        # Calculer le cumul
        cumulative_totals = yearly_totals.cumsum()
        
        fig.add_trace(go.Scatter(
            name='Cumulative count',
            x=grouped_data[x_column],
            y=cumulative_totals,
            mode='lines+markers+text',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=10),
            text=cumulative_totals,
            textposition='top center',
            yaxis='y2'
        ))
    
    # Définir les titres par défaut
    x_axis_title = x_axis_title or x_column
    
    # Configuration du layout
    layout_config = {
        'title': title,
        'xaxis_title': x_axis_title,
        'yaxis_title': bar_y_axis_title,
        'height': height,
        'width': width,
        'template': 'plotly_white',
        'barmode': 'group',  # Barres côte à côte
        'legend': dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    }
    
    # Ajouter le deuxième axe Y si on affiche le cumul
    if show_cumulative:
        layout_config['yaxis2'] = dict(
            title=line_y_axis_title,
            overlaying='y',
            side='right'
        )
    
    fig.update_layout(**layout_config)
    
    return fig

def create_stacked_barplot(
    data,
    x_column,
    y_column,
    stack_column,
    title="",
    x_axis_title=None,
    y_axis_title=None,
    color_map=None,
    show_values=True,
    height=500,
    width=1500,
    custom_order=None,
    rotate_x_labels=False,  # ← Nouveau paramètre
    x_rotation_angle=45     # ← Nouveau paramètre
):
    """
    Crée un barplot empilé avec Plotly et coloration cohérente.

    Args:
        data (pd.DataFrame): DataFrame contenant les données
        x_column (str): Nom de la colonne pour l'axe X (Age At Diagnosis)
        y_column (str): Nom de la colonne pour les valeurs (count)
        stack_column (str): Nom de la colonne pour l'empilement (Main Diagnosis). Si None, crée un barplot simple.
        title (str, optional): Titre du graphique
        x_axis_title (str, optional): Titre de l'axe X
        y_axis_title (str, optional): Titre de l'axe Y
        color_map (dict, optional): Dictionnaire de mapping couleurs pour chaque catégorie d'empilement
        show_values (bool, optional): Afficher les valeurs dans les barres
        height (int, optional): Hauteur du graphique
        width (int, optional): Largeur du graphique
        custom_order (list, optional): Liste définissant l'ordre personnalisé des catégories
        rotate_x_labels (bool, optional): Rotation des labels de l'axe X
        x_rotation_angle (int, optional): Angle de rotation des labels

    Returns:
        plotly.graph_objects.Figure: Figure Plotly du barplot empilé ou simple
    """
    # Si pas de colonne de stratification, utiliser la fonction simple
    if stack_column is None:
        return create_simple_barplot(
            data=data,
            x_column=x_column,
            y_column=y_column,
            title=title,
            x_axis_title=x_axis_title,
            y_axis_title=y_axis_title,
            show_values=show_values,
            height=height,
            width=width,
            custom_order=custom_order,
            rotate_x_labels=rotate_x_labels,
            x_rotation_angle=x_rotation_angle
        )
    
    # Préparer les données groupées
    grouped_data = data.groupby([x_column, stack_column]).size().unstack(fill_value=0).reset_index()
    
    # Appliquer l'ordre personnalisé si fourni
    if custom_order is not None and len(custom_order) > 0:
        # Filtrer les catégories qui existent réellement dans les données
        valid_categories = [cat for cat in custom_order if cat in grouped_data[x_column].values]
        if valid_categories:
            grouped_data[x_column] = pd.Categorical(
                grouped_data[x_column], 
                categories=valid_categories, 
                ordered=True
            )
            grouped_data = grouped_data.sort_values(x_column).reset_index(drop=True)
    
    # Définir les titres par défaut
    x_axis_title = x_axis_title or x_column
    y_axis_title = y_axis_title or "Patient count"
    
    # Préparer les traces pour chaque catégorie d'empilement
    traces = []
    stack_categories = grouped_data.columns[1:]
    
    # Utiliser un color map cohérent ou générer des couleurs
    if color_map is None:
        color_map = create_consistent_color_map(data, stack_column)
    
    for category in stack_categories:
        traces.append(go.Bar(
            name=category,
            x=grouped_data[x_column],
            y=grouped_data[category],
            marker_color=color_map.get(category, px.colors.qualitative.Safe[0]),
            text=grouped_data[category] if show_values else None,
            textposition='inside'
        ))
    
    # Créer la figure avec empilement
    fig = go.Figure(data=traces)
    
    # Configuration du layout
    layout_config = {
        'title': title,
        'barmode': 'stack',
        'xaxis_title': x_axis_title,
        'yaxis_title': y_axis_title,
        'height': height,
        'width': width,
        'template': 'plotly_white',
        'legend_title_text': stack_column
    }
    
    # Ajouter la rotation si demandée
    if rotate_x_labels:
        layout_config['xaxis'] = dict(
            title=x_axis_title,
            tickangle=x_rotation_angle,
            tickmode='linear'
        )
    
    fig.update_layout(**layout_config)
    
    return fig


def create_normalized_barplot(
    data,
    x_column,
    y_column,
    stack_column,
    title="",
    x_axis_title=None,
    y_axis_title=None,
    color_map=None,
    show_values=True,
    height=500,
    width=1500,
    custom_order=None,
    percentage_format=".1f",
    rotate_x_labels=False,  # ← Nouveau paramètre
    x_rotation_angle=45     # ← Nouveau paramètre
):
    """
    Crée un barplot empilé normalisé (100%) avec Plotly et coloration cohérente.
    """
    # Préparer les données groupées
    grouped_data = data.groupby([x_column, stack_column]).size().unstack(fill_value=0)
    
    # Calculer les totaux par catégorie x
    grouped_data_with_totals = grouped_data.copy()
    grouped_data_with_totals['Total'] = grouped_data_with_totals.sum(axis=1)
    
    # Calculer les pourcentages
    normalized_data = grouped_data.div(grouped_data_with_totals['Total'], axis=0) * 100
    normalized_data = normalized_data.reset_index()
    
    # Conserver les valeurs absolues pour l'affichage
    absolute_values = grouped_data.reset_index()
    
    # Appliquer l'ordre personnalisé si fourni
    if custom_order is not None and len(custom_order) > 0:
        valid_categories = [cat for cat in custom_order if cat in normalized_data[x_column].values]
        if valid_categories:
            normalized_data[x_column] = pd.Categorical(
                normalized_data[x_column], 
                categories=valid_categories, 
                ordered=True
            )
            normalized_data = normalized_data.sort_values(x_column).reset_index(drop=True)
            
            # Appliquer le même ordre aux valeurs absolues
            absolute_values[x_column] = pd.Categorical(
                absolute_values[x_column], 
                categories=valid_categories, 
                ordered=True
            )
            absolute_values = absolute_values.sort_values(x_column).reset_index(drop=True)
    
    # Définir les titres par défaut
    x_axis_title = x_axis_title or x_column
    y_axis_title = y_axis_title or "Percentage (%)"
    
    # Préparer les traces pour chaque catégorie d'empilement
    traces = []
    stack_categories = normalized_data.columns[1:]
    
    # Utiliser un color map cohérent ou générer des couleurs
    if color_map is None:
        color_map = create_consistent_color_map(data, stack_column)
    
    for category in stack_categories:
        # Préparer les textes d'affichage (pourcentages et valeurs absolues)
        if show_values:
            text_values = []
            for idx, x_val in enumerate(normalized_data[x_column]):
                pct = normalized_data.loc[idx, category]
                abs_val = absolute_values.loc[idx, category]
                if pct > 0:  # Afficher seulement si la valeur est significative
                    text_values.append(f"{pct:{percentage_format}}% ({int(abs_val)})")
                else:
                    text_values.append("")
        else:
            text_values = None
        
        traces.append(go.Bar(
            name=category,
            x=normalized_data[x_column],
            y=normalized_data[category],
            marker_color=color_map.get(category, px.colors.qualitative.Safe[0]),
            text=text_values,
            textposition='inside',
            textfont=dict(size=10)
        ))
    
    # Créer la figure avec empilement
    fig = go.Figure(data=traces)
    
    # Configuration du layout
    layout_config = {
        'title': title,
        'barmode': 'stack',
        'xaxis_title': x_axis_title,
        'yaxis_title': y_axis_title,
        'height': height,
        'width': width,
        'template': 'plotly_white',
        'legend_title_text': stack_column,
        'yaxis': dict(range=[0, 100])  # Fixer les limites de l'axe Y de 0 à 100%
    }
    
    # Ajouter la rotation si demandée
    if rotate_x_labels:
        layout_config['xaxis'] = dict(
            title=x_axis_title,
            tickangle=x_rotation_angle,
            tickmode='linear'
        )
    
    fig.update_layout(**layout_config)
    
    return fig

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import gaussian_kde
from typing import Optional, Union, Tuple, Dict, Any

def create_histogram_with_density(
    data: pd.DataFrame,
    value_column: str,
    filter_column: Optional[str] = None,
    filter_value: Optional[str] = None,
    date_columns: Optional[Tuple[str, str]] = None,
    title: str = "Distribution with density curve",
    x_axis_title: str = "Values",
    y_axis_title: str = "Frequency",
    bin_size: Optional[float] = None,
    percentile_limit: float = 0.99,
    color_histogram: str = '#2ecc71',
    color_density: str = '#e74c3c',
    opacity: float = 0.75,
    height: int = 400,
    width: Optional[int] = None,
    template: str = "plotly_white"
) -> go.Figure:
    """
    Crée un graphique avec histogramme et courbe de densité pour une variable numérique.
    
    Args:
        data (pd.DataFrame): DataFrame contenant les données
        value_column (str): Nom de la colonne à analyser (ou nom de la colonne calculée)
        filter_column (str, optional): Colonne pour filtrer les données
        filter_value (str, optional): Valeur pour filtrer les données
        date_columns (tuple, optional): Tuple de (date_debut, date_fin) pour calculer une durée
        title (str): Titre du graphique
        x_axis_title (str): Titre de l'axe X
        y_axis_title (str): Titre de l'axe Y
        bin_size (float, optional): Taille des bins. Si None, calculé automatiquement
        percentile_limit (float): Percentile pour limiter l'affichage (éviter les outliers)
        color_histogram (str): Couleur de l'histogramme
        color_density (str): Couleur de la courbe de densité
        opacity (float): Opacité de l'histogramme
        height (int): Hauteur du graphique
        width (int, optional): Largeur du graphique
        template (str): Template Plotly
        
    Returns:
        go.Figure: Figure Plotly avec histogramme et densité
    """
    
    # Copie des données pour éviter les modifications
    processed_data = data.copy()
    
    # Filtrage des données si spécifié
    if filter_column and filter_value:
        if filter_column not in processed_data.columns:
            raise ValueError(f"Colonne de filtrage '{filter_column}' non trouvée")
        processed_data = processed_data[processed_data[filter_column] == filter_value].copy()
    
    # Calcul de la durée si des colonnes de dates sont spécifiées
    if date_columns:
        date_start, date_end = date_columns
        
        if date_start not in processed_data.columns or date_end not in processed_data.columns:
            raise ValueError(f"Colonnes de dates '{date_start}' ou '{date_end}' non trouvées")
        
        # Conversion en datetime
        processed_data[date_start] = pd.to_datetime(processed_data[date_start])
        processed_data[date_end] = pd.to_datetime(processed_data[date_end])
        
        # Calcul de la durée en jours
        processed_data[value_column] = (processed_data[date_end] - processed_data[date_start]).dt.days
    
    # Vérification que la colonne existe
    if value_column not in processed_data.columns:
        raise ValueError(f"Colonne '{value_column}' non trouvée")
    
    # Nettoyage des données (suppression des valeurs nulles et négatives)
    clean_data = processed_data.dropna(subset=[value_column])
    clean_data = clean_data[clean_data[value_column] >= 0]  # Supprime les valeurs négatives
    
    if clean_data.empty:
        raise ValueError("Aucune donnée valide après nettoyage")
    
    values = clean_data[value_column]
    
    # Calcul des statistiques
    mean_val = values.mean()
    std_val = values.std()
    min_val = values.min()
    max_val = values.max()
    
    # Limitation par percentile pour éviter les outliers
    xmax = values.quantile(percentile_limit)
    
    # Calcul automatique de bin_size si non spécifié
    if bin_size is None:
        # Règle de Scott ou Freedman-Diaconis
        n = len(values)
        if n > 1:
            # Règle de Freedman-Diaconis
            iqr = values.quantile(0.75) - values.quantile(0.25)
            bin_size = 2 * iqr / (n ** (1/3))
            bin_size = max(bin_size, (xmax - min_val) / 50)  # Au moins 50 bins
        else:
            bin_size = 1
    
    # Filtrage des valeurs pour l'affichage
    display_values = values[values <= xmax]
    
    # Création de la figure
    fig = go.Figure()
    
    # Histogramme
    fig.add_trace(
        go.Histogram(
            x=display_values,
            name="Histogramme",
            marker_color=color_histogram,
            opacity=opacity,
            xbins=dict(
                start=0,
                end=xmax,
                size=bin_size
            ),
            yaxis='y1',
            hovertemplate="<b>Interval:</b> %{x}<br><b>Frequency:</b> %{y}<extra></extra>"
        )
    )
    
    # Calcul et ajout de la courbe de densité si assez de données
    if len(display_values) > 5:  # Minimum de points pour une densité
        try:
            # Calcul de la densité
            density = gaussian_kde(display_values)
            xs = np.linspace(0, xmax, 500)
            ys = density(xs)
            
            # Ajustement de l'échelle pour correspondre à l'histogramme
            hist, bin_edges = np.histogram(display_values, 
                                         bins=np.arange(0, xmax + bin_size, bin_size))
            scale_factor = len(display_values) * bin_size
            ys_scaled = ys * scale_factor
            
            # Courbe de densité
            fig.add_trace(
                go.Scatter(
                    x=xs,
                    y=ys_scaled,
                    name='Density',
                    line=dict(color=color_density, width=2),
                    yaxis='y1',
                    hovertemplate="<b>Value:</b> %{x:.1f}<br><b>Density:</b> %{y:.1f}<extra></extra>"
                )
            )
        except Exception as e:
            print(f"Impossible de calculer la densité: {e}")
    
    # Calcul de l'espacement des ticks sur l'axe X
    x_range = xmax - min_val
    if x_range <= 50:
        dtick = 5
    elif x_range <= 200:
        dtick = 10
    elif x_range <= 500:
        dtick = 25
    else:
        dtick = 50
    
    # Mise en page
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center'
        ),
        xaxis_title=x_axis_title,
        yaxis_title=y_axis_title,
        bargap=0.05,
        hovermode="x unified",
        showlegend=True,
        template=template,
        height=height,
        width=width,
        xaxis=dict(
            range=[0, xmax],
            dtick=dtick,
            title=x_axis_title
        ),
        yaxis=dict(
            rangemode='tozero',
            title=y_axis_title
        )
    )
    
    # Ajout d'annotations avec les statistiques
    fig.add_annotation(
        x=0.98,
        y=0.98,
        xref='paper',
        yref='paper',
        text=f"<b>Statistics:</b><br>"
             f"N = {len(display_values)}<br>"
             f"Mean = {mean_val:.1f}<br>"
             f"Std Dev = {std_val:.1f}<br>"
             f"Min = {min_val:.1f}<br>"
             f"Max = {max_val:.1f}",
        showarrow=False,
        align="left",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="rgba(0,0,0,0.2)",
        borderwidth=1,
        font=dict(size=10)
    )
    
    return fig

def create_duration_histogram(
    data: pd.DataFrame,
    date_start_col: str,
    date_end_col: str,
    filter_column: Optional[str] = None,
    filter_value: Optional[str] = None,
    title: str = "Distribution of durations",
    unit: str = "days",
    bin_size: Optional[float] = None,
    **kwargs
) -> go.Figure:
    """
    Fonction simplifiée pour créer un histogramme de durées entre deux dates.
    
    Args:
        data (pd.DataFrame): DataFrame contenant les données
        date_start_col (str): Nom de la colonne de date de début
        date_end_col (str): Nom de la colonne de date de fin
        filter_column (str, optional): Colonne pour filtrer les données
        filter_value (str, optional): Valeur pour filtrer les données
        title (str): Titre du graphique
        unit (str): Unité de mesure (jours, mois, années...)
        bin_size (float, optional): Taille des bins
        **kwargs: Arguments supplémentaires pour create_histogram_with_density
        
    Returns:
        go.Figure: Figure Plotly
    """
    
    return create_histogram_with_density(
        data=data,
        value_column='duration_calculated',  # Nom temporaire
        filter_column=filter_column,
        filter_value=filter_value,
        date_columns=(date_start_col, date_end_col),
        title=title,
        x_axis_title=unit.capitalize(),
        y_axis_title="Nombre de patients",
        bin_size=bin_size,
        **kwargs
    )

def create_stratified_histogram_with_density(
    data: pd.DataFrame,
    value_column: str,
    stratification_column: str,
    filter_column: Optional[str] = None,
    filter_value: Optional[str] = None,
    date_columns: Optional[Tuple[str, str]] = None,
    selected_strata: Optional[List] = None,
    max_strata: int = 3,
    title: str = "Stratified distribution with density",
    x_axis_title: str = "Values",
    y_axis_title: str = "Frequency",
    bin_size: Optional[float] = None,
    percentile_limit: float = 0.99,
    opacity: float = 0.6,
    height: int = 500,
    width: Optional[int] = None,
    template: str = "plotly_white",
    show_legend: bool = True
) -> go.Figure:
    """
    Crée un histogramme avec courbes de densité stratifié par une variable (ex: années).
    Affiche plusieurs histogrammes semi-transparents et leurs courbes de densité correspondantes.
    
    Args:
        data (pd.DataFrame): DataFrame contenant les données
        value_column (str): Nom de la colonne à analyser (ou nom de la colonne calculée)
        stratification_column (str): Colonne pour stratifier (ex: 'Year')
        filter_column (str, optional): Colonne pour filtrer les données
        filter_value (str, optional): Valeur pour filtrer les données
        date_columns (tuple, optional): Tuple de (date_debut, date_fin) pour calculer une durée
        selected_strata (list, optional): Liste des strates à afficher. Si None, prend les dernières
        max_strata (int): Nombre maximum de strates à afficher
        title (str): Titre du graphique
        x_axis_title (str): Titre de l'axe X
        y_axis_title (str): Titre de l'axe Y
        bin_size (float, optional): Taille des bins. Si None, calculé automatiquement
        percentile_limit (float): Percentile pour limiter l'affichage
        opacity (float): Opacité des histogrammes
        height (int): Hauteur du graphique
        width (int, optional): Largeur du graphique
        template (str): Template Plotly
        show_legend (bool): Afficher la légende
        
    Returns:
        go.Figure: Figure Plotly avec histogrammes et densités stratifiés
    """
    
    # Copie des données pour éviter les modifications
    processed_data = data.copy()
    
    # Filtrage des données si spécifié
    if filter_column and filter_value:
        if filter_column not in processed_data.columns:
            raise ValueError(f"Colonne de filtrage '{filter_column}' non trouvée")
        processed_data = processed_data[processed_data[filter_column] == filter_value].copy()
    
    # Calcul de la durée si des colonnes de dates sont spécifiées
    if date_columns:
        date_start, date_end = date_columns
        
        if date_start not in processed_data.columns or date_end not in processed_data.columns:
            raise ValueError(f"Colonnes de dates '{date_start}' ou '{date_end}' non trouvées")
        
        # Conversion en datetime
        processed_data[date_start] = pd.to_datetime(processed_data[date_start])
        processed_data[date_end] = pd.to_datetime(processed_data[date_end])
        
        # Calcul de la durée en jours
        processed_data[value_column] = (processed_data[date_end] - processed_data[date_start]).dt.days
    
    # Vérifications
    if value_column not in processed_data.columns:
        raise ValueError(f"Colonne '{value_column}' non trouvée")
    
    if stratification_column not in processed_data.columns:
        raise ValueError(f"Colonne de stratification '{stratification_column}' non trouvée")
    
    # Nettoyage des données
    clean_data = processed_data.dropna(subset=[value_column, stratification_column])
    clean_data = clean_data[clean_data[value_column] >= 0]  # Supprime les valeurs négatives
    
    if clean_data.empty:
        raise ValueError("Aucune donnée valide après nettoyage")
    
    # Sélection des strates
    if selected_strata is None:
        # Prendre les dernières strates (ex: 3 dernières années)
        available_strata = sorted(clean_data[stratification_column].unique())
        if stratification_column == 'Year' or str(clean_data[stratification_column].dtype).startswith('int'):
            # Pour les années ou variables numériques : prendre les plus récentes
            selected_strata = available_strata[-max_strata:]
        else:
            # Pour les variables catégorielles : prendre les plus fréquentes
            strata_counts = clean_data[stratification_column].value_counts()
            selected_strata = strata_counts.head(max_strata).index.tolist()
    else:
        # Filtrer pour ne garder que les strates présentes dans les données
        available_strata = clean_data[stratification_column].unique()
        selected_strata = [s for s in selected_strata if s in available_strata][:max_strata]
    
    if not selected_strata:
        raise ValueError("Aucune strate valide trouvée")
    
    # Couleurs pour les strates
    colors = plotly.colors.qualitative.Set1
    if len(colors) < len(selected_strata):
        colors = colors * (len(selected_strata) // len(colors) + 1)
    
    # Calculer les limites globales pour tous les groupes
    all_values = clean_data[clean_data[stratification_column].isin(selected_strata)][value_column]
    global_max = all_values.quantile(percentile_limit)
    global_min = all_values.min()
    
    # Calcul automatique de bin_size si non spécifié
    if bin_size is None:
        n_total = len(all_values)
        if n_total > 1:
            iqr = all_values.quantile(0.75) - all_values.quantile(0.25)
            bin_size = 2 * iqr / (n_total ** (1/3))
            bin_size = max(bin_size, (global_max - global_min) / 50)
        else:
            bin_size = 1
    
    # Création de la figure
    fig = go.Figure()
    
    # Traitement pour chaque strate
    strata_stats = {}
    
    for i, stratum in enumerate(selected_strata):
        stratum_data = clean_data[clean_data[stratification_column] == stratum]
        stratum_values = stratum_data[value_column]
        
        if len(stratum_values) == 0:
            continue
        
        # Filtrer les valeurs pour l'affichage
        display_values = stratum_values[stratum_values <= global_max]
        
        if len(display_values) == 0:
            continue
        
        # Couleur pour cette strate
        color = colors[i]
        
        # Calculer les statistiques
        strata_stats[stratum] = {
            'n': len(display_values),
            'mean': display_values.mean(),
            'std': display_values.std(),
            'min': display_values.min(),
            'max': display_values.max()
        }
        
        # Ajouter l'histogramme
        fig.add_trace(
            go.Histogram(
                x=display_values,
                name=f"{stratification_column}: {stratum}",
                marker_color=color,
                opacity=opacity,
                xbins=dict(
                    start=0,
                    end=global_max,
                    size=bin_size
                ),
                legendgroup=f"group_{stratum}",
                hovertemplate=f"<b>{stratification_column}: {stratum}</b><br>" +
                             "Interval: %{x}<br>" +
                             "Frequency: %{y}<br>" +
                             f"N = {len(display_values)}<extra></extra>"
            )
        )
        
        # Ajouter la courbe de densité si suffisamment de données
        if len(display_values) > 5:
            try:
                density = gaussian_kde(display_values)
                xs = np.linspace(0, global_max, 500)
                ys = density(xs)
                
                # Ajustement de l'échelle
                hist, bin_edges = np.histogram(display_values, 
                                             bins=np.arange(0, global_max + bin_size, bin_size))
                scale_factor = len(display_values) * bin_size
                ys_scaled = ys * scale_factor
                
                # Courbe de densité
                fig.add_trace(
                    go.Scatter(
                        x=xs,
                        y=ys_scaled,
                        name=f"Density {stratum}",
                        line=dict(color=color, width=3),
                        legendgroup=f"group_{stratum}",
                        showlegend=False,  # Éviter la duplication dans la légende
                        hovertemplate=f"<b>Density {stratification_column}: {stratum}</b><br>" +
                                     "Value: %{x:.1f}<br>" +
                                     "Density: %{y:.1f}<extra></extra>"
                    )
                )
            except Exception as e:
                print(f"Impossible de calculer la densité pour {stratum}: {e}")
    
    # Calcul de l'espacement des ticks
    x_range = global_max - global_min
    if x_range <= 50:
        dtick = 5
    elif x_range <= 200:
        dtick = 10
    elif x_range <= 500:
        dtick = 25
    else:
        dtick = 50
    
    # Mise en page
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center'
        ),
        xaxis_title=x_axis_title,
        yaxis_title=y_axis_title,
        bargap=0.05,
        barmode='overlay',  # Superposition des histogrammes
        hovermode="x unified",
        showlegend=show_legend,
        template=template,
        height=height,
        width=width,
        xaxis=dict(
            range=[0, global_max],
            dtick=dtick,
            title=x_axis_title
        ),
        yaxis=dict(
            rangemode='tozero',
            title=y_axis_title
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01
        )
    )
    
    # Ajout d'annotations avec les statistiques pour chaque strate
    if strata_stats:
        annotation_text = "<b>Stratum-specific statistics:</b><br>"
        for stratum, stats in strata_stats.items():
            annotation_text += f"<b>{stratum}:</b> N={stats['n']}, μ={stats['mean']:.1f}, σ={stats['std']:.1f}<br>"
        
        fig.add_annotation(
            x=0.02,
            y=0.98,
            xref='paper',
            yref='paper',
            text=annotation_text,
            showarrow=False,
            align="left",
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1,
            font=dict(size=9)
        )
    
    return fig

def create_stacked_yes_no_barplot(data, treatment_columns, title="", x_axis_title="", 
                                   y_axis_title="", height=400, width=None, show_values=True):
    """
    Crée un graphique en barres empilées montrant les proportions Oui/Non pour chaque traitement
    
    Args:
        data (pd.DataFrame): DataFrame contenant les données
        treatment_columns (list): Liste des colonnes de traitement à analyser
        title (str): Titre du graphique
        x_axis_title (str): Titre de l'axe X
        y_axis_title (str): Titre de l'axe Y
        height (int): Hauteur du graphique
        width (int): Largeur du graphique
        show_values (bool): Afficher les valeurs sur les barres
    
    Returns:
        plotly.graph_objects.Figure: Figure Plotly
    """

    # Calculer les proportions pour chaque traitement
    proportions_data = []
    
    for col in treatment_columns:
        # Compter les Oui et Non
        counts = data[col].value_counts()
        total = len(data)
        
        oui_count = counts.get('Yes', 0)
        non_count = counts.get('No', 0)
        
        oui_percent = (oui_count / total) * 100 if total > 0 else 0
        non_percent = (non_count / total) * 100 if total > 0 else 0
        
        # Nettoyer le nom du traitement pour l'affichage
        treatment_name = col.replace('Prep Regimen ', '').strip()
        
        proportions_data.append({
            'Traitement': treatment_name,
            'Oui_percent': oui_percent,
            'Non_percent': non_percent,
            'Oui_count': oui_count,
            'Non_count': non_count
        })
    
    proportions_df = pd.DataFrame(proportions_data)
    
    # Trier par proportion de Oui (descendant)
    proportions_df = proportions_df.sort_values('Oui_percent', ascending=False)
    
    # Créer le graphique
    fig = go.Figure()
    
    # Barre pour "Oui"
    fig.add_trace(go.Bar(
        name='Yes',
        x=proportions_df['Traitement'],
        y=proportions_df['Oui_percent'],
        marker_color='#27BDBE',
        text=[f'{p:.1f}%<br>({c})' for p, c in zip(proportions_df['Oui_percent'], proportions_df['Oui_count'])],
        textposition='inside' if show_values else 'none',
        textfont=dict(color='white', size=10)
    ))
    
    # Barre pour "Non"
    fig.add_trace(go.Bar(
        name='No',
        x=proportions_df['Traitement'],
        y=proportions_df['Non_percent'],
        marker_color='#FF6B6B',
        text=[f'{p:.1f}%<br>({c})' for p, c in zip(proportions_df['Non_percent'], proportions_df['Non_count'])],
        textposition='inside' if show_values else 'none',
        textfont=dict(color='white', size=10)
    ))
    
    # Configuration du layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=14)
        ),
        xaxis=dict(
            title=x_axis_title,
            tickfont=dict(size=10),
            tickangle=-45
        ),
        yaxis=dict(
            title=y_axis_title,
            range=[0, 100],
            tickfont=dict(size=10)
        ),
        barmode='stack',
        legend=dict(
            x=1.02,
            y=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        ),
        height=height,
        width=width,
        margin=dict(l=50, r=100, t=60, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Ajout de la grille
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    
    return fig

def calculate_max_followup_days(data):
    """
    Calcule la durée maximale de suivi dans les données pour déterminer 
    jusqu'où dessiner le graphique GVH chronique
    
    Args:
        data (pd.DataFrame): DataFrame avec les données
        
    Returns:
        int: Durée maximale en jours (minimum 365 pour avoir au moins 1 an)
    """
    try:
        df = data.copy()
        
        # Convertir les dates nécessaires
        df['Treatment Date'] = pd.to_datetime(df['Treatment Date'], format='mixed', errors='coerce')
        df['Date Of Last Follow Up'] = pd.to_datetime(df['Date Of Last Follow Up'], format='mixed', errors='coerce')
        df['First Cgvhd Occurrence Date'] = pd.to_datetime(df['First Cgvhd Occurrence Date'], format='mixed', errors='coerce')

        # Calculer les durées de suivi
        df['followup_days'] = (df['Date Of Last Follow Up'] - df['Treatment Date']).dt.days
        df['gvhc_days'] = (df['First Cgvhd Occurrence Date'] - df['Treatment Date']).dt.days
        
        # Nettoyer les valeurs invalides
        valid_followup = df['followup_days'].dropna()
        valid_followup = valid_followup[valid_followup >= 0]
        
        valid_gvhc = df['gvhc_days'].dropna()
        valid_gvhc = valid_gvhc[valid_gvhc >= 0]
        
        # Prendre le maximum entre suivi et événements GVH chronique
        max_followup = valid_followup.max() if len(valid_followup) > 0 else 365
        max_gvhc = valid_gvhc.max() if len(valid_gvhc) > 0 else 365
        
        max_days = max(max_followup, max_gvhc, 365)  # Au minimum 1 an
        
        # Limiter à une valeur raisonnable (ex: 10 ans)
        max_days = min(max_days, 3650)
        
        print(f"Durée maximale calculée pour GVH chronique: {max_days} jours ({max_days/365.25:.1f} ans)")
        return int(max_days)
        
    except Exception as e:
        print(f"Erreur lors du calcul de la durée maximale: {e}")
        return 365  # Fallback à 1 an


def create_competing_risks_analysis(data, gvh_type):
    """
    Crée l'analyse de risques compétitifs pour GvH aiguë ou chronique - Version améliorée
    avec gestion de l'affichage initial limité pour GVH chronique
    """
    try:
        # Import de la classe CompetingRisksAnalyzer
        import modules.competing_risks as cr
        CompetingRisksAnalyzer = cr.CompetingRisksAnalyzer
    except ImportError:
        raise ImportError("CompetingRisksAnalyzer non trouvé. Assurez-vous que modules/competing_risks.py existe.")
    
    # Vérifier les colonnes nécessaires
    required_base_columns = ['Treatment Date', 'Status Last Follow Up', 'Date Of Last Follow Up']
    
    if gvh_type == 'acute':
        required_gvh_columns = ['First Agvhd Occurrence', 'First Agvhd Occurrence Date']
        max_days = 100  # Garder 100 jours pour GVH aiguë
        initial_display_days = 100  # Affichage complet pour GVH aiguë
        title = "Competing Risks Analysis: Acute Graft-versus-Host Disease vs Death (100 Days)"
        event_label = 'Acute GvH'
        event_color = '#e74c3c'
    else:  # chronic
        required_gvh_columns = ['First Cgvhd Occurrence', 'First Cgvhd Occurrence Date']
        
        # NOUVEAUTÉ : Calculer la durée maximale réelle des données pour GVH chronique
        max_days = calculate_max_followup_days(data)
        initial_display_days = 365  # Affichage initial limité à 1 an
        
        title = f"Competing Risks Analysis: Chronic Graft-versus-Host Disease vs Death (up to {max_days} days)"
        event_label = 'Chronic GvH'
        event_color = '#f39c12'
    
    # Vérifier que toutes les colonnes nécessaires existent
    all_required_columns = required_base_columns + required_gvh_columns
    missing_columns = [col for col in all_required_columns if col not in data.columns]
    
    if missing_columns:
        # Créer un graphique d'erreur informatif
        fig = go.Figure()
        fig.add_annotation(
            text=f"<b>Colonnes manquantes pour l'analyse GvH :</b><br>{', '.join(missing_columns)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, 
            font=dict(size=16, family='Arial, sans-serif', color='#e74c3c'),
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#e74c3c",
            borderwidth=2
        )
        fig.update_layout(
            title=title,
            height=600,
            showlegend=False,
            paper_bgcolor='white',
            plot_bgcolor='rgba(248, 249, 250, 0.8)'
        )
        return fig
    
    # Filtrer les données pour ne garder que celles avec les informations de base
    df_filtered = data.dropna(subset=['Treatment Date']).copy()
    
    if len(df_filtered) == 0:
        # Graphique vide si pas de données
        fig = go.Figure()
        fig.add_annotation(
            text="<b>Aucune donnée disponible pour l'analyse</b>",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, 
            font=dict(size=16, family='Arial, sans-serif', color='#f39c12'),
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#f39c12",
            borderwidth=2
        )
        fig.update_layout(
            title=title,
            height=600,
            showlegend=False,
            paper_bgcolor='white',
            plot_bgcolor='rgba(248, 249, 250, 0.8)'
        )
        return fig
    
    try:
        # Initialiser l'analyseur
        analyzer = CompetingRisksAnalyzer(df_filtered, 'Treatment Date')
        
        # Configuration des événements selon le type de GvH
        if gvh_type == 'acute':
            events_config = {
                'aGvHD': {
                    'occurrence_col': 'First Agvhd Occurrence',
                    'date_col': 'First Agvhd Occurrence Date',
                    'label': event_label,
                    'color': event_color
                }
            }
        else:
            events_config = {
                'cGvHD': {
                    'occurrence_col': 'First Cgvhd Occurrence', 
                    'date_col': 'First Cgvhd Occurrence Date', 
                    'label': event_label,
                    'color': event_color
                }
            }
        
        # Configuration du suivi
        followup_config = {
            'status_col': 'Status Last Follow Up',
            'date_col': 'Date Of Last Follow Up',
            'death_value': 'Dead'
        }
        
        # Calculer l'incidence cumulative avec la nouvelle durée maximale
        results, processed_data = analyzer.calculate_cumulative_incidence(
            events_config, followup_config, max_days=max_days
        )
        
        # Créer le graphique avec l'affichage initial adapté
        fig = analyzer.create_competing_risks_plot(
            results, processed_data, events_config, 
            title=title, 
            initial_display_days=initial_display_days if gvh_type == 'chronic' else None
        )
        
        return fig
        
    except Exception as e:
        # Graphique d'erreur si l'analyse échoue
        fig = go.Figure()
        fig.add_annotation(
            text=f"<b>Erreur lors de l'analyse :</b><br>{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, 
            font=dict(size=14, family='Arial, sans-serif', color='#e74c3c'),
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#e74c3c",
            borderwidth=1
        )
        fig.update_layout(
            title=title,
            height=600,
            showlegend=False,
            paper_bgcolor='white',
            plot_bgcolor='rgba(248, 249, 250, 0.8)'
        )
        return fig
   
def create_unified_treatment_barplot(data, treatment_columns, title="", x_axis_title="", 
                                      y_axis_title="", height=400, width=None, show_values=True,
                                      remove_prefix=None):
    """
    Crée un graphique en barres empilées uniformisé montrant les proportions Oui/Non pour chaque traitement
    
    Args:
        data (pd.DataFrame): DataFrame contenant les données
        treatment_columns (list): Liste des colonnes de traitement à analyser
        title (str): Titre du graphique
        x_axis_title (str): Titre de l'axe X
        y_axis_title (str): Titre de l'axe Y
        height (int): Hauteur du graphique
        width (int): Largeur du graphique
        show_values (bool): Afficher les valeurs sur les barres
        remove_prefix (str): Préfixe à supprimer des noms de colonnes pour l'affichage
    
    Returns:
        plotly.graph_objects.Figure: Figure Plotly
    """

    # Calculer les proportions pour chaque traitement
    proportions_data = []
    
    for col in treatment_columns:
        if col not in data.columns:
            continue
            
        # Compter les Oui et Non
        counts = data[col].value_counts()
        total = len(data)
        
        oui_count = counts.get('Oui', 0) + counts.get('Yes', 0)  # Support pour 'Yes' et 'Oui'
        non_count = counts.get('Non', 0) + counts.get('No', 0)   # Support pour 'No' et 'Non'
        
        oui_percent = (oui_count / total) * 100 if total > 0 else 0
        non_percent = (non_count / total) * 100 if total > 0 else 0
        
        # Nettoyer le nom du traitement pour l'affichage
        treatment_name = col
        if remove_prefix and col.startswith(remove_prefix):
            treatment_name = col.replace(remove_prefix, '').strip()
        
        proportions_data.append({
            'Traitement': treatment_name,
            'Oui_percent': oui_percent,
            'Non_percent': non_percent,
            'Oui_count': oui_count,
            'Non_count': non_count
        })
    
    if not proportions_data:
        # Graphique vide si pas de données
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée de traitement disponible",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            title=title,
            height=height,
            width=width
        )
        return fig
    
    proportions_df = pd.DataFrame(proportions_data)
    
    # Trier par proportion de Oui (descendant)
    proportions_df = proportions_df.sort_values('Oui_percent', ascending=False)
    
    # Créer le graphique avec les couleurs standardisées
    fig = go.Figure()
    
    # Barre pour "Oui" - couleur bleu-vert cohérente
    fig.add_trace(go.Bar(
        name='Yes',
        x=proportions_df['Traitement'],
        y=proportions_df['Oui_percent'],
        marker_color='#2ecc71', 
        text=[f'{p:.1f}%<br>({c})' for p, c in zip(proportions_df['Oui_percent'], proportions_df['Oui_count'])],
        textposition='inside' if show_values else 'none',
        textfont=dict(color='white', size=10),
        hovertemplate='<b>%{x}</b><br>' +
                      'Patients with treatment: %{text}<br>' +
                      '<extra></extra>'
    ))
    
    # Barre pour "Non" - couleur rouge-rose cohérente
    fig.add_trace(go.Bar(
        name='No',
        x=proportions_df['Traitement'],
        y=proportions_df['Non_percent'],
        marker_color='#e74c3c', 
        text=[f'{p:.1f}%<br>({c})' for p, c in zip(proportions_df['Non_percent'], proportions_df['Non_count'])],
        textposition='inside' if show_values else 'none',
        textfont=dict(color='white', size=10),
        hovertemplate='<b>%{x}</b><br>' +
                      'Patients without treatment: %{text}<br>' +
                      '<extra></extra>'
    ))
    
    # Configuration du layout uniformisé
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=14)
        ),
        xaxis=dict(
            title=x_axis_title,
            tickfont=dict(size=10),
            tickangle=-45  # Rotation uniforme pour la lisibilité
        ),
        yaxis=dict(
            title=y_axis_title,
            range=[0, 100],
            tickfont=dict(size=10)
        ),
        barmode='stack',  # Barres empilées pour montrer le total de 100%
        legend=dict(
            x=1.02,
            y=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        ),
        height=height,
        width=width,
        margin=dict(l=50, r=100, t=60, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif')
    )
    
    # Ajout de la grille uniforme
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    
    return fig

def create_grouped_barplot_with_cumulative_by_category(
    data,
    x_column,
    group_column,
    title="Distribution by year with cumulative counts by category",
    x_axis_title=None,
    bar_y_axis_title="Number of patients",
    line_y_axis_title="Cumulative count by category",
    height=500,
    width=1500,
    custom_x_order=None,
    show_bars=True
):
    """
    Crée un barplot groupé (barres côte à côte) avec des courbes d'effectif cumulé PAR CATÉGORIE.
    Chaque catégorie a sa propre courbe cumulative.
    
    Args:
        data (pd.DataFrame): DataFrame contenant les données
        x_column (str): Colonne pour l'axe X (ex: Year)
        group_column (str): Colonne pour grouper les barres (ex: Donor Type)
        title (str): Titre du graphique
        x_axis_title (str): Titre de l'axe X
        bar_y_axis_title (str): Titre de l'axe Y pour les barres
        line_y_axis_title (str): Titre de l'axe Y pour les courbes cumulatives
        height (int): Hauteur du graphique
        width (int): Largeur du graphique
        custom_x_order (list): Ordre personnalisé pour l'axe X
        show_bars (bool): Afficher les barres (True) ou seulement les courbes (False)
        
    Returns:
        plotly.graph_objects.Figure: Figure Plotly du barplot groupé avec cumuls par catégorie
    """
    
    # Calculer les données groupées
    grouped_data = data.groupby([x_column, group_column]).size().unstack(fill_value=0)
    
    # Appliquer l'ordre personnalisé si fourni
    if custom_x_order is not None:
        grouped_data = grouped_data.reindex(custom_x_order, fill_value=0)
    
    # Réinitialiser l'index pour avoir x_column comme colonne
    grouped_data = grouped_data.reset_index()
    
    # Obtenir les catégories de groupe
    group_categories = [col for col in grouped_data.columns if col != x_column]
    
    # Créer la figure
    fig = go.Figure()
    
    # Palette de couleurs
    colors = px.colors.qualitative.Safe
    
    # Ajouter les barres groupées si demandé
    if show_bars:
        for i, category in enumerate(group_categories):
            fig.add_trace(go.Bar(
                name=str(category),
                legendgroup=f"group_{category}",
                x=grouped_data[x_column],
                y=grouped_data[category],
                marker_color=colors[i % len(colors)],
                text=grouped_data[category],
                textposition='inside',
                yaxis='y',
                opacity=1.0,
                showlegend=True
            ))
    
    # Calculer et ajouter les courbes cumulatives PAR CATÉGORIE
    for i, category in enumerate(group_categories):
        # Calculer le cumul pour cette catégorie spécifique
        cumulative_data = grouped_data[category].cumsum()
        
        # Couleur plus foncée pour la courbe cumulative
        line_color = colors[i % len(colors)]
        # Rendre la couleur plus foncée/saturée
        if line_color.startswith('rgb'):
            # Extraire les valeurs RGB et les assombrir
            rgb_values = line_color.replace('rgb(', '').replace(')', '').split(',')
            r, g, b = [max(0, int(float(val.strip()) * 0.7)) for val in rgb_values]
            line_color = f'rgb({r},{g},{b})'
        
        fig.add_trace(go.Scatter(
            name=f'{category} (cumulative)',
            legendgroup=f"group_{category}",
            x=grouped_data[x_column],
            y=cumulative_data,
            mode='lines+markers+text',
            line=dict(color=line_color, width=2, dash='dash'),
            marker=dict(size=6),
            text=cumulative_data,
            textposition='top center',
            textfont=dict(size=12),
            showlegend=False,  # Caché car groupé avec la barre
            hovertemplate=f'<b>{category} (cumulative)</b><br>' +
                         'Year: %{x}<br>' +
                         'Cumulative count: %{y}<br>' +
                         '<extra></extra>'
        ))
    
    # Définir les titres par défaut
    x_axis_title = x_axis_title or x_column
    
    # Configuration du layout
    layout_config = {
        'title': {
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        'xaxis_title': x_axis_title,
        'yaxis_title': bar_y_axis_title,
        'height': height,
        'width': width,
        'template': 'plotly_white',
        'barmode': 'group',  # Barres côte à côte
        'legend': dict(
            orientation='v',
            yanchor='top',
            y=1,
            xanchor='left',
            x=1.07,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        ),
        'yaxis': dict(
            title=bar_y_axis_title,
            side='left'
        ),
        'hovermode': 'x unified'
    }
    
    fig.update_layout(**layout_config)
    
    return fig

def create_cmv_status_pie_charts(data, title="Analyse du statut CMV", height=400, width=None):
    """
    Crée 3 pie charts pour analyser le statut CMV des donneurs et receveurs.
    
    Args:
        data (pd.DataFrame): DataFrame contenant les données
        title (str): Titre principal de la visualisation
        height (int): Hauteur des graphiques
        width (int): Largeur totale
        
    Returns:
        plotly.graph_objects.Figure: Figure avec 3 sous-graphiques (pie charts)
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd
    
    # Vérifier les colonnes nécessaires
    required_cols = ['CMV Status Donor', 'CMV Status Patient']
    missing_cols = [col for col in required_cols if col not in data.columns]
    
    if missing_cols:
        # Créer un graphique d'erreur informatif
        fig = go.Figure()
        fig.add_annotation(
            text=f"Colonnes manquantes pour l'analyse CMV :<br>{', '.join(missing_cols)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            title=title,
            height=height,
            width=width,
            showlegend=False
        )
        return fig
    
    # Nettoyer et standardiser les données
    df_clean = data.copy()
    
    # Mapper les valeurs pour les rendre plus lisibles
    donor_mapping = {
        'Transplant donor cytomegalovirus antibody positive': 'Positive',
        'Transplant donor cytomegalovirus antibody negative': 'Negative'
    }
    
    patient_mapping = {
        'Positive': 'Positive',
        'Negative': 'Negative'
    }
    
    # Appliquer les mappings
    df_clean['CMV_Donor_Clean'] = df_clean['CMV Status Donor'].map(donor_mapping)
    df_clean['CMV_Patient_Clean'] = df_clean['CMV Status Patient'].map(patient_mapping)
    
    # Supprimer les lignes avec des valeurs manquantes
    df_clean = df_clean.dropna(subset=['CMV_Donor_Clean', 'CMV_Patient_Clean'])
    
    if df_clean.empty:
        # Graphique vide si pas de données valides
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée CMV valide disponible",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            title=title,
            height=height,
            width=width,
            showlegend=False
        )
        return fig
    
    # Créer les sous-graphiques
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{"type": "pie"}, {"type": "pie"}, {"type": "pie"}]],
        subplot_titles=[
            'Donor CMV Status',
            'Recipient CMV Status', 
            'Donor/Recipient Combinations'
        ],
        horizontal_spacing=0.05
    )
    
    # Couleurs cohérentes
    colors_pos_neg = ['#e74c3c', '#2ecc71']  # Rouge pour négatif, vert pour positif
    colors_combinations = ['#27ae60', '#f39c12', '#e67e22', '#d61704']  # Vert, orange, orange foncé, rouge
    
    # 1. Pie chart Statut Donneur
    donor_counts = df_clean['CMV_Donor_Clean'].value_counts()
    if len(donor_counts) > 0:
        fig.add_trace(
            go.Pie(
                labels=donor_counts.index,
                values=donor_counts.values,
                name="Donor",
                marker_colors=colors_pos_neg,
                textinfo='label+percent+value',
                texttemplate='<b>%{label}</b><br>%{percent}<br>(%{value})',
                hovertemplate='<b>Donor CMV Status: %{label}</b><br>' +
                             'Number: %{value}<br>' +
                             'Percentage: %{percent}<br>' +
                             '<extra></extra>'
            ),
            row=1, col=1
        )
    
    # 2. Pie chart Statut Patient
    patient_counts = df_clean['CMV_Patient_Clean'].value_counts()
    if len(patient_counts) > 0:
        fig.add_trace(
            go.Pie(
                labels=patient_counts.index,
                values=patient_counts.values,
                name="Patient",
                marker_colors=colors_pos_neg,
                textinfo='label+percent+value',
                texttemplate='<b>%{label}</b><br>%{percent}<br>(%{value})',
                hovertemplate='<b>Recipient CMV Status: %{label}</b><br>' +
                             'Number: %{value}<br>' +
                             'Percentage: %{percent}<br>' +
                             '<extra></extra>'
            ),
            row=1, col=2
        )
    
    # 3. Pie chart Combinaisons
    # Créer les combinaisons Donneur/Receveur
    df_clean['CMV_Combination'] = df_clean['CMV_Donor_Clean'] + '/' + df_clean['CMV_Patient_Clean']
    combination_counts = df_clean['CMV_Combination'].value_counts()
    
    # Ordonner les combinaisons de manière logique
    preferred_order = ['Positive/Positive', 'Positive/Negative', 'Negative/Positive', 'Negative/Negative']
    ordered_combinations = []
    ordered_values = []
    ordered_colors = []
    
    for i, combo in enumerate(preferred_order):
        if combo in combination_counts:
            ordered_combinations.append(combo)
            ordered_values.append(combination_counts[combo])
            ordered_colors.append(colors_combinations[i])
    
    # Ajouter les combinaisons restantes si il y en a
    for combo in combination_counts.index:
        if combo not in ordered_combinations:
            ordered_combinations.append(combo)
            ordered_values.append(combination_counts[combo])
            ordered_colors.append('#95a5a6')  # Gris pour les combinaisons inattendues
    
    if len(ordered_combinations) > 0:
        fig.add_trace(
            go.Pie(
                labels=ordered_combinations,
                values=ordered_values,
                name="Combinaisons",
                marker_colors=ordered_colors,
                textinfo='label+percent+value',
                texttemplate='<b>%{label}</b><br>%{percent}<br>(%{value})',
                hovertemplate='<b>Combination: %{label}</b><br>' +
                             'Number: %{value}<br>' +
                             'Percentage: %{percent}<br>' +
                             '<extra></extra>'
            ),
            row=1, col=3
        )
    
    # Mise en forme globale
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'family': 'Arial, sans-serif'}
        },
        height=height,
        width=width,
        showlegend=False,  # Désactiver les légendes car les labels sont sur les secteurs
        font=dict(family="Arial, sans-serif", size=10),
        margin=dict(t=80, b=20, l=20, r=20),
    )
    
    # Mettre à jour les annotations des sous-titres
    fig.update_annotations(font_size=12, font_color="#2c3e50")
    
    return fig

def _is_patient_died_during_conditioning(row):
    """
    Détermine si un patient est décédé pendant la phase de conditionnement.
    
    Un patient est considéré comme décédé pendant le conditionnement si:
    - Son statut de suivi est 'Dead'
    - ET la date de décès/suivi est très proche de la date de traitement (greffe)
    
    Cette fonction utilise une heuristique: si le patient est décédé dans les 7 jours
    suivant la greffe, on considère qu'il est décédé pendant le conditionnement.
    
    Args:
        row (pd.Series): Ligne du DataFrame représentant un patient
        
    Returns:
        bool: True si le patient est décédé pendant le conditionnement
    """
    # Vérifier si le statut est 'Dead'
    status = row.get('Status Last Follow Up', '')
    if status != 'Dead':
        return False
    
    # Vérifier si nous avons les dates nécessaires
    treatment_date = row.get('Treatment Date', None)
    last_followup_date = row.get('Date Of Last Follow Up', None)
    
    if pd.isna(treatment_date) or pd.isna(last_followup_date):
        # Si on n'a pas les dates, on ne peut pas déterminer, donc on suppose que non
        return False
    
    try:
        # Convertir en datetime si ce sont des strings
        if isinstance(treatment_date, str):
            treatment_date = pd.to_datetime(treatment_date, format='mixed', errors='coerce')
        if isinstance(last_followup_date, str):
            last_followup_date = pd.to_datetime(last_followup_date, format='mixed', errors='coerce')
        
        if pd.isna(treatment_date) or pd.isna(last_followup_date):
            return False
        
        # Calculer la différence en jours
        days_diff = (last_followup_date - treatment_date).days
        
        # Si le patient est décédé dans les 7 jours suivant la greffe
        # (ou même jour, ce qui pourrait indiquer une donnée manquante de date)
        return days_diff <= 7
        
    except (ValueError, TypeError):
        # En cas d'erreur de conversion, on ne peut pas déterminer
        return False


def analyze_missing_data(df, columns_to_check, patient_id_col='Long ID'):
    """
    Analyse les données manquantes pour les colonnes spécifiées
    
    Cette fonction prend en compte les cas où les données ne sont pas véritablement
    manquantes mais plutôt non applicables, notamment lorsqu'un patient décède
    pendant la phase de conditionnement.
    
    Args:
        df (pd.DataFrame): Dataset des patients
        columns_to_check (list): Liste des colonnes à analyser
        patient_id_col (str): Nom de la colonne ID patient
        
    Returns:
        tuple: (missing_summary_df, detailed_missing_df)
    """
    # Vérifier que les colonnes existent
    existing_columns = [col for col in columns_to_check if col in df.columns]
    
    if not existing_columns:
        return pd.DataFrame(), pd.DataFrame()
    
    # Colonnes supplémentaires nécessaires pour les calculs conditionnels
    required_cols_for_analysis = existing_columns + [patient_id_col]
    
    # Ajouter les colonnes nécessaires pour les calculs conditionnels
    conditional_cols = [
        'Status Last Follow Up', 'Treatment Date', 'Date Of Last Follow Up',
        'Platelet Reconstitution', 'Anc Recovery',
        'First Agvhd Occurrence', 'First Cgvhd Occurrence',
        'First Relapse'
    ]
    
    for col in conditional_cols:
        if col in df.columns and col not in required_cols_for_analysis:
            required_cols_for_analysis.append(col)
    
    analysis_df = df[required_cols_for_analysis].copy()
    
    # Pré-calculer les patients décédés pendant le conditionnement
    analysis_df['died_during_conditioning'] = analysis_df.apply(
        _is_patient_died_during_conditioning, axis=1
    )
    
    # Définir les colonnes qui ne sont pas applicables si le patient est décédé
    # pendant le conditionnement (événements post-greffe)
    post_transplant_columns = {
        'First Agvhd Occurrence',
        'First aGvHD Maximum Score',
        'First Agvhd Occurrence Date',
        'First Cgvhd Occurrence',
        'First cGvHD Maximum NIH Score',
        'First Cgvhd Occurrence Date',
        'Anc Recovery',
        'Date Anc Recovery',
        'Platelet Reconstitution',
        'Date Platelet Reconstitution',
        'First Relapse',
        'First Relapse Date'
    }
    
    # Résumé par colonne
    missing_summary = []
    total_patients = len(analysis_df)
    
    for col in existing_columns:
        # Cas particuliers pour les colonnes post-greffe si le patient est décédé
        # pendant le conditionnement
        if col in post_transplant_columns:
            # Ne pas compter comme manquant si le patient est décédé pendant le conditionnement
            died_during_cond = analysis_df['died_during_conditioning']
            
            if col == 'First Agvhd Occurrence':
                # Manquant si: vide ET patient n'est PAS décédé pendant conditionnement
                # ET patient n'a PAS de date de suivi (si date de suivi existe = pas de GvH)
                missing_condition = (
                    (analysis_df[col].isna()) & 
                    (~died_during_cond) & 
                    (analysis_df['Date Of Last Follow Up'].isna())
                )
                missing_count = missing_condition.sum()
                
            elif col == 'First aGvHD Maximum Score':
                # Manquant si: vide ET First Agvhd Occurrence = 'Yes' 
                # ET patient n'est PAS décédé pendant conditionnement
                if 'First Agvhd Occurrence' in analysis_df.columns:
                    missing_condition = (
                        (analysis_df[col].isna()) & 
                        (analysis_df['First Agvhd Occurrence'] == 'Yes') &
                        (~died_during_cond)
                    )
                    missing_count = missing_condition.sum()
                else:
                    missing_condition = (analysis_df[col].isna()) & (~died_during_cond)
                    missing_count = missing_condition.sum()
                    
            elif col == 'First Agvhd Occurrence Date':
                # Manquant si: vide ET First Agvhd Occurrence = 'Yes'
                # ET patient n'est PAS décédé pendant conditionnement
                if 'First Agvhd Occurrence' in analysis_df.columns:
                    missing_condition = (
                        (analysis_df[col].isna()) & 
                        (analysis_df['First Agvhd Occurrence'] == 'Yes') &
                        (~died_during_cond)
                    )
                    missing_count = missing_condition.sum()
                else:
                    missing_condition = (analysis_df[col].isna()) & (~died_during_cond)
                    missing_count = missing_condition.sum()
                    
            elif col == 'First Cgvhd Occurrence':
                # Manquant si: vide ET patient n'est PAS décédé pendant conditionnement
                # ET patient n'a PAS de date de suivi (si date de suivi existe = pas de GvH)
                missing_condition = (
                    (analysis_df[col].isna()) & 
                    (~died_during_cond) & 
                    (analysis_df['Date Of Last Follow Up'].isna())
                )
                missing_count = missing_condition.sum()
                
            elif col == 'First cGvHD Maximum NIH Score':
                # Manquant si: vide ET First Cgvhd Occurrence = 'Yes'
                # ET patient n'est PAS décédé pendant conditionnement
                if 'First Cgvhd Occurrence' in analysis_df.columns:
                    missing_condition = (
                        (analysis_df[col].isna()) & 
                        (analysis_df['First Cgvhd Occurrence'] == 'Yes') &
                        (~died_during_cond)
                    )
                    missing_count = missing_condition.sum()
                else:
                    missing_condition = (analysis_df[col].isna()) & (~died_during_cond)
                    missing_count = missing_condition.sum()
                    
            elif col == 'First Cgvhd Occurrence Date':
                # Manquant si: vide ET First Cgvhd Occurrence = 'Yes'
                # ET patient n'est PAS décédé pendant conditionnement
                if 'First Cgvhd Occurrence' in analysis_df.columns:
                    missing_condition = (
                        (analysis_df[col].isna()) & 
                        (analysis_df['First Cgvhd Occurrence'] == 'Yes') &
                        (~died_during_cond)
                    )
                    missing_count = missing_condition.sum()
                else:
                    missing_condition = (analysis_df[col].isna()) & (~died_during_cond)
                    missing_count = missing_condition.sum()
                    
            elif col == 'Anc Recovery':
                # Manquant si: vide ET patient n'est PAS décédé pendant conditionnement
                missing_condition = (analysis_df[col].isna()) & (~died_during_cond)
                missing_count = missing_condition.sum()
                
            elif col == 'Date Anc Recovery':
                # Manquant si: vide ET Anc Recovery = 'Yes'
                # ET patient n'est PAS décédé pendant conditionnement
                if 'Anc Recovery' in analysis_df.columns:
                    missing_condition = (
                        (analysis_df[col].isna()) & 
                        (analysis_df['Anc Recovery'] == 'Yes') &
                        (~died_during_cond)
                    )
                    missing_count = missing_condition.sum()
                else:
                    missing_condition = (analysis_df[col].isna()) & (~died_during_cond)
                    missing_count = missing_condition.sum()
                    
            elif col == 'Platelet Reconstitution':
                # Manquant si: vide ET patient n'est PAS décédé pendant conditionnement
                missing_condition = (analysis_df[col].isna()) & (~died_during_cond)
                missing_count = missing_condition.sum()
                
            elif col == 'Date Platelet Reconstitution':
                # Manquant si: vide ET Platelet Reconstitution = 'Yes'
                # ET patient n'est PAS décédé pendant conditionnement
                if 'Platelet Reconstitution' in analysis_df.columns:
                    missing_condition = (
                        (analysis_df[col].isna()) & 
                        (analysis_df['Platelet Reconstitution'] == 'Yes') &
                        (~died_during_cond)
                    )
                    missing_count = missing_condition.sum()
                else:
                    missing_condition = (analysis_df[col].isna()) & (~died_during_cond)
                    missing_count = missing_condition.sum()
                    
            elif col == 'First Relapse':
                # Manquant si: vide ET patient n'est PAS décédé pendant conditionnement
                # ET patient n'a PAS de date de suivi (si date de suivi existe = pas de rechute)
                missing_condition = (
                    (analysis_df[col].isna()) & 
                    (~died_during_cond) & 
                    (analysis_df['Date Of Last Follow Up'].isna())
                )
                missing_count = missing_condition.sum()
                
            elif col == 'First Relapse Date':
                # Manquant si: vide ET First Relapse = 'Yes'
                # ET patient n'est PAS décédé pendant conditionnement
                if 'First Relapse' in analysis_df.columns:
                    missing_condition = (
                        (analysis_df[col].isna()) & 
                        (analysis_df['First Relapse'] == 'Yes') &
                        (~died_during_cond)
                    )
                    missing_count = missing_condition.sum()
                else:
                    missing_condition = (analysis_df[col].isna()) & (~died_during_cond)
                    missing_count = missing_condition.sum()
            else:
                # Autres colonnes post-greffe - logique par défaut
                missing_condition = (analysis_df[col].isna()) & (~died_during_cond)
                missing_count = missing_condition.sum()
        
        elif col == 'Date Platelet Reconstitution':
            # Compter comme manquant seulement si vide ET Platelet Reconstitution = 'Yes'
            if 'Platelet Reconstitution' in analysis_df.columns:
                missing_condition = (analysis_df[col].isna()) & (analysis_df['Platelet Reconstitution'] == 'Yes')
                missing_count = missing_condition.sum()
            else:
                missing_count = analysis_df[col].isna().sum()

        elif col == 'Date Anc Recovery':
            # Compter comme manquant seulement si vide ET Anc Recovery = 'Yes'
            if 'Anc Recovery' in analysis_df.columns:
                missing_condition = (analysis_df[col].isna()) & (analysis_df['Anc Recovery'] == 'Yes')
                missing_count = missing_condition.sum()
            else:
                missing_count = analysis_df[col].isna().sum()

        elif col == 'First Agvhd Occurrence Date':
            # Compter comme manquant seulement si vide ET First Agvhd Occurrence = 'Yes'
            if 'First Agvhd Occurrence' in analysis_df.columns:
                missing_condition = (analysis_df[col].isna()) & (analysis_df['First Agvhd Occurrence'] == 'Yes')
                missing_count = missing_condition.sum()
            else:
                missing_count = analysis_df[col].isna().sum()

        elif col == 'First aGvHD Maximum Score':
            # Compter comme manquant seulement si vide ET First AGvHD Occurence = 'Yes'
            if 'First Agvhd Occurrence' in analysis_df.columns:
                missing_condition = (analysis_df[col].isna()) & (analysis_df['First Agvhd Occurrence'] == 'Yes')
                missing_count = missing_condition.sum()
            else:
                missing_count = analysis_df[col].isna().sum()

        elif col == 'First Cgvhd Occurrence Date':
            # Compter comme manquant seulement si vide ET First CGvHD Occurrence = 'Yes'
            if 'First Cgvhd Occurrence' in analysis_df.columns:
                missing_condition = (analysis_df[col].isna()) & (analysis_df['First Cgvhd Occurrence'] == 'Yes')
                missing_count = missing_condition.sum()
            else:
                missing_count = analysis_df[col].isna().sum()

        elif col == 'First cGvHD Maximum NIH Score':
            # Compter comme manquant seulement si vide ET First CGvHD Occurence = 'Yes'
            if 'First Cgvhd Occurrence' in analysis_df.columns:
                missing_condition = (analysis_df[col].isna()) & (analysis_df['First Cgvhd Occurrence'] == 'Yes')
                missing_count = missing_condition.sum()
            else:
                missing_count = analysis_df[col].isna().sum()

        elif col == 'First Relapse Date':
            # Compter comme manquant seulement si vide ET First Relapse = 'Yes'
            if 'First Relapse' in analysis_df.columns:
                missing_condition = (analysis_df[col].isna()) & (analysis_df['First Relapse'] == 'Yes')
                missing_count = missing_condition.sum()
            else:
                missing_count = analysis_df[col].isna().sum()

        elif col == 'Death Cause':
            # Compter comme manquant seulement si vide ET LFU = 'Dead'
            if 'Status Last Follow Up' in analysis_df.columns:
                missing_condition = (analysis_df[col].isna()) & (analysis_df['Status Last Follow Up'] == 'Dead')
                missing_count = missing_condition.sum()
            else:
                missing_count = analysis_df[col].isna().sum()

        elif col == 'Death Date':
            # Compter comme manquant seulement si vide ET LFU = 'Dead'
            if 'Status Last Follow Up' in analysis_df.columns:
                missing_condition = (analysis_df[col].isna()) & (analysis_df['Status Last Follow Up'] == 'Dead')
                missing_count = missing_condition.sum()
            else:
                missing_count = analysis_df[col].isna().sum()

        else:
            # Logique standard pour les autres colonnes
            missing_count = analysis_df[col].isna().sum()
        
        missing_percentage = (missing_count / total_patients) * 100
        
        missing_summary.append({
            'Column': col,
            'Total patients': total_patients,
            'Missing data': missing_count,
            'Percentage missing': round(missing_percentage, 2)
        })
    
    # Détail des patients avec données manquantes
    detailed_missing = []
    
    for _, row in analysis_df.iterrows():
        patient_id = row[patient_id_col]
        missing_columns = []
        died_during_cond = row['died_during_conditioning']
        
        for col in existing_columns:
            is_missing = False
            
            if col == 'Date Platelet Reconstitution':
                # Manquant si vide ET Platelet Reconstitution = 'Yes'
                # ET patient n'est PAS décédé pendant conditionnement
                is_missing = (
                    pd.isna(row[col]) and 
                    row.get('Platelet Reconstitution', 'No') == 'Yes' and
                    not died_during_cond
                )
                
            elif col == 'Date Anc Recovery':
                # Manquant si vide ET Anc Recovery = 'Yes'
                # ET patient n'est PAS décédé pendant conditionnement
                is_missing = (
                    pd.isna(row[col]) and 
                    row.get('Anc Recovery', 'No') == 'Yes' and
                    not died_during_cond
                )
                
            elif col == 'Death Cause':
                # Manquant si vide ET Status Last Follow Up = 'Dead'
                is_missing = (
                    pd.isna(row[col]) and 
                    row.get('Status Last Follow Up', '') == 'Dead'
                )
                
            elif col == 'Death Date':
                # Manquant si vide ET Status Last Follow Up = 'Dead'
                is_missing = (
                    pd.isna(row[col]) and 
                    row.get('Status Last Follow Up', '') == 'Dead'
                )
                
            elif col in post_transplant_columns:
                # Pour les autres colonnes post-greffe
                # Manquant si vide ET patient n'est PAS décédé pendant conditionnement
                # (avec logiques additionnelles spécifiques)
                
                if col == 'First Agvhd Occurrence':
                    # Manquant seulement si: vide ET pas décédé pendant conditionnement 
                    # ET pas de date de suivi (si date de suivi = pas de GvH)
                    has_followup = pd.notna(row.get('Date Of Last Follow Up'))
                    is_missing = pd.isna(row[col]) and not died_during_cond and not has_followup
                    
                elif col == 'First aGvHD Maximum Score':
                    is_missing = (
                        pd.isna(row[col]) and 
                        row.get('First Agvhd Occurrence', '') == 'Yes' and
                        not died_during_cond
                    )
                    
                elif col == 'First Agvhd Occurrence Date':
                    is_missing = (
                        pd.isna(row[col]) and 
                        row.get('First Agvhd Occurrence', '') == 'Yes' and
                        not died_during_cond
                    )
                    
                elif col == 'First Cgvhd Occurrence':
                    # Manquant seulement si: vide ET pas décédé pendant conditionnement 
                    # ET pas de date de suivi (si date de suivi = pas de GvH)
                    has_followup = pd.notna(row.get('Date Of Last Follow Up'))
                    is_missing = pd.isna(row[col]) and not died_during_cond and not has_followup
                    
                elif col == 'First cGvHD Maximum NIH Score':
                    is_missing = (
                        pd.isna(row[col]) and 
                        row.get('First Cgvhd Occurrence', '') == 'Yes' and
                        not died_during_cond
                    )
                    
                elif col == 'First Cgvhd Occurrence Date':
                    is_missing = (
                        pd.isna(row[col]) and 
                        row.get('First Cgvhd Occurrence', '') == 'Yes' and
                        not died_during_cond
                    )
                    
                elif col == 'Anc Recovery':
                    is_missing = pd.isna(row[col]) and not died_during_cond
                    
                elif col == 'Platelet Reconstitution':
                    is_missing = pd.isna(row[col]) and not died_during_cond
                    
                elif col == 'First Relapse':
                    # Manquant seulement si: vide ET pas décédé pendant conditionnement 
                    # ET pas de date de suivi (si date de suivi = pas de rechute)
                    has_followup = pd.notna(row.get('Date Of Last Follow Up'))
                    is_missing = pd.isna(row[col]) and not died_during_cond and not has_followup
                    
                elif col == 'First Relapse Date':
                    is_missing = (
                        pd.isna(row[col]) and 
                        row.get('First Relapse', '') == 'Yes' and
                        not died_during_cond
                    )
                else:
                    is_missing = pd.isna(row[col]) and not died_during_cond
            else:
                # Logique standard pour les autres colonnes
                is_missing = pd.isna(row[col])
            
            if is_missing:
                missing_columns.append(col)
        
        if missing_columns:
            detailed_missing.append({
                patient_id_col: patient_id,
                'Missing columns': ', '.join(missing_columns),
                'Nb missing': len(missing_columns)
            })
    
    return pd.DataFrame(missing_summary), pd.DataFrame(detailed_missing)

def create_missing_data_visualization(df, columns_to_check, patient_id_col='Long ID'):
    """
    Crée une visualisation complète des données manquantes
    
    Args:
        df (pd.DataFrame): Dataset des patients
        columns_to_check (list): Liste des colonnes à analyser
        patient_id_col (str): Nom de la colonne ID patient
    
    Returns:
        html.Div: Composant Dash avec visualisation complète
    """
    try:
        # Analyser les données manquantes
        missing_summary, detailed_missing = analyze_missing_data(df, columns_to_check, patient_id_col)
        
        # Créer le graphique en barres des données manquantes
        fig_bar = px.bar(
            missing_summary,
            x='Column',
            y='Missing percentage',
            title='Missing data percentage by column',
            labels={'Missing percentage': 'Missing percentage (%)'},
            color='Missing percentage',
            color_continuous_scale='Reds'
        )
        
        fig_bar.update_layout(
            title={'x': 0.5, 'xanchor': 'center'},
            xaxis_tickangle=-45,
            height=400
        )
        
        # Créer la heatmap des données manquantes
        analysis_df = df[[patient_id_col] + columns_to_check].copy()
        missing_matrix = analysis_df[columns_to_check].isna().astype(int)
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=missing_matrix.T.values,
            y=columns_to_check,
            x=analysis_df.index,
            colorscale=[[0, 'lightblue'], [1, 'red']],
            showscale=True,
            colorbar=dict(
                title="Missing data",
                tickvals=[0, 1],
                ticktext=["Present", "Missing"]
            )
        ))
        
        fig_heatmap.update_layout(
            title='Missing data map by patient',
            title_x=0.5,
            xaxis_title='Patient index',
            yaxis_title='Analyzed columns',
            height=300
        )
        
        # Composant final
        return dbc.Container([
            # En-tête avec résumé
            dbc.Row([
                dbc.Col([
                    dbc.Alert([
                        html.H4("📊 Missing data analysis", className='mb-2'),
                        html.P(f"Analysis of {len(columns_to_check)} column(s) across {len(df)} patients", 
                               className='mb-0')
                    ], color='info', className='mb-3')
                ])
            ]),
            
            # Graphiques
            dbc.Row([
                # Graphique en barres
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6('Overview of missing data')),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_bar)
                        ])
                    ])
                ], width=6),
                
                # Carte thermique
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6('Distribution of missing data')),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_heatmap)
                        ])
                    ])
                ], width=6)
            ], className='mb-4'),
            
            # Tableaux
            dbc.Row([
                # Résumé par colonne
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6('Summary by column')),
                        dbc.CardBody([
                            create_summary_table(missing_summary)
                        ])
                    ])
                ], width=6),
                
                # Détail des patients avec données manquantes
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H6(f'Patients with missing data ({len(detailed_missing)} patients)')
                        ]),
                        dbc.CardBody([
                            create_detailed_table(detailed_missing) if not detailed_missing.empty else 
                            dbc.Alert("No missing data found! 🎉", color='success')
                        ])
                    ])
                ], width=6)
            ])
        ], fluid=True)
        
    except Exception as e:
        return dbc.Alert(f"Erreur lors de l'analyse: {str(e)}", color='danger')

def create_summary_table(missing_summary):
    """Crée le tableau de résumé des données manquantes"""
    return dash_table.DataTable(
        data=missing_summary.to_dict('records'),
        columns=[
            {"name": "Column", "id": "Colonne"},
            {"name": "Total patients", "id": "Total patients", "type": "numeric"},
            {"name": "Missing data", "id": "Données manquantes", "type": "numeric"},
            {"name": "% missing", "id": "Pourcentage manquant", "type": "numeric", 
             "format": {"specifier": ".1f"}}
        ],
        style_table={'height': '300px', 'overflowY': 'auto'},
        style_cell={
            'textAlign': 'center',
            'padding': '10px',
            'fontSize': '12px',
            'fontFamily': 'Arial, sans-serif'
        },
        style_header={
            'backgroundColor': '#0D3182',
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {
                    'filter_query': '{Pourcentage manquant} > 20',
                    'column_id': 'Pourcentage manquant'
                },
                'backgroundColor': '#ffebee',
                'color': 'red',
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'filter_query': '{Pourcentage manquant} > 50',
                    'column_id': 'Pourcentage manquant'
                },
                'backgroundColor': '#ffcdd2',
                'color': 'darkred',
                'fontWeight': 'bold'
            }
        ]
    )

def create_detailed_table(detailed_missing):
    """Crée le tableau détaillé des patients avec données manquantes"""
    return dash_table.DataTable(
        data=detailed_missing.to_dict('records'),
        columns=[
            {"name": "Long ID", "id": "Long ID"},
            {"name": "Missing columns", "id": "Missing columns"},
            {"name": "Nb missing", "id": "Nb missing", "type": "numeric"}
        ],
        style_table={'height': '300px', 'overflowY': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '8px',
            'fontSize': '11px',
            'fontFamily': 'Arial, sans-serif',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_header={
            'backgroundColor': '#0D3182',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {
                    'filter_query': '{Nb missing} > 1',
                    'column_id': 'Nb missing'
                },
                'backgroundColor': '#fff3cd',
                'color': 'orange',
                'fontWeight': 'bold'
            }
        ],
        filter_action='native',
        sort_action='native',
        export_format='xlsx',
        export_headers='display'
    )

# Fonction d'usage simple pour intégration rapide
def quick_missing_analysis(df, columns_to_check):
    """
    Fonction simplifiée pour analyse rapide des données manquantes
    
    Args:
        df (pd.DataFrame): Dataset
        columns_to_check (list ou str): Colonne(s) à analyser
    
    Returns:
        dict: Résumé des données manquantes
    """
    if isinstance(columns_to_check, str):
        columns_to_check = [columns_to_check]
    
    results = {}
    for col in columns_to_check:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            total_count = len(df)
            missing_percentage = (missing_count / total_count) * 100
            
            # Récupérer les Long ID des patients avec données manquantes
            missing_patients = df[df[col].isna()]['Long ID'].tolist() if 'Long ID' in df.columns else []
            
            results[col] = {
                'missing_count': missing_count,
                'total_count': total_count,
                'missing_percentage': round(missing_percentage, 2),
                'missing_patients': missing_patients
            }
    
    return results
def create_upset_plot(data, set_columns, title="UpSet Plot - Treatment Combinations",
                      min_subset_size=None, max_subsets=15, sort_by='degree',
                      height=600, width=None, color_main='#0D3182', color_highlight='#d61704'):
    """
    Crée un UpSet plot (intersection plot) pour visualiser les combinaisons de traitements.
    
    L'UpSet plot est une alternative aux diagrammes de Venn pour visualiser les intersections
    entre plusieurs ensembles. Il est particulièrement utile pour les données de prophylaxie
    où les patients peuvent recevoir plusieurs traitements simultanément.
    
    Structure du plot:
    - En haut: barres horizontales montrant la taille de chaque intersection
    - En bas: matrice de points montrant quels traitements sont inclus dans chaque intersection
    - À gauche: barres verticales montrant la fréquence totale de chaque traitement
    
    Args:
        data (pd.DataFrame): DataFrame contenant les données
        set_columns (list): Liste des colonnes représentant les ensembles (ex: noms des traitements)
        title (str): Titre du graphique
        min_subset_size (int): Taille minimale d'une intersection pour être affichée
        max_subsets (int): Nombre maximum d'intersections à afficher
        sort_by (str): 'degree' (nombre de traitements) ou 'cardinality' (taille de l'intersection)
        height (int): Hauteur du graphique
        width (int): Largeur du graphique
        color_main (str): Couleur principale pour les barres
        color_highlight (str): Couleur pour les intersections à un seul traitement
        
    Returns:
        plotly.graph_objects.Figure: Figure Plotly de type UpSet
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd
    import numpy as np
    
    # Vérifier que les colonnes existent
    available_cols = [col for col in set_columns if col in data.columns]
    if not available_cols:
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune colonne d'ensemble disponible",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(title=title, height=height, width=width)
        return fig
    
    # Convertir les données en format binaire (0/1)
    binary_data = data[available_cols].copy()
    for col in available_cols:
        # Convertir Oui/Yes en 1, tout le reste en 0
        binary_data[col] = binary_data[col].apply(
            lambda x: 1 if str(x).lower() in ['oui', 'yes', '1', 'true'] else 0
        )
    
    # Calculer les fréquences totales par traitement (pour le graphique latéral)
    set_totals = binary_data.sum().sort_values(ascending=True)
    
    # Générer toutes les combinaisons possibles et calculer leurs effectifs
    # Créer une clé unique pour chaque combinaison de traitements
    binary_data['_combination'] = binary_data.apply(
        lambda row: ','.join([col for col in available_cols if row[col] == 1]),
        axis=1
    )
    
    # Compter les effectifs par combinaison
    combination_counts = binary_data['_combination'].value_counts()
    
    # Exclure la combinaison vide (patients sans aucun traitement)
    combination_counts = combination_counts[combination_counts.index != '']
    
    if len(combination_counts) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune combinaison de traitements trouvée",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(title=title, height=height, width=width)
        return fig
    
    # Filtrer par taille minimale si spécifiée
    if min_subset_size is not None:
        combination_counts = combination_counts[combination_counts >= min_subset_size]
    
    # Calculer le 'degree' (nombre de traitements dans chaque combinaison)
    combination_degrees = combination_counts.index.map(
        lambda x: len(x.split(',')) if x else 0
    )
    
    # Créer un DataFrame pour faciliter le tri
    subset_df = pd.DataFrame({
        'combination': combination_counts.index,
        'count': combination_counts.values,
        'degree': combination_degrees
    })
    
    # Trier selon le critère choisi
    if sort_by == 'degree':
        # Trier d'abord par degree décroissant, puis par count décroissant
        subset_df = subset_df.sort_values(['degree', 'count'], ascending=[False, False])
    else:  # cardinality
        subset_df = subset_df.sort_values('count', ascending=False)
    
    # Limiter au nombre maximum de sous-ensembles
    subset_df = subset_df.head(max_subsets)
    
    # Calculer les dimensions pour les sous-graphiques
    n_sets = len(available_cols)
    n_subsets = len(subset_df)
    
    # Largeur par défaut si non spécifiée
    if width is None:
        width = max(800, 200 + n_subsets * 40)
    
    # Créer les sous-graphiques avec make_subplots
    # Disposition: [barres latérales, barres du haut, matrice des points]
    fig = make_subplots(
        rows=2, cols=2,
        column_widths=[0.25, 0.75],
        row_heights=[0.6, 0.4],
        vertical_spacing=0.05,
        horizontal_spacing=0.02,
        subplot_titles=(None, None, None, None),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "scatter"}]
        ]
    )
    
    # --- 1. Graphique latéral: fréquence de chaque traitement ---
    fig.add_trace(
        go.Bar(
            x=set_totals.values,
            y=set_totals.index,
            orientation='h',
            marker_color=color_main,
            name='Total patients',
            text=set_totals.values,
            textposition='outside',
            textfont=dict(size=9),
            hovertemplate='<b>%{y}</b><br>Patients: %{x}<extra></extra>',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # --- 2. Graphique du haut: taille des intersections ---
    # Couleurs différentes selon le degree
    bar_colors = []
    for degree in subset_df['degree']:
        if degree == 1:
            bar_colors.append(color_highlight)  # Intersections simples en rouge
        else:
            # Dégradé de bleu selon le degree
            intensity = 0.4 + (min(degree, 5) / 5) * 0.6
            bar_colors.append(f'rgba(13, 49, 130, {intensity})')
    
    fig.add_trace(
        go.Bar(
            x=list(range(len(subset_df))),
            y=subset_df['count'],
            marker_color=bar_colors,
            name='Intersection size',
            text=subset_df['count'],
            textposition='outside',
            textfont=dict(size=10),
            hovertemplate='<b>Intersection #%{%{x} + 1}</b><br>Patients: %{y}<br>Treatments: %{customdata}<extra></extra>',
            customdata=subset_df['combination'],
            showlegend=False
        ),
        row=1, col=2
    )
    
    # --- 3. Matrice des points: quels traitements sont dans chaque intersection ---
    set_list = list(set_totals.index)  # Ordre trié
    
    # Tracer les lignes de grille horizontales (un traitement = une ligne)
    for i, set_name in enumerate(set_list):
        fig.add_trace(
            go.Scatter(
                x=[-0.5, n_subsets - 0.5],
                y=[i, i],
                mode='lines',
                line=dict(color='lightgray', width=1),
                showlegend=False,
                hoverinfo='skip'
            ),
            row=2, col=2
        )
    
    # Tracer les points et les lignes de connexion
    for subset_idx, row in subset_df.iterrows():
        subset_idx_pos = subset_df.index.get_loc(subset_idx)
        combination = row['combination']
        sets_in_combination = combination.split(',') if combination else []
        
        # Indices des traitements dans cette combinaison
        set_indices = [set_list.index(s) for s in sets_in_combination if s in set_list]
        
        if len(set_indices) == 1:
            # Un seul traitement: juste un point
            fig.add_trace(
                go.Scatter(
                    x=[subset_idx_pos],
                    y=[set_indices[0]],
                    mode='markers',
                    marker=dict(size=12, color=color_highlight, symbol='circle'),
                    showlegend=False,
                    hovertemplate=f'<b>{sets_in_combination[0]}</b><br>Patients: {row["count"]}<extra></extra>'
                ),
                row=2, col=2
            )
        elif len(set_indices) > 1:
            # Plusieurs traitements: points reliés par des lignes
            # Ligne de connexion
            fig.add_trace(
                go.Scatter(
                    x=[subset_idx_pos] * len(set_indices),
                    y=set_indices,
                    mode='lines',
                    line=dict(color=color_main, width=3),
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=2, col=2
            )
            # Points
            for set_idx, set_name in zip(set_indices, sets_in_combination):
                fig.add_trace(
                    go.Scatter(
                        x=[subset_idx_pos],
                        y=[set_idx],
                        mode='markers',
                        marker=dict(size=12, color=color_main, symbol='circle'),
                        showlegend=False,
                        hovertemplate=f'<b>{combination}</b><br>Patients: {row["count"]}<extra></extra>'
                    ),
                    row=2, col=2
                )
    
    # Configuration des axes
    # Axe X du graphique du haut (numéros d'intersection)
    fig.update_xaxes(
        tickvals=list(range(len(subset_df))),
        ticktext=[f'#{i+1}' for i in range(len(subset_df))],
        tickangle=0,
        title_text='',
        row=1, col=2
    )
    
    # Axe Y du graphique latéral (noms des traitements)
    fig.update_yaxes(
        title_text='',
        row=1, col=1
    )
    
    # Axe Y du graphique du haut (effectifs)
    fig.update_yaxes(
        title_text='Patients in intersection',
        row=1, col=2
    )
    
    # Axe Y de la matrice (noms des traitements alignés)
    fig.update_yaxes(
        tickvals=list(range(len(set_list))),
        ticktext=set_list,
        tickmode='array',
        title_text='',
        row=2, col=2
    )
    
    # Axe X de la matrice (aligné avec le graphique du haut)
    fig.update_xaxes(
        tickvals=list(range(len(subset_df))),
        ticktext=[f'#{i+1}' for i in range(len(subset_df))],
        title_text='Intersection number',
        row=2, col=2
    )
    
    # Masquer les axes du sous-graphique vide (bas gauche)
    fig.update_xaxes(visible=False, row=2, col=1)
    fig.update_yaxes(visible=False, row=2, col=1)
    
    # Ajouter une annotation pour le titre du graphique latéral
    fig.add_annotation(
        x=0.5, y=1.05,
        xref='x domain', yref='y domain',
        xanchor='center', yanchor='bottom',
        text='<b>Treatment frequency</b>',
        showarrow=False,
        font=dict(size=11),
        row=1, col=1
    )
    
    # Layout général
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=16, family='Arial, sans-serif')
        ),
        height=height,
        width=width,
        template='plotly_white',
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        margin=dict(l=150, r=50, t=80, b=80)
    )
    
    return fig


def create_upset_plot_simple(data, set_columns, title="UpSet Plot - Treatment Combinations",
                              max_combinations=20, min_patients=1, height=600, width=None):
    """
    Version simplifiée de l'UpSet plot pour les traitements prophylactiques.
    
    Cette version est optimisée pour la visualisation des combinaisons de traitements
    dans AlloGraph, avec une mise en page plus compacte et des tooltips informatifs.
    
    Args:
        data (pd.DataFrame): DataFrame avec les données
        set_columns (list): Liste des colonnes de traitements
        title (str): Titre du graphique
        max_combinations (int): Nombre maximum de combinaisons à afficher
        min_patients (int): Nombre minimum de patients pour afficher une combinaison
        height (int): Hauteur du graphique
        width (int): Largeur du graphique
        
    Returns:
        plotly.graph_objects.Figure: Figure UpSet plot
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd
    
    # Vérifier les colonnes disponibles
    available_cols = [col for col in set_columns if col in data.columns]
    if not available_cols:
        fig = go.Figure()
        fig.add_annotation(
            text="No treatment data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=14
        )
        fig.update_layout(title=title, height=height, width=width or 600)
        return fig
    
    # Convertir en binaire
    binary_data = data[available_cols].copy()
    for col in available_cols:
        binary_data[col] = binary_data[col].apply(
            lambda x: 1 if str(x).lower() in ['oui', 'yes', '1', 'true'] else 0
        )
    
    # Calculer les totaux par traitement
    set_totals = binary_data.sum().sort_values(ascending=True)
    
    # Créer les combinaisons
    binary_data['_combo'] = binary_data.apply(
        lambda row: ','.join([col for col in available_cols if row[col] == 1]),
        axis=1
    )
    
    # Compter et filtrer
    combo_counts = binary_data['_combo'].value_counts()
    combo_counts = combo_counts[combo_counts.index != '']  # Exclure vide
    combo_counts = combo_counts[combo_counts >= min_patients]  # Filtrer minimum
    combo_counts = combo_counts.head(max_combinations)  # Limiter nombre
    
    if len(combo_counts) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No treatment combinations found",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=14
        )
        fig.update_layout(title=title, height=height, width=width or 600)
        return fig
    
    n_sets = len(available_cols)
    n_combos = len(combo_counts)
    
    # Calculer la largeur automatique basée sur le nombre de combinaisons
    if width is None:
        width = max(900, 200 + n_combos * 40)
    
    # Créer la figure avec sous-graphiques - domaines explicites pour alignement
    fig = make_subplots(
        rows=2, cols=2,
        column_widths=[0.20, 0.80],
        row_heights=[0.50, 0.50],
        vertical_spacing=0.02,
        horizontal_spacing=0.01,
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "scatter"}]]
    )
    
    # 1. Barres latérales: fréquence totale
    fig.add_trace(
        go.Bar(
            x=set_totals.values,
            y=set_totals.index,
            orientation='h',
            marker_color='#0D3182',
            text=set_totals.values,
            textposition='outside',
            textfont=dict(size=9),
            hovertemplate='<b>%{y}</b><br>Total: %{x} patients<extra></extra>',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # 2. Barres du haut: taille des intersections
    colors_top = ['#d61704' if len(c.split(',')) == 1 else '#0D3182' 
                  for c in combo_counts.index]
    
    fig.add_trace(
        go.Bar(
            x=list(range(n_combos)),
            y=combo_counts.values,
            marker_color=colors_top,
            text=combo_counts.values,
            textposition='outside',
            textfont=dict(size=10),
            hovertemplate='<b>%{customdata}</b><br>Patients: %{y}<extra></extra>',
            customdata=[c.replace(',', '<br>+ ') for c in combo_counts.index],
            showlegend=False
        ),
        row=1, col=2
    )
    
    # 3. Matrice des points
    set_list = list(set_totals.index)
    
    # Lignes de grille horizontales
    for i in range(n_sets):
        fig.add_trace(
            go.Scatter(
                x=[-0.5, n_combos - 0.5],
                y=[i, i],
                mode='lines',
                line=dict(color='#e0e0e0', width=1.5),
                showlegend=False,
                hoverinfo='skip'
            ),
            row=2, col=2
        )
    
    # Points et connexions
    for i, (combo, count) in enumerate(combo_counts.items()):
        sets_in = combo.split(',') if combo else []
        indices = [set_list.index(s) for s in sets_in if s in set_list]
        
        if len(indices) == 1:
            fig.add_trace(
                go.Scatter(
                    x=[i],
                    y=[indices[0]],
                    mode='markers',
                    marker=dict(size=16, color='#d61704', 
                               line=dict(color='white', width=2)),
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=2, col=2
            )
        elif len(indices) > 1:
            # Ligne de connexion verticale
            fig.add_trace(
                go.Scatter(
                    x=[i] * len(indices),
                    y=indices,
                    mode='lines',
                    line=dict(color='#2E86AB', width=5),
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=2, col=2
            )
            # Points
            for idx in indices:
                fig.add_trace(
                    go.Scatter(
                        x=[i],
                        y=[idx],
                        mode='markers',
                        marker=dict(size=14, color='#0D3182',
                                   line=dict(color='white', width=2)),
                        showlegend=False,
                        hoverinfo='skip'
                    ),
                    row=2, col=2
                )
    
    # Configuration des axes - CLÉ POUR L'ALIGNEMENT
    # Masquer axe X du graphique latéral
    fig.update_xaxes(visible=False, row=1, col=1)
    fig.update_yaxes(title_text='', row=1, col=1)
    
    # Axe X du graphique du haut - sans titre, ticks seulement
    fig.update_xaxes(
        tickvals=list(range(n_combos)),
        ticktext=[f'{i+1}' for i in range(n_combos)],
        tickangle=0,
        title_text='',
        range=[-0.5, n_combos - 0.5],
        constrain='domain',
        row=1, col=2
    )
    fig.update_yaxes(
        title_text='Patients',
        row=1, col=2
    )
    
    # Axe X de la matrice - ALIGNÉ avec le graphique du haut
    fig.update_xaxes(
        tickvals=list(range(n_combos)),
        ticktext=[f'{i+1}' for i in range(n_combos)],
        title_text='Combination',
        range=[-0.5, n_combos - 0.5],
        constrain='domain',
        row=2, col=2
    )
    fig.update_yaxes(
        tickvals=list(range(n_sets)),
        ticktext=set_list,
        tickmode='array',
        title_text='',
        row=2, col=2
    )
    
    # Masher le sous-graphique vide
    fig.update_xaxes(visible=False, row=2, col=1)
    fig.update_yaxes(visible=False, row=2, col=1)
    
    # Layout optimisé pour remplir le conteneur
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=15, family='Arial, sans-serif')
        ),
        height=height,
        width=width,
        template='plotly_white',
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        # Marges réduites pour maximiser l'espace du plot
        margin=dict(l=150, r=30, t=60, b=40),
        # S'assurer que le plot utilise tout l'espace disponible
        autosize=True
    )
    
    return fig
