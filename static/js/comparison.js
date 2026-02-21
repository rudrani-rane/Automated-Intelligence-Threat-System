// ============================================
// ATIS - Asteroid Comparison Tool
// Side-by-side Asteroid Analysis
// ============================================

let asteroidA = null;
let asteroidB = null;
let asteroidC = null;

// Chart theme
const chartLayout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(15,15,30,0.9)',
    font: { family: 'Orbitron, monospace', color: '#00d4ff', size: 12 },
    margin: { l: 60, r: 30, t: 30, b: 50 },
    showlegend: true,
    legend: {
        orientation: 'h',
        y: -0.2,
        x: 0.5,
        xanchor: 'center'
    }
};

const chartConfig = { responsive: true, displayModeBar: false };

// ============================================
// SEARCH FUNCTIONALITY
// ============================================

function setupSearch(inputId, resultsId, slot) {
    const input = document.getElementById(inputId);
    const results = document.getElementById(resultsId);
    
    input.addEventListener('input', async (e) => {
        const query = e.target.value.trim();
        if (query.length < 2) {
            results.innerHTML = '';
            return;
        }
        
        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            
            results.innerHTML = data.slice(0, 5).map(ast => `
                <div class="search-result-item" data-spkid="${ast.spkid}">
                    <strong>${ast.name || `SPKID ${ast.spkid}`}</strong>
                    <span>Threat: ${(ast.threat * 100).toFixed(1)}%</span>
                </div>
            `).join('');
            
            document.querySelectorAll(`#${resultsId} .search-result-item`).forEach(item => {
                item.addEventListener('click', () => {
                    const spkid = item.getAttribute('data-spkid');
                    selectAsteroid(spkid, slot);
                    results.innerHTML = '';
                });
            });
        } catch (err) {
            console.error('Search error:', err);
        }
    });
}

async function selectAsteroid(spkid, slot) {
    try {
        const res = await fetch(`/api/asteroid/${spkid}`);
        const asteroid = await res.json();
        
        if (slot === 'A') {
            asteroidA = asteroid;
            displaySelected('selectedA', asteroid);
        } else if (slot === 'B') {
            asteroidB = asteroid;
            displaySelected('selectedB', asteroid);
        } else if (slot === 'C') {
            asteroidC = asteroid;
            displaySelected('selectedC', asteroid);
        }
        
        // Enable compare button if at least 2 asteroids selected
        const compareBtn = document.getElementById('compareBtn');
        compareBtn.disabled = !(asteroidA && asteroidB);
        
    } catch (err) {
        console.error('Error loading asteroid:', err);
    }
}

function displaySelected(elementId, asteroid) {
    const element = document.getElementById(elementId);
    element.innerHTML = `
        <h4>${asteroid.name || `SPKID ${asteroid.spkid}`}</h4>
        <p><strong>Threat:</strong> ${(asteroid.threat * 100).toFixed(1)}%</p>
        <p><strong>MOID:</strong> ${asteroid.moid?.toFixed(4) || 'N/A'} AU</p>
        <p><strong>PHA:</strong> ${asteroid.pha === 'Y' ? 'Yes ⚠️' : 'No'}</p>
    `;
    element.style.background = 'rgba(0,191,255,0.1)';
    element.style.border = '1px solid #00d4ff';
    element.style.borderRadius = '4px';
    element.style.padding = '12px';
}

// ============================================
// COMPARE BUTTON
// ============================================

document.getElementById('compareBtn').addEventListener('click', () => {
    if (!asteroidA || !asteroidB) return;
    
    // Show results section
    document.getElementById('comparisonResults').style.display = 'block';
    
    // Show/hide third column
    const hasC = asteroidC !== null;
    document.querySelectorAll('[id$="C"], #orbHeaderC, #headerC').forEach(el => {
        el.style.display = hasC ? 'table-cell' : 'none';
    });
    
    // Populate tables
    populateBasicTable();
    populateOrbitalTable();
    
    // Render charts
    renderThreatChart();
    renderOrbitalChart();
    renderSizeVelocityChart();
    renderRiskChart();
    
    // Scroll to results
    document.getElementById('comparisonResults').scrollIntoView({ behavior: 'smooth' });
});

// ============================================
// POPULATE TABLES
// ============================================

function populateBasicTable() {
    const asteroids = [asteroidA, asteroidB, asteroidC].filter(a => a !== null);
    
    // Headers
    document.getElementById('headerA').textContent = asteroidA.name || 'Asteroid A';
    document.getElementById('headerB').textContent = asteroidB.name || 'Asteroid B';
    if (asteroidC) {
        document.getElementById('headerC').textContent = asteroidC.name || 'Asteroid C';
    }
    
    // Data
    const setCell = (prefix, asteroid, formatter) => {
        const value = formatter(asteroid);
        const cell = document.getElementById(prefix);
        if (cell) cell.textContent = value;
    };
    
    asteroids.forEach((ast, idx) => {
        const suffix = ['A', 'B', 'C'][idx];
        
        setCell(`name${suffix}`, ast, a => a.name || '-');
        setCell(`spkid${suffix}`, ast, a => a.spkid);
        setCell(`threat${suffix}`, ast, a => (a.threat * 100).toFixed(1) + '%');
        setCell(`pha${suffix}`, ast, a => a.pha === 'Y' ? 'Yes ⚠️' : 'No');
        setCell(`moid${suffix}`, ast, a => a.moid?.toFixed(4) || 'N/A');
        setCell(`velocity${suffix}`, ast, a => a.v_rel?.toFixed(2) || 'N/A');
        setCell(`h${suffix}`, ast, a => a.H?.toFixed(1) || 'N/A');
        setCell(`obs${suffix}`, ast, a => a.n_obs_used || 'N/A');
    });
}

function populateOrbitalTable() {
    const asteroids = [asteroidA, asteroidB, asteroidC].filter(a => a !== null);
    
    if (asteroidC) {
        document.getElementById('orbHeaderC').style.display = 'table-cell';
    }
    
    const setCell = (prefix, asteroid, formatter) => {
        const value = formatter(asteroid);
        const cell = document.getElementById(prefix);
        if (cell) cell.textContent = value;
    };
    
    asteroids.forEach((ast, idx) => {
        const suffix = ['A', 'B', 'C'][idx];
        
        setCell(`a${suffix}`, ast, a => a.a?.toFixed(3) || 'N/A');
        setCell(`e${suffix}`, ast, a => a.e?.toFixed(4) || 'N/A');
        setCell(`i${suffix}`, ast, a => a.i?.toFixed(2) || 'N/A');
        setCell(`om${suffix}`, ast, a => a.om?.toFixed(2) || 'N/A');
        setCell(`w${suffix}`, ast, a => a.w?.toFixed(2) || 'N/A');
        setCell(`q${suffix}`, ast, a => a.q?.toFixed(3) || 'N/A');
    });
}

// ============================================
// RENDER CHARTS
// ============================================

function renderThreatChart() {
    const asteroids = [asteroidA, asteroidB, asteroidC].filter(a => a !== null);
    const names = asteroids.map(a => a.name || `SPKID ${a.spkid}`);
    const threats = asteroids.map(a => a.threat * 100);
    
    const trace = {
        x: names,
        y: threats,
        type: 'bar',
        marker: {
            color: threats.map(t => 
                t > 70 ? '#ff0000' : 
                t > 40 ? '#ffaa00' : 
                '#00ff00'
            ),
            line: { color: '#00d4ff', width: 1 }
        },
        text: threats.map(t => t.toFixed(1) + '%'),
        textposition: 'outside',
        hovertemplate: '%{x}<br>Threat: %{y:.1f}%<extra></extra>'
    };
    
    const layout = {
        ...chartLayout,
        yaxis: {
            title: 'Threat Score (%)',
            gridcolor: 'rgba(0,212,255,0.1)',
            range: [0, 100]
        },
        xaxis: { gridcolor: 'rgba(0,212,255,0.1)' }
    };
    
    Plotly.newPlot('threatChart', [trace], layout, chartConfig);
}

function renderOrbitalChart() {
    const asteroids = [asteroidA, asteroidB, asteroidC].filter(a => a !== null);
    
    const traces = asteroids.map((ast, idx) => ({
        type: 'scatterpolar',
        r: [
            (ast.e || 0),
            (ast.i || 0) / 180,
            (ast.om || 0) / 360,
            (ast.w || 0) / 360,
            Math.min((ast.a || 0) / 5, 1),
            (ast.e || 0)
        ],
        theta: ['Eccentricity', 'Inclination', 'Long. Asc. Node', 'Arg. Perihelion', 'Semi-major Axis', 'Eccentricity'],
        fill: 'toself',
        name: ast.name || `SPKID ${ast.spkid}`,
        line: { width: 2 }
    }));
    
    const layout = {
        ...chartLayout,
        polar: {
            radialaxis: {
                visible: true,
                range: [0, 1],
                gridcolor: 'rgba(0,212,255,0.2)'
            },
            angularaxis: { gridcolor: 'rgba(0,212,255,0.2)' },
            bgcolor: 'rgba(0,0,0,0)'
        }
    };
    
    Plotly.newPlot('orbitalChart', traces, layout, chartConfig);
}

function renderSizeVelocityChart() {
    const asteroids = [asteroidA, asteroidB, asteroidC].filter(a => a !== null);
    
    // Estimate diameter from absolute magnitude H
    const estimateDiameter = (H) => {
        if (!H) return 0;
        const albedo = 0.14; // Assume typical albedo
        return 1329 / Math.sqrt(albedo) * Math.pow(10, -0.2 * H);
    };
    
    const trace = {
        x: asteroids.map(a => a.v_rel || 0),
        y: asteroids.map(a => estimateDiameter(a.H)),
        mode: 'markers+text',
        type: 'scatter',
        marker: {
            size: 20,
            color: asteroids.map(a => a.threat * 100),
            colorscale: 'Inferno',
            showscale: true,
            colorbar: { title: 'Threat %' },
            line: { color: '#00d4ff', width: 2 }
        },
        text: asteroids.map(a => a.name || `SPKID ${a.spkid}`),
        textposition: 'top center',
        textfont: { size: 10, color: '#00d4ff' },
        hovertemplate: '%{text}<br>Velocity: %{x:.1f} km/s<br>Diameter: %{y:.2f} km<extra></extra>'
    };
    
    const layout = {
        ...chartLayout,
        xaxis: {
            title: 'Relative Velocity (km/s)',
            gridcolor: 'rgba(0,212,255,0.1)'
        },
        yaxis: {
            title: 'Estimated Diameter (km)',
            gridcolor: 'rgba(0,212,255,0.1)',
            type: 'log'
        }
    };
    
    Plotly.newPlot('sizeVelocityChart', [trace], layout, chartConfig);
}

function renderRiskChart() {
    const asteroids = [asteroidA, asteroidB, asteroidC].filter(a => a !== null);
    const names = asteroids.map(a => a.name || `SPKID ${a.spkid}`);
    
    const riskFactors = asteroids.map(ast => {
        const moidRisk = ast.moid < 0.05 ? 100 : Math.max(0, 100 - (ast.moid * 100));
        const velocityRisk = Math.min(100, (ast.v_rel || 0) / 40 * 100);
        const sizeRisk = ast.H ? Math.max(0, 100 - (ast.H - 15) * 5) : 50;
        const observationConfidence = Math.min(100, (ast.n_obs_used || 0) / 50 * 100);
        
        return {
            moid: moidRisk,
            velocity: velocityRisk,
            size: sizeRisk,
            observation: observationConfidence
        };
    });
    
    const traces = [
        {
            x: names,
            y: riskFactors.map(r => r.moid),
            name: 'Proximity Risk',
            type: 'bar',
            marker: { color: 'rgba(255,0,0,0.7)' }
        },
        {
            x: names,
            y: riskFactors.map(r => r.velocity),
            name: 'Velocity Risk',
            type: 'bar',
            marker: { color: 'rgba(255,170,0,0.7)' }
        },
        {
            x: names,
            y: riskFactors.map(r => r.size),
            name: 'Size Risk',
            type: 'bar',
            marker: { color: 'rgba(255,255,0,0.7)' }
        },
        {
            x: names,
            y: riskFactors.map(r => r.observation),
            name: 'Data Confidence',
            type: 'bar',
            marker: { color: 'rgba(0,255,127,0.7)' }
        }
    ];
    
    const layout = {
        ...chartLayout,
        barmode: 'group',
        yaxis: {
            title: 'Risk/Confidence Level (%)',
            gridcolor: 'rgba(0,212,255,0.1)',
            range: [0, 100]
        },
        xaxis: { gridcolor: 'rgba(0,212,255,0.1)' }
    };
    
    Plotly.newPlot('riskChart', traces, layout, chartConfig);
}

// ============================================
// CLEAR BUTTON
// ============================================

document.getElementById('clearBtn').addEventListener('click', () => {
    asteroidA = null;
    asteroidB = null;
    asteroidC = null;
    
    document.getElementById('searchA').value = '';
    document.getElementById('searchB').value = '';
    document.getElementById('searchC').value = '';
    
    document.getElementById('selectedA').innerHTML = '<p>No asteroid selected</p>';
    document.getElementById('selectedB').innerHTML = '<p>No asteroid selected</p>';
    document.getElementById('selectedC').innerHTML = '<p>No asteroid selected</p>';
    
    document.querySelectorAll('.selected-asteroid').forEach(el => {
        el.style.background = '';
        el.style.border = '';
        el.style.padding = '';
    });
    
    document.getElementById('comparisonResults').style.display = 'none';
    document.getElementById('compareBtn').disabled = true;
});

// ============================================
// INITIALIZE
// ============================================

setupSearch('searchA', 'resultsA', 'A');
setupSearch('searchB', 'resultsB', 'B');
setupSearch('searchC', 'resultsC', 'C');
