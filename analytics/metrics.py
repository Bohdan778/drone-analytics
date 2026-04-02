import sys
import os
# Примусово додаємо кореневу папку drone-analytics до шляхів пошуку Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

from parser.parser import parse_ardupilot_log
# Імпортуємо нашу функцію з сусіднього файлу
from haversine import calculate_haversine_distance

def calculate_flight_metrics(df: pd.DataFrame) -> dict:
    """
    Обчислює всі необхідні польотні метрики з DataFrame.
    """
    # 1. Очищення даних
    df = df.dropna(subset=['lat', 'lon', 'acc_x', 'acc_y', 'acc_z']).copy()
    df = df.reset_index(drop=True)

    # Переведення часу з мікросекунд у секунди та крок часу (dt)
    df['time_sec'] = (df['time'] - df['time'].iloc[0]) / 1e6
    dt = df['time_sec'].diff().fillna(0)

    # 2. Базові метрики
    total_duration = df['time_sec'].iloc[-1]
    max_climb = df['alt'].max() - df['alt'].min()

    acc_magnitude = np.sqrt(df['acc_x']**2 + df['acc_y']**2 + df['acc_z']**2)
    max_acceleration = acc_magnitude.max()

    # 3. Виклик функції Haversine з сусіднього модуля
    df['distance_step'] = calculate_haversine_distance(df['lat'], df['lon'])
    total_distance = df['distance_step'].sum()

    # 4. Трапецієвидне інтегрування
    # Базова компенсація гравітації по осі Z (медіана початку польоту)
    gravity_offset = df['acc_z'].iloc[:50].median()

    # Інтегрування для осей X та Y
    for axis in ['x', 'y']:
        a_curr = df[f'acc_{axis}']
        a_prev = a_curr.shift(1).fillna(0)
        df[f'v_{axis}'] = (0.5 * (a_curr + a_prev) * dt).cumsum()

    # Інтегрування для осі Z з відніманням гравітації
    a_z_curr = df['acc_z'] - gravity_offset
    a_z_prev = a_z_curr.shift(1).fillna(0)
    df['v_z'] = (0.5 * (a_z_curr + a_z_prev) * dt).cumsum()

    # Розрахунок швидкостей
    horizontal_speed = np.sqrt(df['v_x']**2 + df['v_y']**2)
    vertical_speed = df['v_z'].abs()

    return {
        "duration_sec": total_duration,
        "max_climb_m": max_climb,
        "max_accel_m_s2": max_acceleration,
        "total_distance_m": total_distance,
        "max_horizontal_speed_m_s": horizontal_speed.max(),
        "max_vertical_speed_m_s": vertical_speed.max()
    }

# --- БЛОК ТЕСТУВАННЯ ---
if __name__ == "__main__":
    print("Читаємо лог-файл...")
    # Шлях вказуємо відносно кореня проєкту: папка data -> файл 00000001.BIN
    df = parse_ardupilot_log("data/00000019.BIN")

    print("Рахуємо метрики...")
    result = calculate_flight_metrics(df)

    print("\n--- Результати польоту ---")
    for key, value in result.items():
        print(f"{key}: {round(value, 2)}")
