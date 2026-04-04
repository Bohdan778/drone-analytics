import sys
import os

from dotenv import load_dotenv
load_dotenv()

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import tempfile

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


from parser.parser import parse_ardupilot_log
from analytics.metrics import calculate_flight_metrics, prepare_trajectory_data
from visualization.plot_3d import plot_trajectory
import plotly.express as px

st.set_page_config(page_title="Drone Analyzer", layout="wide")

# Prevent browser auto-translation (fixes React 'removeChild' Node errors)
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

st.title("Drone Flight Analyzer")
st.caption("Upload ArduPilot log file (.bin / .log)")

uploaded_file = st.file_uploader("Upload flight log", type=["bin", "log"])

# @st.cache_data  # Тимчасово вимкнено, щоб завжди виконувався новий код!
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

        # --- TELEMETRY CHARTS ---
        st.subheader("📈 Telemetry Trends")
        tab_speed, tab_alt = st.tabs(["Speed over Time", "Altitude over Time"])
        
        with tab_speed:
            fig_speed = px.line(trajectory, x="time_sec", y="speed_3d", 
                                title="3D Speed vs Time", 
                                labels={"time_sec": "Time (s)", "speed_3d": "Speed (m/s)"},
                                template="plotly_dark")
            fig_speed.update_traces(line=dict(color="cyan", width=2))
            st.plotly_chart(fig_speed, use_container_width=True)
            
        with tab_alt:
            fig_alt = px.line(trajectory, x="time_sec", y="z_enu", 
                              title="Relative Altitude vs Time", 
                              labels={"time_sec": "Time (s)", "z_enu": "Altitude (m)"},
                              template="plotly_dark")
            fig_alt.update_traces(line=dict(color="magenta", width=2))
            st.plotly_chart(fig_alt, use_container_width=True)

        # --- RAW DATA ---
        with st.expander("Show raw data"):
            st.dataframe(df)

        st.subheader("Hybrid AI Diagnostics")
        st.caption("Rule-based heuristics combined with optional LLM deep analysis.")
        
        use_llm = st.checkbox("Enable Deep LLM Analysis (Requires Gemini API Key)", value=False)
        
        if st.button("Generate Diagnostic Report"):
            with st.spinner("Analyzing telemetry..."):
                report = ["### Flight Diagnostic Summary\n"]
                
                # 1. Smart Crash Detection (Acceleration Spike + High Vertical Speed)
                is_crash = metrics['max_accel_m_s2'] > 30 and metrics['max_vertical_speed_m_s'] > 5
                
                if is_crash:
                    report.append("- **Status:** **CRASH OR SEVERE IMPACT DETECTED.** Extreme acceleration spikes found.")
                    report.append("  - *Note: High impact combined with excessive vertical speed strongly indicates a collision.*")
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
                if 15 < metrics['max_accel_m_s2'] <= 30 and not is_crash:
                    report.append("- **Dynamics:** Aggressive maneuvers, hard braking, or high wind turbulence detected.")
                    
                st.markdown("\n".join(report))
                
                if not use_llm:
                    st.success("Analysis completed using Local Heuristics.")
                
                if use_llm:
                    api_key = os.environ.get("GEMINI_API_KEY")
                    if HAS_GENAI and api_key:
                        st.markdown("### 🧠 LLM Deep Insights")
                        import time
                        llm_success = False
                        last_error = ""
                        
                        for attempt in range(3):
                            try:
                                client = genai.Client(api_key=api_key)
                                prompt = f"Analyze drone flight. Max speed: {metrics['max_horizontal_speed_m_s']:.2f}m/s, max accel: {metrics['max_accel_m_s2']:.2f}m/s^2, max altitude: {metrics['max_climb_m']:.2f}m, duration: {metrics['duration_sec']:.2f}s. Keep it short, professional, and highlight any anomalies."
                                response = client.models.generate_content(
                                    model="gemini-2.0-flash",
                                    contents=prompt
                                )
                                st.success("✅ Analysis Mode: **Hybrid AI (LLM + Local)**")
                                st.info(response.text)
                                st.caption("Generated by Gemini 2.0 Flash")
                                llm_success = True
                                break
                            except Exception as e:
                                last_error = str(e)
                                time.sleep(2)
                                
                        if not llm_success:
                            st.warning("⚠️ LLM temporarily unavailable (API quota exceeded).")
                            st.info("✔ Analysis Mode: **Local AI Engine** (Graceful Fallback)\nThe local heuristics report above already contains the critical safety analysis.")
                            with st.expander("View API Error Details"):
                                st.error(last_error)
                    else:
                        st.warning("Cannot use LLM: API key is missing in .env or `google-genai` is not installed.")

    except Exception as e:
        st.error("Error processing file")
        st.exception(e)