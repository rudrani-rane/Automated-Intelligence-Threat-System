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
def compute_threat_scores(mu, sigma, graph):

    # Feature indices (from preprocessing)
    H_INDEX = 0
    MOID_INDEX = 10

    # --- AI latent risk ---
    latent_risk = torch.norm(mu, dim=1)

    # --- uncertainty factor ---
    uncertainty = sigma.mean(dim=1)

    # --- orbital proximity risk ---
    moid = graph.x[:, MOID_INDEX]
    proximity_risk = 1 / (moid.abs() + 1e-3)

    # --- energy proxy (bigger asteroid = smaller H) ---
    H = graph.x[:, H_INDEX]
    energy_proxy = -H

    # Normalize components
    def normalize(x):
        return (x - x.min()) / (x.max() - x.min() + 1e-8)

    latent_risk = normalize(latent_risk)
    uncertainty = normalize(uncertainty)
    proximity_risk = normalize(proximity_risk)
    energy_proxy = normalize(energy_proxy)

    # Final hybrid threat score
    threat_score = (
        0.35 * latent_risk
        + 0.25 * uncertainty
        + 0.25 * proximity_risk
        + 0.15 * energy_proxy
    )

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