"""
This module contains common functions used in the dashboards.
"""

import plotly.graph_objects as go
import pandas as pd


def prepare_data(file):
    """
    Load the data and prepare it for display.

    Parameters:
    -----------
    file: str
        The path or URL to the CSV file containing the data.

    Returns:
    --------
    df: pd.DataFrame
        The cleaned data.
    """
    df = pd.read_csv(file, compression="gzip", low_memory=False)
    df = df[df.nature_mutation == "Vente"]
    df = df.drop([
        'numero_disposition',
        'nature_mutation',
        'adresse_code_voie',
        'code_commune',
        'ancien_code_commune',
        'ancien_nom_commune',
        'id_parcelle',
        'ancien_id_parcelle',
        'numero_volume',
        'lot1_numero',
        'lot2_numero',
        'lot3_numero',
        'lot4_numero',
        'lot5_numero',
        'lot1_surface_carrez',
        'lot2_surface_carrez',
        'lot3_surface_carrez',
        'lot4_surface_carrez',
        'lot5_surface_carrez',
        'nombre_lots',
        'code_type_local',
        'code_nature_culture',
        'nature_culture',
        'code_nature_culture_speciale',
        'nature_culture_speciale',
        'surface_terrain',
        'code_departement',
        'nom_commune',
        ], axis=1)
    df = df.dropna()

    df['type_local'] = df['type_local'].apply(
        lambda x: "Local" if x.startswith("Local") else x
    )

    return df


def get_map(df):
    """Return a plotly map with the data."""

    # Generate texts for the markers
    # Add to the text:
    # - the surface of the building
    # - the number of rooms
    # - the type of building
    # - the price
    # - the address
    text = [
        f"Surface: {surface} m²\n"
        f"Rooms: {rooms}\n"
        f"Type: {type_local}\n"
        f"Price: {price} €\n"
        f"Address: {int(number):d} {address}"
        for surface, rooms, type_local, price, address, number in zip(
            df["surface_reelle_bati"],
            df["nombre_pieces_principales"],
            df["type_local"],
            df["valeur_fonciere"],
            df["adresse_nom_voie"],
            df["adresse_numero"]
        )
    ]

    # Plot figure
    fig = go.Figure(
        go.Scattermapbox(
            lat=df["latitude"],
            lon=df["longitude"],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=9
            ),
            customdata=text,
        )
    )
    # Compute as center the mean of the coordinates
    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()
    fig.update_layout(
        height=800,
        mapbox_style="open-street-map",
        mapbox_zoom=11,
        mapbox_center={"lat": center_lat, "lon": center_lon}
        )

    return fig
