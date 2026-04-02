import pandas as pd
import numpy as np

from analytics.haversine import calculate_haversine_distance

def calculate_flight_metrics(df: pd.DataFrame) -> dict:
    """
    Compute key flight metrics from telemetry data.

    Returns:
        dict with flight statistics
    """

    df = df.copy()

    df = df.dropna(subset=['lat', 'lon', 'acc_x', 'acc_y', 'acc_z'])
    df = df.reset_index(drop=True)

    df['time_sec'] = (df['time'] - df['time'].iloc[0]) / 1e6
    dt = df['time_sec'].diff()
    dt.iloc[0] = 0

    total_duration = df['time_sec'].iloc[-1]

    df['distance_step'] = calculate_haversine_distance(df['lat'], df['lon'])
    total_distance = df['distance_step'].sum()

    acc_mag = np.sqrt(df['acc_x']**2 + df['acc_y']**2 + df['acc_z']**2)
    max_acceleration = acc_mag.max()

    max_climb = df['alt'].max() - df['alt'].min()

    """
    THEORETICAL JUSTIFICATION:
    1. Double Integration of IMU (Acceleration -> Velocity -> Position):
       Integrating data from accelerometers accumulates errors over time (drift).
       Sensor noise and small biases during the first integration (into velocity)
       result in a linear error. Therefore, pure inertial navigation without correction quickly becomes inaccurate.
       For final velocity metrics, it is more reliable to use the derivative from GPS.
       However, an algorithmic implementation of trapezoidal integration is provided below to obtain
       velocity from the acceleration array.

    2. Quaternions vs Euler Angles:
       For correct spatial rotation and transformations, it is advantageous to use quaternions
       rather than Euler Angles, as the latter are prone to "gimbal lock" (loss
       of one degree of freedom when rotation axes align). Quaternions provide continuous interpolation.
    """
    df[['v_x', 'v_y', 'v_z']] = 0.0

    gravity_offset = df['acc_z'].iloc[:100].mean()
    acc_z_corrected = df['acc_z'] - gravity_offset

    for axis in ['x', 'y']:
        a = df[f'acc_{axis}']
        df[f'v_{axis}'] = (0.5 * (a + a.shift(1).fillna(0)) * dt).cumsum()

    df['v_z'] = (0.5 * (acc_z_corrected + acc_z_corrected.shift(1).fillna(0)) * dt).cumsum()

    pos_mask = df['distance_step'] > 0
    if pos_mask.any():
        pos_df = df[pos_mask]
        pos_dt = pos_df['time_sec'].diff()
        h_speed = pos_df['distance_step'] / pos_dt.replace(0, np.nan)
        max_h_speed = h_speed.clip(upper=50).max()
        if pd.isna(max_h_speed):
            max_h_speed = 0.0
    else:
        max_h_speed = 0.0

    alt_mask = df['alt'].diff().abs() > 0
    if alt_mask.any():
        alt_df = df[alt_mask]
        alt_dt = alt_df['time_sec'].diff()
        v_speed = alt_df['alt'].diff() / alt_dt.replace(0, np.nan)
        max_v_speed = v_speed.abs().clip(upper=50).max()
        if pd.isna(max_v_speed):
            max_v_speed = 0.0
    else:
        max_v_speed = 0.0

    return {
        "duration_sec": float(total_duration),
        "max_climb_m": float(max_climb),
        "max_accel_m_s2": float(max_acceleration),
        "total_distance_m": float(total_distance),
        "max_horizontal_speed_m_s": float(max_h_speed),
        "max_vertical_speed_m_s": float(max_v_speed),
    }

def prepare_trajectory_data(df):
    import numpy as np

    df = df.copy()

    """
    Mathematical conversion of global WGS-84 coordinates to a local Cartesian
    ENU (East-North-Up) system. Calculated relative to the starting point
    in meters. A simplified Flat Earth approximation is used,
    which is mathematically justified and accurate for short-distance local flights.
    """
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

    if {'v_x', 'v_y', 'v_z'}.issubset(df.columns):
        df['speed_3d'] = np.sqrt(df['v_x']**2 + df['v_y']**2 + df['v_z']**2)
    else:
        df['speed_3d'] = 0.0

    return df[['time_sec', 'x_enu', 'y_enu', 'z_enu', 'speed_3d']]