"""
Analytics Engine for Historical Threat Analysis
Provides trend analysis, statistical insights, and data export capabilities
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import logging

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Analyzes historical threat data and generates insights
    """
    
    def __init__(self):
        self.threat_history: List[Dict] = []
        self.max_history_days = 30
        
    def record_snapshot(self, threat_data: np.ndarray, spkids: np.ndarray, 
                       names: Optional[np.ndarray] = None):
        """
        Record a snapshot of current threat levels
        
        Args:
            threat_data: Array of threat scores
            spkids: Array of SPKID identifiers
            names: Optional array of asteroid names
        """
        timestamp = datetime.now()
        
        snapshot = {
            'timestamp': timestamp.isoformat(),
            'objects': []
        }
        
        for i, (spkid, threat) in enumerate(zip(spkids, threat_data)):
            obj_data = {
                'spkid': str(spkid),
                'threat_score': float(threat),
            }
            if names is not None:
                obj_data['name'] = str(names[i])
            
            snapshot['objects'].append(obj_data)
        
        self.threat_history.append(snapshot)
        
        # Clean old data
        self._clean_old_snapshots()
        
        logger.debug(f"Recorded threat snapshot with {len(snapshot['objects'])} objects")
    
    def _clean_old_snapshots(self):
        """Remove snapshots older than max_history_days"""
        if not self.threat_history:
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.max_history_days)
        
        self.threat_history = [
            snapshot for snapshot in self.threat_history
            if datetime.fromisoformat(snapshot['timestamp']) > cutoff_date
        ]
    
    def get_threat_trends(self, spkid: str, days: int = 7) -> Dict:
        """
        Get threat trend for a specific object
        
        Args:
            spkid: Object SPKID identifier
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend data points and statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        trend_data = []
        for snapshot in self.threat_history:
            snapshot_time = datetime.fromisoformat(snapshot['timestamp'])
            if snapshot_time < cutoff_date:
                continue
            
            # Find this object in the snapshot
            for obj in snapshot['objects']:
                if obj['spkid'] == spkid:
                    trend_data.append({
                        'timestamp': snapshot['timestamp'],
                        'threat_score': obj['threat_score']
                    })
                    break
        
        if not trend_data:
            return {
                'spkid': spkid,
                'data_points': 0,
                'trend': []
            }
        
        # Calculate statistics
        scores = [point['threat_score'] for point in trend_data]
        
        return {
            'spkid': spkid,
            'data_points': len(trend_data),
            'trend': trend_data,
            'statistics': {
                'current': scores[-1] if scores else 0,
                'min': min(scores) if scores else 0,
                'max': max(scores) if scores else 0,
                'mean': np.mean(scores) if scores else 0,
                'std': np.std(scores) if scores else 0,
                'change': scores[-1] - scores[0] if len(scores) > 1 else 0,
                'percent_change': ((scores[-1] - scores[0]) / scores[0] * 100) if len(scores) > 1 and scores[0] != 0 else 0
            }
        }
    
    def get_top_movers(self, limit: int = 10, direction: str = 'increase') -> List[Dict]:
        """
        Get objects with largest threat changes
        
        Args:
            limit: Maximum number of results
            direction: 'increase' or 'decrease'
            
        Returns:
            List of objects with largest changes
        """
        if len(self.threat_history) < 2:
            return []
        
        # Compare most recent snapshot with oldest
        recent = self.threat_history[-1]
        old = self.threat_history[0]
        
        # Build lookup for old scores
        old_scores = {obj['spkid']: obj['threat_score'] for obj in old['objects']}
        
        movers = []
        for obj in recent['objects']:
            spkid = obj['spkid']
            current_score = obj['threat_score']
            old_score = old_scores.get(spkid, current_score)
            
            change = current_score - old_score
            
            if direction == 'increase' and change > 0:
                movers.append({
                    'spkid': spkid,
                    'name': obj.get('name', f"Object {spkid}"),
                    'current_threat': current_score,
                    'previous_threat': old_score,
                    'change': change,
                    'percent_change': (change / old_score * 100) if old_score != 0 else 0
                })
            elif direction == 'decrease' and change < 0:
                movers.append({
                    'spkid': spkid,
                    'name': obj.get('name', f"Object {spkid}"),
                    'current_threat': current_score,
                    'previous_threat': old_score,
                    'change': change,
                    'percent_change': (change / old_score * 100) if old_score != 0 else 0
                })
        
        # Sort by absolute change
        movers.sort(key=lambda x: abs(x['change']), reverse=True)
        
        return movers[:limit]
    
    def get_system_statistics(self) -> Dict:
        """
        Get overall system statistics
        
        Returns:
            Dictionary with high-level statistics
        """
        if not self.threat_history:
            return {
                'snapshots': 0,
                'total_objects': 0,
                'avg_threat': 0,
                'critical_count': 0,
                'high_count': 0,
                'monitoring_duration_days': 0
            }
        
        recent = self.threat_history[-1]
        oldest = self.threat_history[0]
        
        threats = [obj['threat_score'] for obj in recent['objects']]
        
        duration = datetime.fromisoformat(recent['timestamp']) - datetime.fromisoformat(oldest['timestamp'])
        
        return {
            'snapshots': len(self.threat_history),
            'total_objects': len(recent['objects']),
            'avg_threat': float(np.mean(threats)) if threats else 0,
            'max_threat': float(np.max(threats)) if threats else 0,
            'critical_count': sum(1 for t in threats if t >= 0.9),
            'high_count': sum(1 for t in threats if 0.7 <= t < 0.9),
            'medium_count': sum(1 for t in threats if 0.5 <= t < 0.7),
            'low_count': sum(1 for t in threats if t < 0.5),
            'monitoring_duration_days': duration.days,
            'first_snapshot': oldest['timestamp'],
            'latest_snapshot': recent['timestamp']
        }
    
    def generate_time_series_chart_data(self, days: int = 7) -> Dict:
        """
        Generate data for time series charts
        
        Args:
            days: Number of days to include
            
        Returns:
            Chart-ready data structure
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        timestamps = []
        avg_threats = []
        max_threats = []
        critical_counts = []
        
        for snapshot in self.threat_history:
            snapshot_time = datetime.fromisoformat(snapshot['timestamp'])
            if snapshot_time < cutoff_date:
                continue
            
            threats = [obj['threat_score'] for obj in snapshot['objects']]
            
            timestamps.append(snapshot['timestamp'])
            avg_threats.append(float(np.mean(threats)) if threats else 0)
            max_threats.append(float(np.max(threats)) if threats else 0)
            critical_counts.append(sum(1 for t in threats if t >= 0.9))
        
        return {
            'labels': timestamps,
            'datasets': [
                {
                    'label': 'Average Threat',
                    'data': avg_threats,
                    'borderColor': '#00bfff',
                    'backgroundColor': 'rgba(0,191,255,0.1)',
                    'tension': 0.4
                },
                {
                    'label': 'Maximum Threat',
                    'data': max_threats,
                    'borderColor': '#ff3333',
                    'backgroundColor': 'rgba(255,51,51,0.1)',
                    'tension': 0.4
                },
                {
                    'label': 'Critical Objects',
                    'data': critical_counts,
                    'borderColor': '#ffa500',
                    'backgroundColor': 'rgba(255,165,0,0.1)',
                    'type': 'bar',
                    'yAxisID': 'y1'
                }
            ]
        }
    
    def export_to_csv(self, spkid: Optional[str] = None) -> str:
        """
        Export threat history to CSV format
        
        Args:
            spkid: Optional SPKID to filter by single object
            
        Returns:
            CSV string
        """
        rows = []
        
        for snapshot in self.threat_history:
            timestamp = snapshot['timestamp']
            for obj in snapshot['objects']:
                if spkid and obj['spkid'] != spkid:
                    continue
                
                rows.append({
                    'timestamp': timestamp,
                    'spkid': obj['spkid'],
                    'name': obj.get('name', ''),
                    'threat_score': obj['threat_score']
                })
        
        if not rows:
            return "timestamp,spkid,name,threat_score\n"
        
        df = pd.DataFrame(rows)
        return df.to_csv(index=False)
    
    def export_to_json(self, days: int = 7) -> str:
        """
        Export recent threat history to JSON
        
        Args:
            days: Number of days to include
            
        Returns:
            JSON string
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_snapshots = [
            snapshot for snapshot in self.threat_history
            if datetime.fromisoformat(snapshot['timestamp']) > cutoff_date
        ]
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'days': days,
            'snapshots': recent_snapshots,
            'summary': self.get_system_statistics()
        }
        
        return json.dumps(export_data, indent=2)


# Global analytics engine instance
analytics_engine: Optional[AnalyticsEngine] = None


def get_analytics_engine() -> Optional[AnalyticsEngine]:
    """Get the global analytics engine instance"""
    return analytics_engine


def initialize_analytics_engine() -> AnalyticsEngine:
    """Initialize the global analytics engine"""
    global analytics_engine
    analytics_engine = AnalyticsEngine()
    logger.info("Analytics engine initialized")
    return analytics_engine
