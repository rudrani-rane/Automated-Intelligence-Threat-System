import torch
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from src.graph.graph_builder import build_graph
from src.models.gnn_model import ATISGNN


OUTPUT_DIR = Path("outputs/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WATCHLIST_PATH = Path("outputs/watchlist.csv")


# Threat Score Calculation
def compute_threat_scores(mu, sigma, graph, raw_moid=None, raw_H=None):
    """
    Compute hybrid threat score from GNN embeddings + physical orbital parameters.

    Parameters
    ----------
    mu       : GNN mean embedding tensor  (N, D)
    sigma    : GNN uncertainty tensor     (N, D)
    graph    : PyG Data object (graph.x contains StandardScaler-normalised features)
    raw_moid : numpy array of raw MOID values in AU (N,) — preferred over scaled graph feature
    raw_H    : numpy array of raw absolute magnitude H (N,)  — preferred over scaled graph feature
    """
    import numpy as np

    def normalize(x):
        return (x - x.min()) / (x.max() - x.min() + 1e-8)

    # --- AI latent risk (L2 norm of GNN embedding) ---
    latent_risk = normalize(torch.norm(mu, dim=1))

    # --- GNN uncertainty ---
    uncertainty = normalize(sigma.mean(dim=1))

    # --- Orbital proximity risk (use raw AU MOID when available) ---
    if raw_moid is not None:
        # Raw MOID in AU: values like 0.0001 to 0.5 AU
        # 1/(moid + eps) gives large values for close-approaching asteroids
        moid_au = torch.tensor(raw_moid, dtype=torch.float32)
        proximity_risk = normalize(1.0 / (moid_au.abs() + 1e-4))
    else:
        # Fallback: use scaled graph feature (less accurate)
        moid = graph.x[:, 10]
        proximity_risk = normalize(1.0 / (moid.abs() + 1e-3))

    # --- Energy proxy: smaller H = larger/brighter asteroid = more dangerous ---
    if raw_H is not None:
        H_tensor = torch.tensor(raw_H, dtype=torch.float32)
        # Low H value → large asteroid → high threat → energy_proxy should be HIGH
        # So we negate H: large (-H) means small H (big asteroid)
        energy_proxy = normalize(-H_tensor)
    else:
        H = graph.x[:, 0]
        energy_proxy = normalize(-H)

    # Final hybrid score — weights sum to 1.0
    threat_score = (
        0.35 * latent_risk
        + 0.25 * uncertainty
        + 0.25 * proximity_risk
        + 0.15 * energy_proxy
    )

    # Re-normalize composite to full [0, 1] range so top threats reach critical tier
    # (CLT otherwise compresses weighted sums of independent factors toward 0.5)
    threat_score = normalize(threat_score)

    return threat_score.detach()


# Visualization 1 — Radar Scatter
def plot_threat_radar(mu, threat_score):

    proj = mu.detach().cpu().numpy()
    score = threat_score.cpu().numpy()

    plt.figure(figsize=(8,8), facecolor="black")
    plt.style.use("dark_background")

    plt.scatter(
        proj[:,0],
        proj[:,1],
        c=score,
        s=5,
        cmap="inferno"
    )

    plt.colorbar(label="Threat Score")
    plt.title("Planetary Defense Radar View")

    plt.savefig(OUTPUT_DIR / "planetary_radar.png", dpi=300)
    plt.close()


# Visualization 2 — Earth Proximity Map
def plot_earth_proximity(graph, threat_score):

    MOID_INDEX = 10
    moid = graph.x[:, MOID_INDEX].detach().cpu().numpy()
    score = threat_score.detach().cpu().numpy()

    plt.figure(figsize=(7,6))
    plt.hexbin(moid, score, gridsize=60, cmap="inferno")
    plt.colorbar(label="Threat Density")

    plt.xlabel("MOID (Normalized)")
    plt.ylabel("Threat Score")
    plt.title("Earth Proximity Threat Map")

    plt.savefig(OUTPUT_DIR / "earth_proximity_map.png", dpi=300)
    plt.close()


# Visualization 3 — Top Threat Watchlist
def save_watchlist(threat_score, graph):

    scores = threat_score.detach().cpu().numpy()
    spkid = graph.sp_id if hasattr(graph, "sp_id") else list(range(len(scores)))

    df = pd.DataFrame({
        "spkid": spkid,
        "threat_score": scores
    })

    df = df.sort_values("threat_score", ascending=False)

    df.head(100).to_csv(WATCHLIST_PATH, index=False)

    print("\nTop 10 Threat Objects:")
    print(df.head(10))


# MAIN ENGINE
def run_threat_engine():

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("\nLaunching Threat Intelligence Engine...")

    graph = build_graph()
    graph = graph.to(device)

    model = ATISGNN(in_channels=graph.x.shape[1]).to(device)

    # Load trained weights if later added
    model.eval()

    with torch.no_grad():
        mu, sigma = model(graph.x, graph.edge_index)

    threat_score = compute_threat_scores(mu, sigma, graph)

    plot_threat_radar(mu, threat_score)
    plot_earth_proximity(graph, threat_score)
    save_watchlist(threat_score, graph)

    print("\nThreat Intelligence Analysis Complete.")


if __name__ == "__main__":
    run_threat_engine()