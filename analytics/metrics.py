import pandas as pd
import numpy as np
from analytics.haversine import calculate_haversine_distance

def calculate_flight_metrics(df: pd.DataFrame) -> dict:
    df = df.copy()

    # 1. CLEAN DATA (Видаляємо "Нульовий острів" і порожні рядки)
    df = df.dropna(subset=['lat', 'lon', 'alt', 'acc_x', 'acc_y', 'acc_z'])
    df = df[(df['lat'].abs() > 1.0) & (df['lon'].abs() > 1.0)]
    df = df.reset_index(drop=True)

    if df.empty:
        raise ValueError("Немає валідних GPS-даних у лозі")

    # TIME
    df['time_sec'] = (df['time'] - df['time'].iloc[0]) / 1e6
    dt = df['time_sec'].diff().fillna(0)
    total_duration = df['time_sec'].iloc[-1]

    # 2. DISTANCE (ІЗ ЗАХИСТОМ ВІД ШУМУ ТА СТРИБКІВ)
    raw_distance_step = calculate_haversine_distance(df['lat'], df['lon'])
    
    # Фільтр 1: Захист від телепортації (якщо дрон "стрибнув" більше ніж на 50м за мілісекунду)
    safe_distance_step = np.where(raw_distance_step > 50, 0.0, raw_distance_step)
    
    # Фільтр 2: Захист від GPS-шуму (ігноруємо мікро-рухи менше 0.5 метра)
    safe_distance_step = np.where(safe_distance_step < 0.5, 0.0, safe_distance_step)
    
    total_distance = safe_distance_step.sum()

    # ACCELERATION MAGNITUDE
    acc_mag = np.sqrt(df['acc_x']**2 + df['acc_y']**2 + df['acc_z']**2)
    max_acceleration = acc_mag.max()

    # ALTITUDE
    max_altitude = df['alt'].max()
    min_altitude = df['alt'].min()
    max_climb = max_altitude - min_altitude

    # =========================================================
    # IMU -> VELOCITY (TRAPEZOIDAL INTEGRATION FIX)
    # =========================================================
    df[['v_x', 'v_y', 'v_z']] = 0.0

    # GRAVITY & TILT COMPENSATION
    acc_x_corrected = df['acc_x'] - df['acc_x'].mean()
    acc_y_corrected = df['acc_y'] - df['acc_y'].mean()
    g_est = df['acc_z'].iloc[:200].mean()
    acc_z_corrected = df['acc_z'] - g_est

    # TRAPEZOIDAL INTEGRATION
    df['v_x'] = ((0.5 * (acc_x_corrected + acc_x_corrected.shift(1).fillna(acc_x_corrected))) * dt).cumsum()
    df['v_y'] = ((0.5 * (acc_y_corrected + acc_y_corrected.shift(1).fillna(acc_y_corrected))) * dt).cumsum()
    df['v_z'] = ((0.5 * (acc_z_corrected + acc_z_corrected.shift(1).fillna(acc_z_corrected))) * dt).cumsum()

    # SPEEDS FROM IMU
    df['speed_horizontal'] = np.sqrt(df['v_x']**2 + df['v_y']**2)
    df['speed_3d'] = np.sqrt(df['v_x']**2 + df['v_y']**2 + df['v_z']**2)

    max_horizontal_speed = df['speed_horizontal'].max()
    max_vertical_speed = df['v_z'].abs().max()

    # SIMPLE DRIFT MITIGATION
    stationary_mask = acc_mag < 1.5
    df.loc[stationary_mask, ['v_x', 'v_y', 'v_z']] *= 0.98

    return {
        "duration_sec": float(total_duration),
        "total_distance_m": float(total_distance),
        "max_altitude_m": float(max_altitude),
        "max_climb_m": float(max_climb),
        "max_accel_m_s2": float(max_acceleration),
        "max_horizontal_speed_m_s": float(max_horizontal_speed),
        "max_vertical_speed_m_s": float(max_vertical_speed),
    }

# =========================================================
# TRAJECTORY PREPARATION
# =========================================================

def prepare_trajectory_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Також чистимо координати для 3D графіка від глітчів!
    df = df.dropna(subset=['lat', 'lon', 'alt'])
    df = df[(df['lat'].abs() > 1.0) & (df['lon'].abs() > 1.0)]

    df['time_sec'] = (df['time'] - df['time'].iloc[0]) / 1e6

    R = 6371000.0

    lat0 = np.radians(df['lat'].iloc[0])
    lon0 = np.radians(df['lon'].iloc[0])
    alt0 = df['alt'].iloc[0]

    lat = np.radians(df['lat'])
    lon = np.radians(df['lon'])

    df['x_enu'] = R * (lon - lon0) * np.cos(lat0)
    df['y_enu'] = R * (lat - lat0)
    df['z_enu'] = df['alt'] - alt0

    if {'v_x', 'v_y', 'v_z'}.issubset(df.columns):
        df['speed_3d'] = np.sqrt(df['v_x']**2 + df['v_y']**2 + df['v_z']**2)
    else:
        df['speed_3d'] = 0.0

    return df[['time_sec', 'x_enu', 'y_enu', 'z_enu', 'speed_3d']]