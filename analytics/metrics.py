import pandas as pd
import numpy as np

from analytics.haversine import calculate_haversine_distance

def calculate_flight_metrics(df: pd.DataFrame) -> dict:
    """
    Compute key flight metrics using GPS + IMU fusion.

    Key principles:
    - Distance → Haversine (GPS)
    - Velocity → obtained from IMU via trapezoidal integration (REQUIRED)
    - ENU motion assumption for short-range accuracy
    """

    df = df.copy()

    # --- CLEAN DATA ---
    df = df.dropna(subset=['lat', 'lon', 'alt', 'acc_x', 'acc_y', 'acc_z'])
    df = df.reset_index(drop=True)

    # --- TIME ---
    df['time_sec'] = (df['time'] - df['time'].iloc[0]) / 1e6
    dt = df['time_sec'].diff().fillna(0)

    total_duration = df['time_sec'].iloc[-1]

    # --- DISTANCE (GPS HAVERSINE) ---
    df['distance_step'] = calculate_haversine_distance(df['lat'], df['lon'])
    total_distance = df['distance_step'].sum()

    # --- ACCELERATION MAGNITUDE ---
    acc_mag = np.sqrt(df['acc_x']**2 + df['acc_y']**2 + df['acc_z']**2)
    max_acceleration = acc_mag.max()

    # --- ALTITUDE ---
    max_altitude = df['alt'].max()
    min_altitude = df['alt'].min()
    max_climb = max_altitude - min_altitude

    # =========================================================
    #  IMU → VELOCITY (TRAPEZOIDAL INTEGRATION)
    # =========================================================

    df[['v_x', 'v_y', 'v_z']] = 0.0

    # --- GRAVITY COMPENSATION ---
    # Estimate gravity from first stable samples
    g_est = df['acc_z'].iloc[:200].mean()
    acc_z_corrected = df['acc_z'] - g_est

    # --- TRAPEZOIDAL INTEGRATION ---
    for axis in ['x', 'y']:
        a = df[f'acc_{axis}']
        df[f'v_{axis}'] = (
            (0.5 * (a + a.shift(1).fillna(a))) * dt
        ).cumsum()

    df['v_z'] = (
        (0.5 * (acc_z_corrected + acc_z_corrected.shift(1).fillna(acc_z_corrected)))
        * dt
    ).cumsum()

    # --- SPEEDS FROM IMU (REQUIRED BY TASK) ---
    df['speed_horizontal'] = np.sqrt(df['v_x']**2 + df['v_y']**2)
    df['speed_3d'] = np.sqrt(df['v_x']**2 + df['v_y']**2 + df['v_z']**2)

    max_horizontal_speed = df['speed_horizontal'].max()
    max_vertical_speed = df['v_z'].abs().max()

    # =========================================================
    #  SIMPLE DRIFT MITIGATION (OPTIONAL BUT PRO)
    # =========================================================
    # If drone is stationary (low accel), slowly damp velocity
    stationary_mask = acc_mag < 1.5  # near gravity only
    df.loc[stationary_mask, ['v_x', 'v_y', 'v_z']] *= 0.98

    return {
        "duration_sec": float(total_duration),
        "total_distance_m": float(total_distance),

        "max_altitude_m": float(max_altitude),
        "max_climb_m": float(max_climb),

        "max_accel_m_s2": float(max_acceleration),

        #  IMPORTANT (IMU-based)
        "max_horizontal_speed_m_s": float(max_horizontal_speed),
        "max_vertical_speed_m_s": float(max_vertical_speed),
    }

# =========================================================
#  TRAJECTORY PREPARATION (UNCHANGED BUT CLEANED)
# =========================================================

def prepare_trajectory_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert WGS84 → ENU (local Cartesian system).

    Accurate for short-range flights.
    """

    df = df.copy()

    df['time_sec'] = (df['time'] - df['time'].iloc[0]) / 1e6

    required = ['lat', 'lon', 'alt']
    if not all(col in df.columns for col in required):
        raise ValueError(f"Missing required columns: {required}")

    R = 6371000.0

    lat0 = np.radians(df['lat'].iloc[0])
    lon0 = np.radians(df['lon'].iloc[0])
    alt0 = df['alt'].iloc[0]

    lat = np.radians(df['lat'])
    lon = np.radians(df['lon'])

    df['x_enu'] = R * (lon - lon0) * np.cos(lat0)
    df['y_enu'] = R * (lat - lat0)
    df['z_enu'] = df['alt'] - alt0

    # --- Use IMU-based speed if available ---
    if {'v_x', 'v_y', 'v_z'}.issubset(df.columns):
        df['speed_3d'] = np.sqrt(df['v_x']**2 + df['v_y']**2 + df['v_z']**2)
    else:
        df['speed_3d'] = 0.0

    return df[['time_sec', 'x_enu', 'y_enu', 'z_enu', 'speed_3d']]