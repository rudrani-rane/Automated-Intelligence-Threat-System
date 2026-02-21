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

@app.on_event("startup")
async def start_background_tasks():
    """Initialize background live data updater"""
    asyncio.create_task(background_updater())