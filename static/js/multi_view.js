// ============================================
// ATIS - Multi-View Dashboard
// Synchronized Multi-Panel Visualization
// ============================================

let selectedAsteroid = null;
let scenes = {};
let renderers = {};
let cameras = {};
let animationFrames = {};

// ============================================
// LAYOUT MANAGEMENT
// ============================================

const layouts = {
    quad: {
        grid: 'repeat(2, 1fr) / repeat(2, 1fr)',
        views: [1, 2, 3, 4]
    },
    horizontal: {
        grid: '1fr / repeat(2, 1fr)',
        views: [1, 2]
    },
    vertical: {
        grid: 'repeat(2, 1fr) / 1fr',
        views: [1, 3]
    },
    triple: {
        grid: 'repeat(2, 1fr) / repeat(2, 1fr)',
        views: [1, 2, 3]
    }
};

function setLayout(layoutName) {
    const layout = layouts[layoutName];
    const grid = document.getElementById('viewGrid');
    grid.style.gridTemplate = layout.grid;
    
    // Show/hide views
    for (let i = 1; i <= 4; i++) {
        const view = document.getElementById(`view${i}`);
        if (layout.views.includes(i)) {
            view.style.display = 'flex';
        } else {
            view.style.display = 'none';
        }
    }
    
    // Resize renderers
    setTimeout(() => {
        Object.values(renderers).forEach(renderer => {
            const canvas = renderer.domElement;
            const parent = canvas.parentElement;
            renderer.setSize(parent.clientWidth, parent.clientHeight - 50);
        });
    }, 100);
}

document.getElementById('layoutSelect').addEventListener('change', (e) => {
    setLayout(e.target.value);
});

// ============================================
// VIEW 1: 3D ORBITAL PATH
// ============================================

function initOrbitView() {
    const canvas = document.getElementById('canvas1');
    
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000000, 0.001);
    
    const camera = new THREE.PerspectiveCamera(
        60,
        canvas.parentElement.clientWidth / (canvas.parentElement.clientHeight - 50),
        0.1,
        500
    );
    camera.position.set(0, 15, 25);
    camera.lookAt(0, 0, 0);
    
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setSize(canvas.parentElement.clientWidth, canvas.parentElement.clientHeight - 50);
    renderer.setPixelRatio(window.devicePixelRatio);
    
    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    
    const sunLight = new THREE.PointLight(0xffd700, 2, 100);
    scene.add(sunLight);
    
    // Sun
    const sunGeometry = new THREE.SphereGeometry(0.7, 32, 32);
    const sunMaterial = new THREE.MeshBasicMaterial({ color: 0xffd700, emissive: 0xffd700 });
    const sun = new THREE.Mesh(sunGeometry, sunMaterial);
    scene.add(sun);
    
    // Sun glow effect
    const sunGlowGeometry = new THREE.SphereGeometry(1.0, 32, 32);
    const sunGlowMaterial = new THREE.MeshBasicMaterial({
        color: 0xffd700,
        transparent: true,
        opacity: 0.3,
        side: THREE.BackSide
    });
    const sunGlow = new THREE.Mesh(sunGlowGeometry, sunGlowMaterial);
    scene.add(sunGlow);
    
    // Earth
    const earthGeometry = new THREE.SphereGeometry(0.3, 32, 32);
    const earthMaterial = new THREE.MeshPhongMaterial({ 
        color: 0x2233ff,
        emissive: 0x112244,
        shininess: 25
    });
    const earth = new THREE.Mesh(earthGeometry, earthMaterial);
    earth.position.set(1, 0, 0);
    scene.add(earth);
    
    // Earth orbit
    const earthOrbitPoints = [];
    for (let i = 0; i <= 100; i++) {
        const angle = (i / 100) * Math.PI * 2;
        earthOrbitPoints.push(new THREE.Vector3(Math.cos(angle), 0, Math.sin(angle)));
    }
    const earthOrbitGeometry = new THREE.BufferGeometry().setFromPoints(earthOrbitPoints);
    const earthOrbitMaterial = new THREE.LineBasicMaterial({ color: 0x00bfff, opacity: 0.3, transparent: true });
    const earthOrbit = new THREE.Line(earthOrbitGeometry, earthOrbitMaterial);
    scene.add(earthOrbit);
    
    // Store references
    scenes['orbit3d'] = scene;
    cameras['orbit3d'] = camera;
    renderers['orbit3d'] = renderer;
    
    // Mouse controls
    setupOrbitControls(canvas, camera);
    
    // Animation
    function animate() {
        animationFrames['orbit3d'] = requestAnimationFrame(animate);
        earth.rotation.y += 0.01;
        renderer.render(scene, camera);
    }
    animate();
}

function setupOrbitControls(canvas, camera) {
    let isDragging = false;
    let previousMouse = { x: 0, y: 0 };
    
    canvas.addEventListener('mousedown', (e) => {
        isDragging = true;
        previousMouse = { x: e.clientX, y: e.clientY };
    });
    
    canvas.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        const deltaX = e.clientX - previousMouse.x;
        const deltaY = e.clientY - previousMouse.y;
        
        camera.position.applyAxisAngle(new THREE.Vector3(0, 1, 0), deltaX * 0.005);
        const currentDistance = camera.position.length();
        camera.position.y += deltaY * 0.05;
        camera.position.normalize().multiplyScalar(currentDistance);
        camera.lookAt(0, 0, 0);
        
        previousMouse = { x: e.clientX, y: e.clientY };
    });
    
    canvas.addEventListener('mouseup', () => isDragging = false);
    
    canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        const distance = camera.position.length();
        const newDistance = distance + (e.deltaY > 0 ? 1 : -1);
        camera.position.normalize().multiplyScalar(Math.max(5, Math.min(80, newDistance)));
        camera.lookAt(0, 0, 0);
    });
}

// ============================================
// VIEW 2: CLOSE APPROACH TIMELINE
// ============================================

function updateTimelineChart(asteroidId) {
    fetch(`/api/close-approaches/${asteroidId}?years_ahead=10&num_samples=200`)
        .then(res => res.json())
        .then(data => {
            const trace = {
                x: data.approaches.map(a => a.date),
                y: data.approaches.map(a => a.distance),
                mode: 'lines+markers',
                type: 'scatter',
                line: {
                    color: '#00d4ff',
                    width: 2
                },
                marker: {
                    size: 6,
                    color: data.approaches.map(a => a.distance < 0.05 ? '#ff0000' : '#00d4ff'),
                    line: {
                        color: '#ffffff',
                        width: 1
                    }
                },
                hovertemplate: 'Date: %{x}<br>Distance: %{y:.4f} AU<extra></extra>'
            };
            
            const layout = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(15,15,30,0.9)',
                font: { family: 'Orbitron, monospace', color: '#00d4ff' },
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
                margin: { l: 60, r: 30, t: 20, b: 50 },
                shapes: [{
                    type: 'line',
                    x0: data.approaches[0]?.date || 0,
                    x1: data.approaches[data.approaches.length - 1]?.date || 0,
                    y0: 0.05,
                    y1: 0.05,
                    line: {
                        color: 'rgba(255,0,0,0.5)',
                        width: 2,
                        dash: 'dash'
                    }
                }]
            };
            
            Plotly.newPlot('chart1', [trace], layout, { responsive: true, displayModeBar: false });
        })
        .catch(err => console.error('Error loading timeline:', err));
}

// ============================================
// VIEW 3: ORBITAL ELEMENTS RADAR
// ============================================

function updateRadarChart(asteroidData) {
    const trace = {
        type: 'scatterpolar',
        r: [
            asteroidData.e || 0,
            (asteroidData.i || 0) / 180,
            (asteroidData.om || 0) / 360,
            (asteroidData.w || 0) / 360,
            Math.min((asteroidData.a || 0) / 5, 1),
            asteroidData.e || 0
        ],
        theta: ['Eccentricity', 'Inclination', 'Long. Asc. Node', 'Arg. Perihelion', 'Semi-major Axis', 'Eccentricity'],
        fill: 'toself',
        fillcolor: 'rgba(0,212,255,0.2)',
        line: {
            color: '#00d4ff',
            width: 2
        },
        marker: {
            size: 8,
            color: '#00d4ff'
        }
    };
    
    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(15,15,30,0.9)',
        font: { family: 'Orbitron, monospace', color: '#00d4ff', size: 10 },
        polar: {
            radialaxis: {
                visible: true,
                range: [0, 1],
                gridcolor: 'rgba(0,212,255,0.2)',
                tickfont: { size: 9 }
            },
            angularaxis: {
                gridcolor: 'rgba(0,212,255,0.2)'
            },
            bgcolor: 'rgba(0,0,0,0)'
        },
        margin: { l: 80, r: 80, t: 20, b: 80 }
    };
    
    Plotly.newPlot('chart2', [trace], layout, { responsive: true, displayModeBar: false });
}

// ============================================
// VIEW 4: IMPACT ASSESSMENT
// ============================================

function updateImpactChart(asteroidId) {
    fetch(`/api/impact-assessment/${asteroidId}`)
        .then(res => res.json())
        .then(data => {
            const damageZones = [
                { zone: 'Total Destruction', radius: data.damage_radii.total_destruction || 0 },
                { zone: 'Severe Damage', radius: data.damage_radii.severe_damage || 0 },
                { zone: 'Moderate Damage', radius: data.damage_radii.moderate_damage || 0 },
                { zone: 'Light Damage', radius: data.damage_radii.light_damage || 0 }
            ];
            
            const trace = {
                x: damageZones.map(d => d.radius),
                y: damageZones.map(d => d.zone),
                type: 'bar',
                orientation: 'h',
                marker: {
                    color: ['#ff0000', '#ff6600', '#ffaa00', '#ffff00'],
                    line: { color: '#00d4ff', width: 1 }
                },
                hovertemplate: '%{y}<br>Radius: %{x:.1f} km<extra></extra>'
            };
            
            const layout = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(15,15,30,0.9)',
                font: { family: 'Orbitron, monospace', color: '#00d4ff' },
                xaxis: {
                    title: 'Damage Radius (km)',
                    gridcolor: 'rgba(0,212,255,0.1)'
                },
                yaxis: {
                    gridcolor: 'rgba(0,212,255,0.1)',
                    autorange: 'reversed'
                },
                margin: { l: 150, r: 30, t: 20, b: 50 },
                annotations: [{
                    x: Math.max(...damageZones.map(d => d.radius)) * 0.5,
                    y: 2,
                    text: `Impact Energy: ${data.impact_energy_megatons.toFixed(1)} MT`,
                    showarrow: false,
                    font: { size: 14, color: '#ffaa00' }
                }]
            };
            
            Plotly.newPlot('chart3', [trace], layout, { responsive: true, displayModeBar: false });
        })
        .catch(err => console.error('Error loading impact assessment:', err));
}

// ============================================
// ASTEROID SEARCH
// ============================================

const searchInput = document.getElementById('asteroidSearch');
const searchResults = document.getElementById('searchResults');

searchInput.addEventListener('input', async (e) => {
    const query = e.target.value.trim();
    if (query.length < 2) {
        searchResults.innerHTML = '';
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
        
        // Add click handlers
        document.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const spkid = item.getAttribute('data-spkid');
                loadAsteroid(spkid);
                searchResults.innerHTML = '';
            });
        });
    } catch (err) {
        console.error('Search error:', err);
    }
});

// ============================================
// ASTEROID LOADING
// ============================================

async function loadAsteroid(spkid) {
    try {
        const res = await fetch(`/api/asteroid/${spkid}`);
        const asteroid = await res.json();
        
        selectedAsteroid = asteroid;
        
        // Update info panel
        document.getElementById('infoName').textContent = asteroid.name || '-';
        document.getElementById('infoSpkid').textContent = asteroid.spkid;
        document.getElementById('infoThreat').textContent = (asteroid.threat * 100).toFixed(1) + '%';
        document.getElementById('infoMoid').textContent = asteroid.moid?.toFixed(4) || '-';
        document.getElementById('infoVelocity').textContent = asteroid.v_rel?.toFixed(2) || '-';
        document.getElementById('infoPha').textContent = asteroid.pha === 'Y' ? 'Yes ⚠️' : 'No';
        
        // Update all views
        updateOrbitView(spkid);
        updateTimelineChart(spkid);
        updateRadarChart(asteroid);
        updateImpactChart(spkid);
        
    } catch (err) {
        console.error('Error loading asteroid:', err);
    }
}

function updateOrbitView(spkid) {
    fetch(`/api/orbital-path/${spkid}?num_points=200`)
        .then(res => res.json())
        .then(data => {
            const scene = scenes['orbit3d'];
            
            // Remove old orbit
            const oldOrbit = scene.getObjectByName('asteroidOrbit');
            if (oldOrbit) scene.remove(oldOrbit);
            
            const oldMarker = scene.getObjectByName('asteroidMarker');
            if (oldMarker) scene.remove(oldMarker);
            
            // Add new orbit
            const points = data.orbit.map(p => new THREE.Vector3(p[0], p[2], p[1]));
            const geometry = new THREE.BufferGeometry().setFromPoints(points);
            const material = new THREE.LineBasicMaterial({ color: 0xff00ff });
            const orbit = new THREE.Line(geometry, material);
            orbit.name = 'asteroidOrbit';
            scene.add(orbit);
            
            // Add asteroid marker
            const markerGeometry = new THREE.SphereGeometry(0.1, 16, 16);
            const markerMaterial = new THREE.MeshBasicMaterial({ color: 0xff00ff });
            const marker = new THREE.Mesh(markerGeometry, markerMaterial);
            marker.position.set(points[0].x, points[0].y, points[0].z);
            marker.name = 'asteroidMarker';
            scene.add(marker);
        })
        .catch(err => console.error('Error loading orbit:', err));
}

// ============================================
// SYNC AND RESET
// ============================================

document.getElementById('syncViews').addEventListener('click', () => {
    if (selectedAsteroid) {
        loadAsteroid(selectedAsteroid.spkid);
    }
});

document.getElementById('resetViews').addEventListener('click', () => {
    // Clear all views
    selectedAsteroid = null;
    
    const scene = scenes['orbit3d'];
    const oldOrbit = scene.getObjectByName('asteroidOrbit');
    if (oldOrbit) scene.remove(oldOrbit);
    const oldMarker = scene.getObjectByName('asteroidMarker');
    if (oldMarker) scene.remove(oldMarker);
    
    Plotly.purge('chart1');
    Plotly.purge('chart2');
    Plotly.purge('chart3');
    
    // Reset info
    document.getElementById('infoName').textContent = '-';
    document.getElementById('infoSpkid').textContent = '-';
    document.getElementById('infoThreat').textContent = '-';
    document.getElementById('infoMoid').textContent = '-';
    document.getElementById('infoVelocity').textContent = '-';
    document.getElementById('infoPha').textContent = '-';
});

// ============================================
// WINDOW RESIZE
// ============================================

window.addEventListener('resize', () => {
    Object.keys(renderers).forEach(key => {
        const renderer = renderers[key];
        const camera = cameras[key];
        const canvas = renderer.domElement;
        const parent = canvas.parentElement;
        
        camera.aspect = parent.clientWidth / (parent.clientHeight - 50);
        camera.updateProjectionMatrix();
        renderer.setSize(parent.clientWidth, parent.clientHeight - 50);
    });
    
    Plotly.Plots.resize('chart1');
    Plotly.Plots.resize('chart2');
    Plotly.Plots.resize('chart3');
});

// ============================================
// INITIALIZE
// ============================================

initOrbitView();
setLayout('quad');

// Auto-load a sample asteroid for better UX
setTimeout(() => {
    // Load a well-known asteroid (433 Eros) as example
    loadAsteroid('20000433').catch(() => {
        // Fallback: try loading any asteroid from search
        fetch('/api/search?q=eros')
            .then(res => res.json())
            .then(results => {
                if (results && results.length > 0) {
                    loadAsteroid(results[0].spkid);
                }
            })
            .catch(err => console.error('Error auto-loading asteroid:', err));
    });
}, 500);
