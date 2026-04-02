import sys
import os
<<<<<<< HEAD
import streamlit as st
from parser.parser import parse_log
from analytics.metrics import calculate_metrics, prepare_trajectory_data
from visualization.plot_3d import plot_trajectory

=======
import tempfile  # Додали для роботи з тимчасовими файлами

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

# Імпорти ваших модулів
from parser.parser import parse_ardupilot_log
from analytics.metrics import calculate_flight_metrics
# from visualization.plot_3d import plot_trajectory
>>>>>>> 7471c51 (Fix)

# 1. Фікс шляхів (щоб імпорти працювали без помилок)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# 2. Налаштування сторінки МАЄ БУТИ ПЕРШИМ!
st.set_page_config(page_title="Drone Analyzer", layout="wide")


# ---------------- UI ----------------
st.title("🚁 Drone Flight Analyzer")


# ---------------- UI ----------------

st.set_page_config(page_title="Drone Analyzer", layout="wide")

st.title("🚁 Drone Flight Analyzer")

st.write("Завантаж лог файл польоту дрона (.bin або .log)")

uploaded_file = st.file_uploader("Обери файл", type=["bin", "log"])

# ---------------- LOGIC ----------------
if uploaded_file:
    try:
        # Створюємо тимчасовий фізичний файл, щоб парсер не сварився на startswith
        with tempfile.NamedTemporaryFile(delete=False, suffix=".BIN") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            # 1. Парсинг (передаємо шлях до тимчасового файлу)
            data = parse_ardupilot_log(tmp_path)

            # 2. Метрики
            metrics = calculate_flight_metrics(data)

<<<<<<< HEAD
        # ---------------- METRICS ----------------
        st.subheader("📊 Основні показники")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Макс швидкість", f"{metrics.get('max_speed', 0):.2f} m/s")
        with col2:
            st.metric("Дистанція", f"{metrics.get('distance', 0):.2f} m")
        with col3:
            st.metric("Макс висота", f"{metrics.get('max_altitude', 0):.2f} m")

        # ---------------- 3D PLOT ----------------
        st.subheader("🛰️ 3D Траєкторія польоту")

        # ТВОЯ РОБОТА: Конвертуємо координати (WGS-84 -> ENU), потім малюємо!
        prepared_df = prepare_trajectory_data(data)
        fig = plot_trajectory(prepared_df)

        st.plotly_chart(fig, use_container_width=True)

        # ---------------- RAW DATA (optional) ----------------
        with st.expander("Показати сирі дані"):
            st.dataframe(data)
=======
            st.success("Файл успішно оброблено ✅")

            # ---------------- METRICS ----------------

            st.subheader("📊 Основні показники")

            col1, col2, col3 = st.columns(3)

            # Використовуємо ПРАВИЛЬНІ ключі, які повертає наше ядро аналітики
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

            # ---------------- 3D PLOT ----------------

            # st.subheader("🛰️ 3D Траєкторія польоту")
            # fig = plot_trajectory(data)
            # st.plotly_chart(fig, use_container_width=True)

            # ---------------- RAW DATA (optional) ----------------

            with st.expander("Показати сирі дані"):
                st.write(data)
                
        finally:
            # Пробуємо видалити, але ігноруємо помилку блокування Windows
            try:
                os.remove(tmp_path)
            except PermissionError:
                pass
>>>>>>> 7471c51 (Fix)

    except Exception as e:
        st.error(f"Помилка обробки файлу: {e}")
