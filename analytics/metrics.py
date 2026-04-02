import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

from parser.parser import parse_ardupilot_log
from analytics.haversine import calculate_haversine_distance

def calculate_flight_metrics(df: pd.DataFrame) -> dict:

    df.dropna(subset=['lat', 'lon', 'acc_x', 'acc_y', 'acc_z'], inplace=True)
    df.reset_index(drop=True, inplace=True)

    df['time_sec'] = (df['time'] - df['time'].iloc[0]) / 1e6
    dt = df['time_sec'].diff().fillna(0)

    total_duration = df['time_sec'].iloc[-1]
    max_climb = df['alt'].max() - df['alt'].min()

    acc_magnitude = np.sqrt(df['acc_x']**2 + df['acc_y']**2 + df['acc_z']**2)
    max_acceleration = acc_magnitude.max()

    df['distance_step'] = calculate_haversine_distance(df['lat'], df['lon'])
    total_distance = df['distance_step'].sum()

    gravity_offset = df['acc_z'].iloc[:50].median()

    for axis in ['x', 'y']:
        a_curr = df[f'acc_{axis}']
        a_prev = a_curr.shift(1).fillna(0)
        df[f'v_{axis}'] = (0.5 * (a_curr + a_prev) * dt).cumsum()

    a_z_curr = df['acc_z'] - gravity_offset
    a_z_prev = a_z_curr.shift(1).fillna(0)
    df['v_z'] = (0.5 * (a_z_curr + a_z_prev) * dt).cumsum()

    safe_dt = dt.replace(0, 1e-6) 
    
    raw_horizontal_speed = df['distance_step'] / safe_dt
    
    valid_h_speeds = raw_horizontal_speed[raw_horizontal_speed < 100]
    
    max_h_speed = valid_h_speeds.max() if not valid_h_speeds.empty else 0.0
    
    alt_step = df['alt'].diff().fillna(0)
    vertical_speed = (alt_step / safe_dt).abs()
    valid_v_speeds = vertical_speed[vertical_speed < 50]
    max_v_speed = valid_v_speeds.max() if not valid_v_speeds.empty else 0.0

    return {
        "duration_sec": total_duration,
        "max_climb_m": max_climb,
        "max_accel_m_s2": max_acceleration,
        "total_distance_m": total_distance,
        "max_horizontal_speed_m_s": max_h_speed,
        "max_vertical_speed_m_s": max_v_speed
    }

def prepare_trajectory_data(df: pd.DataFrame) -> pd.DataFrame:
    R = 6371000.0  

    lat0 = np.radians(df['lat'].iloc[0])
    lon0 = np.radians(df['lon'].iloc[0])
    alt0 = df['alt'].iloc[0]

    lat = np.radians(df['lat'])
    lon = np.radians(df['lon'])

    df['x_enu'] = R * (lon - lon0) * np.cos(lat0)
    df['y_enu'] = R * (lat - lat0)
    df['z_enu'] = df['alt'] - alt0

    if 'v_x' in df.columns and 'v_y' in df.columns and 'v_z' in df.columns:
        df['speed_3d'] = np.sqrt(df['v_x']**2 + df['v_y']**2 + df['v_z']**2)
    else:
        df['speed_3d'] = 0 

    columns_for_plot = ['time_sec', 'x_enu', 'y_enu', 'z_enu', 'speed_3d']
    return df[columns_for_plot]