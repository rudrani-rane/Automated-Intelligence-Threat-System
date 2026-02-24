# src/models/train.py

import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path

from src.graph.graph_builder import build_graph
from src.models.gnn_model import ATISGNN, ORBITAL_FEATURE_START
from src.utils.visualization import (
    plot_embedding_galaxy,
    plot_uncertainty,
    plot_threat_density
)

# CONFIG
OUTPUT_DIR = Path("outputs/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_DIR = Path("outputs")
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = MODEL_DIR / "best_model.pth"


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

    # Orbital-only features: strip neo (col 0) and pha (col 1) to prevent label leakage
    # graph.x cols: 0=neo, 1=pha, 2=H, 3=epoch, 4=e, 5=a, 6=q, 7=i, 8=om, 9=w,
    #               10=ad, 11=n, 12=per_y, 13=moid, 14=data_arc, 15=condition_code, 16=rms
    x_orbital = graph.x[:, ORBITAL_FEATURE_START:]   # (N, 15)
    in_ch     = x_orbital.shape[1]

    PHA_INDEX = 1  # in full graph.x

    # PHA binary ground truth labels (z-scores: non-PHA ≈ -0.47, PHA ≈ +2.14)
    pha_labels = (graph.x[:, PHA_INDEX] > 0).float().to(device)   # (N,)
    n_pha    = pha_labels.sum().item()
    n_nonpha = len(pha_labels) - n_pha
    print(f"Dataset: {n_pha:.0f} PHA, {n_nonpha:.0f} non-PHA asteroids")

    # Positive class weight to counter class imbalance (~18% PHA)
    pos_w = torch.tensor([n_nonpha / (n_pha + 1e-6)], device=device)
    print(f"PHA positive class weight: {pos_w.item():.2f}x")

    # Pure classification model (no risk_head needed)
    model     = ATISGNN(in_channels=in_ch).to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.005)

    # Cosine annealing gives smooth LR decay without premature stalls
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=300, eta_min=1e-5)

    best_loss  = float('inf')
    num_epochs = 300
    history    = {"loss": [], "pha_acc": [], "lr": []}

    for epoch in range(num_epochs):

        model.train()
        optimizer.zero_grad()

        mu, sigma, pha_logit = model(x_orbital, graph.edge_index)

        # PRIMARY: weighted BCE — directly optimises PHA detection recall
        bce_loss = nn.BCEWithLogitsLoss(pos_weight=pos_w)(
            pha_logit.squeeze(), pha_labels
        )

        # SECONDARY: mild uncertainty penalty so sigma stays meaningful
        uncert_loss = sigma.mean()

        loss = bce_loss + 0.01 * uncert_loss

        loss.backward()
        optimizer.step()
        scheduler.step()

        with torch.no_grad():
            pha_pred  = (pha_logit.squeeze() > 0).float()
            pha_acc   = (pha_pred == pha_labels).float().mean().item()
            # recall specifically (PHAs correctly identified)
            tp        = ((pha_pred == 1) & (pha_labels == 1)).sum().item()
            pha_recall = tp / (n_pha + 1e-8)

        history["loss"].append(loss.item())
        history["pha_acc"].append(pha_acc)
        history["lr"].append(optimizer.param_groups[0]['lr'])

        if epoch % 10 == 0:
            print(
                f"Epoch {epoch:03d}/{num_epochs} | "
                f"BCE {bce_loss.item():.4f} | "
                f"Acc {pha_acc*100:.1f}% | "
                f"Recall {pha_recall*100:.1f}% | "
                f"LR {optimizer.param_groups[0]['lr']:.5f}"
            )

        if loss.item() < best_loss:
            best_loss = loss.item()
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': loss.item(),
                'history': history,
                'in_channels': in_ch,
                'orbital_feature_start': ORBITAL_FEATURE_START
            }, MODEL_PATH)
            if epoch % 10 == 0:
                print(f"    ✓ Best model saved (loss: {best_loss:.4f})")

    print("\n" + "="*70)
    print("✅ TRAINING COMPLETE!")
    print(f"✓ Best model saved to: {MODEL_PATH}")
    print(f"✓ Best loss: {best_loss:.4f}")
    print(f"✓ Total epochs: {num_epochs}")
    print("="*70 + "\n")

    return model, None, history


if __name__ == "__main__":
    train()

