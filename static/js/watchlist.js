// Watchlist with WebSocket Real-Time Updates

async function updateWatchlist() {
    const res = await fetch("/api/watchlist");
    const data = await res.json();
    updateWatchlistTable(data.watchlist);
}

function updateWatchlistTable(watchlist) {
    let table = document.getElementById("watchlist");
    table.innerHTML = "";

    watchlist.forEach(obj => {
        const threatColor = obj.threat_score > 0.7 ? '#ff3333' : 
                           obj.threat_score > 0.4 ? '#ffa500' : '#00ff7f';
        
        table.innerHTML += `<tr style="border-left: 3px solid ${threatColor};">
            <td><a href="${obj.url}" target="_blank" style="color: var(--electric-blue); text-decoration: none;">${obj.name} ↗</a></td>
            <td>${obj.spkid}</td>
            <td style="color: ${threatColor}; font-weight: bold;">${(obj.threat_score * 100).toFixed(1)}%</td>
            <td>${obj.moid.toFixed(4)} AU</td>
        </tr>`;
    });
}

// Subscribe to WebSocket updates when connected
window.addEventListener('ws_connected', () => {
    console.log('Subscribing to watchlist updates...');
    wsClient.subscribe('watchlist');
});

// Handle watchlist updates from WebSocket
window.addEventListener('ws_watchlist_update', (event) => {
    console.log('Received watchlist update:', event.detail);
    updateWatchlistTable(event.detail);
    
    // Update last update timestamp
    const now = new Date();
    const timeEl = document.getElementById('lastUpdateTime');
    if (timeEl) {
        timeEl.textContent = now.toLocaleTimeString();
    }
});

// Initial load
updateWatchlist();