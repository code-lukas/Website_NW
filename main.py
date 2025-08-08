import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import pydeck as pdk
import yaml
import time

db_path = "./meta.sqlite3"
questions_file_path = './data/questions.txt'
travel_destinations_path = './data/destinations.csv'

# Streamlit app configuration
st.set_page_config(
    page_title="Urlaubsgruppe",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None
)


def compute_zoom(lat_diff, lon_diff):
    """Approximate zoom level based on lat/lon span."""
    max_diff = max(lat_diff, lon_diff)
    if max_diff < 0.05:
        return 12
    elif max_diff < 0.5:
        return 10
    elif max_diff < 1:
        return 8
    elif max_diff < 5:
        return 6
    elif max_diff < 15:
        return 4
    elif max_diff < 40:
        return 3
    else:
        return 2


def karte() -> None:
    st.write('# 🌎 Weltkarte')
    data = pd.read_csv(travel_destinations_path)

    if data.empty:
        st.warning("Noch keine Orte vorhanden.")
        return

    min_lat, max_lat = data['lat'].min(), data['lat'].max()
    min_lon, max_lon = data['lon'].min(), data['lon'].max()

    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2

    lat_diff = max_lat - min_lat
    lon_diff = max_lon - min_lon
    zoom = compute_zoom(lat_diff, lon_diff)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=data,
        get_position='[lon, lat]',
        get_color='[255, 0, 0, 160]',
        radiusMinPixels=6,  # Ensures point is always at least 6px wide
        radiusMaxPixels=20,  # Optional: cap max size
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=zoom,
        pitch=0,
    )

    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

    # Input form
    with st.form("map_form", clear_on_submit=True):
        location = st.text_input("Füge einen neuen Ort hinzu:")
        submitted = st.form_submit_button("Hinzufügen")

        if submitted and location:
            with open(travel_destinations_path, 'a') as f:
                f.write(f"{location.replace(' ', '')}\n")
            st.rerun()


# Fragen section
def fragen() -> None:
    st.write('# ❓Fragen')

    # Input with a submit button
    with st.form("question_form", clear_on_submit=True):
        question = st.text_input("Füge eine neue Frage hinzu:")
        submitted = st.form_submit_button("Hinzufügen")

        if submitted and question:
            with open(questions_file_path, 'a') as f:
                f.write(f"{question}\n")
            st.rerun()

    try:
        with open(questions_file_path, 'r') as f:
            questions = f.readlines()
        for i, q in enumerate(questions):
            st.write(f'{i + 1}. {q.strip()}')
            st.divider()

    except FileNotFoundError:
        with open(questions_file_path, 'w+') as f:
            pass
        st.rerun()


def kosten() -> None:
    # Kosten
    df = pd.read_csv('./data/costs.csv')
    df.set_index('reisename', inplace=True)  # Use reisename as index

    second_to_last_trip, last_trip = df['kosten'].to_list()[-2:]

    st.write('# 💳 Kosten')
    st.bar_chart(df, color='#239614')
    col1, col2, col3, col4 = st.columns(4)

    delta = (last_trip - second_to_last_trip) / second_to_last_trip * 100

    with col1:
        st.metric('Günstigste Reise', f"{df['kosten'].min()} €")

    with col2:
        st.metric('Teuerste Reise', f"{df['kosten'].max()} €")

    with col3:
        st.metric('Kosten der letzten Reise', f'{last_trip} €', f'{delta:+.1f} %')

    with col4:
        st.metric('Gesamtkosten', f"{df['kosten'].sum()} €")


with open('./config.yml') as file:
    config = yaml.load(file, Loader=yaml.SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

# Initialize session state for authentication and message refreshing
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None
    st.session_state["username"] = None
    st.session_state["name"] = None

if "clear_messages_trigger" not in st.session_state:
    st.session_state["clear_messages_trigger"] = False

if "last_refresh_time" not in st.session_state:
    st.session_state["last_refresh_time"] = time.time()

# Login form
if st.session_state["authentication_status"] is None:
    name, authentication_status, username = authenticator.login()
    if authentication_status:
        st.session_state["authentication_status"] = True
        st.session_state["username"] = username
        st.session_state["name"] = name
    elif authentication_status is False:
        st.error("Username/password is incorrect")
else:
    name = st.session_state["name"]
    username = st.session_state["username"]

# Main application
if st.session_state["authentication_status"]:
    karte()
    fragen()
    kosten()
