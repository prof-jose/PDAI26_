"""
Streamlit app to estimate the price of a property based on the price of
similar properties.
"""

import geopy.distance as gd
import numpy as np
import pandas as pd
import streamlit as st
import locale
import json


# Constants
SHOW_MAP = True  # Set to False while developing to avoid API calls
TOKEN_FILE = "token.json"  # You need a token file with the Mapbox API key
FILE = (
    "https://files.data.gouv.fr/geo-dvf/latest/csv/2022/"
    "departements/75.csv.gz"
)
RELEVANT_COLUMNS = [
    'surface_reelle_bati',  # Surface area of the property
    'nombre_pieces_principales',  # Number of rooms
    'longitude',
    'latitude'
    ]


def init():
    """
    Initialize token and locale.

    Returns:
    --------
    token: str
        The token to access the mapbox API.
    """
    # Get authentication token from file
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        token = json.load(f)["token"]

    # Set locale for currency formatting based on US conventions
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

    return token


def prepare_data(file):
    """
    Load the data and prepare clean train and test sets.

    Parameters:
    -----------
    file: str
        The path or URL to the CSV file containing the data.

    Returns:
    --------
    train: pd.DataFrame
        The training set.
    test: pd.DataFrame
        The test set.
    """

    df = pd.read_csv(file, compression="gzip", low_memory=False)

    # Select the 80% earliest dates as the "database"
    # and the 20% latest to simulate the "new data"
    df = df.sort_values("date_mutation")
    df = df[df.type_local == "Appartement"]
    df = df[df.nature_mutation == "Vente"]
    train_size = int(0.8 * len(df))
    train = df[:train_size]
    test = df[train_size:]

    # We need to remove the rows where the following columns are missing:
    # - surface_reelle_bati
    # - nombre_pieces_principales
    # - longitude
    # - latitude
    train = train.dropna(subset=RELEVANT_COLUMNS)
    train = train.drop_duplicates(subset=RELEVANT_COLUMNS)
    test = test.dropna(subset=RELEVANT_COLUMNS)

    return train, test


def format_row_info(row):
    """
    Display the information of the selected property.

    Parameters:
    -----------
    row: pd.DataFrame
        The row of the dataframe corresponding to the selected property.
    """
    street_name = row.adresse_nom_voie.values[0]
    street_number = int(row.adresse_numero.values[0])
    street_zone = row.nom_commune.values[0]

    st.write(f"### {street_number} {street_name}, {street_zone}")

    surface = int(row.surface_reelle_bati.values[0])
    rooms = int(row.nombre_pieces_principales.values[0])
    type_local = row.type_local.values[0]
    plural = "s" if rooms > 1 else ""

    st.write(f"{surface} m² | {rooms} room{plural} | {type_local}")


def get_similarities(train, row):
    """
    Compute the similarity between the selected property and each property in
    the training set.

    Parameters:
    -----------
    train: pd.DataFrame
        The training set.

    row: pd.DataFrame
        The row of the dataframe corresponding to the selected property.

    Returns:
    --------
    similarities: pd.Series
        The similarity between the selected property and each property in the
        training set.
    """

    data = train[RELEVANT_COLUMNS].copy()

    # Standardize the data
    mu = data.mean()
    sd = data.std()
    data_sd = (data - mu) / sd

    # Compute the distance to the selected property
    x = row[RELEVANT_COLUMNS].copy().reset_index().drop('index', axis=1)
    xn = (x - mu) / sd

    return np.sqrt(np.square(data_sd.values - xn.values).sum(axis=1))


def display_map(comparables, row):
    """
    Display a map with the location of the selected property and the
    comparables.

    Parameters:
    -----------
    comparables: pd.DataFrame
        A dataframe with the comparables.

    row: pd.DataFrame
        The row of the dataframe corresponding to the selected property.
    """

    map_df = pd.DataFrame({
        "col1": comparables.latitude.tolist() + [row.latitude.values[0]],
        "col2": comparables.longitude.tolist() + [row.longitude.values[0]],
        "col3": [2]*comparables.shape[0] + [5],
        "col4": [[0, 0.0, 1.0]]*comparables.shape[0] + [[1.0, 0, 0]]
    })

    st.map(
        map_df,
        latitude='col1',
        longitude='col2',
        size='col3',
        color='col4',
        zoom=12
    )


def display_price_data(comparables, row):
    """
    Display the asking price and the estimated sale price.

    Parameters:
    -----------
    comparables: pd.DataFrame
        A dataframe with the comparables.

    row: pd.DataFrame
        The row of the dataframe corresponding to the selected property.
    """

    with st.container(border=True):

        price_col, est_col = st.columns(2)

        with price_col:

            st.write("**Asking price**")
            asking_price = locale.currency(
                row.valeur_fonciere.values[0],
                grouping=True
                )
            st.write(f"€ {asking_price[1:]}")

        with est_col:
            st.write("**Estimated sale price**")
            estimated_price = locale.currency(
                comparables.valeur_fonciere.mean(),
                grouping=True
                )
            st.write(f"€ {estimated_price[1:]}")


def list_comparables(comparables, token):
    """
    Format the info about comparables.

    Parameters:
    -----------
    comparables: pd.DataFrame
        A dataframe with the comparables.

    token: str
        The token to access the mapbox API.
    """
    nrows = comparables.shape[0]

    for i in range(nrows):
        st.divider()

        c0, c1, c2 = st.columns([1, 8, 4])
        with c0:
            st.image("icon.png", width=30)
        with c1:
            num = int(comparables.iloc[i].adresse_numero)
            name = comparables.iloc[i].adresse_nom_voie
            st.markdown(f"**{num} {name}**")
        with c2:
            st.write(f"{comparables.iloc[i].nom_commune}")
        cols = st.columns(7)

        with cols[0]:
            st.write("**Similarity**")
            st.progress(comparables.iloc[i].Similarity)

        with cols[1]:
            st.write("**%**")
            st.write(np.floor(100*comparables.iloc[i].Similarity))

        with cols[2]:
            st.write("**Surface**")
            st.write(comparables.iloc[i].surface_reelle_bati)
        with cols[3]:
            st.write("**Rooms**")
            st.write(comparables.iloc[i].nombre_pieces_principales)
        with cols[4]:
            st.write("**Distance (m)**")
            st.write(comparables.iloc[i].dist_meters)
        with cols[5]:
            st.write("**Price**")
            st.write(comparables.iloc[i].valeur_fonciere)
        with cols[6]:
            if SHOW_MAP:
                st.image(f"https://api.mapbox.com/styles/v1/mapbox/streets-v12/static/{comparables.iloc[i].longitude},{comparables.iloc[i].latitude},16,0,60/200x200?access_token={token}")
    st.divider()


def main():
    """
    Run the streamlit app.
    """

    # Init and prepare data
    token = init()
    train, test = prepare_data(FILE)

    # Display title and input box
    st.title("Real estate prices in France")
    prop_id = st.selectbox("Select a property:", test.sample(50).id_mutation.values)

    # Display data for that property:
    row = test[test.id_mutation == prop_id].head(1)
    format_row_info(row)

    # Compute similarities in order to find the comparables
    train['Similarity'] = get_similarities(train, row)
    train['Similarity'] = np.exp(-train['Similarity'])

    # Display the estimated price based on comparables
    comparables = train.sort_values(
        'Similarity',
        ascending=False
        ).head(5).copy()
    display_price_data(comparables, row)

    # Display map of comparables
    st.header("Analysis of Comparables")
    st.write("The previous estimation is based on the following comparables:")
    display_map(comparables, row)

    # List the comparables
    row = row.reset_index().drop('index', axis=1)
    distance = comparables.apply(
        lambda r: gd.distance(
            (r.latitude, r.longitude),
            (row.loc[0, 'latitude'], row.loc[0, 'longitude'])
            ).km,
        axis=1
    )
    comparables['dist_meters'] = (distance*1000).astype(int)

    list_comparables(comparables, token)


if __name__ == "__main__":
    main()
