import torch
import pandas as pd
from src.graph.graph_builder import build_graph
from src.models.gnn_model import ATISGNN
from src.risk.threat_engine import compute_threat_scores

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Initializing AI Threat System...")

# Load raw data for asteroid metadata
RAW_DF = pd.read_csv("data/raw/sbdb_query_results.csv")
PROCESSED_DF = pd.read_csv("data/processed/processed_asteroids.csv")

# Create mapping from processed index to asteroid metadata
ASTEROID_METADATA = RAW_DF.set_index("spkid").to_dict("index")
SPKIDS = PROCESSED_DF["spkid"].values

print(f"Loaded {len(SPKIDS)} asteroid records")

graph = build_graph().to(device)

model = ATISGNN(in_channels=graph.x.shape[1]).to(device)
model.eval()

with torch.no_grad():
    mu, sigma = model(graph.x, graph.edge_index)

threat_score = compute_threat_scores(mu, sigma, graph)

MU = mu.detach().cpu().numpy()
THREAT = threat_score.detach().cpu().numpy()
MOID = graph.x[:,10].detach().cpu().numpy()