import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, LayerNorm

# Column indices in processed_asteroids.csv (after spkid removed):
# 0=neo, 1=pha, 2=H, 3=epoch, 4=e, 5=a, 6=q, 7=i, 8=om, 9=w,
# 10=ad, 11=n, 12=per_y, 13=moid, 14=data_arc, 15=condition_code, 16=rms
# Orbital-only features start at index 2 (skip neo & pha to avoid label leakage).
ORBITAL_FEATURE_START = 2


class ATISGNN(nn.Module):
    """
    Graph Attention Network with:
    - Orbital-only input (neo/pha columns stripped) to prevent PHA label leakage
    - Probabilistic latent embedding (mu, sigma)
    - Dedicated PHA binary classifier head trained with weighted BCE loss
    """
    def __init__(self, in_channels, hidden_channels=64, latent_dim=32, heads=4):
        """
        in_channels: number of ORBITAL features (graph.x.shape[1] - ORBITAL_FEATURE_START)
        """
        super().__init__()

        # Initial projection
        self.input_proj = nn.Linear(in_channels, hidden_channels)

        # Graph Attention Layers
        self.gat1 = GATConv(hidden_channels, hidden_channels, heads=heads, concat=False)
        self.norm1 = LayerNorm(hidden_channels)

        self.gat2 = GATConv(hidden_channels, latent_dim, heads=heads, concat=False)
        self.norm2 = LayerNorm(latent_dim)

        # Probabilistic embedding heads
        self.mu_head    = nn.Linear(latent_dim, latent_dim)
        self.sigma_head = nn.Linear(latent_dim, latent_dim)

        # PHA binary classifier head (optimised with weighted BCEWithLogitsLoss)
        self.pha_head = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 1)
        )

    def forward(self, x, edge_index):
        """
        x: orbital-only features tensor  (N, in_channels)
           Pass graph.x[:, ORBITAL_FEATURE_START:] as input.
        Returns: mu, sigma, pha_logit  (pha_logit is raw pre-sigmoid)
        """
        # Initial encoding
        h0 = F.relu(self.input_proj(x))

        # First attention block with residual
        h1 = self.gat1(h0, edge_index)
        h1 = self.norm1(h1 + h0)
        h1 = F.elu(h1)

        # Second attention block
        h2 = self.gat2(h1, edge_index)
        h2 = self.norm2(h2)
        h2 = F.elu(h2)

        # Probabilistic embedding
        mu    = self.mu_head(h2)
        sigma = F.softplus(self.sigma_head(h2))  # ensures positive uncertainty

        # PHA classification logit
        pha_logit = self.pha_head(mu)

        return mu, sigma, pha_logit