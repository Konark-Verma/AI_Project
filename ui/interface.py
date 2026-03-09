import streamlit as st
from agents.travel_agent import plan_trip
from maps.map_visualizer import show_map

def run_interface():

    st.title("✈ AI Travel Planner")

    col1, col2 = st.columns(2)

    with col1:
        source = st.text_input("From")

    with col2:
        destination = st.text_input("To")

    budget = st.number_input("Budget")

    if st.button("Generate Travel Plan"):

        result = plan_trip(source, destination, budget)

        st.subheader("Recommended Transport")
        st.write(result["transport"])

        st.subheader("Travel Route")

        st.write(" → ".join(result["route"]))

        st.subheader("Distance")

        st.write(round(result["distance"],2),"km")

        st.subheader("Famous Places")

        for p in result["places"]:
            st.write("•",p)

        st.subheader("Travel Map")

        show_map(result["coords"])