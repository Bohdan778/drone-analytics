import plotly.graph_objects as go

def plot_trajectory(df):
    # Беремо копію, щоб не зламати оригінальний датафрейм
    df = df.copy()

    # Перевіряємо, чи є потрібні колонки (ті, що видає prepare_trajectory_data)
    required_cols = ['x_enu', 'y_enu', 'z_enu']
    if not all(col in df.columns for col in required_cols):
         raise ValueError(f"DataFrame повинен містити колонки: {required_cols}")

    fig = go.Figure()

    # --- ОСЬ ТУТ ВСТАВЛЕНО НОВИЙ КОД ---
    # Визначаємо, за чим розфарбовувати лінію: за часом чи за швидкістю
    if 'time_sec' in df.columns:
        line_color = df['time_sec']
        colorbar_title = "Час (с)"
        show_colorbar = True
    elif 'speed_3d' in df.columns:
        line_color = df['speed_3d']
        colorbar_title = "Швидкість (м/с)"
        show_colorbar = True
    else:
        line_color = 'blue'
        colorbar_title = None
        show_colorbar = False
    # -----------------------------------

    fig.add_trace(go.Scatter3d(
        x=df['x_enu'],
        y=df['y_enu'],
        z=df['z_enu'],
        mode='lines',
        line=dict(
            width=5,
            color=line_color,
            colorscale='Turbo', # Яскрава палітра
            colorbar=dict(title=colorbar_title) if show_colorbar else None,
            showscale=show_colorbar
        ),
        name='Траєкторія дрона'
    ))

    # Додаємо підписи осей
    fig.update_layout(
        title="3D Траєкторія польоту дрона",
        scene=dict(
            xaxis_title='X (Схід), метри',
            yaxis_title='Y (Північ), метри',
            zaxis_title='Z (Висота), метри',
            aspectmode='manual', 
            aspectratio=dict(x=1, y=1, z=0.8)
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    return fig