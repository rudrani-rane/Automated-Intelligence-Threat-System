// ============================================
// ATIS - Orbital Simulator
// Real Keplerian Orbit Visualization
// ============================================

const canvas = document.getElementById("scene");

// Scene Setup
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x000000, 0.0005);

// Camera Setup
const camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);
camera.position.set(0, 10, 20);

// Renderer Setup
const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
scene.add(ambientLight);

const sunLight = new THREE.PointLight(0xffd700, 2, 100);
sunLight.position.set(0, 0, 0);
scene.add(sunLight);

// ============================================
// SUN
// ============================================

const sunGeometry = new THREE.SphereGeometry(0.5, 32, 32);
const sunMaterial = new THREE.MeshBasicMaterial({
    color: 0xffd700,
    emissive: 0xffd700,
    emissiveIntensity: 1
});
const sun = new THREE.Mesh(sunGeometry, sunMaterial);
scene.add(sun);

// Sun glow
const sunGlowGeometry = new THREE.SphereGeometry(0.7, 32, 32);
const sunGlowMaterial = new THREE.MeshBasicMaterial({
    color: 0xffd700,
    transparent: true,
    opacity: 0.3,
    side: THREE.BackSide
});
const sunGlow = new THREE.Mesh(sunGlowGeometry, sunGlowMaterial);
scene.add(sunGlow);

// ============================================
// EARTH
// ============================================

const earthGeometry = new THREE.SphereGeometry(0.3, 32, 32);
const earthMaterial = new THREE.MeshPhongMaterial({
    color: 0x2233ff,
    emissive: 0x112244,
    shininess: 25
});
const earth = new THREE.Mesh(earthGeometry, earthMaterial);
earth.position.set(1, 0, 0);  // 1 AU from Sun
scene.add(earth);

// ============================================
// STAR FIELD
// ============================================

function createStarField() {
    const starGeometry = new THREE.BufferGeometry();
    const starCount = 8000;
    const positions = new Float32Array(starCount * 3);
    
    for (let i = 0; i < starCount * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 150;
        positions[i + 1] = (Math.random() - 0.5) * 150;
        positions[i + 2] = (Math.random() - 0.5) * 150;
    }
    
    starGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const starMaterial = new THREE.PointsMaterial({
        color: 0xffffff,
        size: 0.08,
        transparent: true,
        opacity: 0.7
    });
    
    return new THREE.Points(starGeometry, starMaterial);
}

const starField = createStarField();
scene.add(starField);

// ============================================
// ORBITAL PATHS
// ============================================

let orbitLines = [];
let asteroidMarkers = [];
let currentAsteroidData = null;

function loadEarthOrbit() {
    // Draw Earth's orbit (circular)
    const earthOrbitPoints = [];
    for (let i = 0; i <= 100; i++) {
        const angle = (i / 100) * Math.PI * 2;
        earthOrbitPoints.push(new THREE.Vector3(
            Math.cos(angle),
            0,
            Math.sin(angle)
        ));
    }
    
    const earthOrbitGeometry = new THREE.BufferGeometry().setFromPoints(earthOrbitPoints);
    const earthOrbitMaterial = new THREE.LineBasicMaterial({
        color: 0x00bfff,
        transparent: true,
        opacity: 0.5
    });
    const earthOrbitLine = new THREE.Line(earthOrbitGeometry, earthOrbitMaterial);
    scene.add(earthOrbitLine);
    orbitLines.push(earthOrbitLine);
}

function loadAsteroidOrbit(spkid) {
    fetch(`/api/orbital-path/${spkid}`)
        .then(res => res.json())
        .then(data => {
            currentAsteroidData = data;
            
            // Create orbit line
            const points = data.path.map(p => new THREE.Vector3(p.x, p.z, p.y));
            const geometry = new THREE.BufferGeometry().setFromPoints(points);
            const material = new THREE.LineBasicMaterial({
                color: 0xff00ff,
                transparent: true,
                opacity: 0.8
            });
            const orbitLine = new THREE.Line(geometry, material);
            scene.add(orbitLine);
            orbitLines.push(orbitLine);
            
            // Add asteroid marker at current position
            const asteroidGeometry = new THREE.SphereGeometry(0.1, 16, 16);
            const asteroidMaterial = new THREE.MeshPhongMaterial({
                color: 0xff00ff,
                emissive: 0xff00ff,
                emissiveIntensity: 0.5
            });
            const asteroidMarker = new THREE.Mesh(asteroidGeometry, asteroidMaterial);
            asteroidMarker.position.set(data.path[0].x, data.path[0].z, data.path[0].y);
            scene.add(asteroidMarker);
            asteroidMarkers.push(asteroidMarker);
            
            // Update info panel
            displayOrbitalInfo(data);
            
            console.log(`✓ Loaded orbit for ${data.name}`);
        })
        .catch(err => console.error("Error loading orbit:", err));
}

function displayOrbitalInfo(data) {
    const infoDiv = document.getElementById('orbitalInfo');
    const elements = data.orbital_elements;
    
    infoDiv.innerHTML = `
        <div style="margin-bottom: 16px;">
            <h4 style="color: var(--electric-blue); margin-bottom: 8px;">
                <a href="https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=${data.spkid}" target="_blank" style="color: var(--electric-blue); text-decoration: none;">
                    ${data.name} ↗
                </a>
            </h4>
            <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">SPKID: ${data.spkid}</div>
        </div>
        
        <div style="font-size: 0.875rem; font-family: var(--font-mono);">
            <div style="margin-bottom: 12px; padding: 12px; background: rgba(0,191,255,0.05); border-left: 2px solid var(--electric-blue); border-radius: 4px;">
                <strong>Orbital Elements</strong>
            </div>
            
            <table style="width: 100%; font-size: 0.75rem;">
                <tr>
                    <td style="padding: 4px; color: rgba(255,255,255,0.7);">Semi-major Axis:</td>
                    <td style="padding: 4px; text-align: right;"><strong>${elements.semi_major_axis_au.toFixed(4)} AU</strong></td>
                </tr>
                <tr>
                    <td style="padding: 4px; color: rgba(255,255,255,0.7);">Eccentricity:</td>
                    <td style="padding: 4px; text-align: right;"><strong>${elements.eccentricity.toFixed(4)}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 4px; color: rgba(255,255,255,0.7);">Inclination:</td>
                    <td style="padding: 4px; text-align: right;"><strong>${elements.inclination_deg.toFixed(2)}°</strong></td>
                </tr>
                <tr>
                    <td style="padding: 4px; color: rgba(255,255,255,0.7);">Long. Asc. Node:</td>
                    <td style="padding: 4px; text-align: right;"><strong>${elements.longitude_ascending_node_deg.toFixed(2)}°</strong></td>
                </tr>
                <tr>
                    <td style="padding: 4px; color: rgba(255,255,255,0.7);">Arg. Perihelion:</td>
                    <td style="padding: 4px; text-align: right;"><strong>${elements.argument_perihelion_deg.toFixed(2)}°</strong></td>
                </tr>
                <tr style="border-top: 1px solid var(--border-gray);">
                    <td style="padding: 8px 4px 4px 4px; color: rgba(255,255,255,0.7);">Orbital Period:</td>
                    <td style="padding: 8px 4px 4px 4px; text-align: right;"><strong>${elements.orbital_period_years.toFixed(2)} years</strong></td>
                </tr>
            </table>
        </div>
    `;
}

function clearOrbits() {
    orbitLines.forEach(line => scene.remove(line));
    asteroidMarkers.forEach(marker => scene.remove(marker));
    orbitLines = [];
    asteroidMarkers = [];
    currentAsteroidData = null;
    
    document.getElementById('orbitalInfo').innerHTML = `
        <p style="color: rgba(255,255,255,0.6); text-align: center; padding: 20px;">
            Select an asteroid to view orbital details
        </p>
    `;
}

// ============================================
// SEARCH FUNCTIONALITY
// ============================================

let searchTimeout;
const searchInput = document.getElementById('asteroidSearch');
const searchResults = document.getElementById('searchResults');

searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    const query = e.target.value.trim();
    
    if (query.length < 2) {
        searchResults.innerHTML = '';
        return;
    }
    
    searchTimeout = setTimeout(() => {
        fetch(`/api/search?query=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                if (data.results && data.results.length > 0) {
                    searchResults.innerHTML = data.results.slice(0, 5).map(item => `
                        <div 
                            onclick="selectAsteroid(${item.spkid})" 
                            style="padding: 8px; margin-bottom: 4px; background: rgba(0,191,255,0.1); border-radius: 4px; cursor: pointer; font-size: 0.75rem;"
                            onmouseover="this.style.background='rgba(0,191,255,0.2)'"
                            onmouseout="this.style.background='rgba(0,191,255,0.1)'"
                        >
                            <strong>${item.spkid}</strong>
                        </div>
                    `).join('');
                } else {
                    searchResults.innerHTML = '<div style="padding: 8px; color: rgba(255,255,255,0.5); font-size: 0.75rem;">No results found</div>';
                }
            });
    }, 300);
});

function selectAsteroid(spkid) {
    clearOrbits();
    loadEarthOrbit();
    loadAsteroidOrbit(spkid);
    searchResults.innerHTML = '';
    searchInput.value = '';
}

// ============================================
// ANIMATION LOOP
// ============================================

let time = 0;

function animate() {
    requestAnimationFrame(animate);
    time += 0.01;
    
    // Rotate Earth around Sun
    const earthAngle = time * 0.05;
    earth.position.set(
        Math.cos(earthAngle),
        0,
        Math.sin(earthAngle)
    );
    earth.rotation.y += 0.01;
    
    // Pulse sun glow
    sunGlow.scale.set(
        1 + Math.sin(time) * 0.1,
        1 + Math.sin(time) * 0.1,
        1 + Math.sin(time) * 0.1
    );
    
    // Slowly rotate star field
    starField.rotation.y += 0.0001;
    
    renderer.render(scene, camera);
}

animate();

// ============================================
// MOUSE CONTROLS
// ============================================

let isDragging = false;
let previousMousePosition = { x: 0, y: 0 };

canvas.addEventListener('mousedown', (e) => {
    isDragging = true;
    previousMousePosition = { x: e.clientX, y: e.clientY };
});

canvas.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    
    const deltaX = e.clientX - previousMousePosition.x;
    const deltaY = e.clientY - previousMousePosition.y;
    
    camera.position.applyAxisAngle(new THREE.Vector3(0, 1, 0), deltaX * 0.005);
    
    const currentDistance = camera.position.length();
    camera.position.y += deltaY * 0.05;
    camera.position.normalize().multiplyScalar(currentDistance);
    
    camera.lookAt(0, 0, 0);
    
    previousMousePosition = { x: e.clientX, y: e.clientY };
});

canvas.addEventListener('mouseup', () => {
    isDragging = false;
});

canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomSpeed = 0.1;
    const currentDistance = camera.position.length();
    const newDistance = currentDistance + (e.deltaY > 0 ? zoomSpeed : -zoomSpeed);
    
    camera.position.normalize().multiplyScalar(Math.max(5, Math.min(50, newDistance)));
    camera.lookAt(0, 0, 0);
});

// ============================================
// WINDOW RESIZE
// ============================================

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Load Earth orbit by default
loadEarthOrbit();
