import pandas as pd
import numpy as np
from analytics.haversine import calculate_haversine_distance

def calculate_flight_metrics(df: pd.DataFrame) -> dict:
    df = df.copy()

    # 1. CLEAN DATA
    df = df.dropna(subset=['lat', 'lon', 'alt', 'acc_x', 'acc_y', 'acc_z'])
    df = df[(df['lat'].abs() > 1.0) & (df['lon'].abs() > 1.0)]
    
    # --- МЕДІАННИЙ СМАРТ-ФІЛЬТР (ВБИВЦЯ ГЛІТЧІВ) ---
    if not df.empty:
        lat_med = df['lat'].median()
        lon_med = df['lon'].median()
        
        # Поріг 0.1 градуса = ~11 км від центру. 
        # Достатньо для більшості локальних польотів.
        THRESHOLD = 0.1 
        df = df[(df['lat'] - lat_med).abs() < THRESHOLD]
        df = df[(df['lon'] - lon_med).abs() < THRESHOLD]
    # ----------------------------------------------
    
    df = df.reset_index(drop=True)

    if df.empty:
        raise ValueError("Немає валідних GPS-даних у лозі")

    # TIME
    df['time_sec'] = (df['time'] - df['time'].iloc[0]) / 1e6
    dt = df['time_sec'].diff().fillna(0)
    total_duration = df['time_sec'].iloc[-1]

    # 2. DISTANCE
    raw_distance_step = calculate_haversine_distance(df['lat'], df['lon'])
    safe_distance_step = np.where(raw_distance_step > 50, 0.0, raw_distance_step)
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
    # IMU -> VELOCITY
    # =========================================================
    df[['v_x', 'v_y', 'v_z']] = 0.0

    acc_x_corrected = df['acc_x'] - df['acc_x'].mean()
    acc_y_corrected = df['acc_y'] - df['acc_y'].mean()
    g_est = df['acc_z'].iloc[:200].mean() if len(df) > 200 else df['acc_z'].mean()
    acc_z_corrected = df['acc_z'] - g_est

    df['v_x'] = ((0.5 * (acc_x_corrected + acc_x_corrected.shift(1).fillna(acc_x_corrected))) * dt).cumsum()
    df['v_y'] = ((0.5 * (acc_y_corrected + acc_y_corrected.shift(1).fillna(acc_y_corrected))) * dt).cumsum()
    df['v_z'] = ((0.5 * (acc_z_corrected + acc_z_corrected.shift(1).fillna(acc_z_corrected))) * dt).cumsum()

    df['speed_horizontal'] = np.sqrt(df['v_x']**2 + df['v_y']**2)
    df['speed_3d'] = np.sqrt(df['v_x']**2 + df['v_y']**2 + df['v_z']**2)

    max_horizontal_speed = df['speed_horizontal'].max()
    max_vertical_speed = df['v_z'].abs().max()

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

    df = df.dropna(subset=['lat', 'lon', 'alt'])
    df = df[(df['lat'].abs() > 1.0) & (df['lon'].abs() > 1.0)]

    if df.empty:
        raise ValueError("Немає валідних GPS-даних після очищення")

    # --- СМАРТ-ФІЛЬТР ---
    lat_med = df['lat'].median()
    lon_med = df['lon'].median()
    
    THRESHOLD = 0.1
    df = df[(df['lat'] - lat_med).abs() < THRESHOLD]
    df = df[(df['lon'] - lon_med).abs() < THRESHOLD]
    
    df = df.reset_index(drop=True)

    if df.empty:
        raise ValueError("Після фільтрації глітчів не залишилося даних")

    df['time_sec'] = (df['time'] - df['time'].iloc[0]) / 1e6

    R = 6371000.0

    # --- РОЗУМНИЙ ЦЕНТР КООРДИНАТ ---
    # Нуль (0,0,0) на графіку тепер прив'язаний до центру польоту 
    # та мінімальної висоти, а не до першої точки.
    lat0 = np.radians(lat_med)
    lon0 = np.radians(lon_med)
    alt0 = df['alt'].min()

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