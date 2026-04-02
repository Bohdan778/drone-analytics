import numpy as np
import pandas as pd

def calculate_haversine_distance(lat: pd.Series, lon: pd.Series) -> pd.Series:

    lat1 = np.radians(lat.shift(1).fillna(lat))
    lon1 = np.radians(lon.shift(1).fillna(lon))
    lat2 = np.radians(lat)
    lon2 = np.radians(lon)

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    R = 6371000
    
    return R * c