import pandas as pd
from pymavlink import mavutil


def parse_ardupilot_log(file_path: str) -> pd.DataFrame:
    mlog = mavutil.mavlink_connection(file_path)

    records = {}

    while True:
        msg = mlog.recv_match(blocking=False)
        if msg is None:
            break

        msg_type = msg.get_type()
        time = getattr(msg, "TimeUS", None)

        if time is None:
            continue

        if time not in records:
            records[time] = {"time": time}

        if msg_type == "SIM":
            records[time].update({
                "lat": getattr(msg, "Lat", None),
                "lon": getattr(msg, "Lng", None),
                "alt": getattr(msg, "Alt", None)
            })

        elif msg_type == "IMU":
            records[time].update({
                "acc_x": getattr(msg, "AccX", None),
                "acc_y": getattr(msg, "AccY", None),
                "acc_z": getattr(msg, "AccZ", None)
            })

    df = pd.DataFrame(records.values())

    # сортуємо
    df = df.sort_values(by="time")

    # заповнюємо пропуски
    df = df.ffill()

    # залишаємо тільки потрібні колонки
    df = df[["time", "lat", "lon", "alt", "acc_x", "acc_y", "acc_z"]]

    return df


if __name__ == "__main__":
    df = parse_ardupilot_log("data/00000001.BIN")
    print(df.head())