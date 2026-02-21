import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, LayerNorm


class ATISGNN(nn.Module):
    def __init__(self, in_channels, hidden_channels=64, latent_dim=32, heads=4):
        super().__init__()

        # Initial projection
        self.input_proj = nn.Linear(in_channels, hidden_channels)

        # Graph Attention Layers
        self.gat1 = GATConv(hidden_channels, hidden_channels, heads=heads, concat=False)
        self.norm1 = LayerNorm(hidden_channels)

        self.gat2 = GATConv(hidden_channels, latent_dim, heads=heads, concat=False)
        self.norm2 = LayerNorm(latent_dim)

        # Probabilistic output heads
        self.mu_head = nn.Linear(latent_dim, latent_dim)
        self.sigma_head = nn.Linear(latent_dim, latent_dim)

    def forward(self, x, edge_index):

        # Initial encoding
        h0 = F.relu(self.input_proj(x))

        # First attention block
        h1 = self.gat1(h0, edge_index)
        h1 = self.norm1(h1 + h0)  # residual connection
        h1 = F.elu(h1)

        # Second attention block
        h2 = self.gat2(h1, edge_index)
        h2 = self.norm2(h2)
        h2 = F.elu(h2)

        # Probabilistic outputs
        mu = self.mu_head(h2)
        sigma = F.softplus(self.sigma_head(h2))  # ensures positive uncertainty

        return mu, sigma