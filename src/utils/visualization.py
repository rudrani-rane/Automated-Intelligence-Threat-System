import matplotlib.pyplot as plt
import torch
from sklearn.decomposition import PCA
from pathlib import Path

OUTPUT_DIR = Path("outputs/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Orbital Embedding Galaxy Plot
def plot_embedding_galaxy(mu, pha_flags, epoch):

    pca = PCA(n_components=2)
    proj = pca.fit_transform(mu.detach().cpu().numpy())

    plt.figure(figsize=(8,8), facecolor="black")
    plt.style.use("dark_background")

    pha_mask = pha_flags.cpu().numpy() == 1

    plt.scatter(
        proj[~pha_mask,0],
        proj[~pha_mask,1],
        s=2,
        alpha=0.3,
        label="Non-PHA"
    )

    plt.scatter(
        proj[pha_mask,0],
        proj[pha_mask,1],
        s=8,
        alpha=0.9,
        label="PHA"
    )

    plt.legend()
    plt.title(f"Asteroid Embedding Galaxy — Epoch {epoch}")

    plt.savefig(OUTPUT_DIR / f"galaxy_epoch_{epoch}.png", dpi=300)
    plt.close()


# Uncertainty Evolution Plot
def plot_uncertainty(history):

    plt.figure(figsize=(10,5))
    plt.plot(history["sigma"], label="Mean Sigma")
    plt.title("Uncertainty Evolution During Training")
    plt.legend()
    plt.savefig(OUTPUT_DIR / "uncertainty_curve.png")
    plt.close()


# Threat Density Map
def plot_threat_density(mu, moid):

    risk_proxy = torch.norm(mu.detach(), dim=1).cpu().numpy()
    moid = moid.detach().cpu().numpy()

    plt.figure(figsize=(7,6))
    plt.hexbin(moid, risk_proxy, gridsize=50, cmap="inferno")
    plt.colorbar(label="Density")
    plt.xlabel("MOID")
    plt.ylabel("Latent Risk Proxy")
    plt.title("Asteroid Threat Density Map")

    plt.savefig(OUTPUT_DIR / "threat_density.png", dpi=300)
    plt.close()