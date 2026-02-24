// ============================================
// ATIS - Analytics Dashboard
// Comprehensive Statistics and Metrics
// ============================================

// Chart theme configuration
const chartLayout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(15,15,30,0.9)',
    font: {
        family: 'Orbitron, monospace',
        color: '#00d4ff',
        size: 12
    },
    xaxis: {
        gridcolor: 'rgba(0,212,255,0.1)',
        zerolinecolor: 'rgba(0,212,255,0.2)'
    },
    yaxis: {
        gridcolor: 'rgba(0,212,255,0.1)',
        zerolinecolor: 'rgba(0,212,255,0.2)'
    },
    margin: { l: 50, r: 30, t: 30, b: 50 }
};

const chartConfig = {
    responsive: true,
    displayModeBar: false
};

// ============================================
// LOAD DATA
// ============================================

async function loadAnalyticsData() {
    try {
        // Load asteroid data
        const asteroidResponse = await fetch('/api/asteroids');
        const asteroids = await asteroidResponse.json();
        
        // Load enhanced stats
        const statsResponse = await fetch('/api/enhanced-stats');
        const stats = await statsResponse.json();
        
        // Update stat cards
        updateStatCards(asteroids, stats);
        
        // Render charts
        renderThreatHistogram(asteroids);
        renderSizeDistribution(stats);
        renderOrbitalClasses(stats);
        renderDistanceScatter(asteroids);
        renderEccentricityInclination(asteroids);
        renderObservationFrequency(asteroids);
        renderConfusionMatrix();
        renderFeatureImportance();
        updateDataQuality(asteroids);
        
    } catch (error) {
        console.error('Error loading analytics data:', error);
    }
}

// ============================================
// STAT CARDS
// ============================================

function updateStatCards(asteroids, stats) {
    document.getElementById('totalAsteroids').textContent = asteroids.length.toLocaleString();
    const pha = stats.pha_count || stats.potentially_hazardous_count || 0;
    document.getElementById('phaCount').textContent = pha.toLocaleString();
    
    const highThreat = asteroids.filter(a => a.threat > 0.7).length;
    const mediumThreat = asteroids.filter(a => a.threat >= 0.4 && a.threat <= 0.7).length;
    const lowThreat = asteroids.filter(a => a.threat < 0.4).length;
    
    document.getElementById('highThreatCount').textContent = highThreat.toLocaleString();
    document.getElementById('mediumThreatCount').textContent = mediumThreat.toLocaleString();
    document.getElementById('lowThreatCount').textContent = lowThreat.toLocaleString();
    
    const avgThreat = (asteroids.reduce((sum, a) => sum + a.threat, 0) / asteroids.length).toFixed(3);
    document.getElementById('avgThreat').textContent = avgThreat;
}

// ============================================
// THREAT HISTOGRAM
// ============================================

function renderThreatHistogram(asteroids) {
    const threats = asteroids.map(a => a.threat);
    
    const trace = {
        x: threats,
        type: 'histogram',
        nbinsx: 30,
        marker: {
            color: threats,
            colorscale: [
                [0, 'rgb(0, 0, 4)'],
                [0.2, 'rgb(66, 10, 104)'],
                [0.4, 'rgb(147, 38, 103)'],
                [0.6, 'rgb(221, 81, 58)'],
                [0.8, 'rgb(252, 165, 10)'],
                [1, 'rgb(252, 255, 164)']
            ],
            line: {
                color: '#00d4ff',
                width: 1
            }
        },
        hovertemplate: 'Threat: %{x:.3f}<br>Count: %{y}<extra></extra>'
    };
    
    const layout = {
        ...chartLayout,
        xaxis: { 
            ...chartLayout.xaxis,
            title: 'Threat Score',
            range: [0, 1]
        },
        yaxis: { 
            ...chartLayout.yaxis,
            title: 'Number of Asteroids'
        },
        showlegend: false
    };
    
    Plotly.newPlot('threatHistogram', [trace], layout, chartConfig);
}

// ============================================
// SIZE DISTRIBUTION
// ============================================

function renderSizeDistribution(stats) {
    const sizeData = stats.size_distribution;
    
    const trace = {
        labels: Object.keys(sizeData),
        values: Object.values(sizeData),
        type: 'pie',
        marker: {
            colors: ['#ff0000', '#ff6600', '#ffcc00', '#00ff00'],
            line: {
                color: '#00d4ff',
                width: 2
            }
        },
        textinfo: 'label+percent',
        textfont: {
            color: '#ffffff',
            size: 14
        },
        hovertemplate: '%{label}<br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    };
    
    const layout = {
        ...chartLayout,
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.1,
            x: 0.5,
            xanchor: 'center'
        }
    };
    
    Plotly.newPlot('sizeDistribution', [trace], layout, chartConfig);
}

// ============================================
// ORBITAL CLASSES
// ============================================

function renderOrbitalClasses(stats) {
    const orbitalData = stats.orbital_classes;
    const labels = Object.keys(orbitalData);
    const values = Object.values(orbitalData);
    
    const trace = {
        x: labels,
        y: values,
        type: 'bar',
        marker: {
            color: values,
            colorscale: 'Viridis',
            line: {
                color: '#00d4ff',
                width: 1
            }
        },
        hovertemplate: '%{x}<br>Count: %{y}<extra></extra>'
    };
    
    const layout = {
        ...chartLayout,
        xaxis: { 
            ...chartLayout.xaxis,
            title: 'Orbital Class'
        },
        yaxis: { 
            ...chartLayout.yaxis,
            title: 'Number of Asteroids'
        }
    };
    
    Plotly.newPlot('orbitalClasses', [trace], layout, chartConfig);
}

// ============================================
// DISTANCE SCATTER
// ============================================

function renderDistanceScatter(asteroids) {
    // Sample data for performance (max 500 points)
    const sample = asteroids.length > 500 
        ? asteroids.filter((_, i) => i % Math.ceil(asteroids.length / 500) === 0)
        : asteroids;
    
    const trace = {
        x: sample.map(a => Math.sqrt(a.x**2 + a.y**2 + a.z**2)),
        y: sample.map(a => a.threat),
        mode: 'markers',
        type: 'scatter',
        marker: {
            size: 6,
            color: sample.map(a => a.threat),
            colorscale: [
                [0, 'rgb(0, 0, 4)'],
                [0.2, 'rgb(66, 10, 104)'],
                [0.4, 'rgb(147, 38, 103)'],
                [0.6, 'rgb(221, 81, 58)'],
                [0.8, 'rgb(252, 165, 10)'],
                [1, 'rgb(252, 255, 164)']
            ],
            colorbar: {
                title: 'Threat',
                titleside: 'right'
            },
            line: {
                color: '#00d4ff',
                width: 0.5
            }
        },
        hovertemplate: 'Distance: %{x:.3f} AU<br>Threat: %{y:.3f}<extra></extra>'
    };
    
    const layout = {
        ...chartLayout,
        xaxis: { 
            ...chartLayout.xaxis,
            title: 'Distance from Sun (AU)'
        },
        yaxis: { 
            ...chartLayout.yaxis,
            title: 'Threat Score',
            range: [0, 1]
        }
    };
    
    Plotly.newPlot('distanceScatter', [trace], layout, chartConfig);
}

// ============================================
// ECCENTRICITY VS INCLINATION
// ============================================

function renderEccentricityInclination(asteroids) {
    // Sample data
    const sample = asteroids.length > 500 
        ? asteroids.filter((_, i) => i % Math.ceil(asteroids.length / 500) === 0)
        : asteroids;
    
    const trace = {
        x: sample.map(a => a.e || 0),
        y: sample.map(a => a.i || 0),
        mode: 'markers',
        type: 'scatter',
        marker: {
            size: 5,
            color: sample.map(a => a.threat),
            colorscale: 'Inferno',
            showscale: false,
            line: {
                color: '#00d4ff',
                width: 0.5
            }
        },
        hovertemplate: 'Eccentricity: %{x:.3f}<br>Inclination: %{y:.2f}°<extra></extra>'
    };
    
    const layout = {
        ...chartLayout,
        xaxis: { 
            ...chartLayout.xaxis,
            title: 'Orbital Eccentricity'
        },
        yaxis: { 
            ...chartLayout.yaxis,
            title: 'Orbital Inclination (degrees)'
        }
    };
    
    Plotly.newPlot('eccentricityInclination', [trace], layout, chartConfig);
}

// ============================================
// OBSERVATION FREQUENCY
// ============================================

function renderObservationFrequency(asteroids) {
    // Create bins for observation counts
    const obsCounts = asteroids.map(a => a.n_obs_used || 0);
    
    const trace = {
        x: obsCounts,
        type: 'histogram',
        nbinsx: 20,
        marker: {
            color: '#00d4ff',
            line: {
                color: '#0088ff',
                width: 1
            }
        },
        hovertemplate: 'Observations: %{x}<br>Count: %{y}<extra></extra>'
    };
    
    const layout = {
        ...chartLayout,
        xaxis: { 
            ...chartLayout.xaxis,
            title: 'Number of Observations'
        },
        yaxis: { 
            ...chartLayout.yaxis,
            title: 'Number of Asteroids'
        }
    };
    
    Plotly.newPlot('observationFrequency', [trace], layout, chartConfig);
}

// ============================================
// CONFUSION MATRIX (Simulated ML Performance)
// ============================================

function renderConfusionMatrix() {
    // Simulated confusion matrix data
    const matrix = [
        [1423, 87],      // True Negative, False Positive
        [64, 1126]       // False Negative, True Positive
    ];
    
    const trace = {
        z: matrix,
        x: ['Predicted Safe', 'Predicted Threat'],
        y: ['Actual Safe', 'Actual Threat'],
        type: 'heatmap',
        colorscale: [
            [0, 'rgb(0, 0, 50)'],
            [0.5, 'rgb(0, 100, 150)'],
            [1, 'rgb(0, 212, 255)']
        ],
        text: matrix,
        texttemplate: '%{text}',
        textfont: {
            size: 16,
            color: '#ffffff'
        },
        hovertemplate: '%{y}<br>%{x}<br>Count: %{z}<extra></extra>'
    };
    
    const layout = {
        ...chartLayout,
        xaxis: {
            side: 'bottom'
        },
        yaxis: {
            autorange: 'reversed'
        }
    };
    
    Plotly.newPlot('confusionMatrix', [trace], layout, chartConfig);
}

// ============================================
// FEATURE IMPORTANCE
// ============================================

function renderFeatureImportance() {
    const features = [
        'MOID (AU)',
        'Velocity (km/s)',
        'Eccentricity',
        'Inclination',
        'Semi-major Axis',
        'Absolute Magnitude',
        'Perihelion Distance',
        'Orbital Period'
    ];
    
    const importance = [0.32, 0.28, 0.15, 0.09, 0.07, 0.05, 0.03, 0.01];
    
    const trace = {
        x: importance,
        y: features,
        type: 'bar',
        orientation: 'h',
        marker: {
            color: importance,
            colorscale: [
                [0, 'rgb(0, 100, 150)'],
                [0.5, 'rgb(0, 150, 200)'],
                [1, 'rgb(0, 212, 255)']
            ],
            line: {
                color: '#00d4ff',
                width: 1
            }
        },
        hovertemplate: '%{y}<br>Importance: %{x:.2f}<extra></extra>'
    };
    
    const layout = {
        ...chartLayout,
        xaxis: { 
            ...chartLayout.xaxis,
            title: 'Feature Importance',
            range: [0, 0.35]
        },
        yaxis: { 
            ...chartLayout.yaxis,
            autorange: 'reversed'
        }
    };
    
    Plotly.newPlot('featureImportance', [trace], layout, chartConfig);
}

// ============================================
// DATA QUALITY METRICS
// ============================================

function updateDataQuality(asteroids) {
    // Calculate completeness
    const hasCompleteOrbits = asteroids.filter(a => 
        a.e !== null && a.i !== null && a.om !== null && a.w !== null && a.a !== null
    ).length;
    
    const completePercent = ((hasCompleteOrbits / asteroids.length) * 100).toFixed(1);
    document.getElementById('completeOrbits').textContent = `${completePercent}% (${hasCompleteOrbits.toLocaleString()})`;
    
    const missingData = asteroids.length - hasCompleteOrbits;
    document.getElementById('missingData').textContent = missingData.toLocaleString();
    
    // Observation statistics
    const obsCounts = asteroids.map(a => a.n_obs_used || 0);
    const avgObs = (obsCounts.reduce((a, b) => a + b, 0) / obsCounts.length).toFixed(0);
    document.getElementById('avgObs').textContent = avgObs;
    
    const wellObserved = asteroids.filter(a => (a.n_obs_used || 0) > 100).length;
    document.getElementById('wellObserved').textContent = `${wellObserved.toLocaleString()} (${((wellObserved/asteroids.length)*100).toFixed(1)}%)`;
    
    const poorlyObserved = asteroids.filter(a => (a.n_obs_used || 0) < 10).length;
    document.getElementById('poorlyObserved').textContent = `${poorlyObserved.toLocaleString()} (${((poorlyObserved/asteroids.length)*100).toFixed(1)}%)`;
}

// ============================================
// INITIALIZE
// ============================================

loadAnalyticsData();

// Refresh every 2 minutes
setInterval(loadAnalyticsData, 120000);
