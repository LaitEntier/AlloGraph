import plotly.graph_objects as go
import pandas as pd
import plotly.express as px

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
    percentage_format=".1f"  # Format des pourcentages affichés
):
    """
    Crée un barplot empilé normalisé (100%) avec Plotly.

    Args:
        data (pd.DataFrame): DataFrame contenant les données
        x_column (str): Nom de la colonne pour l'axe X (Age At Diagnosis)
        y_column (str): Nom de la colonne pour les valeurs (count)
        stack_column (str): Nom de la colonne pour l'empilement (Main Diagnosis)
        title (str, optional): Titre du graphique
        x_axis_title (str, optional): Titre de l'axe X
        y_axis_title (str, optional): Titre de l'axe Y
        color_map (dict, optional): Dictionnaire de mapping couleurs pour chaque catégorie d'empilement
        show_values (bool, optional): Afficher les pourcentages dans les barres
        height (int, optional): Hauteur du graphique
        width (int, optional): Largeur du graphique
        custom_order (list, optional): Liste définissant l'ordre personnalisé des catégories
        percentage_format (str, optional): Format de chaîne pour les pourcentages (ex: ".1f" pour 1 décimale)

    Returns:
        plotly.graph_objects.Figure: Figure Plotly du barplot empilé normalisé
    """
    
    # Préparer les données groupées
    grouped_data = data.groupby([x_column, stack_column]).size().unstack(fill_value=0)
    
    # Calculer les totaux par catégorie x
    grouped_data_with_totals = grouped_data.copy()
    grouped_data_with_totals['Total'] = grouped_data_with_totals.sum(axis=1)
    
    # Calculer les pourcentages
    normalized_data = grouped_data.div(grouped_data_with_totals['Total'], axis=0) * 100
    normalized_data = normalized_data.reset_index()
    
    # Conserver les valeurs absolues pour l'affichage (si nécessaire)
    absolute_values = grouped_data.reset_index()
    
    # Définir les titres par défaut
    x_axis_title = x_axis_title or x_column
    y_axis_title = y_axis_title or "Pourcentage (%)"
    
    # Préparer les traces pour chaque catégorie d'empilement
    traces = []
    stack_categories = normalized_data.columns[1:]
    
    # Utiliser un color map prédéfini ou générer des couleurs
    if color_map is None:
        if isinstance(custom_order, list) and len(custom_order) > 0:
            # Utiliser l'ordre personnalisé pour les catégories
            sorted_categories = [cat for cat in custom_order if cat in stack_categories]
            # Ajouter les catégories manquantes à la fin
            for cat in stack_categories:
                if cat not in sorted_categories:
                    sorted_categories.append(cat)
            stack_categories = sorted_categories
        
        color_map = {cat: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] 
                    for i, cat in enumerate(stack_categories)}
    
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
            marker_color=color_map[category] if isinstance(color_map, dict) else 
                      color_map[list(stack_categories).index(category) % len(color_map)],
            text=text_values,
            textposition='inside',
            textfont=dict(size=10)
        ))
    
    # Créer la figure avec empilement
    fig = go.Figure(data=traces)
    fig.update_layout(
        title=title,
        barmode='stack',
        xaxis_title=x_axis_title,
        yaxis_title=y_axis_title,
        height=height,
        width=width,
        template='plotly_white',
        legend_title_text=stack_column,
        # Fixer les limites de l'axe Y de 0 à 100%
        yaxis=dict(range=[0, 100])
    )
    
    return fig

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
    custom_order=None
):
    """
    Crée un barplot empilé avec Plotly.

    Args:
        data (pd.DataFrame): DataFrame contenant les données
        x_column (str): Nom de la colonne pour l'axe X (Age At Diagnosis)
        y_column (str): Nom de la colonne pour les valeurs (count)
        stack_column (str): Nom de la colonne pour l'empilement (Main Diagnosis)
        title (str, optional): Titre du graphique
        x_axis_title (str, optional): Titre de l'axe X
        y_axis_title (str, optional): Titre de l'axe Y
        color_map (dict, optional): Dictionnaire de mapping couleurs pour chaque catégorie d'empilement
        show_values (bool, optional): Afficher les valeurs dans les barres
        height (int, optional): Hauteur du graphique
        width (int, optional): Largeur du graphique
        custom_order (list, optional): Liste définissant l'ordre personnalisé des catégories

    Returns:
        plotly.graph_objects.Figure: Figure Plotly du barplot empilé
    """
    # Préparer les données groupées
    grouped_data = data.groupby([x_column, stack_column]).size().unstack(fill_value=0).reset_index()
    
    # Définir les titres par défaut
    x_axis_title = x_axis_title or x_column
    y_axis_title = y_axis_title or "Nombre de patients"
    
    # Préparer les traces pour chaque catégorie d'empilement
    traces = []
    stack_categories = grouped_data.columns[1:]
    
    # Utiliser un color map prédéfini ou générer des couleurs
    if color_map is None:
        color_map = px.colors.qualitative.Plotly[:len(stack_categories)]
    
    for i, category in enumerate(stack_categories):
        traces.append(go.Bar(
            name=category,
            x=grouped_data[x_column],
            y=grouped_data[category],
            marker_color=color_map[i % len(color_map)],
            text=grouped_data[category] if show_values else None,
            textposition='inside'
        ))
    
    # Créer la figure avec empilement
    fig = go.Figure(data=traces)
    fig.update_layout(
        title=title,
        barmode='stack',
        xaxis_title=x_axis_title,
        yaxis_title=y_axis_title,
        height=height,
        width=width,
        template='plotly_white',
        legend_title_text=stack_column
    )
    
    return fig
