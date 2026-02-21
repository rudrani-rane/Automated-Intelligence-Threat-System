import torch
import pandas as pd
from pathlib import Path
from sklearn.neighbors import NearestNeighbors
from torch_geometric.data import Data

PROCESSED_PATH = Path("data/processed/processed_asteroids.csv")


def build_graph(k_neighbors=5):

    # Load processed dataset
    df = pd.read_csv(PROCESSED_PATH)

    # Keep asteroid ID separately
    asteroid_ids = df["spkid"].values

    # Remove ID column from features
    features_df = df.drop(columns=["spkid"])

    # Convert to tensor
    x = torch.tensor(features_df.values, dtype=torch.float)

    # Build KNN graph
    nbrs = NearestNeighbors(n_neighbors=k_neighbors, metric="euclidean")
    nbrs.fit(features_df.values)

    distances, indices = nbrs.kneighbors(features_df.values)

    # Create edge list
    edge_list = []

    for i, neighbors in enumerate(indices):
        for j in neighbors:
            if i != j:
                edge_list.append([i, j])

    edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()

    # Create PyTorch Geometric Data object
    graph_data = Data(x=x, edge_index=edge_index)

    print("Graph built successfully!")
    print(graph_data)

    return graph_data


if __name__ == "__main__":
    build_graph()