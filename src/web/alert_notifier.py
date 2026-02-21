"""
Real-Time Alert Notification System
Monitors threats and sends WebSocket alerts for critical events
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)

class AlertNotifier:
    """
    Monitors threat scores and sends real-time alerts through WebSocket
    """
    
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.alert_history: List[Dict] = []
        self.max_history = 100
        self.previous_threats: Dict[str, float] = {}  # spkid -> threat_score
        
        # Alert thresholds
        self.CRITICAL_THRESHOLD = 0.9
        self.HIGH_THRESHOLD = 0.7
        self.MEDIUM_THRESHOLD = 0.5
        
        # Rate limiting
        self.last_alert_time: Dict[str, datetime] = {}
        self.min_alert_interval = 300  # 5 minutes between duplicate alerts
        
    async def monitor_threats(self, threat_data: np.ndarray, spkids: np.ndarray, 
                             names: Optional[np.ndarray] = None):
        """
        Monitor current threat levels and send alerts for changes
        
        Args:
            threat_data: Array of threat scores
            spkids: Array of SPKID identifiers
            names: Optional array of asteroid names
        """
        current_time = datetime.now()
        alerts_sent = 0
        
        for i, (spkid, threat_score) in enumerate(zip(spkids, threat_data)):
            spkid_str = str(spkid)
            previous_score = self.previous_threats.get(spkid_str, 0.0)
            
            # Check for critical threshold crossings
            if threat_score >= self.CRITICAL_THRESHOLD and previous_score < self.CRITICAL_THRESHOLD:
                if self._should_send_alert(spkid_str, current_time):
                    name = names[i] if names is not None else f"Object {spkid_str}"
                    await self._send_critical_alert(spkid_str, name, threat_score)
                    alerts_sent += 1
            
            # Check for significant increases (>0.1 increase)
            elif threat_score - previous_score > 0.1 and threat_score >= self.HIGH_THRESHOLD:
                if self._should_send_alert(spkid_str, current_time):
                    name = names[i] if names is not None else f"Object {spkid_str}"
                    await self._send_increase_alert(spkid_str, name, previous_score, threat_score)
                    alerts_sent += 1
            
            # Update previous threat scores
            self.previous_threats[spkid_str] = float(threat_score)
        
        if alerts_sent > 0:
            logger.info(f"Sent {alerts_sent} real-time alerts")
    
    def _should_send_alert(self, spkid: str, current_time: datetime) -> bool:
        """
        Check if enough time has passed since last alert for this object
        """
        last_time = self.last_alert_time.get(spkid)
        if last_time is None:
            return True
        
        elapsed_seconds = (current_time - last_time).total_seconds()
        return elapsed_seconds >= self.min_alert_interval
    
    async def _send_critical_alert(self, spkid: str, name: str, threat_score: float):
        """
        Send critical threat alert
        """
        alert_data = {
            'id': f"alert_{datetime.now().timestamp()}",
            'level': 'critical',
            'type': 'critical_threshold',
            'spkid': spkid,
            'name': name,
            'threat_score': float(threat_score),
            'message': f"⚠️ CRITICAL THREAT: {name} has reached threat level {threat_score*100:.1f}%",
            'timestamp': datetime.now().isoformat(),
            'actions': [
                {'label': 'View Details', 'url': f'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={spkid}'},
                {'label': 'Add to Watchlist', 'action': 'add_watchlist'}
            ]
        }
        
        # Add to history
        self._add_to_history(alert_data)
        
        # Broadcast to all users subscribed to alerts
        await self.connection_manager.broadcast_alert(alert_data)
        
        # Update last alert time
        self.last_alert_time[spkid] = datetime.now()
        
        logger.warning(f"CRITICAL ALERT: {name} ({spkid}) - {threat_score*100:.1f}%")
    
    async def _send_increase_alert(self, spkid: str, name: str, 
                                   previous_score: float, new_score: float):
        """
        Send alert for significant threat increase
        """
        increase = new_score - previous_score
        
        alert_data = {
            'id': f"alert_{datetime.now().timestamp()}",
            'level': 'high',
            'type': 'threat_increase',
            'spkid': spkid,
            'name': name,
            'threat_score': float(new_score),
            'previous_score': float(previous_score),
            'increase': float(increase),
            'message': f"⚡ THREAT INCREASE: {name} threat level increased by {increase*100:.1f}% to {new_score*100:.1f}%",
            'timestamp': datetime.now().isoformat(),
            'actions': [
                {'label': 'View Details', 'url': f'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={spkid}'},
            ]
        }
        
        # Add to history
        self._add_to_history(alert_data)
        
        # Broadcast to all users subscribed to alerts
        await self.connection_manager.broadcast_alert(alert_data)
        
        # Update last alert time
        self.last_alert_time[spkid] = datetime.now()
        
        logger.warning(f"THREAT INCREASE: {name} ({spkid}) - {previous_score*100:.1f}% → {new_score*100:.1f}%")
    
    async def send_system_alert(self, message: str, level: str = 'info'):
        """
        Send system-wide alert (e.g., data updates, system status)
        
        Args:
            message: Alert message
            level: Alert level (info, warning, error, critical)
        """
        alert_data = {
            'id': f"system_alert_{datetime.now().timestamp()}",
            'level': level,
            'type': 'system',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to history
        self._add_to_history(alert_data)
        
        # Broadcast to all users
        await self.connection_manager.broadcast_alert(alert_data)
        
        logger.info(f"System alert ({level}): {message}")
    
    def _add_to_history(self, alert_data: Dict):
        """
        Add alert to history, maintaining max size
        """
        self.alert_history.append(alert_data)
        
        # Keep only recent alerts
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
    
    def get_alert_history(self, limit: int = 50) -> List[Dict]:
        """
        Get recent alert history
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent alerts
        """
        return self.alert_history[-limit:]
    
    def get_alert_stats(self) -> Dict:
        """
        Get alert statistics
        
        Returns:
            Dictionary with alert counts by level
        """
        stats = {
            'total': len(self.alert_history),
            'critical': 0,
            'high': 0,
            'medium': 0,
            'info': 0
        }
        
        for alert in self.alert_history:
            level = alert.get('level', 'info')
            if level in stats:
                stats[level] += 1
        
        return stats
    
    async def check_anomalies(self, anomaly_scores: np.ndarray, spkids: np.ndarray,
                             threshold: float = 0.8):
        """
        Check for anomalous behavior detected by ML models
        
        Args:
            anomaly_scores: Array of anomaly scores (0-1, higher = more anomalous)
            spkids: Array of SPKID identifiers
            threshold: Anomaly score threshold for alerts
        """
        anomalous_indices = np.where(anomaly_scores > threshold)[0]
        
        if len(anomalous_indices) > 0:
            for idx in anomalous_indices:
                spkid = str(spkids[idx])
                score = float(anomaly_scores[idx])
                
                alert_data = {
                    'id': f"anomaly_alert_{datetime.now().timestamp()}",
                    'level': 'warning',
                    'type': 'anomaly_detected',
                    'spkid': spkid,
                    'anomaly_score': score,
                    'message': f"🔍 Anomalous behavior detected for object {spkid} (score: {score*100:.1f}%)",
                    'timestamp': datetime.now().isoformat(),
                    'actions': [
                        {'label': 'Investigate', 'url': f'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={spkid}'}
                    ]
                }
                
                self._add_to_history(alert_data)
                await self.connection_manager.broadcast_alert(alert_data)
            
            logger.info(f"Detected {len(anomalous_indices)} anomalies")


# Global alert notifier instance (initialized in main.py)
alert_notifier: Optional[AlertNotifier] = None


def get_alert_notifier() -> Optional[AlertNotifier]:
    """Get the global alert notifier instance"""
    return alert_notifier


def initialize_alert_notifier(connection_manager) -> AlertNotifier:
    """
    Initialize the global alert notifier
    
    Args:
        connection_manager: WebSocket connection manager instance
        
    Returns:
        Initialized AlertNotifier instance
    """
    global alert_notifier
    alert_notifier = AlertNotifier(connection_manager)
    logger.info("Alert notifier initialized")
    return alert_notifier
