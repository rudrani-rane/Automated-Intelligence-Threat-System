import asyncio
import torch
import numpy as np

from src.web.sbdb_client import fetch_live_asteroids
from src.web.state import model, graph
from src.risk.threat_engine import compute_threat_scores


# Global live buffers
LIVE_POINTS = {
    "mu": None,
    "threat": None,
    "spkids": None,
    "names": None
}


def preprocess_live_row(row):
    """
    Minimal normalization so new objects fit feature space.
    Returns (features, spkid, name) tuple.
    """

    try:
        # Extract metadata
        spkid = str(row[0])  # spkid
        name = str(row[1])   # full_name
        
        # Convert numeric values (now shifted by 2 due to spkid and full_name fields)
        features = np.array([
            float(row[4]),  # H
            float(row[5]),  # e
            float(row[6]),  # a
            float(row[7]),  # q
            float(row[8]),  # i
            float(row[9]),  # om
            float(row[10]), # w
            float(row[11]), # ad
            float(row[12]), # n
            float(row[13]), # per
            float(row[14]), # moid
        ])

        # Simple normalization placeholder
        features = (features - features.mean()) / (features.std() + 1e-6)

        return (features, spkid, name)

    except Exception as e:
        print(f"Error processing row: {e}")
        return None


async def background_updater():

    print("Live SBDB updater started...")

    while True:

        rows = fetch_live_asteroids()

        if rows:

            processed = []
            spkids = []
            names = []

            for r in rows[:200]:  # limit batch size
                result = preprocess_live_row(r)
                if result is not None:
                    feat, spkid, name = result
                    processed.append(feat)
                    spkids.append(spkid)
                    names.append(name)

            if processed:

                x = torch.tensor(processed, dtype=torch.float)

                # Forward pass through GNN encoder only
                with torch.no_grad():
                    mu, sigma = model(x, graph.edge_index[:,:1])

                threat = compute_threat_scores(mu, sigma, graph)

                LIVE_POINTS["mu"] = mu.detach().cpu().numpy()
                LIVE_POINTS["threat"] = threat.detach().cpu().numpy()
                LIVE_POINTS["spkids"] = spkids
                LIVE_POINTS["names"] = names

                print(f"Live update: {len(processed)} objects")
                
                # Record snapshot for analytics
                try:
                    from src.web.analytics_engine import get_analytics_engine
                    from src.web.alert_notifier import get_alert_notifier
                    
                    # Record analytics snapshot
                    analytics_engine = get_analytics_engine()
                    if analytics_engine is not None:
                        analytics_engine.record_snapshot(
                            LIVE_POINTS["threat"],
                            np.array(spkids),
                            np.array(names)
                        )
                    
                    # Monitor for alerts
                    alert_notifier = get_alert_notifier()
                    if alert_notifier is not None:
                        await alert_notifier.monitor_threats(
                            LIVE_POINTS["threat"],
                            np.array(spkids),
                            np.array(names)
                        )
                except Exception as e:
                    print(f"Error recording analytics/alerts: {e}")

        await asyncio.sleep(30)  # refresh every 30 sec