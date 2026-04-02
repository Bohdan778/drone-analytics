import sys
import os
import streamlit as st
import pandas as pd
import numpy as np

# 1. Додаємо кореневу папку проекту (DRONE-ANALYTICS) до шляхів пошуку Python.
# Це вирішить проблему з підсвіткою помилок і дозволить знаходити інші модулі.
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(root_dir)

# 2. Правильні абсолютні імпорти (з вказанням папок)
from analytics.metrics import prepare_trajectory_data
from visualization.plot_3d import plot_trajectory

st.title("🚁 Аналіз просторової траєкторії дрона")

# 1. Завантажуємо сирі дані (заміни 'telemetry.csv' на назву вашого файлу з даними)
# Додав кешування, щоб Streamlit не перечитував файл при кожному кліку

@st.cache_data
def load_data():
    # Генеруємо фейковий політ (спіраль), щоб протестувати 3D візуалізацію
    t = np.linspace(0, 100, 500) # 500 точок (секунд)
    
    # Симулюємо координати
    lat = 50.45 + 0.001 * t * np.cos(t / 5)
    lon = 30.52 + 0.001 * t * np.sin(t / 5)
    alt = 10 + 0.5 * t # дрон плавно набирає висоту
    
    # Симулюємо швидкості
    v_x = np.cos(t / 5) * 5
    v_y = np.sin(t / 5) * 5
    v_z = np.ones_like(t) * 0.5
    
    # Збираємо це все у табличку, яку очікує код твого друга
    df = pd.DataFrame({
        'time_sec': t,
        'lat': lat,
        'lon': lon,
        'alt': alt,
        'v_x': v_x,
        'v_y': v_y,
        'v_z': v_z
    })
    return df

df = load_data()

try:
    # 2. Робота твого друга: підготовка даних
    st.write("🔄 Обробка даних (WGS-84 -> ENU)...")
    prepared_df = prepare_trajectory_data(df)
    
    # 3. Твоя робота: створення 3D графіка
    st.write("📊 Побудова 3D візуалізації...")
    fig = plot_trajectory(prepared_df)
    
    # 4. Виводимо графік на екран
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"❌ Виникла помилка: {e}")