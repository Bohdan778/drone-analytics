import pytest
import pandas as pd
import plotly.graph_objects as go
from visualization.plot_3d import plot_trajectory


def test_plot_trajectory_returns_figure():
    """Checks that the visualization function returns a valid Plotly Figure."""
    mock_data = pd.DataFrame({
        'time_sec': [0, 1, 2, 3],
        'x_enu': [0, 10, 20, 30],
        'y_enu': [0, 10, 20, 30],
        'z_enu': [0, 5, 10, 15],
        'speed_3d': [0, 5, 5, 5]
    })
    
    fig = plot_trajectory(mock_data)
    
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 3  # Should be 3 layers: Trajectory, Start, End