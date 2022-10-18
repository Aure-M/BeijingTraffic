from cmath import sqrt
import pandas as pd 
import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
from datetime import datetime

def getDay(dates):
    res = []
    for i in range(len(dates)):
        res.append(dates[i].day)
    return res

def getDate(i):
    return i.date()

def isEqual(d1,d2):
    return (d1.year == d2.year)&(d1.month == d2.month)&(d1.day == d2.day)

@st.cache(suppress_st_warning=True)
def isDateEqualTo(dates,d):
    res = []
    for i in range(len(dates)):
        res.append(isEqual(dates[i],d))
    return res

@st.cache(suppress_st_warning=True)
def getTaxiLastPos(taxis,date,hour):
    filt = taxis[isDateEqualTo(taxis.index.map(getDate), date)]
    filt = taxis[(taxis["hours"]<=hour+1)&(taxis["hours"]>=hour-1)][["latitude","longitude","taxiId"]]
    res = []
    taxis = filt["taxiId"].value_counts().index
    for t in taxis:
        res.append(filt.iloc[-1])
    return res

@st.cache(suppress_st_warning=True)
def fetchData():
    taxis = pd.read_csv("./taxis2.csv",index_col="datetime")
    taxis.index = pd.to_datetime(taxis.index)
    taxis.sort_index(axis=0,inplace = True)
    return taxis

def mapTaxis(taxis,date,hour):
    beijing = {"lat":40.190632, "lon":116.412144,"radius":sqrt(16411/(np.pi*2))}
    lastTaxisPositions = getTaxiLastPos(taxis,date,hour)
    m = folium.Map(location=[beijing["lat"],beijing["lon"]])
    st.write(len(lastTaxisPositions))
    for taxi in lastTaxisPositions:
        lat,lon,taxiId = taxi["latitude"], taxi["longitude"], taxi["taxiId"]     
        folium.Marker(
            [lat,lon],
            icon=folium.Icon(icon="glyphicon-map-marker",color="black"),
            tooltip = "taxi {}".format(int(taxiId))
        ).add_to(m)
    
    st_data = st_folium(m, width = 800,height=600)



