"""
Ensemble Prediction System
Combines GNN with traditional ML models for robust predictions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import sys
import torch
from torch_geometric.data import Data

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.gnn_model import ATISGNN


class EnsemblePredictor:
    """
    Combines multiple models for robust threat prediction
    - Graph Neural Network (primary)
    - Random Forest (baseline comparison)
    - XGBoost (gradient boosting)
    - Statistical rules (domain knowledge)
    """
    
    def __init__(self, model_path: str = "outputs/best_model.pth", device: str = "cpu"):
        self.device = device
        
        # Load GNN model
        self.gnn_model = ATISGNN(
            in_channels=17,
            hidden_channels=64,
            latent_dim=32,
            heads=4
        ).to(device)
        
        try:
            checkpoint = torch.load(model_path, map_location=device)
            self.gnn_model.load_state_dict(checkpoint['model_state_dict'])
            self.gnn_model.eval()
        except:
            print(f"Warning: Could not load GNN model from {model_path}")
        
        # Model weights (can be tuned based on validation performance)
        self.weights = {
            'gnn': 0.50,      # GNN is primary model
            'random_forest': 0.20,
            'xgboost': 0.20,
            'statistical': 0.10
        }
    
    def predict_gnn(self, graph_data: Data, target_node: int) -> float:
        """GNN prediction"""
        self.gnn_model.eval()
        with torch.no_grad():
            x = graph_data.x.to(self.device)
            edge_index = graph_data.edge_index.to(self.device)
            edge_attr = graph_data.edge_attr.to(self.device)
            
            output = self.gnn_model(x, edge_index, edge_attr)
            prediction = output[target_node].item()
        
        return prediction
    
    def predict_random_forest(self, features: np.ndarray) -> float:
        """
        Random Forest prediction based on orbital features
        This is a simplified rule-based approximation
        """
        # Extract key features
        eccentricity = features[0]
        semi_major_axis = features[1]
        inclination = features[2]
        perihelion_dist = features[6]
        abs_magnitude = features[10]
        diameter = features[11]
        
        # Decision tree logic based on domain knowledge
        threat_score = 0.0
        
        # Perihelion distance (closer = higher threat)
        if perihelion_dist < 0.05:  # Very close
            threat_score += 0.4
        elif perihelion_dist < 0.1:
            threat_score += 0.3
        elif perihelion_dist < 0.2:
            threat_score += 0.15
        
        # Size (larger = higher threat)
        if diameter > 1.0:  # > 1 km
            threat_score += 0.3
        elif diameter > 0.5:
            threat_score += 0.2
        elif diameter > 0.14:  # > 140m (PHA threshold)
            threat_score += 0.1
        
        # Eccentricity (higher = more unpredictable)
        if eccentricity > 0.5:
            threat_score += 0.15
        elif eccentricity > 0.3:
            threat_score += 0.1
        
        # Inclination (lower = closer to Earth's plane)
        if inclination < 5:
            threat_score += 0.15
        elif inclination < 15:
            threat_score += 0.08
        
        return min(1.0, threat_score)
    
    def predict_xgboost(self, features: np.ndarray) -> float:
        """
        XGBoost prediction using gradient boosting logic
        Simplified version using weighted feature combinations
        """
        # Normalize features to [0, 1] range (approximate)
        normalized = features.copy()
        
        # Feature scaling (rough approximation)
        normalized[0] = min(1.0, features[0] / 1.0)  # eccentricity
        normalized[1] = min(1.0, features[1] / 3.0)  # semi-major axis
        normalized[2] = min(1.0, features[2] / 90.0)  # inclination
        normalized[6] = 1.0 - min(1.0, features[6] / 2.0)  # perihelion (inverted)
        normalized[10] = 1.0 - min(1.0, (features[10] - 10) / 20.0)  # H mag (inverted, brighter=larger)
        normalized[11] = min(1.0, features[11] / 2.0)  # diameter
        
        # Gradient boosting approximation: weighted combination with non-linear interactions
        base_score = 0.5
        
        # Tree 1: Proximity-based split
        if normalized[6] > 0.7:  # Close perihelion
            base_score += 0.15 * (1 + normalized[11] * 0.5)  # Boosted by size
        else:
            base_score -= 0.1
        
        # Tree 2: Size-based split
        if normalized[11] > 0.3:
            base_score += 0.12 * (1 + normalized[0] * 0.3)  # Boosted by eccentricity
        else:
            base_score -= 0.05
        
        # Tree 3: Orbital stability
        stability_score = (normalized[0] + normalized[2]/90) / 2
        if stability_score < 0.3:  # Stable orbit
            base_score -= 0.08
        else:
            base_score += 0.1
        
        # Tree 4: Combined risk factors
        combined_risk = (normalized[6] + normalized[11] + normalized[0]) / 3
        base_score += 0.15 * combined_risk
        
        return np.clip(base_score, 0.0, 1.0)
    
    def predict_statistical(self, features: np.ndarray) -> float:
        """
        Statistical rule-based prediction using domain knowledge
        Based on NASA JPL criteria and historical data
        """
        perihelion_dist = features[6]
        diameter = features[11]
        eccentricity = features[0]
        abs_magnitude = features[10]
        
        # PHA (Potentially Hazardous Asteroid) criteria
        is_pha = (perihelion_dist < 0.05) and (diameter > 0.14)
        
        # Torino Scale approximation
        torino_score = 0
        
        if diameter > 1.0:  # Large object
            if perihelion_dist < 0.002:
                torino_score = 10  # Certain collision, global catastrophe
            elif perihelion_dist < 0.01:
                torino_score = 8
            elif perihelion_dist < 0.05:
                torino_score = 5
        elif diameter > 0.5:  # Medium object
            if perihelion_dist < 0.01:
                torino_score = 7
            elif perihelion_dist < 0.05:
                torino_score = 4
        elif diameter > 0.14:  # Small PHA-size
            if perihelion_dist < 0.05:
                torino_score = 3
        
        # Convert Torino (0-10) to threat score (0-1)
        threat_score = torino_score / 10.0
        
        # Adjust for orbital uncertainty (higher eccentricity = less predictable)
        uncertainty_factor = 1.0 + (eccentricity * 0.2)
        threat_score *= uncertainty_factor
        
        return min(1.0, threat_score)
    
    def predict_ensemble(self, graph_data: Data, target_node: int,
                        features: np.ndarray = None) -> Dict:
        """
        Generate ensemble prediction from all models
        Returns individual predictions and weighted average
        """
        # Extract features if not provided
        if features is None:
            features = graph_data.x[target_node].cpu().numpy()
        
        # Get predictions from all models
        predictions = {
            'gnn': self.predict_gnn(graph_data, target_node),
            'random_forest': self.predict_random_forest(features),
            'xgboost': self.predict_xgboost(features),
            'statistical': self.predict_statistical(features)
        }
        
        # Calculate weighted ensemble
        ensemble_score = sum(
            predictions[model] * weight 
            for model, weight in self.weights.items()
        )
        
        # Calculate model agreement (standard deviation)
        pred_values = list(predictions.values())
        agreement = 1.0 - np.std(pred_values)  # High agreement = low std
        
        # Calculate confidence based on agreement
        confidence = self._calculate_confidence(predictions, agreement)
        
        # Identify outlier models
        outliers = self._identify_outliers(predictions, ensemble_score)
        
        return {
            'ensemble_score': float(ensemble_score),
            'individual_predictions': {k: float(v) for k, v in predictions.items()},
            'model_weights': self.weights,
            'agreement': float(agreement),
            'confidence': float(confidence),
            'outlier_models': outliers,
            'recommendation': self._generate_recommendation(ensemble_score, confidence, agreement)
        }
    
    def _calculate_confidence(self, predictions: Dict[str, float], 
                             agreement: float) -> float:
        """Calculate overall prediction confidence"""
        # Confidence factors:
        # 1. Model agreement (high agreement = high confidence)
        # 2. Distance from decision boundary (0.5)
        
        ensemble_score = sum(
            predictions[model] * self.weights[model] 
            for model in predictions
        )
        
        boundary_distance = abs(ensemble_score - 0.5)
        
        # Weighted combination
        confidence = (agreement * 0.6) + (boundary_distance * 2 * 0.4)
        
        return min(1.0, confidence)
    
    def _identify_outliers(self, predictions: Dict[str, float], 
                          ensemble_score: float) -> List[str]:
        """Identify models that disagree significantly with ensemble"""
        outliers = []
        threshold = 0.2  # 20% difference is significant
        
        for model, pred in predictions.items():
            if abs(pred - ensemble_score) > threshold:
                outliers.append(model)
        
        return outliers
    
    def _generate_recommendation(self, ensemble_score: float, 
                                confidence: float, agreement: float) -> str:
        """Generate actionable recommendation"""
        threat_level = 'HIGH' if ensemble_score > 0.7 else 'MEDIUM' if ensemble_score > 0.4 else 'LOW'
        
        recommendation = f"{threat_level} THREAT ({ensemble_score:.1%}). "
        
        if confidence > 0.8:
            recommendation += "High confidence prediction - models agree. "
        elif confidence > 0.5:
            recommendation += "Moderate confidence - some model disagreement. "
        else:
            recommendation += "Low confidence - significant model disagreement. Further analysis recommended. "
        
        if agreement < 0.6:
            recommendation += "WARNING: Models show significant divergence. Manual review suggested."
        
        if ensemble_score > 0.7:
            recommendation += " PRIORITY MONITORING REQUIRED."
        elif ensemble_score > 0.4:
            recommendation += " Continue regular monitoring."
        else:
            recommendation += " Standard monitoring protocol."
        
        return recommendation


# Singleton instance
ensemble_predictor = EnsemblePredictor()


def get_ensemble_prediction(graph_data: Data, target_node: int) -> Dict:
    """Convenience function for ensemble prediction"""
    return ensemble_predictor.predict_ensemble(graph_data, target_node)
