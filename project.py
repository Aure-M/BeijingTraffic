import pandas as pd 
import streamlit as st
import datetime 
from prj_utils import fetchData, mapTaxis
    


#----------------------------
taxis = fetchData()

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

if option == 'Taxis dashboard':
    if dashOption == "Taxis on map":
        mapTaxis(taxis,date,hour)