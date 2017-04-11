import os


def read_csv_as_df(csv_path):
    import pandas as pd
    data = pd.read_csv(csv_path)
    return data


def get_csv():
    csv_path = os.path.join(os.path.dirname(__file__), "../IF1706_20161108.csv")
    return read_csv_as_df(csv_path)
