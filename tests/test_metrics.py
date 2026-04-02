import pytest
import pandas as pd
import numpy as np
from analytics.metrics import calculate_flight_metrics, prepare_trajectory_data


@pytest.fixture
def mock_telemetry_data():
    """Creates a fake DataFrame for metrics testing."""
    times = np.linspace(0, 10e6, 11)  # 10 seconds (in microseconds)
    return pd.DataFrame({
        'time': times,
        'lat': np.linspace(50.0, 50.01, 11),
        'lon': np.linspace(30.0, 30.01, 11),
        'alt': np.linspace(100, 120, 11),
        'acc_x': np.zeros(11),
        'acc_y': np.zeros(11),
        'acc_z': np.full(11, -9.81)
    })


def test_calculate_flight_metrics(mock_telemetry_data):
    metrics = calculate_flight_metrics(mock_telemetry_data)
    
    assert "duration_sec" in metrics
    assert metrics["duration_sec"] == 10.0
    assert metrics["max_climb_m"] == 20.0
    assert metrics["max_accel_m_s2"] >= 0.0
    assert metrics["total_distance_m"] > 0.0


def test_prepare_trajectory_data(mock_telemetry_data):
    trajectory_df = prepare_trajectory_data(mock_telemetry_data)
    
    assert "x_enu" in trajectory_df.columns
    assert "y_enu" in trajectory_df.columns
    assert "z_enu" in trajectory_df.columns
    assert trajectory_df["z_enu"].iloc[-1] == 20.0