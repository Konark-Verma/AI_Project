import folium
from streamlit_folium import st_folium

def show_map(coords):

    m = folium.Map(location=coords[0], zoom_start=3)

    for c in coords:

        folium.Marker(c).add_to(m)

    st_folium(m, width=900, height=500)