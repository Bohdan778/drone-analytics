import sys
import os
import tempfile

# Path fix
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st

# Setup page once
st.set_page_config(page_title="Drone Analyzer", layout="wide")

# Imports
from parser.parser import parse_ardupilot_log
from analytics.metrics import calculate_flight_metrics, prepare_trajectory_data
from visualization.plot_3d import plot_trajectory

# UI
st.title("Drone Flight Analyzer")
st.write("Завантаж лог файл польоту дрона (.bin або .log)")

uploaded_file = st.file_uploader("Обери файл", type=["bin", "log"])

# LOGIC
if uploaded_file:
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".BIN") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            # 1. Parse
            data = parse_ardupilot_log(tmp_path)

            # 2. Metrics
            metrics = calculate_flight_metrics(data)

            st.success("Файл успішно оброблено")

            # METRICS
            st.subheader("Основні показники")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Макс швидкість",
                    f"{metrics.get('max_horizontal_speed_m_s', 0):.2f} m/s"
                )

            with col2:
                st.metric(
                    "Дистанція",
                    f"{metrics.get('total_distance_m', 0):.2f} m"
                )

            with col3:
                st.metric(
                    "Макс висота",
                    f"{metrics.get('max_climb_m', 0):.2f} m"
                )

            # 3D PLOT
            st.subheader("3D Траєкторія польоту")
            
            # Safe plot execution
            try:
                prepared_df = prepare_trajectory_data(data)
                fig = plot_trajectory(prepared_df)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as plot_error:
                st.warning(f"Не вдалося побудувати 3D траєкторію: {plot_error}")

            # RAW DATA
            with st.expander("Показати сирі дані"):
                st.write(data)
                
        finally:
            # Cleanup
            try:
                os.remove(tmp_path)
            except PermissionError:
                pass

    except Exception as e:
        st.error(f"Помилка обробки файлу: {e}")


