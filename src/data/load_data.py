import pandas as pd
from pathlib import Path

DATA_PATH = Path("data/raw/sbdb_query_results.csv")

def load_raw_data():
    df = pd.read_csv(DATA_PATH)
    return df

if __name__ == "__main__":
    df = load_raw_data()
    print("Loaded dataset shape:", df.shape)