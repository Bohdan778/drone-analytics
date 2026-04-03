import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import tempfile


from parser.parser import parse_ardupilot_log
from analytics.metrics import calculate_flight_metrics, prepare_trajectory_data
from visualization.plot_3d import plot_trajectory

st.set_page_config(page_title="Drone Analyzer", layout="wide")

# Prevent browser auto-translation (fixes React 'removeChild' Node errors)
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

st.title("Drone Flight Analyzer")
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

        st.subheader("Key Metrics")

        col1, col2, col3 = st.columns(3)

        col1.metric("Max Speed", f"{metrics['max_horizontal_speed_m_s']:.2f} m/s")
        col2.metric("Distance", f"{metrics['total_distance_m']:.2f} m")
        col3.metric("Max Altitude", f"{metrics['max_climb_m']:.2f} m")

        st.subheader("3D Flight Trajectory")

        color_mode = st.selectbox(
            "Color trajectory by:",
            ["Time", "Speed"]
        )

        color_column = "time_sec" if color_mode == "Time" else "speed_3d"

        fig = plot_trajectory(trajectory, color_column)
        st.plotly_chart(fig, width="stretch")

        # --- RAW DATA ---
        with st.expander("Show raw data"):
            st.dataframe(df)

        st.subheader("Auto-Diagnostics (Offline AI System)")
        st.caption("Heuristic analysis running locally without API costs.")
        
        if st.button("Generate Diagnostic Report"):
            with st.spinner("Analyzing telemetry heuristically..."):
                report = ["### Flight Diagnostic Summary\n"]
                
                # 1. Mission Status & Crash Detection
                if metrics['max_accel_m_s2'] > 30:
                    report.append("- **Status:** **CRASH OR SEVERE IMPACT DETECTED.** Extreme acceleration spikes found.")
                elif metrics['duration_sec'] < 10:
                    report.append("- **Status:** **ABORTED FLIGHT.** The mission was extremely short.")
                else:
                    report.append("- **Status:** **NOMINAL.** Mission completed without critical structural impacts.")
                
                report.append("\n### Deep Dive Analysis\n")
                
                # 2. Speed Analysis
                if metrics['max_horizontal_speed_m_s'] > 20:
                    report.append("- **Speed:** High-speed flight profile. Ensure motors and props are rated for this stress.")
                elif metrics['max_horizontal_speed_m_s'] < 2:
                    report.append("- **Speed:** Hovering or very slow inspection flight.")
                else:
                    report.append("- **Speed:** Normal cruising speed.")
                    
                # 3. Altitude Checks
                if metrics['max_climb_m'] > 120:
                    report.append("- **Altitude:** Exceeded 120m (standard regulatory limit in many EU/US regions). Check local airspace rules.")
                
                # 4. Maneuverability
                if 15 < metrics['max_accel_m_s2'] <= 30:
                    report.append("- **Dynamics:** Aggressive maneuvers, hard braking, or high wind turbulence detected.")
                    
                st.markdown("\n".join(report))
                st.success("Analysis completed locally.")

    except Exception as e:
        st.error("Error processing file")
        st.exception(e)