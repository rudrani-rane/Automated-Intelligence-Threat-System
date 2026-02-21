import plotly.graph_objs as go
import pandas as pd
import torch


# Orbital Galaxy View
def orbital_galaxy_figure(mu, threat_score):

    mu = mu.detach().cpu().numpy()
    score = threat_score.detach().cpu().numpy()

    fig = go.Figure()

    fig.add_trace(go.Scattergl(
        x=mu[:, 0],
        y=mu[:, 1],
        mode="markers",
        marker=dict(
            size=4,
            color=score,
            colorscale="Inferno",
            showscale=True,
            colorbar=dict(title="Threat")
        ),
        name="Asteroids"
    ))

    fig.update_layout(
        template="plotly_dark",
        title="🌌 Orbital Embedding Galaxy",
        xaxis_title="Latent X",
        yaxis_title="Latent Y"
    )

    return fig


# Earth Proximity Radar
def earth_radar_figure(graph, threat_score):

    MOID_INDEX = 10

    moid = graph.x[:, MOID_INDEX].detach().cpu().numpy()
    score = threat_score.detach().cpu().numpy()

    fig = go.Figure()

    fig.add_trace(go.Scattergl(
        x=moid,
        y=score,
        mode="markers",
        marker=dict(
            size=5,
            color=score,
            colorscale="Inferno",
        )
    ))

    fig.update_layout(
        template="plotly_dark",
        title="🌍 Earth Proximity Threat Radar",
        xaxis_title="MOID (Normalized)",
        yaxis_title="Threat Score"
    )

    return fig


# Watchlist Table
def watchlist_table():

    df = pd.read_csv("outputs/watchlist.csv")

    table = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns)),
        cells=dict(values=[df[col] for col in df.columns])
    )])

    table.update_layout(template="plotly_dark")

    return table