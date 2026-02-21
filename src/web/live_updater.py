import asyncio
import torch
import numpy as np

from src.web.sbdb_client import fetch_live_asteroids
from src.web.state import model, graph
from src.risk.threat_engine import compute_threat_scores


# Global live buffers
LIVE_POINTS = {
    "mu": None,
    "threat": None
}


def preprocess_live_row(row):
    """
    Minimal normalization so new objects fit feature space.
    (Later we can load scaler from training pipeline.)
    """

    try:
        # Convert numeric values
        features = np.array([
            float(row[3]),  # H
            float(row[4]),  # e
            float(row[5]),  # a
            float(row[6]),  # q
            float(row[7]),  # i
            float(row[8]),  # om
            float(row[9]),  # w
            float(row[10]), # ad
            float(row[11]), # n
            float(row[12]), # per
            float(row[13]), # moid
        ])

        # Simple normalization placeholder
        features = (features - features.mean()) / (features.std() + 1e-6)

        return features

    except:
        return None


async def background_updater():

    print("Live SBDB updater started...")

    while True:

        rows = fetch_live_asteroids()

        if rows:

            processed = []

            for r in rows[:200]:  # limit batch size
                feat = preprocess_live_row(r)
                if feat is not None:
                    processed.append(feat)

            if processed:

                x = torch.tensor(processed, dtype=torch.float)

                # Forward pass through GNN encoder only
                with torch.no_grad():
                    mu, sigma = model(x, graph.edge_index[:,:1])

                threat = compute_threat_scores(mu, sigma, graph)

                LIVE_POINTS["mu"] = mu.detach().cpu().numpy()
                LIVE_POINTS["threat"] = threat.detach().cpu().numpy()

                print(f"Live update: {len(processed)} objects")

        await asyncio.sleep(30)  # refresh every 30 sec