"""
Impact Calculator
Calculates impact effects, energy, damage radius, and risk assessment
"""

import numpy as np
from typing import Dict, Tuple
import math


class ImpactCalculator:
    """Calculate asteroid impact effects and damage assessments"""
    
    # Historical impact reference events
    REFERENCE_EVENTS = {
        "tunguska": {"year": 1908, "energy_mt": 15, "diameter_m": 60, "damage_radius_km": 30},
        "chelyabinsk": {"year": 2013, "energy_mt": 0.5, "diameter_m": 20, "damage_radius_km": 5},
        "hiroshima": {"year": 1945, "energy_mt": 0.015, "damage_radius_km": 2},
        "chicxulub": {"year": -65000000, "energy_mt": 100000000, "diameter_m": 10000, "damage_radius_km": 1000},
    }
    
    def __init__(self):
        pass
    
    def calculate_impact_effects(
        self,
        diameter_m: float,
        velocity_km_s: float,
        density_g_cm3: float = 2.6,
        impact_angle_deg: float = 45.0
    ) -> Dict[str, float]:
        """
        Calculate comprehensive impact effects
        
        Parameters:
        -----------
        diameter_m : float - Asteroid diameter in meters
        velocity_km_s : float - Impact velocity in km/s
        density_g_cm3 : float - Asteroid density (g/cm³)
        impact_angle_deg : float - Impact angle from horizontal
        
        Returns:
        --------
        Dict with impact parameters
        """
        
        # Calculate mass
        radius_m = diameter_m / 2
        volume_m3 = (4/3) * np.pi * radius_m**3
        mass_kg = volume_m3 * (density_g_cm3 * 1000)
        
        # Kinetic energy
        velocity_m_s = velocity_km_s * 1000
        energy_joules = 0.5 * mass_kg * velocity_m_s**2
        energy_mt = energy_joules / 4.184e15  # Convert to megatons TNT
        
        # Impact angle efficiency (0-90 degrees)
        angle_efficiency = np.sin(np.radians(impact_angle_deg))
        effective_energy_mt = energy_mt * angle_efficiency
        
        # Crater dimensions (using scaling laws)
        crater_diameter_km = self._calculate_crater_diameter(
            diameter_m / 1000, velocity_km_s, density_g_cm3
        )
        
        # Damage radii
        damage_radii = self._calculate_damage_radii(effective_energy_mt)
        
        # Seismic effects
        earthquake_magnitude = self._calculate_earthquake_magnitude(energy_mt)
        
        # Atmospheric effects
        atmospheric_effects = self._calculate_atmospheric_effects(
            diameter_m, velocity_km_s, impact_angle_deg
        )
        
        return {
            "mass_kg": float(mass_kg),
            "mass_metric_tons": float(mass_kg / 1000),
            "energy_joules": float(energy_joules),
            "energy_megatons": float(energy_mt),
            "effective_energy_megatons": float(effective_energy_mt),
            "crater_diameter_km": float(crater_diameter_km),
            "earthquake_magnitude": float(earthquake_magnitude),
            **damage_radii,
            **atmospheric_effects
        }
    
    def _calculate_crater_diameter(self, diameter_km: float, velocity_km_s: float, density: float) -> float:
        """Calculate impact crater diameter using scaling laws"""
        # Simplified crater scaling (actual calculation more complex)
        # D_crater ≈ D_asteroid * (velocity/12)^0.44 * (density/2.6)^0.33
        
        crater_d = diameter_km * (velocity_km_s / 12) ** 0.44 * (density / 2.6) ** 0.33 * 20
        return max(crater_d, diameter_km * 10)  # Minimum 10x diameter
    
    def _calculate_damage_radii(self, energy_mt: float) -> Dict[str, float]:
        """Calculate damage zones based on impact energy"""
        
        # Overpressure-based damage radii (empirical formulas)
        # Based on nuclear weapons effects scaling
        
        # Total destruction (>20 psi overpressure)
        r_total = 2.2 * (energy_mt ** 0.33)  # km
        
        # Severe damage (5-20 psi)
        r_severe = 4.0 * (energy_mt ** 0.33)  # km
        
        # Moderate damage (1-5 psi)
        r_moderate = 8.0 * (energy_mt ** 0.33)  # km
        
        # Light damage (0.1-1 psi)
        r_light = 20.0 * (energy_mt ** 0.33)  # km
        
        # Thermal radiation burns (3rd degree)
        r_thermal = 3.5 * (energy_mt ** 0.41)  # km
        
        return {
            "damage_radius_total_km": float(r_total),
            "damage_radius_severe_km": float(r_severe),
            "damage_radius_moderate_km": float(r_moderate),
            "damage_radius_light_km": float(r_light),
            "thermal_radiation_radius_km": float(r_thermal),
        }
    
    def _calculate_earthquake_magnitude(self, energy_mt: float) -> float:
        """Calculate equivalent earthquake Richter magnitude"""
        # Gutenberg-Richter relation
        # log10(E) = 11.8 + 1.5*M (E in ergs)
        
        energy_joules = energy_mt * 4.184e15
        energy_ergs = energy_joules * 1e7
        
        magnitude = (np.log10(energy_ergs) - 11.8) / 1.5
        return max(magnitude, 0)
    
    def _calculate_atmospheric_effects(
        self, diameter_m: float, velocity_km_s: float, angle_deg: float
    ) -> Dict[str, any]:
        """Calculate atmospheric entry and airburst effects"""
        
        # Atmospheric penetration
        # Small objects (<50m) may airburst, large objects reach ground
        
        airburst_altitude_km = None
        reaches_ground = True
        
        if diameter_m < 50:
            # Likely airburst
            airburst_altitude_km = 10 + (50 - diameter_m) / 5  # Simplified
            reaches_ground = False
        elif diameter_m < 100:
            # Possible airburst or ground impact
            airburst_altitude_km = 5.0
            reaches_ground = np.random.random() > 0.5  # Uncertain
        
        # Fireball brightness
        fireball_brightness = self._calculate_fireball_brightness(diameter_m, velocity_km_s)
        
        return {
            "airburst_altitude_km": airburst_altitude_km,
            "reaches_ground": reaches_ground,
            "fireball_brightness_magnitude": float(fireball_brightness),
            "visible_range_km": float(1000 if fireball_brightness < -20 else 500)
        }
    
    def _calculate_fireball_brightness(self, diameter_m: float, velocity_km_s: float) -> float:
        """Calculate fireball absolute magnitude"""
        # Empirical relation based on meteor observations
        energy_kt = 0.5 * (diameter_m**3) * 2600 * (velocity_km_s * 1000)**2 / 4.184e12
        
        magnitude = -5 * np.log10(energy_kt) - 10
        return magnitude
    
    def compare_to_historical(self, energy_mt: float) -> Dict[str, any]:
        """Compare impact to historical events"""
        
        comparisons = {}
        
        for event_name, event_data in self.REFERENCE_EVENTS.items():
            ratio = energy_mt / event_data["energy_mt"]
            comparisons[event_name] = {
                "energy_ratio": float(ratio),
                "equivalent_count": float(ratio),
                "description": f"{ratio:.1f}x {event_name.capitalize()} event"
            }
        
        return comparisons
    
    def calculate_population_exposure(
        self, 
        damage_radius_km: float,
        impact_lat: float,
        impact_lon: float,
        population_density: float = 50  # people per km²
    ) -> Dict[str, float]:
        """
        Estimate population exposure (simplified)
        
        Parameters:
        -----------
        damage_radius_km : float - Radius of damage zone
        impact_lat : float - Impact latitude
        impact_lon : float - Impact longitude
        population_density : float - Average population density
        
        Returns:
        --------
        Dict with exposure estimates
        """
        
        # Affected area
        area_km2 = np.pi * damage_radius_km**2
        
        # Estimated exposed population
        exposed_population = int(area_km2 * population_density)
        
        # Casualty estimates (highly simplified)
        casualties_low = int(exposed_population * 0.01)  # 1% for light damage
        casualties_high = int(exposed_population * 0.5)  # 50% for severe damage
        
        return {
            "affected_area_km2": float(area_km2),
            "estimated_exposed_population": exposed_population,
            "casualties_estimate_low": casualties_low,
            "casualties_estimate_high": casualties_high,
        }
    
    def calculate_warning_time(
        self,
        current_distance_au: float,
        velocity_km_s: float
    ) -> Dict[str, float]:
        """Calculate time until potential impact"""
        
        # Convert AU to km
        distance_km = current_distance_au * 149597870.7
        
        # Time to Earth (simplified straight-line)
        time_seconds = distance_km / velocity_km_s
        time_days = time_seconds / 86400
        time_years = time_days / 365.25
        
        return {
            "warning_time_seconds": float(time_seconds),
            "warning_time_days": float(time_days),
            "warning_time_years": float(time_years),
        }
    
    def assess_mitigation_feasibility(
        self,
        warning_time_years: float,
        diameter_m: float
    ) -> Dict[str, any]:
        """Assess feasibility of deflection/mitigation"""
        
        feasibility = "NONE"
        recommended_method = "Observation only"
        
        if warning_time_years > 10:
            if diameter_m < 100:
                feasibility = "HIGH"
                recommended_method = "Kinetic impactor"
            elif diameter_m < 500:
                feasibility = "MEDIUM"
                recommended_method = "Gravity tractor or kinetic impactor"
            else:
                feasibility = "LOW"
                recommended_method = "Nuclear deflection (theoretical)"
        elif warning_time_years > 5:
            if diameter_m < 100:
                feasibility = "MEDIUM"
                recommended_method = "Kinetic impactor"
            else:
                feasibility = "LOW"
                recommended_method = "Nuclear deflection"
        elif warning_time_years > 1:
            feasibility = "LOW"
            recommended_method = "Civil defense / evacuation"
        
        return {
            "mitigation_feasibility": feasibility,
            "recommended_method": recommended_method,
            "minimum_warning_needed_years": 10.0 if diameter_m > 500 else 5.0,
        }
