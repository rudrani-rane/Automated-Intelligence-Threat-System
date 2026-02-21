import dash
from dash import dcc, html
import torch

from src.graph.graph_builder import build_graph
from src.models.gnn_model import ATISGNN
from src.risk.threat_engine import compute_threat_scores
from src.dashboard.visuals import (
    orbital_galaxy_figure,
    earth_radar_figure,
    watchlist_table
)


# LOAD SYSTEM STATE
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Launching Planetary Defense Dashboard...")

graph = build_graph()
graph = graph.to(device)

model = ATISGNN(in_channels=graph.x.shape[1]).to(device)
model.eval()

with torch.no_grad():
    mu, sigma = model(graph.x, graph.edge_index)

threat_score = compute_threat_scores(mu, sigma, graph)


# BUILD VISUALS
galaxy_fig = orbital_galaxy_figure(mu, threat_score)
radar_fig = earth_radar_figure(graph, threat_score)
watchlist_fig = watchlist_table()

# DASH APP
app = dash.Dash(__name__)

app.layout = html.Div(
    style={"backgroundColor": "black", "padding": "20px"},
    children=[

        html.H1(
            "🛰️ Automated Intelligence Threat System — Mission Control",
            style={"color": "white"}
        ),

        html.Div([
            dcc.Graph(figure=galaxy_fig),
        ]),

        html.Div([
            dcc.Graph(figure=radar_fig),
        ]),

        html.Div([
            dcc.Graph(figure=watchlist_fig),
        ])
    ]
)


# RUN SERVER
if __name__ == "__main__":
    app.run(debug=True)