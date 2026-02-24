import torch
import pandas as pd
from pathlib import Path
from src.graph.graph_builder import build_graph
from src.models.gnn_model import ATISGNN, ORBITAL_FEATURE_START
from src.risk.threat_engine import compute_threat_scores

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("\n" + "="*70)
print("🛰️  ATIS - Automated Threat Intelligence System")
print("="*70)
print(f"\nLoading NASA Asteroid Data...")

# Load raw data for asteroid metadata
RAW_DF = pd.read_csv("data/raw/sbdb_query_results.csv")
PROCESSED_DF = pd.read_csv("data/processed/processed_asteroids.csv")

# Create mapping from processed index to asteroid metadata
ASTEROID_METADATA = RAW_DF.set_index("spkid").to_dict("index")
SPKIDS = PROCESSED_DF["spkid"].values

print(f"✓ Loaded {len(SPKIDS):,} real asteroids from NASA JPL SBDB")

print(f"\nInitializing Graph Neural Network...")
graph = build_graph().to(device)
print(f"✓ Graph: {graph.x.shape[0]:,} nodes, {graph.edge_index.shape[1]:,} edges")

# Orbital-only features: strip neo (col 0) and pha (col 1) to prevent label leakage
x_orbital   = graph.x[:, ORBITAL_FEATURE_START:]   # (N, 15)
in_channels = x_orbital.shape[1]

model = ATISGNN(in_channels=in_channels).to(device)

# Try to load trained model
MODEL_PATH = Path("outputs/best_model.pth")
if MODEL_PATH.exists():
    try:
        checkpoint = torch.load(MODEL_PATH, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'], strict=False)
        print(f"✓ Loaded trained model from {MODEL_PATH}")
        print(f"  Trained for {checkpoint.get('epoch', 'unknown')} epochs")
        loss_val = checkpoint.get('loss')
        if loss_val is not None:
            print(f"  Best loss: {loss_val:.4f}")
    except Exception as e:
        print(f"Could not load model: {e}")
        print(f"   Using untrained model initialization")
else:
    print(f"ℹ️  No trained model found at {MODEL_PATH}")
    print(f"   Using untrained model (train with: python -m src.models.train)")

model.eval()

print(f"\n⚡ Running inference...")
with torch.no_grad():
    mu, sigma, pha_logit = model(x_orbital, graph.edge_index)

# Build raw (unscaled) MOID and H arrays aligned with SPKIDS
# These are in physical units: MOID in AU, H in mag — needed for meaningful threat scoring
import numpy as _np
_raw_idx = RAW_DF.set_index("spkid")
# Normalize index type (JPL spkids can be int or float in CSV)
_raw_idx.index = _raw_idx.index.astype(float)

_raw_moid = []
_raw_H = []
_raw_pha = []
for s in SPKIDS:
    key = float(s)
    if key in _raw_idx.index:
        row = _raw_idx.loc[key]
        _raw_moid.append(float(row["moid"]))
        _raw_H.append(float(row["H"]))
        _raw_pha.append(str(row["pha"]).strip().upper() == "Y")
    else:
        _raw_moid.append(0.05)
        _raw_H.append(22.0)
        _raw_pha.append(False)

RAW_MOID = _np.array(_raw_moid, dtype=float)   # MOID in AU — physically meaningful
RAW_H    = _np.array(_raw_H, dtype=float)        # Absolute magnitude — physical units
RAW_PHA  = _np.array(_raw_pha, dtype=bool)       # Potentially Hazardous Asteroid flag

threat_score = compute_threat_scores(mu, sigma, graph, raw_moid=RAW_MOID, raw_H=RAW_H)

MU     = mu.detach().cpu().numpy()
THREAT = threat_score.detach().cpu().numpy()
MOID   = RAW_MOID   # AU values — physically meaningful

# PHA_PROB: fit a Gradient Boosting classifier on orbital features for accurate PHA probability
# The GNN embedding is used as input so the classifier benefits from graph structure
print(f"\n🎯 Training PHA probability classifier on GNN embeddings + orbital features...")
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler as _SSc

# Features: GNN mu embedding + raw physical orbital params (MOID, H)
_pha_X = _np.hstack([
    MU,                            # (N, 32) GNN embeddings
    RAW_MOID.reshape(-1, 1),       # raw MOID in AU
    RAW_H.reshape(-1, 1),          # absolute magnitude
])
_pha_y = RAW_PHA.astype(int)

_pha_scaler = _SSc()
_pha_X_sc   = _pha_scaler.fit_transform(_pha_X)

_pha_clf = GradientBoostingClassifier(
    n_estimators=200,
    learning_rate=0.1,
    max_depth=5,
    subsample=0.8,
    random_state=42
)
_pha_clf.fit(_pha_X_sc, _pha_y)

PHA_PROB     = _pha_clf.predict_proba(_pha_X_sc)[:, 1]  # (N,) probability of PHA=1

# Cross-validated metrics for honest out-of-sample performance estimates
from sklearn.model_selection import StratifiedKFold, cross_validate
_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
_cv_res = cross_validate(
    GradientBoostingClassifier(n_estimators=200, learning_rate=0.1, max_depth=5,
                                subsample=0.8, random_state=42),
    _pha_X_sc, _pha_y, cv=_cv,
    scoring=['accuracy', 'precision', 'recall', 'f1', 'roc_auc'],
    n_jobs=-1
)
PHA_CV_METRICS = {
    'accuracy':  float(_cv_res['test_accuracy'].mean()),
    'precision': float(_cv_res['test_precision'].mean()),
    'recall':    float(_cv_res['test_recall'].mean()),
    'f1':        float(_cv_res['test_f1'].mean()),
    'roc_auc':   float(_cv_res['test_roc_auc'].mean()),
}
print(f"✓ PHA 5-fold CV — Acc: {PHA_CV_METRICS['accuracy']*100:.1f}%  "
      f"Recall: {PHA_CV_METRICS['recall']*100:.1f}%  "
      f"F1: {PHA_CV_METRICS['f1']*100:.1f}%  "
      f"ROC-AUC: {PHA_CV_METRICS['roc_auc']:.3f}")

print(f"✓ Computed threat scores for {len(SPKIDS):,} asteroids")
print(f"\nThreat Distribution:")
print(f"   - Critical (>70%): {(THREAT > 0.7).sum():,} asteroids")
print(f"   - High (50-70%):   {((THREAT >= 0.5) & (THREAT <= 0.7)).sum():,} asteroids")
print(f"   - Medium (30-50%): {((THREAT >= 0.3) & (THREAT < 0.5)).sum():,} asteroids")
print(f"   - Low (<30%):      {(THREAT < 0.3).sum():,} asteroids")
print(f"   - PHAs in dataset: {RAW_PHA.sum():,}")
print(f"\nSystem Ready! Access at http://localhost:8000")
print("="*70 + "\n")