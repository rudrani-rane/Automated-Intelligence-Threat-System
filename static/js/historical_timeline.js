// ============================================
// ATIS - Historical Timeline
// Close Approach Timeline Visualization
// ============================================

let selectedAsteroid = null;
let timelineData = null;

// Chart configuration
const chartLayout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(15,15,30,0.9)',
    font: { family: 'Orbitron, monospace', color: '#00d4ff', size: 12 },
    margin: { l: 70, r: 30, t: 30, b: 70 }
};

const chartConfig = { responsive: true, displayModeBar: false };

// ============================================
// SEARCH FUNCTIONALITY
// ============================================

const searchInput = document.getElementById('asteroidSearch');
const searchResults = document.getElementById('searchResults');
const loadBtn = document.getElementById('loadTimelineBtn');

searchInput.addEventListener('input', async (e) => {
    const query = e.target.value.trim();
    if (query.length < 2) {
        searchResults.innerHTML = '';
        loadBtn.disabled = true;
        return;
    }
    
    try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const results = await res.json();
        
        searchResults.innerHTML = results.slice(0, 5).map(ast => `
            <div class="search-result-item" data-spkid="${ast.spkid}">
                <strong>${ast.name || `SPKID ${ast.spkid}`}</strong>
                <span>Threat: ${(ast.threat * 100).toFixed(1)}%</span>
            </div>
        `).join('');
        
        document.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const spkid = item.getAttribute('data-spkid');
                selectAsteroid(spkid);
                searchResults.innerHTML = '';
            });
        });
    } catch (err) {
        console.error('Search error:', err);
    }
});

async function selectAsteroid(spkid) {
    try {
        const res = await fetch(`/api/asteroid/${spkid}`);
        selectedAsteroid = await res.json();
        
        searchInput.value = selectedAsteroid.name || `SPKID ${selectedAsteroid.spkid}`;
        loadBtn.disabled = false;
        
    } catch (err) {
        console.error('Error loading asteroid:', err);
    }
}

// ============================================
// LOAD TIMELINE
// ============================================

loadBtn.addEventListener('click', async () => {
    if (!selectedAsteroid) return;
    
    loadBtn.textContent = 'Loading...';
    loadBtn.disabled = true;
    
    try {
        // Fetch timeline data
        const res = await fetch(`/api/historical-timeline/${selectedAsteroid.spkid}`);
        timelineData = await res.json();
        
        if (timelineData.timeline.length === 0) {
            alert('No close approach data available for this asteroid');
            loadBtn.textContent = 'Load Timeline';
            return;
        }
        
        // Show results
        document.getElementById('timelineResults').style.display = 'block';
        
        // Update statistics
        updateStatistics();
        
        // Render timeline chart
        renderTimelineChart();
        
        // Populate table
        populateTable();
        
        // Render additional charts
        renderDecadeChart();
        renderRiskChart();
        
        // Load multi-source data
        loadMultiSourceData();
        
        // Scroll to results
        document.getElementById('timelineResults').scrollIntoView({ behavior: 'smooth' });
        
    } catch (err) {
        console.error('Error loading timeline:', err);
        alert('Error loading timeline data');
    } finally {
        loadBtn.textContent = 'Load Timeline';
        loadBtn.disabled = false;
    }
});

// ============================================
// UPDATE STATISTICS
// ============================================

function updateStatistics() {
    const stats = timelineData.statistics;
    
    document.getElementById('totalApproaches').textContent = stats.total_approaches.toLocaleString();
    document.getElementById('historicalCount').textContent = stats.historical_count.toLocaleString();
    document.getElementById('futureCount').textContent = stats.future_count.toLocaleString();
    
    const closestEver = Math.min(
        stats.closest_historical?.distance_ld || Infinity,
        stats.closest_future?.distance_ld || Infinity
    );
    
    document.getElementById('closestDistance').textContent = 
        closestEver === Infinity ? '-' : closestEver.toFixed(1);
}

// ============================================
// TIMELINE CHART
// ============================================

function renderTimelineChart() {
    const timeline = timelineData.timeline;
    
    // Separate historical and future
    const historical = timeline.filter(t => !t.is_future);
    const future = timeline.filter(t => t.is_future);
    
    const traces = [];
    
    // Historical trace
    if (historical.length > 0) {
        traces.push({
            x: historical.map(t => t.date),
            y: historical.map(t => t.distance_au),
            mode: 'markers+lines',
            name: 'Historical',
            line: { color: '#00d4ff', width: 2 },
            marker: {
                size: 8,
                color: historical.map(t => getRiskColor(t.risk_level)),
                line: { color: '#ffffff', width: 1 }
            },
            hovertemplate: 'Date: %{x}<br>Distance: %{y:.4f} AU<br>%{text}<extra></extra>',
            text: historical.map(t => `${t.distance_ld.toFixed(1)} LD - ${t.risk_level}`)
        });
    }
    
    // Future trace
    if (future.length > 0) {
        traces.push({
            x: future.map(t => t.date),
            y: future.map(t => t.distance_au),
            mode: 'markers+lines',
            name: 'Future Predictions',
            line: { color: '#ff00ff', width: 2, dash: 'dash' },
            marker: {
                size: 8,
                color: future.map(t => getRiskColor(t.risk_level)),
                line: { color: '#ffffff', width: 1 }
            },
            hovertemplate: 'Date: %{x}<br>Distance: %{y:.4f} AU<br>%{text}<extra></extra>',
            text: future.map(t => `${t.distance_ld.toFixed(1)} LD - ${t.risk_level}`)
        });
    }
    
    const layout = {
        ...chartLayout,
        xaxis: {
            title: 'Date',
            gridcolor: 'rgba(0,212,255,0.1)',
            type: 'date'
        },
        yaxis: {
            title: 'Distance from Earth (AU)',
            gridcolor: 'rgba(0,212,255,0.1)',
            type: 'log'
        },
        shapes: [
            {
                type: 'line',
                x0: timeline[0]?.date,
                x1: timeline[timeline.length - 1]?.date,
                y0: 0.05,
                y1: 0.05,
                line: {
                    color: 'rgba(255,170,0,0.5)',
                    width: 2,
                    dash: 'dash'
                }
            },
            {
                type: 'line',
                x0: timeline[0]?.date,
                x1: timeline[timeline.length - 1]?.date,
                y0: 0.002,
                y1: 0.002,
                line: {
                    color: 'rgba(255,0,0,0.5)',
                    width: 2,
                    dash: 'dash'
                }
            }
        ],
        annotations: [
            {
                x: timeline[Math.floor(timeline.length / 2)]?.date,
                y: 0.05,
                text: 'Close Approach Threshold (0.05 AU)',
                showarrow: false,
                yshift: 10,
                font: { size: 10, color: '#ffaa00' }
            }
        ]
    };
    
    Plotly.newPlot('timelineChart', traces, layout, chartConfig);
}

function getRiskColor(riskLevel) {
    const colors = {
        'critical': '#ff0000',
        'high': '#ff6600',
        'medium': '#ffaa00',
        'low': '#00ff00'
    };
    return colors[riskLevel] || '#00d4ff';
}

// ============================================
// POPULATE TABLE
// ============================================

function populateTable() {
    const tbody = document.getElementById('approachesTableBody');
    const timeline = timelineData.timeline;
    
    tbody.innerHTML = timeline.map(approach => `
        <tr style="background: ${approach.is_future ? 'rgba(255,0,255,0.05)' : 'rgba(0,191,255,0.05)'};">
            <td>${new Date(approach.date).toLocaleDateString()}</td>
            <td>${approach.year}</td>
            <td>${approach.distance_au.toFixed(4)}</td>
            <td>${approach.distance_ld.toFixed(1)}</td>
            <td>${approach.velocity_km_s?.toFixed(2) || 'N/A'}</td>
            <td style="color: ${getRiskColor(approach.risk_level)};">
                <strong>${approach.risk_level.toUpperCase()}</strong>
            </td>
            <td>${approach.is_future ? '🔮 Future' : '📜 Historical'}</td>
        </tr>
    `).join('');
}

// ============================================
// DECADE CHART
// ============================================

function renderDecadeChart() {
    const timeline = timelineData.timeline;
    
    // Group by decade
    const decades = {};
    timeline.forEach(t => {
        const decade = Math.floor(t.year / 10) * 10;
        if (!decades[decade]) {
            decades[decade] = 0;
        }
        decades[decade]++;
    });
    
    const decadeLabels = Object.keys(decades).sort();
    const counts = decadeLabels.map(d => decades[d]);
    
    const trace = {
        x: decadeLabels.map(d => d + 's'),
        y: counts,
        type: 'bar',
        marker: {
            color: '#00d4ff',
            line: { color: '#0088ff', width: 1 }
        },
        hovertemplate: '%{x}<br>Approaches: %{y}<extra></extra>'
    };
    
    const layout = {
        ...chartLayout,
        xaxis: {
            title: 'Decade',
            gridcolor: 'rgba(0,212,255,0.1)'
        },
        yaxis: {
            title: 'Number of Approaches',
            gridcolor: 'rgba(0,212,255,0.1)'
        }
    };
    
    Plotly.newPlot('decadeChart', [trace], layout, chartConfig);
}

// ============================================
// RISK CHART
// ============================================

function renderRiskChart() {
    const timeline = timelineData.timeline;
    
    // Count by risk level
    const riskCounts = {
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0
    };
    
    timeline.forEach(t => {
        riskCounts[t.risk_level]++;
    });
    
    const trace = {
        labels: ['Critical', 'High', 'Medium', 'Low'],
        values: Object.values(riskCounts),
        type: 'pie',
        marker: {
            colors: ['#ff0000', '#ff6600', '#ffaa00', '#00ff00'],
            line: { color: '#00d4ff', width: 2 }
        },
        textinfo: 'label+percent',
        textfont: { color: '#ffffff', size: 14 },
        hovertemplate: '%{label}<br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    };
    
    const layout = {
        ...chartLayout,
        showlegend: false
    };
    
    Plotly.newPlot('riskChart', [trace], layout, chartConfig);
}

// ============================================
// MULTI-SOURCE DATA
// ============================================

async function loadMultiSourceData() {
    const multiSourceDiv = document.getElementById('multiSourceData');
    
    try {
        const res = await fetch(`/api/multi-source/${selectedAsteroid.spkid}`);
        const data = await res.json();
        
        let html = '<h3 style="color: #00d4ff; margin-bottom: 16px;">Data Sources Integration</h3>';
        
        // Data quality
        html += `
            <div style="padding: 16px; background: rgba(0,191,255,0.1); border-radius: 4px; margin-bottom: 16px;">
                <strong style="color: #00d4ff;">Data Quality Score:</strong>
                <div style="margin-top: 8px;">
                    <div style="background: rgba(0,0,0,0.5); height: 24px; border-radius: 4px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #00ff00, #00d4ff); height: 100%; width: ${data.data_quality.completeness}%; display: flex; align-items: center; justify-content: center; font-weight: bold;">
                            ${data.data_quality.completeness.toFixed(0)}%
                        </div>
                    </div>
                    <p style="margin-top: 8px; font-size: 0.9rem;">
                        Confidence: <strong style="color: #00d4ff;">${data.data_quality.confidence.toUpperCase()}</strong> 
                        (${data.data_quality.sources_available}/${data.data_quality.total_sources} sources available)
                    </p>
                </div>
            </div>
        `;
        
        // Source details
        const sources = data.sources;
        
        if (sources.sbdb?.available) {
            html += `<div class="stat-row"><span>JPL SBDB:</span> <span style="color: #00ff00;">✓ Available</span></div>`;
        } else {
            html += `<div class="stat-row"><span>JPL SBDB:</span> <span style="color: #ff0000;">✗ Unavailable</span></div>`;
        }
        
        if (sources.close_approaches?.available) {
            html += `<div class="stat-row"><span>Close Approach DB:</span> <span style="color: #00ff00;">✓ ${sources.close_approaches.total_count} approaches</span></div>`;
        } else {
            html += `<div class="stat-row"><span>Close Approach DB:</span> <span style="color: #ff0000;">✗ Unavailable</span></div>`;
        }
        
        if (sources.sentry?.available) {
            if (sources.sentry.on_sentry_list) {
                html += `
                    <div class="stat-row" style="background: rgba(255,100,0,0.1); padding: 12px; border-left: 3px solid #ff6600;">
                        <span>CNEOS Sentry:</span> 
                        <span style="color: #ff6600;"><strong>⚠️ ON SENTRY LIST</strong></span>
                    </div>
                    <div class="stat-row"><span>Palermo Scale:</span> <span style="color: #ffaa00;">${sources.sentry.palermo_scale_max.toFixed(2)}</span></div>
                    <div class="stat-row"><span>Torino Scale:</span> <span style="color: #ffaa00;">${sources.sentry.torino_scale_max}</span></div>
                    <div class="stat-row"><span>Impact Probability:</span> <span style="color: #ff6600;">${(sources.sentry.impact_probability * 100).toExponential(2)}%</span></div>
                `;
            } else {
                html += `<div class="stat-row"><span>CNEOS Sentry:</span> <span style="color: #00ff00;">✓ Not on risk list</span></div>`;
            }
        }
        
        multiSourceDiv.innerHTML = html;
        
    } catch (err) {
        console.error('Error loading multi-source data:', err);
        multiSourceDiv.innerHTML = '<p style="color: #ff6600;">Error loading multi-source data</p>';
    }
}
