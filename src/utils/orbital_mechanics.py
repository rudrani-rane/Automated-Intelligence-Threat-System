"""
Orbital Mechanics Utilities
Keplerian orbit calculations for asteroid trajectory visualization
"""

import numpy as np
from typing import Tuple, List
import math


def calculate_orbital_position(a: float, e: float, i: float, om: float, w: float, M: float) -> Tuple[float, float, float]:
    """
    Calculate 3D position from Keplerian orbital elements
    
    Parameters:
    -----------
    a : float - Semi-major axis (AU)
    e : float - Eccentricity
    i : float - Inclination (degrees)
    om : float - Longitude of ascending node (degrees)
    w : float - Argument of perihelion (degrees)
    M : float - Mean anomaly (degrees)
    
    Returns:
    --------
    (x, y, z) : Tuple[float, float, float] - Position in 3D space (AU)
    """
    
    # Convert degrees to radians
    i_rad = np.radians(i)
    om_rad = np.radians(om)
    w_rad = np.radians(w)
    M_rad = np.radians(M)
    
    # Solve Kepler's equation for eccentric anomaly E
    E = solve_keplers_equation(M_rad, e)
    
    # Calculate true anomaly
    nu = 2 * np.arctan2(
        np.sqrt(1 + e) * np.sin(E / 2),
        np.sqrt(1 - e) * np.cos(E / 2)
    )
    
    # Calculate distance from focus
    r = a * (1 - e * np.cos(E))
    
    # Position in orbital plane
    x_orb = r * np.cos(nu)
    y_orb = r * np.sin(nu)
    
    # Rotate to 3D space
    x = (np.cos(om_rad) * np.cos(w_rad) - np.sin(om_rad) * np.sin(w_rad) * np.cos(i_rad)) * x_orb + \
        (-np.cos(om_rad) * np.sin(w_rad) - np.sin(om_rad) * np.cos(w_rad) * np.cos(i_rad)) * y_orb
    
    y = (np.sin(om_rad) * np.cos(w_rad) + np.cos(om_rad) * np.sin(w_rad) * np.cos(i_rad)) * x_orb + \
        (-np.sin(om_rad) * np.sin(w_rad) + np.cos(om_rad) * np.cos(w_rad) * np.cos(i_rad)) * y_orb
    
    z = (np.sin(w_rad) * np.sin(i_rad)) * x_orb + \
        (np.cos(w_rad) * np.sin(i_rad)) * y_orb
    
    return (float(x), float(y), float(z))


def solve_keplers_equation(M: float, e: float, tolerance: float = 1e-6, max_iterations: int = 30) -> float:
    """
    Solve Kepler's equation: M = E - e*sin(E)
    Using Newton-Raphson iteration
    
    Parameters:
    -----------
    M : float - Mean anomaly (radians)
    e : float - Eccentricity
    tolerance : float - Convergence tolerance
    max_iterations : int - Maximum iterations
    
    Returns:
    --------
    E : float - Eccentric anomaly (radians)
    """
    
    # Initial guess
    E = M if e < 0.8 else np.pi
    
    for _ in range(max_iterations):
        f = E - e * np.sin(E) - M
        f_prime = 1 - e * np.cos(E)
        
        E_new = E - f / f_prime
        
        if abs(E_new - E) < tolerance:
            return E_new
        
        E = E_new
    
    return E


def generate_orbital_path(a: float, e: float, i: float, om: float, w: float, num_points: int = 100) -> List[Tuple[float, float, float]]:
    """
    Generate complete orbital ellipse as series of 3D points
    
    Parameters:
    -----------
    a : float - Semi-major axis (AU)
    e : float - Eccentricity
    i : float - Inclination (degrees)
    om : float - Longitude of ascending node (degrees)
    w : float - Argument of perihelion (degrees)
    num_points : int - Number of points along orbit
    
    Returns:
    --------
    List of (x, y, z) tuples representing orbital path
    """
    
    path = []
    for idx in range(num_points + 1):
        M = (idx / num_points) * 360.0  # Mean anomaly from 0 to 360 degrees
        pos = calculate_orbital_position(a, e, i, om, w, M)
        path.append(pos)
    
    return path


def calculate_velocity(a: float, e: float, i: float, om: float, w: float, M: float, mu: float = 1.0) -> Tuple[float, float, float]:
    """
    Calculate orbital velocity vector
    
    Parameters:
    -----------
    a : float - Semi-major axis (AU)
    e : float - Eccentricity
    i : float - Inclination (degrees)
    om : float - Longitude of ascending node (degrees)
    w : float - Argument of perihelion (degrees)
    M : float - Mean anomaly (degrees)
    mu : float - Gravitational parameter (AU^3/day^2)
    
    Returns:
    --------
    (vx, vy, vz) : Tuple[float, float, float] - Velocity vector (AU/day)
    """
    
    # Convert degrees to radians
    i_rad = np.radians(i)
    om_rad = np.radians(om)
    w_rad = np.radians(w)
    M_rad = np.radians(M)
    
    # Solve for eccentric anomaly
    E = solve_keplers_equation(M_rad, e)
    
    # Calculate true anomaly
    nu = 2 * np.arctan2(
        np.sqrt(1 + e) * np.sin(E / 2),
        np.sqrt(1 - e) * np.cos(E / 2)
    )
    
    # Distance and mean motion
    r = a * (1 - e * np.cos(E))
    n = np.sqrt(mu / a**3)
    
    # Velocity in orbital plane
    vx_orb = -(n * a / np.sqrt(1 - e**2)) * np.sin(nu)
    vy_orb = (n * a / np.sqrt(1 - e**2)) * (e + np.cos(nu))
    
    # Rotate to 3D space
    vx = (np.cos(om_rad) * np.cos(w_rad) - np.sin(om_rad) * np.sin(w_rad) * np.cos(i_rad)) * vx_orb + \
         (-np.cos(om_rad) * np.sin(w_rad) - np.sin(om_rad) * np.cos(w_rad) * np.cos(i_rad)) * vy_orb
    
    vy = (np.sin(om_rad) * np.cos(w_rad) + np.cos(om_rad) * np.sin(w_rad) * np.cos(i_rad)) * vx_orb + \
         (-np.sin(om_rad) * np.sin(w_rad) + np.cos(om_rad) * np.cos(w_rad) * np.cos(i_rad)) * vy_orb
    
    vz = (np.sin(w_rad) * np.sin(i_rad)) * vx_orb + \
         (np.cos(w_rad) * np.sin(i_rad)) * vy_orb
    
    return (float(vx), float(vy), float(vz))


def calculate_close_approach_distance(a: float, e: float, i: float, om: float, w: float) -> float:
    """
    Calculate minimum possible Earth approach distance (MOID approximation)
    
    Parameters:
    -----------
    a : float - Semi-major axis (AU)
    e : float - Eccentricity
    i : float - Inclination (degrees)
    om : float - Longitude of ascending node (degrees)
    w : float - Argument of perihelion (degrees)
    
    Returns:
    --------
    float - Approximate minimum orbital intersection distance (AU)
    """
    
    # Earth's orbit (circular approximation)
    earth_a = 1.0
    
    # Perihelion and aphelion of asteroid
    q = a * (1 - e)  # perihelion
    Q = a * (1 + e)  # aphelion
    
    # Check if orbits can intersect
    if q > earth_a or Q < earth_a:
        # Orbits don't cross Earth's orbit radially
        return min(abs(q - earth_a), abs(Q - earth_a))
    
    # Simplified MOID calculation (proper calculation requires numerical integration)
    # This is an approximation based on inclination
    moid = abs(earth_a * np.sin(np.radians(i)))
    
    return max(moid, 0.001)  # Minimum 0.001 AU


def absolute_magnitude_to_diameter(H: float, albedo: float = 0.14) -> float:
    """
    Convert absolute magnitude to approximate diameter
    
    Parameters:
    -----------
    H : float - Absolute magnitude
    albedo : float - Assumed albedo (default 0.14 for C-type)
    
    Returns:
    --------
    float - Estimated diameter in kilometers
    """
    
    return 10 ** ((3.1236 - 0.5 * np.log10(albedo) - 0.2 * H))


def calculate_impact_energy(diameter_km: float, velocity_km_s: float, density: float = 2.6) -> float:
    """
    Calculate kinetic energy of impact in megatons TNT
    
    Parameters:
    -----------
    diameter_km : float - Asteroid diameter (km)
    velocity_km_s : float - Impact velocity (km/s)
    density : float - Asteroid density (g/cm³), default 2.6 for stony
    
    Returns:
    --------
    float - Impact energy in megatons TNT equivalent
    """
    
    # Calculate mass (kg)
    radius_m = (diameter_km * 1000) / 2
    volume_m3 = (4/3) * np.pi * radius_m**3
    mass_kg = volume_m3 * (density * 1000)  # density in kg/m³
    
    # Calculate kinetic energy (Joules)
    velocity_m_s = velocity_km_s * 1000
    energy_joules = 0.5 * mass_kg * velocity_m_s**2
    
    # Convert to megatons TNT (1 megaton = 4.184e15 J)
    energy_megatons = energy_joules / 4.184e15
    
    return energy_megatons


def time_to_epoch(years_from_now: float, epoch_jd: float = 2461000.5) -> float:
    """
    Convert time offset to mean anomaly change
    
    Parameters:
    -----------
    years_from_now : float - Time offset in years
    epoch_jd : float - Reference epoch (Julian Date)
    
    Returns:
    --------
    float - Mean anomaly offset (degrees)
    """
    
    # Mean motion (degrees per day)
    days = years_from_now * 365.25
    
    return days


def calculate_orbital_period(a: float) -> float:
    """
    Calculate orbital period using Kepler's third law
    
    Parameters:
    -----------
    a : float - Semi-major axis (AU)
    
    Returns:
    --------
    float - Orbital period in years
    """
    
    return a ** 1.5
