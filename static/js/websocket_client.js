// WebSocket Client for Real-Time Updates

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.connectionId = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000; // 3 seconds
        this.subscriptions = new Set();
        this.messageHandlers = new Map();
        this.statusElement = null;
    }

    connect(url = null) {
        // Default WebSocket URL
        if (!url) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            url = `${protocol}//${host}/api/ws`;
        }

        try {
            this.ws = new WebSocket(url);
            
            this.ws.onopen = () => this.onOpen();
            this.ws.onmessage = (event) => this.onMessage(event);
            this.ws.onerror = (error) => this.onError(error);
            this.ws.onclose = () => this.onClose();
            
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.scheduleReconnect();
        }
    }

    onOpen() {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.updateStatus('connected', '🟢 Connected');
        
        // Resubscribe to topics after reconnection
        this.subscriptions.forEach(topic => {
            this.subscribe(topic);
        });

        // Trigger connected event
        this.triggerEvent('connected');
    }

    onMessage(event) {
        try {
            const message = JSON.parse(event.data);
            const type = message.type;

            // Handle message based on type
            switch (type) {
                case 'connection':
                    this.connectionId = message.connection_id;
                    console.log('Connection ID:', this.connectionId);
                    break;

                case 'threat_update':
                    this.handleThreatUpdate(message.data);
                    break;

                case 'watchlist_update':
                    this.handleWatchlistUpdate(message.data);
                    break;

                case 'alert':
                    this.handleAlert(message.data);
                    break;

                case 'system_status':
                    this.handleSystemStatus(message.data);
                    break;

                case 'pong':
                    // Heartbeat response
                    break;

                case 'subscription_response':
                    console.log(`Subscribed to ${message.topic}:`, message.success);
                    break;

                default:
                    // Call registered handlers
                    if (this.messageHandlers.has(type)) {
                        this.messageHandlers.get(type)(message);
                    }
            }

        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    onError(error) {
        console.error('WebSocket error:', error);
        this.updateStatus('error', '🔴 Error');
    }

    onClose() {
        console.log('WebSocket disconnected');
        this.isConnected = false;
        this.updateStatus('disconnected', '🟡 Disconnected');
        this.triggerEvent('disconnected');
        
        // Attempt reconnection
        this.scheduleReconnect();
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting in ${this.reconnectDelay/1000}s... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            this.updateStatus('reconnecting', `🟡 Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay);
        } else {
            console.error('Max reconnection attempts reached');
            this.updateStatus('failed', '🔴 Connection Failed');
        }
    }

    send(message) {
        if (this.isConnected && this.ws) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected. Message not sent:', message);
        }
    }

    subscribe(topic) {
        this.subscriptions.add(topic);
        this.send({
            type: 'subscribe',
            topic: topic
        });
    }

    unsubscribe(topic) {
        this.subscriptions.delete(topic);
        this.send({
            type: 'unsubscribe',
            topic: topic
        });
    }

    ping() {
        this.send({ type: 'ping' });
    }

    getStats() {
        this.send({ type: 'get_stats' });
    }

    registerHandler(messageType, handler) {
        this.messageHandlers.set(messageType, handler);
    }

    handleThreatUpdate(data) {
        // Trigger custom event
        this.triggerEvent('threat_update', data);
    }

    handleWatchlistUpdate(data) {
        // Update watchlist table if present
        if (typeof updateWatchlistTable === 'function') {
            updateWatchlistTable(data);
        }
        this.triggerEvent('watchlist_update', data);
    }

    handleAlert(data) {
        // Show alert notification
        this.showNotification('Alert', data.message || 'New asteroid threat detected!', 'warning');
        this.triggerEvent('alert', data);
    }

    handleSystemStatus(data) {
        // Update status display if present
        if (document.getElementById('wsConnectionCount')) {
            document.getElementById('wsConnectionCount').textContent = data.active_connections || 0;
        }
        this.triggerEvent('system_status', data);
    }

    triggerEvent(eventName, data = null) {
        const event = new CustomEvent(`ws_${eventName}`, { detail: data });
        window.dispatchEvent(event);
    }

    showNotification(title, message, type = 'info') {
        // Check if browser supports notifications
        if (!('Notification' in window)) {
            console.log('Notifications not supported');
            return;
        }

        // Request permission if needed
        if (Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: '/static/favicon.ico',
                badge: '/static/badge.png'
            });
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    new Notification(title, {
                        body: message,
                        icon: '/static/favicon.ico'
                    });
                }
            });
        }

        // Also show in-page notification
        this.showInPageAlert(message, type);
    }

    showInPageAlert(message, type = 'info') {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `ws-alert ws-alert-${type}`;
        alert.textContent = message;
        alert.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: rgba(0, 212, 255, 0.9);
            color: white;
            border-radius: 4px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
            max-width: 300px;
            font-family: 'Orbitron', monospace;
        `;

        if (type === 'warning') {
            alert.style.background = 'rgba(255, 165, 0, 0.9)';
        } else if (type === 'error') {
            alert.style.background = 'rgba(255, 51, 51, 0.9)';
        }

        document.body.appendChild(alert);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            alert.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    }

    updateStatus(status, text) {
        // Update status element if exists
        if (this.statusElement) {
            this.statusElement.textContent = text;
            this.statusElement.className = `ws-status ws-status-${status}`;
        }

        // Update all elements with class 'ws-status-indicator'
        document.querySelectorAll('.ws-status-indicator').forEach(el => {
            el.textContent = text;
            el.className = `ws-status-indicator ws-status-${status}`;
        });
    }

    setStatusElement(element) {
        this.statusElement = element;
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Global WebSocket client instance
const wsClient = new WebSocketClient();

// Auto-connect on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        wsClient.connect();
    });
} else {
    wsClient.connect();
}

// Heartbeat every 30 seconds
setInterval(() => {
    if (wsClient.isConnected) {
        wsClient.ping();
    }
}, 30000);

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .ws-status {
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-family: 'Orbitron', monospace;
        font-size: 0.9rem;
    }

    .ws-status-connected {
        color: #00ff7f;
    }

    .ws-status-disconnected {
        color: #ffa500;
    }

    .ws-status-reconnecting {
        color: #ffa500;
    }

    .ws-status-error, .ws-status-failed {
        color: #ff3333;
    }
`;
document.head.appendChild(style);
