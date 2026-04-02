import sys
import os
import streamlit as st

# 1. Фікс шляхів (щоб імпорти працювали без помилок)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# 2. Налаштування сторінки МАЄ БУТИ ПЕРШИМ!
st.set_page_config(page_title="Drone Analyzer", layout="wide")

# Імпорти ваших модулів
from parser.parser import parse_log
from analytics.metrics import calculate_metrics, prepare_trajectory_data
from visualization.plot_3d import plot_trajectory

# ---------------- UI ----------------
st.title("🚁 Drone Flight Analyzer")
st.write("Завантаж лог файл польоту дрона (.bin або .log)")

uploaded_file = st.file_uploader("Обери файл", type=["bin", "log"])

# ---------------- LOGIC ----------------
if uploaded_file:
    try:
        # 1. Парсинг (робота напарника)
        data = parse_log(uploaded_file)

        # 2. Метрики (робота напарника)
        metrics = calculate_metrics(data)

        st.success("Файл успішно оброблено ✅")

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
            # st.dataframe виглядає набагато краще для таблиць, ніж st.write
            st.dataframe(data) 

    except Exception as e:
        st.error(f"Помилка обробки файлу: {e}")