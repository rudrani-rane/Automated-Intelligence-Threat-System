"""
Anomaly Detection System
Identifies unusual asteroids that don't fit typical patterns
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from scipy import stats
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))


class AnomalyDetector:
    """
    Detects anomalous asteroids using multiple techniques:
    - Isolation Forest (ensemble-based)
    - Statistical outlier detection (Z-score)
    - Cluster-based anomaly detection
    - Context-aware scoring
    """
    
    def __init__(self, contamination: float = 0.05):
        """
        Args:
            contamination: Expected proportion of anomalies (default 5%)
        """
        self.contamination = contamination
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        # Storage for population statistics
        self.feature_stats = {}
    
    def fit(self, features: np.ndarray, feature_names: List[str] = None):
        """
        Fit anomaly detector on asteroid population
        
        Args:
            features: Array of shape (n_asteroids, n_features)
            feature_names: Names of features
        """
        if feature_names is None:
            feature_names = [
                'eccentricity', 'semi_major_axis', 'inclination', 
                'longitude_ascending', 'argument_perihelion', 'mean_anomaly',
                'perihelion_distance', 'aphelion_distance', 'orbital_period',
                'mean_motion', 'absolute_magnitude', 'diameter'
            ]
        
        self.feature_names = feature_names
        
        # Normalize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Fit Isolation Forest
        self.isolation_forest.fit(features_scaled)
        
        # Calculate population statistics for each feature
        for i, name in enumerate(feature_names):
            self.feature_stats[name] = {
                'mean': float(np.mean(features[:, i])),
                'std': float(np.std(features[:, i])),
                'median': float(np.median(features[:, i])),
                'q25': float(np.percentile(features[:, i], 25)),
                'q75': float(np.percentile(features[:, i], 75)),
                'min': float(np.min(features[:, i])),
                'max': float(np.max(features[:, i]))
            }
        
        self.is_fitted = True
    
    def detect_anomaly(self, features: np.ndarray, 
                      asteroid_id: str = None) -> Dict:
        """
        Detect if an asteroid is anomalous
        
        Args:
            features: Array of shape (n_features,) for single asteroid
            asteroid_id: Identifier for the asteroid
            
        Returns:
            Dict with anomaly scores and explanations
        """
        if not self.is_fitted:
            # Use default statistics if not fitted
            self._initialize_default_stats()
        
        # Ensure features is 2D
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Get various anomaly scores
        isolation_score = self._isolation_forest_score(features)
        statistical_score = self._statistical_outlier_score(features)
        contextual_score = self._contextual_anomaly_score(features)
        
        # Combine scores (weighted average)
        combined_score = (
            isolation_score * 0.4 +
            statistical_score * 0.35 +
            contextual_score * 0.25
        )
        
        # Identify anomalous features
        anomalous_features = self._identify_anomalous_features(features[0])
        
        # Generate explanation
        explanation = self._generate_explanation(
            combined_score, anomalous_features, features[0]
        )
        
        # Determine if asteroid is anomalous
        is_anomalous = combined_score > 0.6
        
        return {
            'asteroid_id': asteroid_id,
            'is_anomalous': bool(is_anomalous),
            'anomaly_score': float(combined_score),
            'severity': self._get_severity_level(combined_score),
            'individual_scores': {
                'isolation_forest': float(isolation_score),
                'statistical_outlier': float(statistical_score),
                'contextual': float(contextual_score)
            },
            'anomalous_features': anomalous_features,
            'explanation': explanation,
            'recommendations': self._generate_recommendations(combined_score, anomalous_features)
        }
    
    def _isolation_forest_score(self, features: np.ndarray) -> float:
        """Isolation Forest anomaly score"""
        if not self.is_fitted:
            return 0.5  # Neutral score if not fitted
        
        features_scaled = self.scaler.transform(features)
        
        # Get anomaly score (-1 for outliers, 1 for inliers)
        score = self.isolation_forest.score_samples(features_scaled)[0]
        
        # Convert to [0, 1] where 1 is most anomalous
        # Typical range is [-0.5, 0.5], anything below -0.1 is suspicious
        normalized_score = 1 - (score + 0.5)  # Maps [-0.5, 0.5] to [1, 0]
        
        return np.clip(normalized_score, 0, 1)
    
    def _statistical_outlier_score(self, features: np.ndarray) -> float:
        """Statistical outlier detection using Z-scores"""
        z_scores = []
        
        for i, feature_name in enumerate(self.feature_names):
            if feature_name in self.feature_stats:
                stats = self.feature_stats[feature_name]
                value = features[0, i]
                
                # Calculate Z-score
                if stats['std'] > 0:
                    z = abs((value - stats['mean']) / stats['std'])
                    z_scores.append(z)
        
        if not z_scores:
            return 0.5
        
        # Maximum Z-score across features
        max_z = max(z_scores)
        
        # Convert Z-score to [0, 1]
        # Z > 3 is highly unusual (99.7% within 3 std)
        # Z > 4 is extremely unusual
        score = min(1.0, max_z / 4.0)
        
        return score
    
    def _contextual_anomaly_score(self, features: np.ndarray) -> float:
        """
        Context-aware anomaly detection
        Some combinations are unusual even if individual values are normal
        """
        scores = []
        
        # Extract key features
        eccentricity = features[0, 0]
        semi_major_axis = features[0, 1]
        inclination = features[0, 2]
        perihelion_dist = features[0, 6]
        diameter = features[0, 11]
        
        # Unusual combination 1: Very large but distant
        if diameter > 1.0 and perihelion_dist > 1.0:
            scores.append(0.8)  # Unusual: large asteroids are typically closer
        
        # Unusual combination 2: High eccentricity but low inclination
        if eccentricity > 0.7 and inclination < 5:
            scores.append(0.9)  # Very unusual orbit
        
        # Unusual combination 3: Very close perihelion but high inclination
        if perihelion_dist < 0.05 and inclination > 60:
            scores.append(0.85)  # Unusual for NEO
        
        # Unusual combination 4:極端な軌道要素
        if eccentricity > 0.9:  # Highly elliptical
            scores.append(0.7)
        
        if inclination > 80:  # Nearly perpendicular to ecliptic
            scores.append(0.75)
        
        # Unusual combination 5: Very small but threatening
        if diameter < 0.1 and perihelion_dist < 0.01:
            scores.append(0.6)  # Small but very close
        
        if not scores:
            return 0.0
        
        # Return maximum contextual anomaly
        return max(scores)
    
    def _identify_anomalous_features(self, features: np.ndarray) -> List[Dict]:
        """Identify which features are anomalous"""
        anomalous = []
        
        for i, feature_name in enumerate(self.feature_names):
            if feature_name not in self.feature_stats:
                continue
            
            stats = self.feature_stats[feature_name]
            value = features[i]
            
            # Calculate Z-score
            if stats['std'] > 0:
                z = abs((value - stats['mean']) / stats['std'])
                
                # Features with Z > 2.5 are unusual (98.8% within 2.5 std)
                if z > 2.5:
                    # Determine direction
                    if value > stats['mean']:
                        direction = 'high'
                        comparison = f"{((value - stats['mean']) / stats['mean'] * 100):.1f}% above average"
                    else:
                        direction = 'low'
                        comparison = f"{((stats['mean'] - value) / stats['mean'] * 100):.1f}% below average"
                    
                    anomalous.append({
                        'feature': feature_name,
                        'value': float(value),
                        'z_score': float(z),
                        'direction': direction,
                        'population_mean': stats['mean'],
                        'population_median': stats['median'],
                        'comparison': comparison
                    })
        
        # Sort by Z-score (most anomalous first)
        anomalous.sort(key=lambda x: x['z_score'], reverse=True)
        
        return anomalous
    
    def _generate_explanation(self, score: float, 
                             anomalous_features: List[Dict],
                             features: np.ndarray) -> str:
        """Generate human-readable explanation"""
        if score < 0.3:
            explanation = "This asteroid has typical characteristics for a Near-Earth Object. "
        elif score < 0.6:
            explanation = "This asteroid shows some unusual characteristics. "
        else:
            explanation = "This asteroid has highly unusual characteristics compared to the NEO population. "
        
        if anomalous_features:
            top_anomaly = anomalous_features[0]
            explanation += f"Most notably, its {top_anomaly['feature'].replace('_', ' ')} "
            explanation += f"is {top_anomaly['direction']} ({top_anomaly['comparison']}). "
            
            if len(anomalous_features) > 1:
                explanation += "Additionally, "
                other_features = [f['feature'].replace('_', ' ') for f in anomalous_features[1:3]]
                explanation += f"{', '.join(other_features)} "
                explanation += "are also outside typical ranges. "
        
        # Add contextual insights
        eccentricity = features[0]
        inclination = features[2]
        
        if eccentricity > 0.7:
            explanation += "The highly elliptical orbit suggests potential long-period variations. "
        
        if inclination > 60:
            explanation += "The steep inclination is rare among NEOs and may indicate a cometary origin. "
        
        return explanation
    
    def _get_severity_level(self, score: float) -> str:
        """Convert score to severity level"""
        if score > 0.8:
            return 'EXTREME'
        elif score > 0.6:
            return 'HIGH'
        elif score > 0.4:
            return 'MODERATE'
        elif score > 0.2:
            return 'LOW'
        else:
            return 'NORMAL'
    
    def _generate_recommendations(self, score: float, 
                                 anomalous_features: List[Dict]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if score > 0.7:
            recommendations.append("HIGH PRIORITY: Verify observational data for errors")
            recommendations.append("Request additional observations from multiple observatories")
            recommendations.append("Update orbital elements with latest astrometry")
        
        if score > 0.5:
            recommendations.append("Investigate potential data quality issues")
            recommendations.append("Check for recent close encounters that may explain unusual orbit")
            recommendations.append("Consider manual review by orbital dynamics expert")
        
        # Feature-specific recommendations
        for feature in anomalous_features[:2]:  # Top 2 anomalous features
            if 'eccentricity' in feature['feature'] and feature['direction'] == 'high':
                recommendations.append("High eccentricity: Monitor for potential perturbations from Jupiter")
            
            if 'inclination' in feature['feature'] and feature['direction'] == 'high':
                recommendations.append("High inclination: Investigate possible cometary origin")
            
            if 'perihelion' in feature['feature'] and feature['direction'] == 'low':
                recommendations.append("Very close perihelion: Priority for close approach monitoring")
        
        if not recommendations:
            recommendations.append("Standard monitoring protocol is sufficient")
        
        return recommendations
    
    def _initialize_default_stats(self):
        """Initialize with approximate population statistics"""
        # Based on typical NEO population
        self.feature_names = [
            'eccentricity', 'semi_major_axis', 'inclination', 
            'longitude_ascending', 'argument_perihelion', 'mean_anomaly',
            'perihelion_distance', 'aphelion_distance', 'orbital_period',
            'mean_motion', 'absolute_magnitude', 'diameter'
        ]
        
        self.feature_stats = {
            'eccentricity': {'mean': 0.25, 'std': 0.15, 'median': 0.22},
            'semi_major_axis': {'mean': 1.5, 'std': 0.8, 'median': 1.3},
            'inclination': {'mean': 15, 'std': 12, 'median': 10},
            'perihelion_distance': {'mean': 0.8, 'std': 0.5, 'median': 0.7},
            'aphelion_distance': {'mean': 2.5, 'std': 1.5, 'median': 2.0},
            'orbital_period': {'mean': 600, 'std': 400, 'median': 500},
            'absolute_magnitude': {'mean': 20, 'std': 3, 'median': 20},
            'diameter': {'mean': 0.3, 'std': 0.4, 'median': 0.15}
        }
        
        self.is_fitted = True


# Singleton instance
anomaly_detector = AnomalyDetector()


def detect_anomalies(features: np.ndarray, asteroid_id: str = None) -> Dict:
    """Convenience function for anomaly detection"""
    return anomaly_detector.detect_anomaly(features, asteroid_id)
