import pandas as pd
from visualization.plot_3d import plot_trajectory

# fake data (щоб перевірити)
data = {
    'lat': [50.45, 50.451, 50.452, 50.453],
    'lon': [30.52, 30.521, 30.522, 30.523],
    'alt': [100, 110, 120, 130]
}

df = pd.DataFrame(data)

fig = plot_trajectory(df)
fig.show()