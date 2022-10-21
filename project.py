import pandas as pd 
import streamlit as st
import datetime 
from prj_utils import createFavoritePlaces, fetchAdjacencyMatrix, fetchData, findBestAreaToGoToFavoritesPlaces, getCentersData, mapShortestPath, mapTaxis, taxistrafficAnalysis
    


#----------------------------
# Initialization
if 'taxis' not in st.session_state:
    st.session_state['taxis'] = fetchData()
    taxis = st.session_state['taxis']
if 'centers' not in st.session_state:
    st.session_state['centers'] = getCentersData(taxis)
    centers = st.session_state['centers']
if 'adjacencyMatrix' not in st.session_state:
    st.session_state['adjacencyMatrix'] = fetchAdjacencyMatrix()
    adjacencyMatrix = st.session_state['adjacencyMatrix']
if 'favoritePlaces' not in st.session_state:
    st.session_state['favoritePlaces'] = createFavoritePlaces()
    favoritePlaces = st.session_state['favoritePlaces']


#----------------------------



with st.sidebar:
    option = st.selectbox(
    'Select the app',
    ('Taxis dashboard', 'Suggestion feature'))
    
    if option == 'Taxis dashboard':
        st.subheader("Choose a screen")
        dashOption = st.selectbox(
            '',
            ('Taxis on map', 'Traffic analysis')
        )
        
 
        if dashOption == "Taxis on map":
            date = st.slider(
                "Choose Day",
                datetime.datetime(2008,2,2),datetime.datetime(2008,2,8),
                value=datetime.datetime(2008,2,6)
            )
            hour = st.slider(
                "Choose hour of the day ",
                0,24,
                value=6
            )
    else:
        screenOption = st.selectbox(
            '',
            ('Find shortest Path', 'Residential area suggestion')
        )
    pitch = st.slider(
                "Map orientation",
                0,100,
                value=70
    )

if option == 'Taxis dashboard':
    if dashOption == "Taxis on map":
        mapTaxis(date,hour,pitch)
    else:
        taxistrafficAnalysis(pitch)
else:
    if screenOption == "Find shortest Path":
        mapShortestPath(pitch)
    else:
        findBestAreaToGoToFavoritesPlaces(pitch)


