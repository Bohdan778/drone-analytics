import plotly.graph_objects as go
import numpy as np

def plot_trajectory(df, color_column="time_sec"):
    df = df.copy()

    required_cols = ['x_enu', 'y_enu', 'z_enu']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns: {required_cols}")

    if df.empty:
        raise ValueError("Empty DataFrame")

    if color_column in df.columns:
        color = df[color_column].fillna(0)
    else:
        color = np.linspace(0, 1, len(df))

    fig = go.Figure()

    fig.add_trace(go.Scatter3d(
        x=df['x_enu'],
        y=df['y_enu'],
        z=df['z_enu'],
        mode='lines',
        line=dict(
            width=6,
            color=color,
            colorscale='Turbo',
            colorbar=dict(
                title=color_column.upper(),
                thickness=15
            ),
            showscale=True
        ),
        hovertemplate=(
            "<b>Position</b><br>"
            "X: %{x:.1f} m<br>"
            "Y: %{y:.1f} m<br>"
            "Z: %{z:.1f} m<br>"
            "<extra></extra>"
        ),
        name="Trajectory"
    ))

    fig.add_trace(go.Scatter3d(
        x=[df['x_enu'].iloc[0]],
        y=[df['y_enu'].iloc[0]],
        z=[df['z_enu'].iloc[0]],
        mode='markers+text',
        marker=dict(size=8, color='green'),
        text=["START"],
        textposition="top center",
        name="Start"
    ))

    fig.add_trace(go.Scatter3d(
        x=[df['x_enu'].iloc[-1]],
        y=[df['y_enu'].iloc[-1]],
        z=[df['z_enu'].iloc[-1]],
        mode='markers+text',
        marker=dict(size=8, color='red'),
        text=["END"],
        textposition="top center",
        name="End"
    ))

    fig.update_layout(
        title={
            "text": "Drone Flight Trajectory",
            "x": 0.5
        },
        scene=dict(
            xaxis=dict(
                title='East (m)',
                showbackground=True,
                backgroundcolor="rgb(20,20,20)",
                gridcolor="gray"
            ),
            yaxis=dict(
                title='North (m)',
                showbackground=True,
                backgroundcolor="rgb(20,20,20)",
                gridcolor="gray"
            ),
            zaxis=dict(
                title='Altitude (m)',
                showbackground=True,
                backgroundcolor="rgb(20,20,20)",
                gridcolor="gray"
            ),
            aspectmode='cube', 
            camera=dict(
                eye=dict(x=1.8, y=1.8, z=1.2)
            )
        ),
        template="plotly_dark",
        margin=dict(l=0, r=0, b=0, t=40)
    )

    return fig