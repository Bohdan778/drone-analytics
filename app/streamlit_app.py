import streamlit as st

# Імпорти ваших модулів
from parser.parser import parse_log
from analytics.metrics import calculate_metrics
from visualization.plot_3d import plot_trajectory


# ---------------- UI ----------------

st.set_page_config(page_title="Drone Analyzer", layout="wide")

st.title("🚁 Drone Flight Analyzer")

st.write("Завантаж лог файл польоту дрона (.bin або .log)")

uploaded_file = st.file_uploader("Обери файл", type=["bin", "log"])


# ---------------- LOGIC ----------------

if uploaded_file:

    try:
        # 1. Парсинг
        data = parse_log(uploaded_file)

        # 2. Метрики
        metrics = calculate_metrics(data)

        st.success("Файл успішно оброблено ✅")

        # ---------------- METRICS ----------------

        st.subheader("📊 Основні показники")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Макс швидкість",
                f"{metrics.get('max_speed', 0):.2f} m/s"
            )

        with col2:
            st.metric(
                "Дистанція",
                f"{metrics.get('distance', 0):.2f} m"
            )

        with col3:
            st.metric(
                "Макс висота",
                f"{metrics.get('max_altitude', 0):.2f} m"
            )

        # ---------------- 3D PLOT ----------------

        st.subheader("🛰️ 3D Траєкторія польоту")

        fig = plot_trajectory(data)
        st.plotly_chart(fig, use_container_width=True)

        # ---------------- RAW DATA (optional) ----------------

        with st.expander("Показати сирі дані"):
            st.write(data)

    except Exception as e:
        st.error(f"Помилка: {e}")