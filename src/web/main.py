import asyncio
from src.web.live_updater import background_updater

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.web.api import router

app = FastAPI(
    title="ATIS - Automated Threat Intelligence System",
    description="Planetary Defense Mission Control • Real-Time NEO Monitoring",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(router, prefix="/api", tags=["API"])


@app.get("/")
def home(request: Request):
    """Mission Control Homepage"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/galaxy")
def galaxy_page(request: Request):
    """3D Orbital Galaxy Visualization"""
    return templates.TemplateResponse("galaxy.html", {"request": request})

@app.get("/radar")
def radar_page(request: Request):
    """Earth Proximity Radar Analysis"""
    return templates.TemplateResponse("radar.html", {"request": request})

@app.get("/watchlist")
def watchlist_page(request: Request):
    """Threat Watchlist Dashboard"""
    return templates.TemplateResponse("watchlist.html", {"request": request})

@app.get("/trajectory")
def trajectory_page(request: Request):
    """Trajectory Detection System"""
    return templates.TemplateResponse("trajectory.html", {"request": request})

@app.get("/orbital-simulator")
def orbital_simulator_page(request: Request):
    """Real Keplerian Orbital Path Simulator"""
    return templates.TemplateResponse("orbital_simulator.html", {"request": request})

@app.get("/time-machine")
def time_machine_page(request: Request):
    """Time-Based Asteroid Position Viewer"""
    return templates.TemplateResponse("time_machine.html", {"request": request})

@app.get("/analytics")
def analytics_page(request: Request):
    """Comprehensive Analytics Dashboard"""
    return templates.TemplateResponse("analytics.html", {"request": request})

@app.get("/multi-view")
def multi_view_page(request: Request):
    """Multi-Panel Synchronized Visualization Dashboard"""
    return templates.TemplateResponse("multi_view.html", {"request": request})

@app.get("/approach-corridor")
def approach_corridor_page(request: Request):
    """Close Approach Corridor Visualization"""
    return templates.TemplateResponse("approach_corridor.html", {"request": request})

@app.get("/impact-simulation")
def impact_simulation_page(request: Request):
    """Impact Ground Track and Damage Zone Simulation"""
    return templates.TemplateResponse("impact_simulation.html", {"request": request})

@app.get("/comparison")
def comparison_page(request: Request):
    """Asteroid Side-by-Side Comparison Tool"""
    return templates.TemplateResponse("comparison.html", {"request": request})

@app.get("/historical-timeline")
def historical_timeline_page(request: Request):
    """Historical Close Approach Timeline Analysis"""
    return templates.TemplateResponse("historical_timeline.html", {"request": request})

@app.get("/ml-dashboard")
def ml_dashboard_page(request: Request):
    """Machine Learning Performance & Explainability Dashboard"""
    return templates.TemplateResponse("ml_dashboard.html", {"request": request})

@app.get("/user-dashboard")
def user_dashboard_page(request: Request):
    """User Account Dashboard and Watchlist"""
    return templates.TemplateResponse("user_dashboard.html", {"request": request})

@app.get("/alerts")
def alerts_page(request: Request):
    """Real-Time Alert Monitoring Dashboard"""
    return templates.TemplateResponse("alerts.html", {"request": request})

@app.on_event("startup")
async def start_background_tasks():
    """Initialize background tasks and services"""
    from src.web.websocket_manager import broadcast_periodic_updates, connection_manager
    from src.web.alert_notifier import initialize_alert_notifier
    from src.web.analytics_engine import initialize_analytics_engine
    
    # Initialize systems
    initialize_alert_notifier(connection_manager)
    initialize_analytics_engine()
    
    # Start background tasks
    asyncio.create_task(background_updater())
    asyncio.create_task(broadcast_periodic_updates())