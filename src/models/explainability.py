"""
ML Model Explainability Module
Provides SHAP values, attention weights, and feature importance analysis for GNN predictions
"""

import torch
import numpy as np
from typing import Dict, List, Tuple, Optional
import pandas as pd
from torch_geometric.data import Data
from pathlib import Path
import sys

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.gnn_model import ATISGNN


class ModelExplainer:
    """Explains GNN model predictions using various techniques"""
    
    def __init__(self, model_path: str = "outputs/best_model.pth", device: str = "cpu"):
        self.device = device
        self.model = ATISGNN(
            in_channels=17,
            hidden_channels=64,
            latent_dim=32,
            heads=4
        ).to(device)
        
        # Load trained model
        try:
            checkpoint = torch.load(model_path, map_location=device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()
        except:
            print(f"Warning: Could not load model from {model_path}")
    
    def extract_attention_weights(self, graph_data: Data) -> Dict[str, np.ndarray]:
        """
        Extract attention weights from GNN layers
        Returns attention patterns for each layer
        """
        self.model.eval()
        attention_weights = {}
        
        with torch.no_grad():
            x = graph_data.x.to(self.device)
            edge_index = graph_data.edge_index.to(self.device)
            edge_attr = graph_data.edge_attr.to(self.device)
            
            # Forward pass through each layer and capture attention
            for i, conv in enumerate(self.model.convs):
                # Get attention weights from the layer
                # This is a simplified version - actual implementation depends on GNN layer type
                out = conv(x, edge_index, edge_attr)
                
                # Calculate attention as normalized edge importance
                if hasattr(conv, '_alpha') and conv._alpha is not None:
                    attention = conv._alpha.cpu().numpy()
                else:
                    # Approximate attention from output changes
                    attention = self._approximate_attention(x, out, edge_index)
                
                attention_weights[f'layer_{i+1}'] = attention
                x = out
        
        return attention_weights
    
    def _approximate_attention(self, x_in: torch.Tensor, x_out: torch.Tensor, 
                               edge_index: torch.Tensor) -> np.ndarray:
        """Approximate attention weights from input/output changes"""
        # Calculate magnitude of change for each node
        change = torch.norm(x_out - x_in, dim=1)
        
        # Edge attention is the average of source and target node changes
        src, dst = edge_index
        edge_attention = (change[src] + change[dst]) / 2
        
        # Normalize to [0, 1]
        edge_attention = edge_attention / (edge_attention.max() + 1e-8)
        
        return edge_attention.cpu().numpy()
    
    def compute_feature_importance(self, graph_data: Data, 
                                   target_node: int) -> Dict[str, float]:
        """
        Compute feature importance using gradient-based attribution
        Higher values indicate features that strongly influence the prediction
        """
        self.model.eval()
        
        # Enable gradient computation for input features
        x = graph_data.x.clone().detach().requires_grad_(True).to(self.device)
        edge_index = graph_data.edge_index.to(self.device)
        edge_attr = graph_data.edge_attr.to(self.device)
        
        # Forward pass
        output = self.model(x, edge_index, edge_attr)
        target_output = output[target_node]
        
        # Backward pass
        target_output.backward()
        
        # Feature importance is the gradient magnitude
        importance = torch.abs(x.grad[target_node]).cpu().numpy()
        
        # Map to feature names
        feature_names = [
            'eccentricity', 'semi_major_axis', 'inclination', 
            'longitude_ascending', 'argument_perihelion', 'mean_anomaly',
            'perihelion_distance', 'aphelion_distance', 'orbital_period',
            'mean_motion', 'absolute_magnitude', 'diameter'
        ]
        
        importance_dict = {
            name: float(imp) for name, imp in zip(feature_names, importance)
        }
        
        # Normalize to percentages
        total = sum(importance_dict.values())
        if total > 0:
            importance_dict = {k: v/total * 100 for k, v in importance_dict.items()}
        
        return importance_dict
    
    def compute_shap_values(self, graph_data: Data, target_node: int,
                           num_samples: int = 100) -> Dict[str, float]:
        """
        Compute SHAP-like values using permutation importance
        This is a simplified version suitable for graph neural networks
        """
        self.model.eval()
        
        with torch.no_grad():
            # Get baseline prediction
            x = graph_data.x.to(self.device)
            edge_index = graph_data.edge_index.to(self.device)
            edge_attr = graph_data.edge_attr.to(self.device)
            
            baseline_pred = self.model(x, edge_index, edge_attr)[target_node].item()
            
            feature_names = [
                'eccentricity', 'semi_major_axis', 'inclination', 
                'longitude_ascending', 'argument_perihelion', 'mean_anomaly',
                'perihelion_distance', 'aphelion_distance', 'orbital_period',
                'mean_motion', 'absolute_magnitude', 'diameter'
            ]
            
            shap_values = {}
            
            # For each feature, compute impact of masking it
            for i, feature_name in enumerate(feature_names):
                impacts = []
                
                for _ in range(num_samples):
                    # Create perturbed input by replacing feature with random value
                    x_perturbed = x.clone()
                    
                    # Random perturbation from same distribution
                    random_idx = np.random.randint(0, x.shape[0])
                    x_perturbed[target_node, i] = x[random_idx, i]
                    
                    # Prediction with perturbed feature
                    perturbed_pred = self.model(x_perturbed, edge_index, edge_attr)[target_node].item()
                    
                    # Impact is the difference
                    impacts.append(baseline_pred - perturbed_pred)
                
                # SHAP value is the average impact
                shap_values[feature_name] = np.mean(impacts)
            
            return shap_values
    
    def explain_prediction(self, graph_data: Data, target_node: int,
                          asteroid_id: str = None) -> Dict:
        """
        Generate comprehensive explanation for a prediction
        Combines multiple explainability techniques
        """
        # Get prediction
        self.model.eval()
        with torch.no_grad():
            x = graph_data.x.to(self.device)
            edge_index = graph_data.edge_index.to(self.device)
            edge_attr = graph_data.edge_attr.to(self.device)
            
            prediction = self.model(x, edge_index, edge_attr)[target_node].item()
        
        # Get various explanations
        feature_importance = self.compute_feature_importance(graph_data, target_node)
        shap_values = self.compute_shap_values(graph_data, target_node)
        attention_weights = self.extract_attention_weights(graph_data)
        
        # Identify most influential features
        sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        top_features = sorted_importance[:5]
        
        # Generate human-readable explanation
        explanation_text = self._generate_explanation_text(
            prediction, top_features, shap_values
        )
        
        return {
            'asteroid_id': asteroid_id,
            'prediction': float(prediction),
            'prediction_label': 'High Threat' if prediction > 0.7 else 'Medium Threat' if prediction > 0.4 else 'Low Threat',
            'confidence': self._calculate_confidence(prediction),
            'feature_importance': feature_importance,
            'shap_values': shap_values,
            'attention_weights': {k: v.tolist() for k, v in attention_weights.items()},
            'top_influential_features': [
                {'feature': name, 'importance': value} for name, value in top_features
            ],
            'explanation_text': explanation_text
        }
    
    def _calculate_confidence(self, prediction: float) -> float:
        """Calculate prediction confidence based on distance from decision boundary"""
        # Confidence is higher when prediction is far from 0.5
        distance_from_boundary = abs(prediction - 0.5)
        confidence = min(1.0, distance_from_boundary * 2)
        return float(confidence)
    
    def _generate_explanation_text(self, prediction: float, 
                                   top_features: List[Tuple[str, float]],
                                   shap_values: Dict[str, float]) -> str:
        """Generate human-readable explanation"""
        threat_level = 'high' if prediction > 0.7 else 'medium' if prediction > 0.4 else 'low'
        
        explanation = f"This asteroid has a {threat_level} threat score of {prediction:.2%}. "
        
        # Identify key factors
        positive_factors = [f for f, v in shap_values.items() if v > 0]
        negative_factors = [f for f, v in shap_values.items() if v < 0]
        
        if positive_factors:
            top_positive = sorted([(f, shap_values[f]) for f in positive_factors], 
                                 key=lambda x: x[1], reverse=True)[:3]
            explanation += "The threat score is primarily driven by: "
            explanation += ", ".join([f.replace('_', ' ') for f, _ in top_positive])
            explanation += ". "
        
        if negative_factors:
            top_negative = sorted([(f, shap_values[f]) for f in negative_factors], 
                                 key=lambda x: x[1])[:2]
            explanation += "Factors reducing the threat include: "
            explanation += ", ".join([f.replace('_', ' ') for f, _ in top_negative])
            explanation += ". "
        
        # Add context from top features
        if top_features:
            explanation += f"The most influential factor is {top_features[0][0].replace('_', ' ')} "
            explanation += f"({top_features[0][1]:.1f}% of prediction influence)."
        
        return explanation


# Singleton instance
explainer = ModelExplainer()


def get_explanation(graph_data: Data, target_node: int, 
                   asteroid_id: str = None) -> Dict:
    """Convenience function to get prediction explanation"""
    return explainer.explain_prediction(graph_data, target_node, asteroid_id)
