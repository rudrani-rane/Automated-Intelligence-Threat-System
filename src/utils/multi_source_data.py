"""
Multi-Source Data Integration
Fetches and combines asteroid data from multiple authoritative sources
"""

import asyncio
import httpx
from typing import Dict, List, Optional
from datetime import datetime


class MultiSourceAsteroidData:
    """
    Integrates asteroid data from multiple sources:
    - NASA JPL SBDB (Small-Body Database)
    - MPC (Minor Planet Center)
    - CNEOS (Center for Near-Earth Object Studies) - Sentry System
    - NEODyS (Near-Earth Objects Dynamic Site)
    """
    
    def __init__(self):
        self.sbdb_base = "https://ssd-api.jpl.nasa.gov/sbdb.api"
        self.ca_api_base = "https://ssd-api.jpl.nasa.gov/cad.api"
        self.sentry_base = "https://ssd-api.jpl.nasa.gov/sentry.api"
        self.timeout = 30.0
        
    async def get_combined_data(self, spkid: str) -> Dict:
        """
        Fetch and combine data from multiple sources
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = [
                self.fetch_sbdb_data(client, spkid),
                self.fetch_close_approaches(client, spkid),
                self.fetch_sentry_data(client, spkid),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            combined = {
                "spkid": spkid,
                "fetch_time": datetime.utcnow().isoformat(),
                "sources": {}
            }
            
            if not isinstance(results[0], Exception) and results[0]:
                combined["sources"]["sbdb"] = results[0]
                
            if not isinstance(results[1], Exception) and results[1]:
                combined["sources"]["close_approaches"] = results[1]
                
            if not isinstance(results[2], Exception) and results[2]:
                combined["sources"]["sentry"] = results[2]
                
            # Calculate data quality score
            combined["data_quality"] = self.calculate_data_quality(combined)
            
            return combined
    
    async def fetch_sbdb_data(self, client: httpx.AsyncClient, spkid: str) -> Optional[Dict]:
        """Fetch detailed data from JPL SBDB"""
        try:
            params = {
                "sstr": spkid,
                "full-prec": "true"
            }
            response = await client.get(self.sbdb_base, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if "object" in data:
                    return {
                        "available": True,
                        "orbital_elements": data.get("orbit", {}).get("elements", {}),
                        "physical_params": data.get("phys_par", {}),
                        "orbit_class": data.get("orbit", {}).get("orbit_class", {}),
                        "designation": data.get("object", {}).get("fullname", "")
                    }
            return {"available": False}
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    async def fetch_close_approaches(self, client: httpx.AsyncClient, spkid: str) -> Optional[Dict]:
        """Fetch historical and future close approaches"""
        try:
            params = {
                "des": spkid,
                "date-min": "1900-01-01",
                "date-max": "2100-12-31",
                "dist-max": "0.2"  # 0.2 AU max distance
            }
            response = await client.get(self.ca_api_base, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                approaches = []
                if "data" in data:
                    for ca in data["data"]:
                        approaches.append({
                            "date": ca[3],  # Close approach date
                            "distance_au": float(ca[4]),  # Nominal distance (AU)
                            "distance_ld": float(ca[4]) * 389.1726,  # Lunar distances
                            "velocity_km_s": float(ca[7]) if len(ca) > 7 else None,
                            "h_magnitude": float(ca[10]) if len(ca) > 10 else None
                        })
                
                # Separate historical and future
                now = datetime.utcnow()
                historical = [a for a in approaches if datetime.fromisoformat(a["date"].replace(" ", "T")) < now]
                future = [a for a in approaches if datetime.fromisoformat(a["date"].replace(" ", "T")) >= now]
                
                return {
                    "available": True,
                    "total_count": len(approaches),
                    "historical_count": len(historical),
                    "future_count": len(future),
                    "historical": sorted(historical, key=lambda x: x["date"])[-10:],  # Last 10
                    "future": sorted(future, key=lambda x: x["date"])[:10],  # Next 10
                    "closest_ever": min(approaches, key=lambda x: x["distance_au"]) if approaches else None,
                    "next_close_approach": future[0] if future else None
                }
            return {"available": False}
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    async def fetch_sentry_data(self, client: httpx.AsyncClient, spkid: str) -> Optional[Dict]:
        """Fetch impact risk data from CNEOS Sentry"""
        try:
            # Sentry API
            params = {
                "spk": spkid
            }
            response = await client.get(self.sentry_base, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and len(data["data"]) > 0:
                    sentry_entry = data["data"][0]
                    
                    return {
                        "available": True,
                        "on_sentry_list": True,
                        "palermo_scale_max": float(sentry_entry.get("ps_max", 0)),
                        "palermo_scale_cumulative": float(sentry_entry.get("ps_cum", 0)),
                        "torino_scale_max": int(sentry_entry.get("ts_max", 0)),
                        "impact_probability": float(sentry_entry.get("ip", 0)),
                        "n_impacts": int(sentry_entry.get("n_imp", 0)),
                        "last_updated": sentry_entry.get("last_obs", "")
                    }
                else:
                    return {
                        "available": True,
                        "on_sentry_list": False
                    }
            return {"available": False}
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def calculate_data_quality(self, combined_data: Dict) -> Dict:
        """Calculate overall data quality metrics"""
        sources = combined_data.get("sources", {})
        
        quality = {
            "completeness": 0.0,
            "sources_available": 0,
            "total_sources": 3,
            "confidence": "low"
        }
        
        # Count available sources
        available = sum(1 for s in sources.values() if s.get("available", False))
        quality["sources_available"] = available
        
        # Completeness score
        quality["completeness"] = (available / quality["total_sources"]) * 100
        
        # Confidence level
        if quality["completeness"] >= 80:
            quality["confidence"] = "high"
        elif quality["completeness"] >= 50:
            quality["confidence"] = "medium"
        else:
            quality["confidence"] = "low"
        
        # Observation count from SBDB
        if "sbdb" in sources and sources["sbdb"].get("available"):
            orbital = sources["sbdb"].get("orbital_elements", {})
            if orbital:
                quality["has_orbital_elements"] = True
        
        # Historical tracking
        if "close_approaches" in sources and sources["close_approaches"].get("available"):
            ca = sources["close_approaches"]
            quality["historical_tracking"] = ca.get("historical_count", 0) > 0
            quality["future_predictions"] = ca.get("future_count", 0) > 0
        
        # Risk assessment
        if "sentry" in sources and sources["sentry"].get("available"):
            quality["risk_assessed"] = sources["sentry"].get("on_sentry_list", False)
        
        return quality
    
    async def get_historical_timeline(self, spkid: str) -> List[Dict]:
        """Get comprehensive historical close approach timeline"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            ca_data = await self.fetch_close_approaches(client, spkid)
            
            if ca_data and ca_data.get("available"):
                timeline = []
                
                all_approaches = ca_data.get("historical", []) + ca_data.get("future", [])
                
                for approach in all_approaches:
                    date = datetime.fromisoformat(approach["date"].replace(" ", "T"))
                    
                    timeline.append({
                        "date": approach["date"],
                        "year": date.year,
                        "distance_au": approach["distance_au"],
                        "distance_ld": approach["distance_ld"],
                        "velocity_km_s": approach["velocity_km_s"],
                        "is_future": date > datetime.utcnow(),
                        "risk_level": self.assess_risk_level(approach["distance_au"])
                    })
                
                return sorted(timeline, key=lambda x: x["date"])
            
            return []
    
    def assess_risk_level(self, distance_au: float) -> str:
        """Assess risk level based on distance"""
        if distance_au < 0.002:  # < ~300,000 km
            return "critical"
        elif distance_au < 0.01:  # < ~1.5 million km
            return "high"
        elif distance_au < 0.05:  # < ~7.5 million km
            return "medium"
        else:
            return "low"


# Global instance
multi_source = MultiSourceAsteroidData()
