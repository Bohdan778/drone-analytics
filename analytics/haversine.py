import numpy as np
import pandas as pd

def calculate_haversine_distance(lat: pd.Series, lon: pd.Series) -> pd.Series:
    # Convert to radians
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)

    # Shift for previous point
    lat_prev = lat_rad.shift(1)
    lon_prev = lon_rad.shift(1)

    # Differences
    dlat = lat_rad - lat_prev
    dlon = lon_rad - lon_prev

    # Haversine formula
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat_prev) * np.cos(lat_rad) * np.sin(dlon / 2.0) ** 2
    )

    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    R = 6371000  # Earth radius in meters

    distance = R * c

    # Replace NaN (first row) with 0
    return distance.fillna(0)