from fastapi import APIRouter, HTTPException, Query, Depends, Header, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.web.state import MU, THREAT, MOID, SPKIDS, ASTEROID_METADATA
from src.web.sbdb_client import get_asteroid_name, get_jpl_url
from src.utils.orbital_mechanics import (
    generate_orbital_path, calculate_orbital_position, calculate_velocity,
    absolute_magnitude_to_diameter, calculate_impact_energy, calculate_orbital_period
)
from src.utils.impact_calculator import ImpactCalculator
from src.utils.multi_source_data import multi_source
from src.utils.nbody_simulation import nbody_sim
from src.models.explainability import explainer
from src.models.ensemble_predictor import ensemble_predictor
from src.models.anomaly_detector import anomaly_detector
from src.web.auth import (
    auth_manager, User, UserCreate, UserLogin, Token,
    create_user, login_user, get_current_user
)
from src.web.websocket_manager import connection_manager, handle_client_message
import numpy as np
from typing import Optional
import uuid
import json
import datetime
import torch
from torch_geometric.data import Data

security = HTTPBearer()

router = APIRouter()
impact_calc = ImpactCalculator()


def get_asteroid_index(asteroid_id: str) -> int:
    """
    Helper function to get asteroid index from SPKID
    Raises HTTPException if asteroid not found
    """
    try:
        spkid = int(asteroid_id)
        idx = np.where(SPKIDS == spkid)[0]
        if len(idx) == 0:
            raise HTTPException(status_code=404, detail=f"Asteroid {asteroid_id} not found")
        return int(idx[0])
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid asteroid ID: {asteroid_id}")


@router.get("/galaxy")
def galaxy_data():
    """3D coordinates and threat scores for orbital galaxy visualization"""
    # Create list of objects with names and links
    objects = []
    for i in range(len(SPKIDS)):
        spkid = int(SPKIDS[i])
        objects.append({
            "spkid": spkid,
            "name": get_asteroid_name(spkid),
            "url": get_jpl_url(spkid),
            "x": float(MU[i, 0]),
            "y": float(MU[i, 1]),
            "z": float(MU[i, 2]),
            "threat": float(THREAT[i])
        })
    
    return {"objects": objects}

@router.get("/radar")
def radar_data():
    """MOID vs threat score data for proximity radar"""
    return {
        "moid": MOID.tolist(),
        "threat": THREAT.tolist()
    }

@router.get("/watchlist")
def watchlist():
    """Top 50 ranked threats with names and JPL links"""
    import pandas as pd
    
    # Load from CSV
    df = pd.read_csv("outputs/watchlist.csv")
    
    # Add names and URLs
    records = []
    for _, row in df.head(50).iterrows():
        spkid = int(row["spkid"])
        record = row.to_dict()
        record["name"] = get_asteroid_name(spkid)
        record["url"] = get_jpl_url(spkid)
        records.append(record)
    
    return {"watchlist": records}

from src.web.live_updater import LIVE_POINTS

@router.get("/live")
def live_data():
    """Real-time live asteroid detections from SBDB API"""
    if LIVE_POINTS["mu"] is None:
        return {"objects": []}

    objects = []
    for i in range(len(LIVE_POINTS["spkids"])):
        spkid = LIVE_POINTS["spkids"][i]
        objects.append({
            "spkid": spkid,
            "name": LIVE_POINTS["names"][i],
            "url": get_jpl_url(spkid),
            "x": float(LIVE_POINTS["mu"][i, 0]),
            "y": float(LIVE_POINTS["mu"][i, 1]),
            "z": float(LIVE_POINTS["mu"][i, 2]),
            "threat": float(LIVE_POINTS["threat"][i])
        })
    
    return {"objects": objects}

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
    
    # Find asteroid by ID in processed data
    try:
        spkid = int(asteroid_id)
        idx = np.where(SPKIDS == spkid)[0]
        
        if len(idx) == 0:
            raise HTTPException(status_code=404, detail="Asteroid not found")
        
        idx = idx[0]
        
        # Get raw metadata
        metadata = ASTEROID_METADATA.get(spkid, {})
        
        return {
            "spkid": asteroid_id,
            "name": get_asteroid_name(spkid),
            "url": get_jpl_url(spkid),
            "threat_score": float(THREAT[idx]),
            "embedding": MU[idx].tolist(),
            "moid": metadata.get("moid", "N/A"),
            "orbital_elements": {
                "eccentricity": metadata.get("e", "N/A"),
                "semi_major_axis": metadata.get("a", "N/A"),
                "inclination": metadata.get("i", "N/A"),
                "perihelion": metadata.get("q", "N/A"),
                "aphelion": metadata.get("ad", "N/A"),
                "period_years": metadata.get("per_y", "N/A"),
            },
            "classification": metadata.get("class", "Unknown"),
            "absolute_magnitude": metadata.get("H", "N/A"),
            "is_pha": metadata.get("pha", "N/A")
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asteroid ID")

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


@router.get("/orbital-path/{asteroid_id}")
def get_orbital_path(asteroid_id: str, num_points: int = Query(default=100, ge=10, le=500)):
    """Get complete orbital ellipse for an asteroid"""
    import pandas as pd
    
    try:
        spkid = int(asteroid_id)
        metadata = ASTEROID_METADATA.get(spkid)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Asteroid not found")
        
        # Extract orbital elements
        a = metadata.get("a", 1.0)
        e = metadata.get("e", 0.0)
        i = metadata.get("i", 0.0)
        om = metadata.get("om", 0.0)
        w = metadata.get("w", 0.0)
        
        # Generate orbital path
        path = generate_orbital_path(a, e, i, om, w, num_points)
        
        return {
            "spkid": asteroid_id,
            "name": get_asteroid_name(spkid),
            "orbital_elements": {
                "semi_major_axis_au": a,
                "eccentricity": e,
                "inclination_deg": i,
                "longitude_ascending_node_deg": om,
                "argument_perihelion_deg": w,
                "orbital_period_years": calculate_orbital_period(a)
            },
            "path": [{"x": p[0], "y": p[1], "z": p[2]} for p in path]
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asteroid ID")


@router.get("/asteroid-position/{asteroid_id}")
def get_asteroid_position_at_time(
    asteroid_id: str,
    time_offset_days: float = Query(default=0.0, description="Days from current epoch")
):
    """Calculate asteroid position at specific time"""
    
    try:
        spkid = int(asteroid_id)
        metadata = ASTEROID_METADATA.get(spkid)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Asteroid not found")
        
        # Extract orbital elements
        a = metadata.get("a", 1.0)
        e = metadata.get("e", 0.0)
        i = metadata.get("i", 0.0)
        om = metadata.get("om", 0.0)
        w = metadata.get("w", 0.0)
        
        # Calculate mean anomaly at requested time
        period_days = calculate_orbital_period(a) * 365.25
        M = (time_offset_days / period_days) * 360.0  # Mean anomaly in degrees
        
        # Get position and velocity
        pos = calculate_orbital_position(a, e, i, om, w, M)
        vel = calculate_velocity(a, e, i, om, w, M)
        
        return {
            "spkid": asteroid_id,
            "name": get_asteroid_name(spkid),
            "time_offset_days": time_offset_days,
            "position": {"x": pos[0], "y": pos[1], "z": pos[2]},
            "velocity": {"vx": vel[0], "vy": vel[1], "vz": vel[2]},
            "distance_from_sun_au": np.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2),
            "speed_au_per_day": np.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2)
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asteroid ID")


@router.get("/impact-assessment/{asteroid_id}")
def calculate_impact_assessment(asteroid_id: str):
    """Calculate potential impact effects for an asteroid"""
    
    try:
        spkid = int(asteroid_id)
        metadata = ASTEROID_METADATA.get(spkid)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Asteroid not found")
        
        # Get asteroid properties
        H = metadata.get("H", 20.0)  # Absolute magnitude
        diameter_km = absolute_magnitude_to_diameter(H) / 1000  # Convert to km
        diameter_m = diameter_km * 1000
        
        # Get orbital elements for velocity calculation
        a = metadata.get("a", 1.0)
        e = metadata.get("e", 0.0)
        i = metadata.get("i", 0.0)
        om = metadata.get("om", 0.0)
        w = metadata.get("w", 0.0)
        
        # Calculate typical impact velocity (simplified)
        vel = calculate_velocity(a, e, i, om, w, 0.0)
        velocity_au_day = np.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2)
        velocity_km_s = velocity_au_day * 149597870.7 / 86400  # Convert to km/s
        
        # Typical Earth impact velocity ~20 km/s
        impact_velocity = min(velocity_km_s + 11.2, 72.0)  # Add Earth escape velocity, cap at 72 km/s
        
        # Calculate impact effects
        effects = impact_calc.calculate_impact_effects(
            diameter_m=diameter_m,
            velocity_km_s=impact_velocity,
            density_g_cm3=2.6
        )
        
        # Compare to historical events
        comparisons = impact_calc.compare_to_historical(effects["energy_megatons"])
        
        # Assess mitigation
        idx = np.where(SPKIDS == spkid)[0]
        if len(idx) > 0:
            moid = metadata.get("moid", 0.1)
            warning_time = impact_calc.calculate_warning_time(moid, impact_velocity)
            mitigation = impact_calc.assess_mitigation_feasibility(
                warning_time["warning_time_years"],
                diameter_m
            )
        else:
            warning_time = {}
            mitigation = {}
        
        return {
            "spkid": asteroid_id,
            "name": get_asteroid_name(spkid),
            "asteroid_properties": {
                "absolute_magnitude": H,
                "estimated_diameter_m": diameter_m,
                "estimated_diameter_km": diameter_km,
                "impact_velocity_km_s": impact_velocity
            },
            "impact_effects": effects,
            "historical_comparisons": comparisons,
            "warning_time": warning_time,
            "mitigation_assessment": mitigation,
            "is_potentially_hazardous": metadata.get("pha", "N") == "Y"
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asteroid ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/time-machine")
def get_system_at_time(
    time_offset_days: float = Query(default=0.0, description="Days from current epoch"),
    limit: int = Query(default=100, ge=10, le=1000)
):
    """Get positions of multiple asteroids at a specific time"""
    
    positions = []
    
    for i, spkid in enumerate(SPKIDS[:limit]):
        metadata = ASTEROID_METADATA.get(int(spkid))
        
        if metadata:
            a = metadata.get("a", 1.0)
            e = metadata.get("e", 0.0)
            i = metadata.get("i", 0.0)
            om = metadata.get("om", 0.0)
            w = metadata.get("w", 0.0)
            
            period_days = calculate_orbital_period(a) * 365.25
            M = (time_offset_days / period_days) * 360.0
            
            pos = calculate_orbital_position(a, e, i, om, w, M)
            
            positions.append({
                "spkid": int(spkid),
                "name": get_asteroid_name(int(spkid)),
                "x": pos[0],
                "y": pos[1],
                "z": pos[2],
                "threat": float(THREAT[i]) if i < len(THREAT) else 0.0
            })
    
    # Earth position (circular orbit approximation)
    earth_angle = (time_offset_days / 365.25) * 360.0
    earth_x = np.cos(np.radians(earth_angle))
    earth_y = np.sin(np.radians(earth_angle))
    
    return {
        "time_offset_days": time_offset_days,
        "date": (datetime.datetime.now() + datetime.timedelta(days=time_offset_days)).isoformat(),
        "earth_position": {"x": earth_x, "y": earth_y, "z": 0.0},
        "asteroids": positions
    }


@router.get("/close-approaches/{asteroid_id}")
def get_close_approaches(
    asteroid_id: str,
    years_ahead: float = Query(default=10.0, ge=1.0, le=100.0),
    num_samples: int = Query(default=100, ge=10, le=1000)
):
    """Calculate future close approach distances"""
    
    try:
        spkid = int(asteroid_id)
        metadata = ASTEROID_METADATA.get(spkid)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Asteroid not found")
        
        a = metadata.get("a", 1.0)
        e = metadata.get("e", 0.0)
        i = metadata.get("i", 0.0)
        om = metadata.get("om", 0.0)
        w = metadata.get("w", 0.0)
        
        period_years = calculate_orbital_period(a)
        
        # Sample positions over time
        approaches = []
        min_distance = float('inf')
        min_distance_time = 0
        
        for sample_idx in range(num_samples):
            days = (sample_idx / num_samples) * years_ahead * 365.25
            
            period_days = period_years * 365.25
            M = (days / period_days) * 360.0
            
            pos = calculate_orbital_position(a, e, i, om, w, M)
            
            # Earth position (circular)
            earth_angle = (days / 365.25) * 360.0
            earth_x = np.cos(np.radians(earth_angle))
            earth_y = np.sin(np.radians(earth_angle))
            earth_z = 0.0
            
            # Calculate distance
            distance = np.sqrt(
                (pos[0] - earth_x)**2 +
                (pos[1] - earth_y)**2 +
                (pos[2] - earth_z)**2
            )
            
            if distance < min_distance:
                min_distance = distance
                min_distance_time = days
            
            approaches.append({
                "days_from_now": days,
                "date": (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d"),
                "distance_au": float(distance),
                "distance_km": float(distance * 149597870.7),
                "distance_lunar": float(distance * 389.17)  # Lunar distances
            })
        
        return {
            "spkid": asteroid_id,
            "name": get_asteroid_name(spkid),
            "orbital_period_years": period_years,
            "minimum_approach_distance_au": float(min_distance),
            "minimum_approach_time_days": float(min_distance_time),
            "minimum_approach_date": (datetime.datetime.now() + datetime.timedelta(days=min_distance_time)).strftime("%Y-%m-%d"),
            "approaches": approaches
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asteroid ID")


@router.get("/enhanced-stats")
def get_enhanced_statistics():
    """Enhanced system statistics with scientific metrics"""
    
    # Load raw data for additional stats
    import pandas as pd
    df_raw = pd.read_csv("data/raw/sbdb_query_results.csv")
    
    # Calculate size distribution
    diameters = [absolute_magnitude_to_diameter(H) for H in df_raw["H"].values[:1000]]
    
    # Orbital class counts
    orbital_classes = df_raw["class"].value_counts().to_dict() if "class" in df_raw.columns else {}
    
    # PHA count
    pha_count = int(df_raw["pha"].sum()) if "pha" in df_raw.columns else 0
    
    # Discovery statistics (if data_arc available)
    avg_observation_arc = float(df_raw["data_arc"].mean()) if "data_arc" in df_raw.columns else 0
    
    return {
        "total_objects": len(THREAT),
        "total_in_database": len(df_raw),
        "potentially_hazardous_count": pha_count,
        "threat_distribution": {
            "critical": int(np.sum(THREAT > 0.7)),
            "high": int(np.sum((THREAT > 0.5) & (THREAT <= 0.7))),
            "medium": int(np.sum((THREAT > 0.3) & (THREAT <= 0.5))),
            "low": int(np.sum((THREAT > 0.1) & (THREAT <= 0.3))),
            "minimal": int(np.sum(THREAT <= 0.1))
        },
        "size_distribution": {
            "planet_killers_gt_10km": int(sum(1 for d in diameters if d > 10000)),
            "large_1_10km": int(sum(1 for d in diameters if 1000 < d <= 10000)),
            "medium_100m_1km": int(sum(1 for d in diameters if 100 < d <= 1000)),
            "small_lt_100m": int(sum(1 for d in diameters if d <= 100))
        },
        "orbital_classes": orbital_classes,
        "observation_metrics": {
            "average_data_arc_days": avg_observation_arc,
            "well_observed_count": int(df_raw["data_arc"].gt(10000).sum()) if "data_arc" in df_raw.columns else 0
        },
        "model_performance": {
            "average_threat_score": float(np.mean(THREAT)),
            "std_dev_threat": float(np.std(THREAT)),
            "max_threat": float(np.max(THREAT)),
            "median_threat": float(np.median(THREAT))
        }
    }


@router.get("/multi-source/{asteroid_id}")
async def get_multi_source_data(asteroid_id: str):
    """
    Fetch and combine data from multiple authoritative sources
    - NASA JPL SBDB
    - Close Approach Database
    - CNEOS Sentry System
    """
    try:
        combined_data = await multi_source.get_combined_data(asteroid_id)
        return combined_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching multi-source data: {str(e)}")


@router.get("/historical-timeline/{asteroid_id}")
async def get_historical_timeline(asteroid_id: str):
    """
    Get comprehensive historical and future close approach timeline
    """
    try:
        timeline = await multi_source.get_historical_timeline(asteroid_id)
        
        if not timeline:
            return {
                "asteroid_id": asteroid_id,
                "timeline": [],
                "message": "No close approach data available"
            }
        
        # Add statistics
        historical = [t for t in timeline if not t["is_future"]]
        future_approaches = [t for t in timeline if t["is_future"]]
        
        closest_historical = min(historical, key=lambda x: x["distance_au"]) if historical else None
        closest_future = min(future_approaches, key=lambda x: x["distance_au"]) if future_approaches else None
        
        return {
            "asteroid_id": asteroid_id,
            "timeline": timeline,
            "statistics": {
                "total_approaches": len(timeline),
                "historical_count": len(historical),
                "future_count": len(future_approaches),
                "closest_historical": closest_historical,
                "closest_future": closest_future,
                "time_span_years": (
                    (datetime.datetime.fromisoformat(timeline[-1]["date"].replace(" ", "T")) - 
                     datetime.datetime.fromisoformat(timeline[0]["date"].replace(" ", "T"))).days / 365.25
                ) if len(timeline) > 1 else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching timeline: {str(e)}")


@router.get("/nbody-simulation/{asteroid_id}")
async def run_nbody_simulation(
    asteroid_id: str,
    duration_days: float = Query(365.0, description="Simulation duration in days", ge=1, le=3650)
):
    """
    Run N-body gravitational simulation for asteroid trajectory
    Includes perturbations from Jupiter, Saturn, and Earth
    """
    try:
        idx = np.where(SPKIDS == int(asteroid_id))[0]
        if len(idx) == 0:
            raise HTTPException(status_code=404, detail="Asteroid not found")
        
        idx = idx[0]
        
        # Get asteroid data
        metadata = ASTEROID_METADATA.get(int(asteroid_id), {})
        
        # Initial position (from MU - model latent space, approximate)
        initial_pos = np.array([
            float(MU[idx, 0]) * 5,  # Scale to AU
            float(MU[idx, 1]) * 5,
            float(MU[idx, 2]) * 5
        ])
        
        # Estimate initial velocity from orbital elements
        a = metadata.get("a", 1.5)
        e = metadata.get("e", 0.1)
        
        # Vis-viva equation for velocity magnitude
        r = np.linalg.norm(initial_pos)
        if r > 0:
            v_mag = np.sqrt(1.327e20 * (2/r - 1/a)) * 1.496e11 / 86400  # Convert to AU/day
        else:
            v_mag = 0.01
        
        # Approximate circular velocity direction
        initial_vel = np.array([-initial_pos[1], initial_pos[0], 0])
        if np.linalg.norm(initial_vel) > 0:
            initial_vel = initial_vel / np.linalg.norm(initial_vel) * v_mag
        else:
            initial_vel = np.array([v_mag, 0, 0])
        
        # Run simulation
        result = nbody_sim.simulate_asteroid_perturbation(initial_pos, initial_vel, duration_days)
        
        # Convert numpy arrays to lists for JSON
        trajectory_list = [pos.tolist() for pos in result["trajectory"]]
        jupiter_list = [pos.tolist() for pos in result["jupiter_positions"]]
        earth_list = [pos.tolist() for pos in result["earth_positions"]]
        
        return {
            "asteroid_id": asteroid_id,
            "asteroid_name": get_asteroid_name(int(asteroid_id)),
            "duration_days": duration_days,
            "trajectory": trajectory_list,
            "times": result["times"],
            "perturbations": result["perturbations"],
            "reference_bodies": {
                "jupiter": jupiter_list,
                "earth": earth_list
            },
            "simulation_info": {
                "time_step": 0.5,
                "num_points": len(trajectory_list),
                "includes_perturbations": True,
                "bodies_included": ["Sun", "Jupiter", "Saturn", "Earth"]
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@router.get("/gravitational-encounter/{asteroid_id}")
async def analyze_gravitational_encounter(
    asteroid_id: str,
    encounter_body: str = Query("Earth", description="Body to analyze encounter with (Earth, Jupiter, Mars)")
):
    """
    Analyze gravitational effects during close planetary encounter
    """
    try:
        idx = np.where(SPKIDS == int(asteroid_id))[0]
        if len(idx) == 0:
            raise HTTPException(status_code=404, detail="Asteroid not found")
        
        idx = idx[0]
        metadata = ASTEROID_METADATA.get(int(asteroid_id), {})
        
        # Position and velocity setup (similar to nbody simulation)
        initial_pos = np.array([
            float(MU[idx, 0]) * 5,
            float(MU[idx, 1]) * 5,
            float(MU[idx, 2]) * 5
        ])
        
        a = metadata.get("a", 1.5)
        r = np.linalg.norm(initial_pos)
        v_mag = np.sqrt(1.327e20 * (2/r - 1/a)) * 1.496e11 / 86400 if r > 0 else 0.01
        
        initial_vel = np.array([-initial_pos[1], initial_pos[0], 0])
        if np.linalg.norm(initial_vel) > 0:
            initial_vel = initial_vel / np.linalg.norm(initial_vel) * v_mag
        else:
            initial_vel = np.array([v_mag, 0, 0])
        
        # Run encounter analysis
        result = nbody_sim.get_close_encounter_effects(initial_pos, initial_vel, encounter_body)
        
        return {
            "asteroid_id": asteroid_id,
            "asteroid_name": get_asteroid_name(int(asteroid_id)),
            "encounter_body": encounter_body,
            "analysis": result,
            "interpretation": {
                "risk_level": "High" if result.get("significant_deflection", False) else "Low",
                "deflection_concern": result.get("closest_approach_au", 1.0) < 0.01,
                "monitoring_recommended": result.get("closest_approach_au", 1.0) < 0.05
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.get("/ml-explain/{asteroid_id}")
def explain_prediction(asteroid_id: str):
    """
    Get ML model explanation for a specific asteroid
    Returns SHAP values, feature importance, and attention weights
    """
    try:
        idx = get_asteroid_index(asteroid_id)
        
        # Create minimal graph data for explanation
        # In production, this should use the actual graph structure
        node_features = ASTEROID_METADATA[idx]
        
        # Create simple graph with self-loops for single node analysis
        edge_index = torch.tensor([[idx], [idx]], dtype=torch.long)
        edge_attr = torch.tensor([[1.0, 0.0, 0.0]], dtype=torch.float)
        
        graph_data = Data(
            x=torch.tensor(ASTEROID_METADATA, dtype=torch.float32),
            edge_index=edge_index,
            edge_attr=edge_attr
        )
        
        # Get explanation
        explanation = explainer.explain_prediction(graph_data, idx, asteroid_id)
        
        # Add asteroid metadata
        explanation['asteroid_name'] = get_asteroid_name(int(SPKIDS[idx]))
        explanation['threat_score'] = float(THREAT[idx])
        explanation['moid'] = float(MOID[idx])
        
        return explanation
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")


@router.get("/ensemble-predict/{asteroid_id}")
def ensemble_prediction(asteroid_id: str):
    """
    Get ensemble prediction combining GNN, Random Forest, XGBoost, and statistical models
    Returns individual predictions and weighted ensemble score
    """
    try:
        idx = get_asteroid_index(asteroid_id)
        
        # Create graph data
        edge_index = torch.tensor([[idx], [idx]], dtype=torch.long)
        edge_attr = torch.tensor([[1.0, 0.0, 0.0]], dtype=torch.float)
        
        graph_data = Data(
            x=torch.tensor(ASTEROID_METADATA, dtype=torch.float32),
            edge_index=edge_index,
            edge_attr=edge_attr
        )
        
        # Get ensemble prediction
        prediction = ensemble_predictor.predict_ensemble(graph_data, idx)
        
        # Add asteroid metadata
        prediction['asteroid_id'] = asteroid_id
        prediction['asteroid_name'] = get_asteroid_name(int(SPKIDS[idx]))
        prediction['actual_threat_score'] = float(THREAT[idx])
        prediction['moid'] = float(MOID[idx])
        
        return prediction
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ensemble prediction error: {str(e)}")


@router.get("/anomaly-score/{asteroid_id}")
def anomaly_detection(asteroid_id: str):
    """
    Detect if an asteroid has unusual characteristics
    Returns anomaly score and explanation
    """
    try:
        idx = get_asteroid_index(asteroid_id)
        
        # Get features for this asteroid
        features = ASTEROID_METADATA[idx]
        
        # Fit anomaly detector on full population if not already fitted
        if not anomaly_detector.is_fitted:
            anomaly_detector.fit(ASTEROID_METADATA)
        
        # Detect anomalies
        result = anomaly_detector.detect_anomaly(features, asteroid_id)
        
        # Add asteroid metadata
        result['asteroid_name'] = get_asteroid_name(int(SPKIDS[idx]))
        result['threat_score'] = float(THREAT[idx])
        result['moid'] = float(MOID[idx])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection error: {str(e)}")


@router.get("/ml-performance")
def ml_performance_metrics():
    """
    Get ML model performance metrics
    Returns accuracy, precision, recall, F1, ROC-AUC, etc.
    """
    try:
        # Calculate performance metrics on the dataset
        # This is a simplified version - in production, use a held-out test set
        
        predictions = THREAT  # GNN predictions
        
        # Create synthetic ground truth for demonstration (threshold-based)
        # In production, this should be actual labels
        ground_truth = (MOID < 0.05).astype(int)  # PHA criterion
        
        # Calculate metrics
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, f1_score,
            roc_auc_score, confusion_matrix, roc_curve, precision_recall_curve
        )
        
        # Binary threshold
        pred_binary = (predictions > 0.5).astype(int)
        
        # Metrics
        accuracy = accuracy_score(ground_truth, pred_binary)
        precision = precision_score(ground_truth, pred_binary, zero_division=0)
        recall = recall_score(ground_truth, pred_binary, zero_division=0)
        f1 = f1_score(ground_truth, pred_binary, zero_division=0)
        
        try:
            roc_auc = roc_auc_score(ground_truth, predictions)
        except:
            roc_auc = 0.0
        
        # Confusion matrix
        cm = confusion_matrix(ground_truth, pred_binary)
        
        # ROC curve
        fpr, tpr, thresholds = roc_curve(ground_truth, predictions)
        
        # Precision-Recall curve
        precision_curve, recall_curve, pr_thresholds = precision_recall_curve(ground_truth, predictions)
        
        # Threat distribution
        high_threat = int(np.sum(predictions > 0.7))
        medium_threat = int(np.sum((predictions > 0.4) & (predictions <= 0.7)))
        low_threat = int(np.sum(predictions <= 0.4))
        
        return {
            'metrics': {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1),
                'roc_auc': float(roc_auc)
            },
            'confusion_matrix': {
                'true_negative': int(cm[0, 0]),
                'false_positive': int(cm[0, 1]),
                'false_negative': int(cm[1, 0]),
                'true_positive': int(cm[1, 1])
            },
            'roc_curve': {
                'fpr': fpr.tolist(),
                'tpr': tpr.tolist(),
                'thresholds': thresholds.tolist()
            },
            'pr_curve': {
                'precision': precision_curve.tolist(),
                'recall': recall_curve.tolist(),
                'thresholds': pr_thresholds.tolist()
            },
            'threat_distribution': {
                'high': high_threat,
                'medium': medium_threat,
                'low': low_threat
            },
            'dataset_info': {
                'total_asteroids': len(predictions),
                'positive_class': int(np.sum(ground_truth)),
                'negative_class': int(len(ground_truth) - np.sum(ground_truth))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance metrics error: {str(e)}")


# ================================
# User Authentication & Management
# ================================

async def get_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current user from JWT token"""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


@router.post("/auth/register")
def register(user_create: UserCreate):
    """Register a new user account"""
    try:
        user = create_user(user_create)
        return {
            "success": True,
            "message": "User registered successfully",
            "user": user
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")


@router.post("/auth/login")
def login(user_login: UserLogin):
    """Login and receive JWT token"""
    try:
        token_data = login_user(user_login)
        return token_data
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")


@router.get("/auth/me")
def get_me(current_user: User = Depends(get_user_from_token)):
    """Get current user information"""
    return current_user


@router.post("/auth/watchlist/{asteroid_id}")
def add_to_watchlist_endpoint(
    asteroid_id: str,
    current_user: User = Depends(get_user_from_token)
):
    """Add asteroid to user's personal watchlist"""
    try:
        # Verify asteroid exists
        get_asteroid_index(asteroid_id)
        
        # Add to watchlist
        updated_user = auth_manager.update_watchlist(
            current_user.email, asteroid_id, "add"
        )
        
        return {
            "success": True,
            "message": f"Added asteroid {asteroid_id} to watchlist",
            "watchlist": updated_user.watchlist
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/auth/watchlist/{asteroid_id}")
def remove_from_watchlist_endpoint(
    asteroid_id: str,
    current_user: User = Depends(get_user_from_token)
):
    """Remove asteroid from user's watchlist"""
    try:
        updated_user = auth_manager.update_watchlist(
            current_user.email, asteroid_id, "remove"
        )
        
        return {
            "success": True,
            "message": f"Removed asteroid {asteroid_id} from watchlist",
            "watchlist": updated_user.watchlist
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/watchlist")
def get_user_watchlist(current_user: User = Depends(get_user_from_token)):
    """Get user's personalized watchlist with asteroid details"""
    try:
        asteroids = []
        
        for asteroid_id in current_user.watchlist:
            try:
                idx = get_asteroid_index(asteroid_id)
                spkid = int(SPKIDS[idx])
                
                asteroids.append({
                    "spkid": spkid,
                    "name": get_asteroid_name(spkid),
                    "url": get_jpl_url(spkid),
                    "threat_score": float(THREAT[idx]),
                    "moid": float(MOID[idx]),
                    "added_to_watchlist": True
                })
            except:
                # Skip if asteroid not found
                continue
        
        # Sort by threat score (highest first)
        asteroids.sort(key=lambda x: x['threat_score'], reverse=True)
        
        return {
            "user": current_user.username,
            "count": len(asteroids),
            "watchlist": asteroids
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/auth/preferences")
def update_preferences(
    preferences: dict,
    current_user: User = Depends(get_user_from_token)
):
    """Update user preferences"""
    try:
        updated_user = auth_manager.update_preferences(
            current_user.email, preferences
        )
        
        return {
            "success": True,
            "message": "Preferences updated",
            "preferences": updated_user.preferences
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/auth/alert-settings")
def update_alert_settings(
    alert_settings: dict,
    current_user: User = Depends(get_user_from_token)
):
    """Update user alert notification settings"""
    try:
        updated_user = auth_manager.update_alert_settings(
            current_user.email, alert_settings
        )
        
        return {
            "success": True,
            "message": "Alert settings updated",
            "alert_settings": updated_user.alert_settings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================
# WebSocket Real-Time Updates
# ================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates
    Supports: threat updates, watchlist, alerts, system status
    """
    connection_id = str(uuid.uuid4())
    
    try:
        await connection_manager.connect(websocket, connection_id)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client message
            await handle_client_message(message, connection_id)
            
    except WebSocketDisconnect:
        connection_manager.disconnect(connection_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        connection_manager.disconnect(connection_id)


@router.get("/ws/stats")
def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return {
        'active_connections': connection_manager.get_connection_count(),
        'subscriptions': connection_manager.get_subscription_stats(),
        'topics': list(connection_manager.subscriptions.keys())
    }


# ================================
# Alert Notification System
# ================================

@router.get("/alerts/history")
async def get_alert_history(limit: int = 50):
    """
    Get recent alert history
    
    Args:
        limit: Maximum number of alerts to return (default: 50)
    
    Returns:
        List of recent alerts with details
    """
    from src.web.alert_notifier import get_alert_notifier
    
    notifier = get_alert_notifier()
    if notifier is None:
        return {"alerts": []}
    
    alerts = notifier.get_alert_history(limit)
    return {"alerts": alerts, "count": len(alerts)}


@router.get("/alerts/stats")
async def get_alert_stats():
    """
    Get alert statistics
    
    Returns:
        Alert counts by severity level
    """
    from src.web.alert_notifier import get_alert_notifier
    
    notifier = get_alert_notifier()
    if notifier is None:
        return {"total": 0, "critical": 0, "high": 0, "medium": 0, "info": 0}
    
    stats = notifier.get_alert_stats()
    return stats


@router.post("/alerts/test")
async def send_test_alert(level: str = "info", message: str = "Test alert"):
    """
    Send a test alert (for development/testing)
    
    Args:
        level: Alert level (info, warning, error, critical)
        message: Alert message
    
    Returns:
        Success confirmation
    """
    from src.web.alert_notifier import get_alert_notifier
    
    notifier = get_alert_notifier()
    if notifier is None:
        raise HTTPException(status_code=503, detail="Alert notifier not initialized")
    
    await notifier.send_system_alert(message, level)
    
    return {
        "success": True,
        "message": "Test alert sent",
        "level": level
    }


# ================================
# Analytics & Historical Trends
# ================================

@router.get("/analytics/statistics")
async def get_system_statistics():
    """
    Get overall system statistics
    
    Returns:
        High-level statistics about monitored objects
    """
    from src.web.analytics_engine import get_analytics_engine
    
    engine = get_analytics_engine()
    if engine is None:
        return {
            'snapshots': 0,
            'total_objects': 0,
            'avg_threat': 0,
            'critical_count': 0,
            'high_count': 0,
            'monitoring_duration_days': 0
        }
    
    return engine.get_system_statistics()


@router.get("/analytics/trends/{spkid}")
async def get_object_trend(spkid: str, days: int = 7):
    """
    Get threat trend for a specific object
    
    Args:
        spkid: Object SPKID identifier
        days: Number of days to analyze (default: 7)
    
    Returns:
        Trend data with statistics
    """
    from src.web.analytics_engine import get_analytics_engine
    
    engine = get_analytics_engine()
    if engine is None:
        return {'spkid': spkid, 'data_points': 0, 'trend': []}
    
    return engine.get_threat_trends(spkid, days)


@router.get("/analytics/movers")
async def get_top_movers(limit: int = 10, direction: str = 'increase'):
    """
    Get objects with largest threat changes
    
    Args:
        limit: Maximum number of results (default: 10)
        direction: 'increase' or 'decrease' (default: 'increase')
    
    Returns:
        List of top movers
    """
    from src.web.analytics_engine import get_analytics_engine
    
    if direction not in ['increase', 'decrease']:
        raise HTTPException(status_code=400, detail="Direction must be 'increase' or 'decrease'")
    
    engine = get_analytics_engine()
    if engine is None:
        return []
    
    return engine.get_top_movers(limit, direction)


@router.get("/analytics/timeseries")
async def get_time_series_data(days: int = 7):
    """
    Get time series chart data
    
    Args:
        days: Number of days to include (default: 7)
    
    Returns:
        Chart-ready time series data
    """
    from src.web.analytics_engine import get_analytics_engine
    
    engine = get_analytics_engine()
    if engine is None:
        return {'labels': [], 'datasets': []}
    
    return engine.generate_time_series_chart_data(days)


@router.get("/analytics/export/csv")
async def export_csv(spkid: Optional[str] = None):
    """
    Export threat history to CSV
    
    Args:
        spkid: Optional object ID to filter by
    
    Returns:
        CSV file download
    """
    from fastapi.responses import Response
    from src.web.analytics_engine import get_analytics_engine
    
    engine = get_analytics_engine()
    if engine is None:
        raise HTTPException(status_code=503, detail="Analytics engine not initialized")
    
    csv_data = engine.export_to_csv(spkid)
    
    filename = f"atis_threats_{spkid if spkid else 'all'}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/analytics/export/json")
async def export_json(days: int = 7):
    """
    Export threat history to JSON
    
    Args:
        days: Number of days to include (default: 7)
    
    Returns:
        JSON file download
    """
    from fastapi.responses import Response
    from src.web.analytics_engine import get_analytics_engine
    
    engine = get_analytics_engine()
    if engine is None:
        raise HTTPException(status_code=503, detail="Analytics engine not initialized")
    
    json_data = engine.export_to_json(days)
    
    filename = f"atis_export_{datetime.now().strftime('%Y%m%d')}.json"
    
    return Response(
        content=json_data,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
