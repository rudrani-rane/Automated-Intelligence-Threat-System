import pandas as pd
from sklearn.preprocessing import StandardScaler
from pathlib import Path
from load_data import load_raw_data

PROCESSED_PATH = Path("data/processed/processed_asteroids.csv")

def preprocess():

    df = load_raw_data()

    # Convert Y/N → 1/0
    df["neo"] = df["neo"].map({"Y":1,"N":0})
    df["pha"] = df["pha"].map({"Y":1,"N":0})

    # Drop unused text columns
    df = df.drop(columns=["full_name","pdes","class"])

    # Remove missing important values
    df = df.dropna(subset=["e","a","i","moid","rms"])

    # Filtering rules
    df = df[df["condition_code"] <= 5]
    df = df[df["data_arc"] > 100]
    df = df[df["moid"] < 0.5]

    features = [
        "H","e","a","q","i","om","w","ad","n","per_y",
        "moid","neo","pha","data_arc","condition_code","rms"
    ]

    scaler = StandardScaler()
    df[features] = scaler.fit_transform(df[features])

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)

    print("Processed dataset saved:", df.shape)

if __name__ == "__main__":
    preprocess()