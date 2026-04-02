import pandas as pd
import numpy as np
from pymavlink import mavutil


def parse_ardupilot_log(file_path: str) -> pd.DataFrame:
    """
    Parse ArduPilot log file and extract GPS + IMU data.

    Returns:
        pd.DataFrame with columns:
        time, lat, lon, alt, acc_x, acc_y, acc_z
    """

    mlog = mavutil.mavlink_connection(file_path)

    data = []
    
    gps_times = []
    imu_times = []

    current = {
        "time": None,
        "lat": None,
        "lon": None,
        "alt": None,
        "acc_x": None,
        "acc_y": None,
        "acc_z": None,
    }

    while True:
        msg = mlog.recv_match(blocking=False)
        if msg is None:
            break

        msg_type = msg.get_type()
        time = getattr(msg, "TimeUS", None)

        if time is None:
            continue

        current["time"] = time

        # --- GPS ---
        if msg_type in ["GPS", "GLOBAL_POSITION_INT"]:
            gps_times.append(time)
            lat = getattr(msg, "Lat", None) or getattr(msg, "lat", None)
            lon = getattr(msg, "Lng", None) or getattr(msg, "lon", None)
            alt = getattr(msg, "Alt", None) or getattr(msg, "alt", None)

            # Normalize GPS (if scaled)
            if lat and abs(lat) > 1000:
                lat = lat / 1e7
            if lon and abs(lon) > 1000:
                lon = lon / 1e7
            if alt and abs(alt) > 10000:
                alt = alt / 1000  # mm → meters

            current.update({
                "lat": lat,
                "lon": lon,
                "alt": alt
            })

        # --- IMU ---
        elif msg_type in ["IMU", "RAW_IMU", "SCALED_IMU2"]:
            imu_times.append(time)
            current.update({
                "acc_x": getattr(msg, "AccX", None) or getattr(msg, "xacc", None),
                "acc_y": getattr(msg, "AccY", None) or getattr(msg, "yacc", None),
                "acc_z": getattr(msg, "AccZ", None) or getattr(msg, "zacc", None),
            })

        # Save snapshot if full data available
        if all(v is not None for v in current.values()):
            data.append(current.copy())

    df = pd.DataFrame(data)

    if df.empty:
        raise ValueError("No valid telemetry data found in log")

    df = df.sort_values("time").reset_index(drop=True)

    # Calculate sampling frequency
    def calc_freq(times):
        if len(times) < 2:
            return 0
        times_sec = np.array(times) / 1e6
        diffs = np.diff(times_sec)
        avg_diff = np.mean(diffs[diffs > 0])
        return 1.0 / avg_diff if avg_diff > 0 else 0

    df.attrs['gps_freq_hz'] = calc_freq(gps_times)
    df.attrs['imu_freq_hz'] = calc_freq(imu_times)
    df.attrs['units'] = {
        'lat': 'degrees', 'lon': 'degrees', 'alt': 'meters',
        'acc_x': 'm/s^2 or G', 'acc_y': 'm/s^2 or G', 'acc_z': 'm/s^2 or G',
        'time': 'microseconds'
    }
    
    print(f"Sampling Rates -> GPS: {df.attrs['gps_freq_hz']:.2f} Hz, IMU: {df.attrs['imu_freq_hz']:.2f} Hz")
    print(f"Data Units: {df.attrs['units']}")

    return df