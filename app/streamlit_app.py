import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import tempfile

try:
    # import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

from parser.parser import parse_ardupilot_log
from analytics.metrics import calculate_flight_metrics, prepare_trajectory_data
from visualization.plot_3d import plot_trajectory

st.set_page_config(page_title="Drone Analyzer", layout="wide")

st.title("🚁 Drone Flight Analyzer")
st.caption("Upload ArduPilot log file (.bin / .log)")

uploaded_file = st.file_uploader("Upload flight log", type=["bin", "log"])

@st.cache_data
def process_file(file_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".BIN") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        df = parse_ardupilot_log(tmp_path)
        metrics = calculate_flight_metrics(df)
        trajectory = prepare_trajectory_data(df)
    finally:
        try:
            os.remove(tmp_path)
        except:
            pass

    return df, metrics, trajectory


if uploaded_file:

    if uploaded_file.size == 0:
        st.error("Empty file")
        st.stop()

    try:
        df, metrics, trajectory = process_file(uploaded_file.getvalue())

        st.success("File processed successfully")

        st.subheader("📊 Key Metrics")

        col1, col2, col3 = st.columns(3)

        col1.metric("Max Speed", f"{metrics['max_horizontal_speed_m_s']:.2f} m/s")
        col2.metric("Distance", f"{metrics['total_distance_m']:.2f} m")
        col3.metric("Max Altitude", f"{metrics['max_climb_m']:.2f} m")

        # --- TRAJECTORY ---
        st.subheader("🛰️ 3D Flight Trajectory")

        color_mode = st.selectbox(
            "Color trajectory by:",
            ["Time", "Speed"]
        )

        color_column = "time_sec" if color_mode == "Time" else "speed_3d"

        fig = plot_trajectory(trajectory, color_column)
        st.plotly_chart(fig, width="stretch")

        # --- RAW DATA ---
        with st.expander("🔍 Show raw data"):
            st.dataframe(df)

        st.subheader("🤖 AI Flight Analysis")
        if HAS_GENAI:
            api_key = st.text_input("Enter your Google Gemini API Key for AI analysis", type="password")
            if api_key:
                if st.button("Generate AI Report"):
                    with st.spinner("Analyzing data..."):
                        try:
                            #genai.configure(api_key=api_key)
                            #model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            prompt = f"""
                            You are an aviation expert. Analyze the flight metrics of the drone and provide a brief text summary regarding the success of the mission 
                            or potential problems (e.g., overspeeding, excessive acceleration, which could indicate a crash or an aggressive maneuver).
                            
                            Mission metrics:
                            - Flight duration: {metrics['duration_sec']:.2f} sec
                            - Maximum altitude (climb): {metrics['max_climb_m']:.2f} m
                            - Max horizontal speed: {metrics['max_horizontal_speed_m_s']:.2f} m/s
                            - Max vertical speed: {metrics['max_vertical_speed_m_s']:.2f} m/s
                            - Max acceleration: {metrics['max_accel_m_s2']:.2f} m/s^2
                            - Total distance covered: {metrics['total_distance_m']:.2f} m
                            """
                            
                            #response = model.generate_content(prompt)
                            #st.write(response.text)
                        except Exception as e:
                            st.error(f"Error generating AI report: {e}")
            else:
                st.info("A free Google Gemini API key is required to use the AI assistant. Get it on the Google AI Studio website.")
        else:
            st.warning("The `google-generativeai` library is not installed. AI analysis is unavailable.")

    except Exception as e:
        st.error("Error processing file")
        st.exception(e)