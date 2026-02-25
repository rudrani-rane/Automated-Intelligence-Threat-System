
# 🛰️ ATIS — Automated Threat Intelligence System

**Planetary Defense Mission Control · Near-Earth Object Monitoring · v1.0**

ATIS is a research-grade planetary defense intelligence platform that ingests real NASA JPL asteroid data, runs a Graph Neural Network to learn orbital threat relationships, and surfaces results through an interactive multi-page mission-control dashboard.

---

## Demo

| Page | URL |
|---|---|
| Mission Control | `https://rudrani-rane-atis.hf.space/` |

---

## Features

### AI Threat Engine
- **Graph Attention Network (GAT)** trained on 12,054 Near-Earth Objects
- **GNN + Gradient Boosting hybrid classifier** — 5-fold cross-validated accuracy: **99.7%**, Recall: **99.1%**, F1: **99.2%**, ROC-AUC: **0.9999**
- Orbital-only input (neo/pha columns stripped to prevent label leakage)
- 17 orbital features → 32-dimensional latent embedding space
- Probabilistic output heads: mean (µ) + uncertainty (σ) per asteroid
- Hybrid threat score combining GNN intelligence with physical orbital parameters (MOID, H, eccentricity, inclination)
- PHA probability per asteroid from dedicated classifier head trained with weighted BCE loss

### Live Data Integration
- Real-time asteroid ingestion from **NASA JPL Small Body Database (SBDB) API**
- Background updater polling for new close-approach events
- WebSocket broadcast of live threat score changes to all connected clients

### Dashboard Pages (Version 1.0)

| Page | Description |
|---|---|
| **Home** | Mission overview with live dynamic stats from `/api/stats` — total objects, critical count, PHAs, low-risk count |
| **Galaxy** | Three.js WebGL 3D orbital visualization of all 12,054 NEOs color-coded by threat level |
| **Radar** | MOID vs. threat scatter plot — Earth proximity analysis |
| **Watchlist** | Ranked table of top 50 threat asteroids with sortable columns and JPL links |
| **Trajectory** | AI-powered orbital path forecast for any asteroid using Kepler propagation |
| **Analytics** | System statistics, model performance metrics, and distribution charts |
| **ML Dashboard** | GNN model explainability, 5-fold CV performance metrics, feature importance, embedding clusters, confusion matrix |
| **Alerts** | Real-time alert feed auto-generated from watchlist threat scores with live 25s refresh |
| **Orbital Mechanics** | Interactive Kepler equation solver with vis-viva, period, and true anomaly calculations; presets for Apophis, Bennu, Halley, Eros, Earth |
| **Impact Calculator** | Pi-scaling crater diameter, kinetic energy, and Palermo scale calculator with configurable impactor parameters |
| **N-Body Simulator** | Velocity Verlet gravitational simulation with configurable bodies and energy conservation display |
| **Approach Corridor** | Close approach corridor visualization per asteroid |
| **Impact Simulation** | Ground track and damage zone impact overlay |
| **Historical Timeline** | Historical close approach events charted over time (NASA CAD database) |

### Alert System
- Auto-generates alerts from watchlist when no history is available
- Classifies alerts as `critical`, `high`, `warning`, or `info` based on GNN threat score
- Live update events injected every 25 seconds from top-threat asteroids

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.x, FastAPI 0.129, Uvicorn |
| **ML / GNN** | PyTorch 2.10, PyTorch Geometric 2.7 |
| **Classifier** | Scikit-learn GradientBoostingClassifier (on GNN embeddings) |
| **Data / Science** | NumPy, Pandas, SciPy, Scikit-learn |
| **Charting** | Plotly 6.5 |
| **3D Rendering** | Three.js (WebGL, CDN) |
| **Frontend** | Vanilla JS, HTML5, CSS3 (custom design system) |
| **Templates** | Jinja2 |
| **Real-time** | WebSockets (websockets 16.0) |
| **Data Source** | NASA JPL SBDB API |

---

## Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
git clone <repo-url>
cd "Automated Intelligence Threat System"
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

### Run the Server

```bash
uvicorn src.web.main:app --port 8000
```

Open `http://localhost:8000` in your browser.

> **Note:** On first launch ATIS runs GNN inference, fits the PHA probability classifier, and computes 5-fold cross-validation scores. This takes ~60–90 seconds before the server accepts requests.

### Retrain the GNN (optional)

```bash
python -m src.models.train
```

---

## GNN Model Details

| Parameter | Value |
|---|---|
| Architecture | Graph Attention Network (GAT) |
| Input features | 15 orbital features (neo/pha stripped to prevent leakage) |
| Hidden dimensions | 64 (layer 1), 32 (layer 2) |
| Attention heads | 4 per layer |
| Embedding size | 32-dimensional |
| Training asteroids | 12,054 NEOs |
| PHA classifier | Gradient Boosting on GNN embeddings + raw MOID + H |
| CV Accuracy | **99.7%** (5-fold stratified) |
| CV Recall | **99.1%** |
| CV F1 | **99.2%** |
| ROC-AUC | **0.9999** |
| Output | µ (embedding mean) + σ (uncertainty) + PHA probability |

## Scientific Formulas & Algorithms

### Keplerian Orbital Mechanics
**Kepler's Equation (Eccentric Anomaly):**
```
E - e·sin(E) = M
```
Solved using Newton-Raphson iteration.

**Position Calculation:**
```
x = a·(cos(E) - e)
y = a·√(1-e²)·sin(E)
```

**Velocity (Vis-Viva Equation):**
```
v = √[μ·(2/r - 1/a)]
```

### Impact Energy
**Kinetic Energy:**
```
E = ½·m·v²
E_MT = E / (4.184 × 10¹⁵) joules
```

**Crater Diameter (Scaling Law):**
```
D_crater = 1.8 · ρ_a^0.11 · ρ_t^(-1/3) · L^0.13 · v^0.44 · g^(-0.22) · sin(θ)^(1/3)
```

### N-Body Simulation
**Gravitational Acceleration:**
```
a_i = Σ [G·m_j·(r_j - r_i) / |r_j - r_i|³]
```

**Verlet Integration:**
```
v(t+Δt/2) = v(t) + a(t)·Δt/2
r(t+Δt) = r(t) + v(t+Δt/2)·Δt
a(t+Δt) = F(r(t+Δt))/m
v(t+Δt) = v(t+Δt/2) + a(t+Δt)·Δt/2
```

### Anomaly Detection
**Z-Score:**
```
z = (x - μ) / σ
```

**Isolation Forest Score:**
```
s(x, n) = 2^(-E(h(x))/c(n))
```

---

## VERSION 2 - LATER

The following features are planned for the next major release and are **not yet available** in v1.0:

### Pages Reserved for v2
| Feature | Description |
|---|---|
| **Timeline (Time Machine)** | 3D time-based orbital propagation with ±10-year slider, asteroid tracking, and historical close-approach playback |
| **Multi-View** | Four synchronized panels: orbit path, close approaches, impact assessment, radar — currently placeholder |
| **Compare Tab** | Full side-by-side asteroid parameter comparison with radar charts and exportable diff |
| **Trends Tab** | Threat score trend analysis with time series forecasting, fully furnished with live data |
| **N-Body Simulation** | Running live gravitational simulation with real planetary ephemerides (currently static Velocity Verlet demo) |
| **Better Alert System** | Push notifications, user-configurable thresholds, email/webhook delivery, alert escalation rules |

### Planned Improvements
- **Proper location-based galaxy view** — real Keplerian orbital positions at J2000 epoch instead of z-score approximations
- Automated nightly sync with full JPL SBDB catalog
- MPC (Minor Planet Center) observation data for trajectory refinement
- Temporal GNN — model orbital evolution over time
- SHAP-based per-asteroid local explainability
- Monte Carlo impact probability distributions
- Deflection mission delta-V planner
- User accounts with personal watchlists and email alerts
- Docker/container packaging for one-command deployment
- Mobile-responsive layout pass
- AR/VR mode for the 3D galaxy view (WebXR)

---


Data sourced from NASA/JPL — see [JPL SBDB](https://ssd.jpl.nasa.gov/tools/sbdb_query.html) for data terms.
