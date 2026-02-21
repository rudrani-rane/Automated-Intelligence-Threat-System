# src/models/train.py

import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path

from src.graph.graph_builder import build_graph
from src.models.gnn_model import ATISGNN
from src.utils.visualization import (
    plot_embedding_galaxy,
    plot_uncertainty,
    plot_threat_density
)

# CONFIG
OUTPUT_DIR = Path("outputs/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Graph Smoothness Loss
def graph_smoothness_loss(mu, edge_index):
    src, dst = edge_index
    diff = mu[src] - mu[dst]
    return (diff.pow(2).sum(dim=1)).mean()


# Contrastive Orbital Separation Loss
def contrastive_orbital_loss(mu, pha_flags, margin=1.0):
    """
    Encourages separation between PHA and Non-PHA embeddings
    WITHOUT turning this into a classifier.
    """

    pha_mask = pha_flags == 1
    nonpha_mask = pha_flags == 0

    if pha_mask.sum() == 0 or nonpha_mask.sum() == 0:
        return torch.tensor(0.0, device=mu.device)

    pha_center = mu[pha_mask].mean(dim=0)
    nonpha_center = mu[nonpha_mask].mean(dim=0)

    dist = torch.norm(pha_center - nonpha_center)

    # Hinge-style separation
    loss = torch.relu(margin - dist)

    return loss


# Orbital Cluster Separation Score (Metric)
def orbital_cluster_separation(mu, pha_flags):

    pha_mask = pha_flags == 1
    nonpha_mask = pha_flags == 0

    if pha_mask.sum() == 0 or nonpha_mask.sum() == 0:
        return 0.0

    pha_center = mu[pha_mask].mean(dim=0)
    nonpha_center = mu[nonpha_mask].mean(dim=0)

    separation = torch.norm(pha_center - nonpha_center).item()
    return separation


# Risk Decoder Head
class RiskDecoder(nn.Module):
    def __init__(self, latent_dim):
        super().__init__()
        self.decoder = nn.Linear(latent_dim, 2)

    def forward(self, z):
        return self.decoder(z)


# TRAIN LOOP
def train():

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    graph = build_graph()
    graph = graph.to(device)

    model = ATISGNN(in_channels=graph.x.shape[1]).to(device)
    risk_head = RiskDecoder(latent_dim=32).to(device)

    optimizer = optim.Adam(
        list(model.parameters()) + list(risk_head.parameters()),
        lr=0.001
    )

    # Feature indices
    H_INDEX = 0
    MOID_INDEX = 10
    PHA_INDEX = 12

    history = {
        "loss": [],
        "risk_rmse": [],
        "sigma": [],
        "cluster_sep": []
    }

    # TRAINING
    for epoch in range(50):

        model.train()
        optimizer.zero_grad()

        mu, sigma = model(graph.x, graph.edge_index)

        # ----- Loss 1: Graph Smoothness -----
        smooth_loss = graph_smoothness_loss(mu, graph.edge_index)

        # ----- Loss 2: Uncertainty Regularization -----
        uncert_loss = sigma.mean()

        # ----- Loss 3: Risk Reconstruction -----
        preds = risk_head(mu)
        targets = graph.x[:, [MOID_INDEX, H_INDEX]]
        recon_loss = nn.MSELoss()(preds, targets)

        # ----- Loss 4: ⭐ Contrastive Orbital Separation -----
        pha_flags = graph.x[:, PHA_INDEX]
        contrast_loss = contrastive_orbital_loss(mu, pha_flags)

        # ----- TOTAL LOSS -----
        loss = (
            smooth_loss
            + 0.1 * uncert_loss
            + recon_loss
            + 0.2 * contrast_loss
        )

        loss.backward()
        optimizer.step()

        # METRICS 
        with torch.no_grad():

            risk_rmse = torch.sqrt(((preds - targets) ** 2).mean()).item()
            mean_sigma = sigma.mean().item()
            embed_norm = mu.norm(dim=1).mean().item()
            cluster_sep = orbital_cluster_separation(mu, pha_flags)

        history["loss"].append(loss.item())
        history["risk_rmse"].append(risk_rmse)
        history["sigma"].append(mean_sigma)
        history["cluster_sep"].append(cluster_sep)

        print(
            f"Epoch {epoch:03d} | "
            f"Loss {loss.item():.4f} | "
            f"RiskRMSE {risk_rmse:.4f} | "
            f"Sigma {mean_sigma:.4f} | "
            f"EmbedNorm {embed_norm:.4f} | "
            f"ClusterSep {cluster_sep:.4f}"
        )

        # VISUALIZATION
        if epoch % 5 == 0:
            plot_embedding_galaxy(mu, pha_flags, epoch)

    print("Training complete!")

    # Final visual analytics
    plot_uncertainty(history)
    plot_threat_density(mu, graph.x[:, MOID_INDEX])


if __name__ == "__main__":
    train()