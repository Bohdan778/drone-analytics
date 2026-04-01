import streamlit as st

st.title("🚁 Drone Analytics")

file = st.file_uploader("Upload log file")

if file:
    st.success("File uploaded!")