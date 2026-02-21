// User Dashboard JavaScript

let currentUser = null;
let authToken = null;

// Check authentication on page load
window.addEventListener('DOMContentLoaded', checkAuth);

function checkAuth() {
    // Get token from localStorage
    authToken = localStorage.getItem('atis_token');
    
    if (authToken) {
        // Verify token and load user data
        loadUserData();
    } else {
        // Show authentication section
        showAuthSection();
    }
}

async function loadUserData() {
    try {
        const response = await fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Invalid token');
        }
        
        currentUser = await response.json();
        showDashboard();
        
    } catch (error) {
        console.error('Auth error:', error);
        // Token invalid, clear and show login
        localStorage.removeItem('atis_token');
        authToken = null;
        showAuthSection();
    }
}

function showAuthSection() {
    document.getElementById('authSection').style.display = 'block';
    document.getElementById('dashboardContent').style.display = 'none';
}

function showDashboard() {
    document.getElementById('authSection').style.display = 'none';
    document.getElementById('dashboardContent').style.display = 'block';
    
    // Update user greeting
    document.getElementById('userGreeting').textContent = `Welcome, ${currentUser.username}!`;
    
    // Load dashboard data
    loadWatchlist();
    loadUserStats();
    loadAlertSettings();
}

function showLogin() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('authMessage').style.display = 'none';
}

function showRegister() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
    document.getElementById('authMessage').style.display = 'none';
}

async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }
        
        const data = await response.json();
        
        // Save token
        authToken = data.access_token;
        localStorage.setItem('atis_token', authToken);
        currentUser = data.user;
        
        showDashboard();
        
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const email = document.getElementById('registerEmail').value;
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;
    const full_name = document.getElementById('registerFullName').value || null;
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, username, password, full_name })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }
        
        const data = await response.json();
        
        showMessage('Registration successful! Please login.', 'success');
        
        // Switch to login form
        setTimeout(() => {
            showLogin();
            document.getElementById('loginEmail').value = email;
        }, 1500);
        
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

function showMessage(message, type) {
    const messageDiv = document.getElementById('authMessage');
    messageDiv.textContent = message;
    messageDiv.style.display = 'block';
    messageDiv.style.background = type === 'error' ? 'rgba(255, 0, 0, 0.2)' : 'rgba(0, 255, 0, 0.2)';
    messageDiv.style.border = type === 'error' ? '1px solid #ff0000' : '1px solid #00ff00';
    messageDiv.style.color = 'white';
}

function logout() {
    localStorage.removeItem('atis_token');
    authToken = null;
    currentUser = null;
    location.reload();
}

async function loadWatchlist() {
    try {
        const response = await fetch('/api/auth/watchlist', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to load watchlist');
        
        const data = await response.json();
        
        document.getElementById('watchlistCount').textContent = `${data.count} asteroid${data.count !== 1 ? 's' : ''}`;
        
        const container = document.getElementById('personalWatchlist');
        
        if (data.watchlist.length === 0) {
            container.innerHTML = `
                <p style="color: rgba(255, 255, 255, 0.5);">
                    Your watchlist is empty. Browse the <a href="/galaxy" style="color: var(--electric-blue);">galaxy</a> 
                    or <a href="/watchlist" style="color: var(--electric-blue);">top threats</a> to add asteroids.
                </p>
            `;
            return;
        }
        
        let html = '<div style="display: grid; gap: 1rem;">';
        
        data.watchlist.forEach((asteroid, idx) => {
            const threatColor = asteroid.threat_score > 0.7 ? '#ff3333' : 
                               asteroid.threat_score > 0.4 ? '#ffa500' : '#00ff7f';
            
            html += `
                <div style="padding: 1.5rem; background: rgba(0, 212, 255, 0.05); border-left: 3px solid ${threatColor}; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <a href="${asteroid.url}" target="_blank" style="color: var(--electric-blue); text-decoration: none; font-size: 1.1rem; font-weight: bold;">
                            ${asteroid.name} ↗
                        </a>
                        <div style="margin-top: 0.5rem; font-size: 0.9rem; color: rgba(255, 255, 255, 0.6);">
                            SPKID: ${asteroid.spkid} • MOID: ${asteroid.moid.toFixed(4)} AU
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: ${threatColor};">
                            ${(asteroid.threat_score * 100).toFixed(1)}%
                        </div>
                        <button onclick="removeFromWatchlist('${asteroid.spkid}')" 
                                style="margin-top: 0.5rem; padding: 0.5rem 1rem; background: var(--danger); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85rem;">
                            Remove
                        </button>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading watchlist:', error);
        document.getElementById('personalWatchlist').innerHTML = 
            '<p style="color: var(--danger);">Error loading watchlist</p>';
    }
}

async function removeFromWatchlist(asteroidId) {
    if (!confirm('Remove this asteroid from your watchlist?')) return;
    
    try {
        const response = await fetch(`/api/auth/watchlist/${asteroidId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to remove asteroid');
        
        // Reload watchlist
        loadWatchlist();
        
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function loadUserStats() {
    if (!currentUser) return;
    
    // Format dates
    const createdDate = new Date(currentUser.created_at);
    const lastLoginDate = currentUser.last_login ? new Date(currentUser.last_login) : null;
    
    document.getElementById('accountCreated').textContent = createdDate.toLocaleDateString();
    document.getElementById('lastLogin').textContent = lastLoginDate ? lastLoginDate.toLocaleString() : 'First login';
    document.getElementById('watchlistSize').textContent = currentUser.watchlist.length;
}

function loadAlertSettings() {
    if (!currentUser || !currentUser.alert_settings) return;
    
    const settings = currentUser.alert_settings;
    
    document.getElementById('emailEnabled').checked = settings.email_enabled || false;
    document.getElementById('notifyNewDetections').checked = settings.notify_new_detections || false;
    
    const minThreat = settings.min_threat_score || 0.7;
    document.getElementById('minThreatScore').value = minThreat;
    document.getElementById('threatScoreValue').textContent = (minThreat * 100).toFixed(0) + '%';
}

async function updateAlertSettings(event) {
    event.preventDefault();
    
    const alertSettings = {
        email_enabled: document.getElementById('emailEnabled').checked,
        notify_new_detections: document.getElementById('notifyNewDetections').checked,
        min_threat_score: parseFloat(document.getElementById('minThreatScore').value)
    };
    
    try {
        const response = await fetch('/api/auth/alert-settings', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(alertSettings)
        });
        
        if (!response.ok) throw new Error('Failed to update settings');
        
        alert('Alert settings updated successfully!');
        
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Add to watchlist function (can be called from other pages)
window.addToWatchlist = async function(asteroidId) {
    if (!authToken) {
        alert('Please login to add asteroids to your watchlist');
        location.href = '/user-dashboard';
        return;
    }
    
    try {
        const response = await fetch(`/api/auth/watchlist/${asteroidId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to add to watchlist');
        
        alert('Added to your watchlist!');
        
    } catch (error) {
        alert('Error: ' + error.message);
    }
};
