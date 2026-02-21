import torch
from src.graph.graph_builder import build_graph
from src.models.gnn_model import ATISGNN
from src.risk.threat_engine import compute_threat_scores

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Initializing AI Threat System...")

graph = build_graph().to(device)

model = ATISGNN(in_channels=graph.x.shape[1]).to(device)
model.eval()

with torch.no_grad():
    mu, sigma = model(graph.x, graph.edge_index)

threat_score = compute_threat_scores(mu, sigma, graph)

MU = mu.detach().cpu().numpy()
THREAT = threat_score.detach().cpu().numpy()
MOID = graph.x[:,10].detach().cpu().numpy()