#Sanity Check 
import torch
from src.graph.graph_builder import build_graph
from src.models.gnn_model import ATISGNN

graph = build_graph()

model = ATISGNN(in_channels=graph.x.shape[1])

mu, sigma = model(graph.x, graph.edge_index)

print("Mu shape:", mu.shape)
print("Sigma shape:", sigma.shape)