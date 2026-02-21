"""
Simplified N-Body Gravitational Simulation
Calculates gravitational effects of major bodies on asteroid orbits
"""

import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class CelestialBody:
    """Represents a massive body in the solar system"""
    name: str
    mass: float  # kg
    position: np.ndarray  # [x, y, z] in AU
    velocity: np.ndarray  # [vx, vy, vz] in AU/day


class NBodySimulator:
    """
    Simplified N-body gravity simulator for asteroid perturbations
    Includes Sun, Jupiter, Saturn, Earth for major perturbations
    """
    
    # Constants
    G = 6.67430e-11  # Gravitational constant (m^3 kg^-1 s^-2)
    AU = 1.496e11  # 1 AU in meters
    DAY = 86400  # Seconds in a day
    
    # Solar system masses (kg)
    MASSES = {
        "Sun": 1.989e30,
        "Jupiter": 1.898e27,
        "Saturn": 5.683e26,
        "Earth": 5.972e24,
        "Mars": 6.417e23
    }
    
    def __init__(self):
        """Initialize the simulator with major solar system bodies"""
        self.bodies = []
        self.time = 0.0  # Current simulation time in days
        
    def initialize_solar_system(self, epoch_jd: float = 2451545.0):
        """
        Initialize solar system at a given epoch (default J2000.0)
        Uses simplified circular orbits for demonstration
        """
        self.bodies = []
        
        # Sun (at origin)
        self.bodies.append(CelestialBody(
            name="Sun",
            mass=self.MASSES["Sun"],
            position=np.array([0.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0])
        ))
        
        # Jupiter (5.2 AU, circular orbit approximation)
        jupiter_distance = 5.2
        jupiter_velocity = 2 * np.pi * jupiter_distance / 4332.59  # Orbital period 11.86 years
        self.bodies.append(CelestialBody(
            name="Jupiter",
            mass=self.MASSES["Jupiter"],
            position=np.array([jupiter_distance, 0.0, 0.0]),
            velocity=np.array([0.0, jupiter_velocity, 0.0])
        ))
        
        # Saturn (9.5 AU)
        saturn_distance = 9.5
        saturn_velocity = 2 * np.pi * saturn_distance / 10759.22  # Orbital period 29.46 years
        self.bodies.append(CelestialBody(
            name="Saturn",
            mass=self.MASSES["Saturn"],
            position=np.array([saturn_distance, 0.0, 0.0]),
            velocity=np.array([0.0, saturn_velocity, 0.0])
        ))
        
        # Earth (1 AU)
        earth_distance = 1.0
        earth_velocity = 2 * np.pi * earth_distance / 365.25
        self.bodies.append(CelestialBody(
            name="Earth",
            mass=self.MASSES["Earth"],
            position=np.array([earth_distance, 0.0, 0.0]),
            velocity=np.array([0.0, earth_velocity, 0.0])
        ))
        
    def add_asteroid(self, name: str, position: np.ndarray, velocity: np.ndarray, mass: float = 1e12):
        """Add an asteroid to the simulation (mass in kg, default ~1km diameter)"""
        self.bodies.append(CelestialBody(
            name=name,
            mass=mass,
            position=position.copy(),
            velocity=velocity.copy()
        ))
        
    def calculate_acceleration(self, body_index: int) -> np.ndarray:
        """Calculate gravitational acceleration on a body from all other bodies"""
        body = self.bodies[body_index]
        acceleration = np.zeros(3)
        
        for i, other in enumerate(self.bodies):
            if i == body_index:
                continue
                
            # Vector from body to other
            r_vec = other.position - body.position
            r_mag = np.linalg.norm(r_vec)
            
            if r_mag < 1e-10:  # Avoid division by zero
                continue
            
            # Convert AU to meters for calculation
            r_meters = r_mag * self.AU
            
            # F = G * m1 * m2 / r^2
            # a = G * m2 / r^2
            a_magnitude = self.G * other.mass / (r_meters ** 2)
            
            # Convert back to AU/day^2
            a_magnitude_au_day2 = a_magnitude * (self.DAY ** 2) / self.AU
            
            # Acceleration vector
            acceleration += a_magnitude_au_day2 * (r_vec / r_mag)
        
        return acceleration
    
    def step(self, dt: float = 0.1):
        """
        Advance simulation by dt days using Verlet integration
        dt: time step in days (default 0.1 days = 2.4 hours)
        """
        # Calculate accelerations for all bodies
        accelerations = [self.calculate_acceleration(i) for i in range(len(self.bodies))]
        
        # Update positions and velocities (Verlet integration)
        for i, body in enumerate(self.bodies):
            # v(t + dt/2) = v(t) + a(t) * dt/2
            body.velocity += accelerations[i] * (dt / 2)
            
            # x(t + dt) = x(t) + v(t + dt/2) * dt
            body.position += body.velocity * dt
        
        # Recalculate accelerations at new positions
        new_accelerations = [self.calculate_acceleration(i) for i in range(len(self.bodies))]
        
        # Complete velocity update: v(t + dt) = v(t + dt/2) + a(t + dt) * dt/2
        for i, body in enumerate(self.bodies):
            body.velocity += new_accelerations[i] * (dt / 2)
        
        self.time += dt
    
    def simulate(self, days: float, dt: float = 0.1) -> List[Dict]:
        """
        Run simulation for specified duration
        Returns trajectory data for all bodies
        """
        num_steps = int(days / dt)
        trajectory = {body.name: {"positions": [], "times": []} for body in self.bodies}
        
        for step in range(num_steps):
            # Record positions
            for body in self.bodies:
                trajectory[body.name]["positions"].append(body.position.copy())
                trajectory[body.name]["times"].append(self.time)
            
            # Advance simulation
            self.step(dt)
        
        return trajectory
    
    def simulate_asteroid_perturbation(
        self, 
        asteroid_pos: np.ndarray, 
        asteroid_vel: np.ndarray,
        days: float = 365.0
    ) -> Dict:
        """
        Simulate an asteroid's trajectory including gravitational perturbations
        
        Args:
            asteroid_pos: Initial position [x, y, z] in AU
            asteroid_vel: Initial velocity [vx, vy, vz] in AU/day
            days: Simulation duration in days
            
        Returns:
            Dictionary with trajectory data and perturbation analysis
        """
        # Initialize solar system
        self.initialize_solar_system()
        
        # Add asteroid
        self.add_asteroid("Target", asteroid_pos, asteroid_vel)
        
        # Run simulation
        trajectory = self.simulate(days, dt=0.5)
        
        # Analyze perturbations
        asteroid_trajectory = trajectory["Target"]["positions"]
        
        # Calculate perturbation magnitude
        # Compare to simple two-body Keplerian motion
        perturbations = self.analyze_perturbations(asteroid_trajectory, asteroid_pos, asteroid_vel, days)
        
        return {
            "trajectory": asteroid_trajectory,
            "times": trajectory["Target"]["times"],
            "perturbations": perturbations,
            "jupiter_positions": trajectory["Jupiter"]["positions"],
            "earth_positions": trajectory["Earth"]["positions"]
        }
    
    def analyze_perturbations(
        self, 
        actual_trajectory: List[np.ndarray],
        initial_pos: np.ndarray,
        initial_vel: np.ndarray,
        days: float
    ) -> Dict:
        """Analyze how much the trajectory deviates from simple Keplerian orbit"""
        
        # Simple Keplerian (two-body) reference
        # This is a simplified comparison
        max_deviation = 0.0
        deviations = []
        
        for i, pos in enumerate(actual_trajectory):
            # Approximate Keplerian position (circular orbit assumption)
            t = i * 0.5  # Time step
            
            # Distance from Sun
            r_actual = np.linalg.norm(pos)
            r_initial = np.linalg.norm(initial_pos)
            
            # Deviation from initial orbital radius
            deviation = abs(r_actual - r_initial)
            deviations.append(deviation)
            
            if deviation > max_deviation:
                max_deviation = deviation
        
        avg_deviation = np.mean(deviations)
        
        return {
            "max_deviation_au": float(max_deviation),
            "avg_deviation_au": float(avg_deviation),
            "max_deviation_km": float(max_deviation * self.AU / 1000),
            "perturbation_significant": max_deviation > 0.01  # More than 0.01 AU
        }
    
    def get_close_encounter_effects(
        self,
        asteroid_pos: np.ndarray,
        asteroid_vel: np.ndarray,
        encounter_body: str = "Earth"
    ) -> Dict:
        """
        Calculate gravitational effects during close encounter with a planet
        """
        self.initialize_solar_system()
        self.add_asteroid("Flyby", asteroid_pos, asteroid_vel)
        
        # Find the body index
        body_idx = next((i for i, b in enumerate(self.bodies) if b.name == encounter_body), None)
        asteroid_idx = len(self.bodies) - 1
        
        if body_idx is None:
            return {"error": "Body not found"}
        
        # Simulate encounter (30 days)
        trajectory = self.simulate(30, dt=0.01)
        
        # Find closest approach
        min_distance = float('inf')
        closest_time = 0
        
        asteroid_positions = trajectory["Flyby"]["positions"]
        body_positions = trajectory[encounter_body]["positions"]
        times = trajectory["Flyby"]["times"]
        
        for i, (ast_pos, body_pos) in enumerate(zip(asteroid_positions, body_positions)):
            distance = np.linalg.norm(ast_pos - body_pos)
            if distance < min_distance:
                min_distance = distance
                closest_time = times[i]
        
        return {
            "closest_approach_au": float(min_distance),
            "closest_approach_km": float(min_distance * self.AU / 1000),
            "time_of_closest_approach_days": float(closest_time),
            "encounter_body": encounter_body,
            "significant_deflection": min_distance < 0.01  # Within 0.01 AU
        }


# Global instance
nbody_sim = NBodySimulator()
