import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
import plotly.colors
from scipy.stats import gaussian_kde
from typing import Optional, List, Tuple

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
    colors = px.colors.qualitative.Plotly
    
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
            color_palette = px.colors.qualitative.Plotly
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
    color_map=None
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
        
    Returns:
        plotly.graph_objects.Figure: Figure Plotly du boxplot amélioré
    """
    # Définir les titres par défaut
    x_axis_title = x_axis_title or x_column
    y_axis_title = y_axis_title or y_column
    
    # Cas sans coloration
    if color_column is None or color_column not in data.columns:
        if show_points:
            fig = px.box(
                data,
                x=x_column,
                y=y_column,
                title=title,
                height=height,
                width=width,
                points="all"  # Afficher tous les points
            )
        else:
            fig = px.box(
                data,
                x=x_column,
                y=y_column,
                title=title,
                height=height,
                width=width
            )
    else:
        # Cas avec coloration
        # Utiliser le color_map fourni ou en créer un
        if color_map is None:
            color_map = create_consistent_color_map(data, color_column)
        
        if show_points:
            fig = px.box(
                data,
                x=x_column,
                y=y_column,
                color=color_column,
                color_discrete_map=color_map,
                title=title,
                height=height,
                width=width,
                points="all"  # Afficher tous les points
            )
        else:
            fig = px.box(
                data,
                x=x_column,
                y=y_column,
                color=color_column,
                color_discrete_map=color_map,
                title=title,
                height=height,
                width=width
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
        y_max = data[y_column].max()
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
        showlegend=color_column is not None
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
    title="Distribution et cumul des effectifs",
    x_axis_title=None,
    bar_y_axis_title="Nombre de patients",
    line_y_axis_title="Effectif cumulé",
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
        name='Nombre de patients',
        marker_color=bar_color,
        text=bar_text_values,
        textposition='inside',
        textfont=dict(color=text_color)
    ))

    # Ajout de la courbe cumulative
    fig.add_trace(go.Scatter(
        x=count_data[category_column],
        y=count_data['Cumulative'],
        name='Effectif cumulé',
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
    title="Distribution par année avec effectifs cumulés",
    x_axis_title=None,
    bar_y_axis_title="Nombre de patients",
    line_y_axis_title="Effectif cumulé",
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
    colors = px.colors.qualitative.Plotly
    
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
            name='Effectif cumulé',
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
    y_axis_title = y_axis_title or "Nombre de patients"
    
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
            marker_color=color_map.get(category, px.colors.qualitative.Plotly[0]),
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
    y_axis_title = y_axis_title or "Pourcentage (%)"
    
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
            marker_color=color_map.get(category, px.colors.qualitative.Plotly[0]),
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
    title: str = "Distribution avec densité",
    x_axis_title: str = "Valeurs",
    y_axis_title: str = "Fréquence",
    bin_size: Optional[float] = None,
    percentile_limit: float = 0.99,
    color_histogram: str = '#27BDBE',
    color_density: str = '#FF6B6B',
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
        
    Examples:
        # Exemple 1: Durée d'aplasie
        fig = create_histogram_with_density(
            data=df,
            value_column='duree_aplasie',
            filter_column='Anc Recovery',
            filter_value='Yes',
            date_columns=('Treatment Date', 'Date Anc Recovery'),
            title="Durée d'aplasie",
            x_axis_title="Jours",
            y_axis_title="Nombre de patients",
            bin_size=2
        )
        
        # Exemple 2: Âge au diagnostic
        fig = create_histogram_with_density(
            data=df,
            value_column='Age At Diagnosis',
            title="Distribution de l'âge au diagnostic",
            x_axis_title="Âge (années)",
            y_axis_title="Nombre de patients",
            bin_size=5
        )
        
        # Exemple 3: Durée de suivi
        fig = create_histogram_with_density(
            data=df,
            value_column='duree_suivi',
            date_columns=('Treatment Date', 'Date Of Last Contact'),
            title="Durée de suivi",
            x_axis_title="Jours",
            y_axis_title="Nombre de patients"
        )
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
            hovertemplate="<b>Intervalle:</b> %{x}<br><b>Fréquence:</b> %{y}<extra></extra>"
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
                    name='Densité',
                    line=dict(color=color_density, width=2),
                    yaxis='y1',
                    hovertemplate="<b>Valeur:</b> %{x:.1f}<br><b>Densité:</b> %{y:.1f}<extra></extra>"
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
        text=f"<b>Statistiques:</b><br>"
             f"N = {len(display_values)}<br>"
             f"Moyenne = {mean_val:.1f}<br>"
             f"Écart-type = {std_val:.1f}<br>"
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
    title: str = "Distribution des durées",
    unit: str = "jours",
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
    title: str = "Distribution stratifiée avec densité",
    x_axis_title: str = "Valeurs",
    y_axis_title: str = "Fréquence",
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
        
    Examples:
        # Durée d'aplasie par année (3 dernières années)
        fig = create_stratified_histogram_with_density(
            data=df,
            value_column='duree_aplasie',
            stratification_column='Year',
            filter_column='Anc Recovery',
            filter_value='Yes',
            date_columns=('Treatment Date', 'Date Anc Recovery'),
            title="Durée d'aplasie par année",
            x_axis_title="Jours",
            y_axis_title="Nombre de patients",
            bin_size=2,
            max_strata=3
        )
        
        # Âge au diagnostic par diagnostic principal
        fig = create_stratified_histogram_with_density(
            data=df,
            value_column='Age At Diagnosis',
            stratification_column='Main Diagnosis',
            title="Âge au diagnostic par pathologie",
            x_axis_title="Âge (années)",
            bin_size=5,
            max_strata=3
        )
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
                             "Intervalle: %{x}<br>" +
                             "Fréquence: %{y}<br>" +
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
                        name=f"Densité {stratum}",
                        line=dict(color=color, width=3),
                        legendgroup=f"group_{stratum}",
                        showlegend=False,  # Éviter la duplication dans la légende
                        hovertemplate=f"<b>Densité {stratification_column}: {stratum}</b><br>" +
                                     "Valeur: %{x:.1f}<br>" +
                                     "Densité: %{y:.1f}<extra></extra>"
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
        annotation_text = "<b>Statistiques par strate:</b><br>"
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
        
        oui_count = counts.get('Oui', 0)
        non_count = counts.get('Non', 0)
        
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
        name='Oui',
        x=proportions_df['Traitement'],
        y=proportions_df['Oui_percent'],
        marker_color='#27BDBE',
        text=[f'{p:.1f}%<br>({c})' for p, c in zip(proportions_df['Oui_percent'], proportions_df['Oui_count'])],
        textposition='inside' if show_values else 'none',
        textfont=dict(color='white', size=10)
    ))
    
    # Barre pour "Non"
    fig.add_trace(go.Bar(
        name='Non',
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

def create_competing_risks_analysis(data, gvh_type):
    """
    Crée l'analyse de risques compétitifs pour GvH aiguë ou chronique
    
    Args:
        data (pd.DataFrame): DataFrame avec les données
        gvh_type (str): Type de GvH ('acute' ou 'chronic')
        
    Returns:
        plotly.graph_objects.Figure: Figure de l'analyse des risques compétitifs
    """
    try:
        # Import de la classe CompetingRisksAnalyzer
        import modules.competing_risks as cr
        CompetingRisksAnalyzer = cr.CompetingRisksAnalyzer
    except ImportError:
        # Fallback si le module n'est pas trouvé
        raise ImportError("CompetingRisksAnalyzer non trouvé. Assurez-vous que modules/competing_risks.py existe.")
    
    # Vérifier les colonnes nécessaires
    required_base_columns = ['Treatment Date', 'Status Last Follow Up', 'Date Of Last Follow Up']
    
    if gvh_type == 'acute':
        required_gvh_columns = ['First Agvhd Occurrence', 'First Agvhd Occurrence Date']
        max_days = 100
        title = "Analyse de Risques Compétitifs : GvH Aiguë vs Décès (100 jours post-allogreffe)"
        event_label = 'GvH Aiguë'
        event_color = 'red'
    else:  # chronic
        required_gvh_columns = ['First Cgvhd Occurrence', 'First Cgvhd Occurrence Date']
        max_days = 365
        title = "Analyse de Risques Compétitifs : GvH Chronique vs Décès (365 jours)"
        event_label = 'GvH Chronique'
        event_color = 'orange'
    
    # Vérifier que toutes les colonnes nécessaires existent
    all_required_columns = required_base_columns + required_gvh_columns
    missing_columns = [col for col in all_required_columns if col not in data.columns]
    
    if missing_columns:
        # Créer un graphique d'erreur informatif
        fig = go.Figure()
        fig.add_annotation(
            text=f"Colonnes manquantes pour l'analyse GvH :<br>{', '.join(missing_columns)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            title=title,
            height=500,
            showlegend=False
        )
        return fig
    
    # Filtrer les données pour ne garder que celles avec les informations de base
    df_filtered = data.dropna(subset=['Treatment Date']).copy()
    
    if len(df_filtered) == 0:
        # Graphique vide si pas de données
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée disponible pour l'analyse",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            title=title,
            height=500,
            showlegend=False
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
        
        # Calculer l'incidence cumulative
        results, processed_data = analyzer.calculate_cumulative_incidence(
            events_config, followup_config, max_days=max_days
        )
        
        # Créer le graphique
        fig = analyzer.create_competing_risks_plot(
            results, processed_data, events_config, title=title
        )
        
        return fig
        
    except Exception as e:
        # Graphique d'erreur si l'analyse échoue
        fig = go.Figure()
        fig.add_annotation(
            text=f"Erreur lors de l'analyse des risques compétitifs :<br>{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=14
        )
        fig.update_layout(
            title=title,
            height=500,
            showlegend=False
        )
        return fig
