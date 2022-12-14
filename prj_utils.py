from cmath import sqrt
import pandas as pd 
import streamlit as st
import folium
import pydeck as pdk
from streamlit_folium import st_folium
import numpy as np
from scipy.sparse.csgraph import dijkstra
from datetime import datetime
from math import ceil, radians, cos, sin, asin, sqrt

#---------------------------------------------------------------------------
beijing = {"lat":40.190632, "lon":116.412144,"radius":sqrt(16411/(np.pi*2))}
#---------------------------------------------------------------------------
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
    filt = taxis[(taxis["hours"]<=hour)&(taxis["hours"]>=hour-1)][["latitude","longitude","taxiId","to_zone"]]
    res = []
    taxis = filt["taxiId"].value_counts().index
    
    for t in taxis:
        res.append(filt[filt["taxiId"] == t].iloc[-1])
    return pd.DataFrame(res)

@st.cache(suppress_st_warning=True)
def fetchData():
    taxis = pd.read_csv("./taxisFiltered.csv",index_col="datetime")
    taxis.index = pd.to_datetime(taxis.index)
    taxis.sort_index(axis=0,inplace = True)
    return taxis

@st.cache(suppress_st_warning=True)
def fetchAdjacencyMatrix():
    data = np.genfromtxt("./matriceAdjacence.txt")
    return data.reshape((data.shape[0],int(data.shape[1]/2),2))

@st.cache(suppress_st_warning=True)
def createFavoritePlaces():
    return []

def mapTaxis(date,hour,pitch):
    st.write("### Taxis on map")
    st.write("The point on this plot represent the last position known of all the taxis at a certain time (date and hour)")
    taxis = st.session_state['taxis']
    lastTaxisPositions = getTaxiLastPos(taxis,date,hour)
    zoned = lastTaxisPositions["to_zone"].value_counts()

    # Define a layer to display on a map
    layer = pdk.Layer(
        "ScatterplotLayer",
        lastTaxisPositions,
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=6,
        radius_min_pixels=1,
        radius_max_pixels=100,
        line_width_min_pixels=1,
        get_position="[longitude,latitude]",
        get_radius=30,
        get_fill_color=[0, 255, 50],
        get_line_color=[0, 0, 0],
    )

    # Set the viewport location
    view_state = pdk.ViewState(latitude=beijing["lat"], longitude=beijing["lon"], zoom=10, bearing=0, pitch=pitch)

    # Render
    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
            'html': '<b>Taxi ID:</b> {taxiId}',
            'style': {
                'color': 'white'
            }
        }
    )

    st.pydeck_chart(r)
    col1, col2, col3 = st.columns(3)
    l = int(len(zoned)/3)
    with col1:
        for i in range(l+1):
            st.write("Area_{} : ".format(int(zoned.index[i])), zoned[zoned.index[i]])
    with col2:
        for i in range(l+1,l*2+1):
            st.write("Area_{} : ".format(int(zoned.index[i])), zoned[zoned.index[i]])
    with col3:
        for i in range(l*2+1,l*3+1):
            st.write("Area_{} : ".format(int(zoned.index[i])), zoned[zoned.index[i]])
#---------------------------------------------------------------------------

def distance(lat1, lat2, lon1, lon2):
	
	# The math module contains a function named
	# radians which converts from degrees to radians.
	lon1 = radians(lon1)
	lon2 = radians(lon2)
	lat1 = radians(lat1)
	lat2 = radians(lat2)
	
	# Haversine formula
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2

	c = 2 * asin(sqrt(a))
	
	# Radius of earth in kilometers. Use 3956 for miles
	r = 6371
	
	# calculate the result
	return(c * r)
	
	
def getDistance(A,B):
    return distance(A["latitude"],B["latitude"],A["longitude"],B["longitude"])

@st.cache(suppress_st_warning=True)
def definecentersData(data,zoneRadius=5):
    locations = data[["longitude","latitude"]].value_counts()
    centers = []
    for current in locations.index.to_list():
        shoulBeACenter = True
        for c in centers:
            if distance(current[1],c[1],current[0],c[0])<zoneRadius:
                shoulBeACenter = False
                break
        if shoulBeACenter:
            centers.append(current)
    
    return centers

@st.cache(suppress_st_warning=True)
def getCentersData(taxis):
    
    centers = definecentersData(taxis,)
    centersData = taxis.groupby(by="to_zone")["speed","res_T","res_D"].mean()
    centersData[["longitude","latitude"]] = centers
    centersData["name"] = ["Area n_{}".format(c) for c in centersData.index]
    
    COLOR_RANGE = [
        [199, 233, 180],
        [237, 248, 177],
        [255, 255, 204],
        [255, 237, 160],
        [254, 217, 118],
        [254, 178, 76],
        [253, 141, 60],
        [252, 78, 42],
        [227, 26, 28],
        [189, 0, 38],
        [128, 0, 38],
    ]
    COLOR_RANGE.reverse()
    max = centersData["speed"].mean()
    min = centersData["speed"].min()
    BREAKS = np.linspace(min,max,num=len(COLOR_RANGE))

    def color_scale(val):
        for i, b in enumerate(BREAKS):
            if val < b:
                return COLOR_RANGE[i]
        return COLOR_RANGE[i]

    centersData["color"] = centersData["speed"].map(color_scale)
    return centersData

def taxistrafficAnalysis(pitch):
    st.write("### Taxis analysis")
    st.write("You can see a scatter of the areas from areas resulting from the partition of Beijing. The areas with the highest congestion rates are redder and the ones with the lowest rate whiter ")
    centersData = st.session_state['centers']

    layers = [
        pdk.Layer(
            "ScatterplotLayer",
            centersData,
            stroked=True,
            filled=True,
            radius_scale=6,
            radius_min_pixels=1,
            radius_max_pixels=100,
            line_width_min_pixels=1,
            get_position="[longitude, latitude]",
            auto_highlight=True,
            elevation_scale=50,
            get_fill_color = "color",
            get_radius=400,
            pickable=True,
            opacity=0.8,
        ),
    ]

    # Set the viewport location
    view_state = pdk.ViewState(
        longitude=beijing["lon"],
        latitude=beijing["lat"],
        zoom=8,
        min_zoom=5,
        max_zoom=15,
        pitch=pitch,
    )

    # Render
    r = pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            tooltip={
                'html': '<b>Area:</b> {name} </br> <b> Average Speed:</b>{speed} km/h',
                'style': {
                    'color': 'white'
                }
            }
        )
    st.pydeck_chart(r)

#---------------------------------------------------------------------------

def findShortestPath(a,b,adjacencyMatrix): 
    dist_matrix,predecessors = dijkstra(csgraph = adjacencyMatrix,indices = a, directed = True, return_predecessors = True)
    path = []
    time = 0
    tmp = b
    while tmp != a:
        path.append(tmp)
        time+=dist_matrix[tmp]
        tmp = int(predecessors[tmp])
        if tmp == -9999:
            return None, None
    path.append(a)
    path.reverse()
    return path, time


def pathMapDataProcessing(path,pathCoords):
    coordsDF = pd.DataFrame([[pathCoords]],columns=["path"])
    centers = pd.DataFrame(pathCoords,columns=["longitude","latitude"], index=path)
    colors = [[0,255,0]]
    for i in range(1, len(centers)):
        if i == len(centers)-1:
            colors.append([255,0,0])
        else:
            colors.append([255,140,0])
    centers["color"] = colors
            
    return coordsDF, centers
    
def mapShortestPath(pitch):
    
    centers = st.session_state['centers']
    adjacencyMatrix =st.session_state['adjacencyMatrix']

    pointA = st.selectbox(
        'Choose the area from which you are leaving',
        centers.index,
        index = 0
    )
    pointB = st.selectbox(
        'Choose the area where you are going',
        centers.index,
        index = 6
    )
    path,timeNeeded = findShortestPath(a=pointA,b=pointB,adjacencyMatrix=adjacencyMatrix[:,:,0])
    
    pathCoords = [list(centers[centers.index == area][["longitude","latitude"]].itertuples(index = False))[0] for area in path]
    pathCoords = [list(i) for i in pathCoords]

    coordsDF, centersCoord = pathMapDataProcessing(path,pathCoords)
    st.write("### Average time(min) : ",ceil(timeNeeded))
    view_state = pdk.ViewState(
        longitude=beijing["lon"],
        latitude=beijing["lat"],
        zoom=8,
        min_zoom=5,
        max_zoom=15,
        pitch = pitch
    )
    layers = [
        pdk.Layer(
            type="PathLayer",
            data=coordsDF,
            pickable=True,
            get_color=[255,255,255],
            width_scale=20,
            width_min_pixels=2,
            get_path="path",
            get_width=5,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            data = centersCoord,
            pickable=True,
            opacity=0.8,
            stroked=True,
            filled=True,
            radius_scale=5,
            radius_min_pixels=1,
            radius_max_pixels=100,
            get_radius=80,
            line_width_min_pixels=1,
            get_position="[longitude,latitude]",
            get_color="color",
            get_line_color=[0, 0, 0],
        )
    ]
    
    r = pdk.Deck(
        layers=layers,
        initial_view_state=view_state
    )
    st.pydeck_chart(r)


#---------------------------------------------------------------------------

def findBestMatch(areas,adjacencyMatrix):
    res = []
    for a in range(len(adjacencyMatrix)):
        time_i = []
        for b in areas:
            _, t = findShortestPath(a=a,b=b,adjacencyMatrix=adjacencyMatrix)
            if t == None:
                time_i.append(None)
                break
            else:
                time_i.append(t)
        res.append(time_i)
    res = pd.DataFrame(data=res,columns=areas)
    res["total"] = res.sum(axis=1)
    res.dropna(inplace=True)
    return res

def findBestAreaToGoToFavoritesPlaces(pitch):
    favoritePlaces = st.session_state['favoritePlaces']
    centers = st.session_state['centers']
    adjacencyMatrix =st.session_state['adjacencyMatrix']
    
    tab1, tab2 = st.tabs(["Add a place here", "See the results here"])

    with tab1:
        # Form to add a favorite place
        place = st.text_input('Place name', '')
        location = st.selectbox(
            'Choose the place area',
            centers.index,
            index = 6
        )
        if st.button("Add Favorite place"):
            st.session_state['favoritePlaces'].append([location,place])
        
        st.write("#### Select the places that tou want for the calculation")
        checkBoxs = [st.checkbox('PLACE : {} | AREA : {}'.format(favoritePlaces[i][1], favoritePlaces[i][0]),key = i) for i in range(len(favoritePlaces))]

    with tab2:
        # Data preprocessing
        st.write("The area that is suggested is colored in BLUE and your favorites places are in YELLOW")
        favPlaceDF = pd.DataFrame(favoritePlaces,columns=["zone","name"])
        favPlaceDF[["longitude","latitude"]] = [list(centers[centers.index == favoritePlaces[i][0]][["longitude","latitude"]].itertuples(index = False))[0] for i in range(len(favoritePlaces))]
        
        # Best match calculation
        res = findBestMatch(favPlaceDF[checkBoxs]["zone"],adjacencyMatrix=adjacencyMatrix[:,:,0])
        res[["longitude","latitude"]] = centers[["longitude","latitude"]]
        res.sort_values(by="total", inplace = True)
        res = res[:1]

        # Creation of the dataframe of plotted points (favorite Places and the bestMatch)
        points = []
        for i in range(len(favPlaceDF[checkBoxs])):
            c = favPlaceDF.iloc[i]
            points.append([c["longitude"], c["latitude"], c["name"],[255, 255, 0]])
        for i in range(len(res)):
            c = res.iloc[i]
            points.append([c["longitude"], c["latitude"], "Area {}".format(c.name),[0, 150, 255]])
        points = pd.DataFrame(points, columns=["longitude","latitude","name", "color"])


        view_state = pdk.ViewState(
            longitude=beijing["lon"],
            latitude=beijing["lat"],
            zoom=8,
            min_zoom=5,
            max_zoom=15,
            pitch = pitch
        )

        layers = [
            pdk.Layer(
                "ScatterplotLayer",
                data = points,
                pickable=True,
                opacity=0.8,
                stroked=True,
                filled=True,
                radius_scale=10,
                radius_min_pixels=1,
                radius_max_pixels=100,
                get_radius=50,
                line_width_min_pixels=1,
                get_position="[longitude,latitude]",
                get_color="color",
                get_line_color=[0, 0, 0],
            )
        ]
        
        r = pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            tooltip={
                'html': '<b>{name}</b> ',
                'style': {
                    'color': 'white'
                }
            }
        )
        st.pydeck_chart(r)