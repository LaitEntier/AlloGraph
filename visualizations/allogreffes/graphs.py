import plotly.graph_objects as go
import pandas as pd

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