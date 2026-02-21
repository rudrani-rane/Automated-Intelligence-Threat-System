from fastapi import APIRouter, HTTPException
from src.web.state import MU, THREAT, MOID
import numpy as np

router = APIRouter()

@router.get("/galaxy")
def galaxy_data():
    """3D coordinates and threat scores for orbital galaxy visualization"""
    return {
        "x": MU[:,0].tolist(),
        "y": MU[:,1].tolist(),
        "z": MU[:,2].tolist(),
        "threat": THREAT.tolist()
    }

@router.get("/radar")
def radar_data():
    """MOID vs threat score data for proximity radar"""
    return {
        "moid": MOID.tolist(),
        "threat": THREAT.tolist()
    }

@router.get("/watchlist")
def watchlist():
    """Top 50 ranked threats from watchlist CSV"""
    import pandas as pd
    df = pd.read_csv("outputs/watchlist.csv")
    return df.head(50).to_dict(orient="records")

from src.web.live_updater import LIVE_POINTS

@router.get("/live")
def live_data():
    """Real-time live asteroid detections from SBDB API"""
    if LIVE_POINTS["mu"] is None:
        return {"x": [], "y": [], "z": [], "threat": []}

    return {
        "x": LIVE_POINTS["mu"][:,0].tolist(),
        "y": LIVE_POINTS["mu"][:,1].tolist(),
        "z": LIVE_POINTS["mu"][:,2].tolist(),
        "threat": LIVE_POINTS["threat"].tolist()
    }

@router.get("/stats")
def system_stats():
    """System statistics and metrics"""
    return {
        "total_objects": len(THREAT),
        "high_risk_count": int(np.sum(THREAT > 0.7)),
        "medium_risk_count": int(np.sum((THREAT > 0.4) & (THREAT <= 0.7))),
        "low_risk_count": int(np.sum(THREAT <= 0.4)),
        "average_threat": float(np.mean(THREAT)),
        "max_threat": float(np.max(THREAT)),
        "min_threat": float(np.min(THREAT)),
        "average_moid": float(np.mean(MOID)),
        "model_status": "operational",
        "live_updates_active": LIVE_POINTS["mu"] is not None
    }

@router.get("/asteroid/{asteroid_id}")
def asteroid_details(asteroid_id: str):
    """Detailed information for a specific asteroid"""
    import pandas as pd
    
    # Load original data
    df = pd.read_csv("data/processed/processed_asteroids.csv")
    
    # Find asteroid by ID
    asteroid = df[df["spkid"] == int(asteroid_id)]
    
    if asteroid.empty:
        raise HTTPException(status_code=404, detail="Asteroid not found")
    
    idx = asteroid.index[0]
    
    return {
        "spkid": asteroid_id,
        "threat_score": float(THREAT[idx]),
        "embedding": MU[idx].tolist(),
        "moid": float(MOID[idx]),
        "orbital_elements": asteroid.iloc[0].to_dict()
    }

@router.get("/threat-distribution")
def threat_distribution():
    """Histogram data for threat score distribution"""
    bins = np.linspace(0, 1, 21)
    hist, edges = np.histogram(THREAT, bins=bins)
    
    return {
        "bins": edges.tolist(),
        "counts": hist.tolist()
    }

@router.get("/proximity-zones")
def proximity_zones():
    """Count of asteroids in different proximity zones"""
    critical = int(np.sum(MOID < 0.05))
    warning = int(np.sum((MOID >= 0.05) & (MOID < 0.15)))
    safe = int(np.sum(MOID >= 0.15))
    
    return {
        "critical": critical,
        "warning": warning,
        "safe": safe,
        "total": len(MOID)
    }

@router.get("/search")
def search_asteroids(query: str = ""):
    """Search asteroids by ID or name"""
    import pandas as pd
    
    if not query:
        return {"results": []}
    
    df = pd.read_csv("data/processed/processed_asteroids.csv")
    
    # Search by spkid
    results = df[df["spkid"].astype(str).str.contains(query, case=False)]
    
    return {
        "query": query,
        "count": len(results),
        "results": results.head(20).to_dict(orient="records")
    }
