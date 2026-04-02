import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.metrics import calculate_flight_metrics
from analytics.metrics import prepare_trajectory_data
from parser.parser import parse_ardupilot_log


if __name__ == "__main__":
    print("Читаємо лог-файл...")
    
    df = parse_ardupilot_log("data/00000019.BIN")

    print("Рахуємо метрики...")
    
    result = calculate_flight_metrics(df)

    print("\n--- Результати польоту ---")
    for key, value in result.items():
        print(f"{key}: {round(value, 2)}")

    print("\nГотуємо дані для 3D траєкторії...")
    
    trajectory_df = prepare_trajectory_data(df)

    print("\n--- Дані для 3D графіка (перші 5 точок) ---")
    print(trajectory_df.tail())

    print("\n--- Максимальне віддалення від старту ---")
    print(f"Далі на Схід (X): {trajectory_df['x_enu'].max():.2f} м")
    print(f"Далі на Північ (Y): {trajectory_df['y_enu'].max():.2f} м")
    print(f"Макс. Висота (Z): {trajectory_df['z_enu'].max():.2f} м")