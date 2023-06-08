import re
import io
import folium
from folium.plugins import MarkerCluster
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium
from cryptography.fernet import Fernet


def decrypt(password):
    try:
        cipher_suite = Fernet(password.encode("utf-8"))
        with open("data", 'rb') as fichier_chiffre:
            contenu_chiffre = fichier_chiffre.read()
        contenu_dechiffre = cipher_suite.decrypt(contenu_chiffre)
        return io.BytesIO(contenu_dechiffre)
    except Exception as e:
        return None

######

## UTILS

######

def convertir_en_liste(chaine):
    valeurs = re.findall(r'[\d.]+|NULL', chaine)
    liste = []
    for valeur in valeurs:
        if valeur == 'NULL':
            liste.append(None)
        else:
            liste.append(float(valeur))
    return liste

@st.cache_data
def data(password):
    df = pd.read_csv(decrypt(password))
    df["project_id_t"] = df["project_id_t"].apply(convertir_en_liste)
    df["longitude_t"] = df["longitude_t"].apply(convertir_en_liste)
    df["latitude_t"] = df["latitude_t"].apply(convertir_en_liste)
    df['association'] = [[{"project": str(int(x)), "coords": [y, z]} for x, y, z in zip(col1, col2, col3)] for col1, col2, col3 in zip(df['project_id_t'], df['latitude_t'], df['longitude_t'])]
    return df

def questions(password):
    df = data(password)
    return df["text"].unique()

def reponses(question, password):
    df = data(password)
    df = df[df.text == question]
    return df["values_extract"].unique()

def repartition_project(question, password):
    df = data(password)
    df = df[df.text == question]
    fig = px.pie(df, "values_extract", "nb_project")
    return fig

def carto_project(question, reponse, password):
    df = data(password)
    projects = df[(df.text == question) & (df.values_extract == reponse)]["association"].values[0]
    m = folium.Map(location=[47, 3], zoom_start=5)
    marker_cluster = MarkerCluster().add_to(m)
    for p in projects:
        if None not in p["coords"]:
            folium.Marker(
                location=p["coords"],
                popup="Project n°" + p["project"],
                icon=folium.Icon(color="green", icon="ok-sign"),
            ).add_to(marker_cluster)
    return m

######

## APP

######

st.set_page_config(page_title="Perrine's Project", page_icon=None,) # layout="wide",)

with st.expander("Déverrouillage"):
    password = st.text_input("Mot de Passe", type="password")
    test_ok = True if decrypt(password) is not None else False

if test_ok:
    st.title("The PR Project")

    question = st.selectbox("Question", questions(password))

    st.subheader(question)
    st.plotly_chart(repartition_project(question, password), use_container_width=True)

    reponse = st.selectbox("Réponses", reponses(question, password))

    st.subheader("Situation des projets ayant repondu : " + reponse)
    map = st_folium(carto_project(question, reponse, password), width=800)