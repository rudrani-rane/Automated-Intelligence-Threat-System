// ============================================
// ATIS - Impact Simulation
// Ground Track and Damage Zone Visualization
// ============================================

const canvas = document.getElementById("scene");

// Scene Setup
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x000000, 0.001);

// Camera
const camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);
camera.position.set(0, 0, 15);
camera.lookAt(0, 0, 0);

// Renderer
const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);

const sunLight = new THREE.DirectionalLight(0xffffff, 0.8);
sunLight.position.set(5, 3, 5);
scene.add(sunLight);

// ============================================
// EARTH
// ============================================

const earthRadius = 5;
const earthGeometry = new THREE.SphereGeometry(earthRadius, 64, 64);

// Earth texture (simplified - using color)
const earthMaterial = new THREE.MeshPhongMaterial({
    color: 0x2244aa,
    emissive: 0x112244,
    shininess: 20,
    specular: 0x333333
});

const earth = new THREE.Mesh(earthGeometry, earthMaterial);
scene.add(earth);

// Cloud layer
const cloudGeometry = new THREE.SphereGeometry(earthRadius + 0.02, 64, 64);
const cloudMaterial = new THREE.MeshPhongMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 0.2
});
const clouds = new THREE.Mesh(cloudGeometry, cloudMaterial);
scene.add(clouds);

// Atmosphere glow
const glowGeometry = new THREE.SphereGeometry(earthRadius + 0.3, 32, 32);
const glowMaterial = new THREE.MeshBasicMaterial({
    color: 0x00bfff,
    transparent: true,
    opacity: 0.15,
    side: THREE.BackSide
});
const atmosphere = new THREE.Mesh(glowGeometry, glowMaterial);
scene.add(atmosphere);

// ============================================
// STAR FIELD
// ============================================

const starGeometry = new THREE.BufferGeometry();
const starCount = 8000;
const positions = new Float32Array(starCount * 3);

for (let i = 0; i < starCount * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 200;
    positions[i + 1] = (Math.random() - 0.5) * 200;
    positions[i + 2] = (Math.random() - 0.5) * 200;
}

starGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
const starMaterial = new THREE.PointsMaterial({
    color: 0xffffff,
    size: 0.1,
    transparent: true,
    opacity: 0.8
});
const starField = new THREE.Points(starGeometry, starMaterial);
scene.add(starField);

// ============================================
// IMPACT VISUALIZATION OBJECTS
// ============================================

let impactPoint = null;
let damageZones = [];
let trajectoryLine = null;
let selectedAsteroid = null;
let impactData = null;

// ============================================
// UI CONTROLS
// ============================================

const latSlider = document.getElementById('impactLat');
const lonSlider = document.getElementById('impactLon');
const angleSlider = document.getElementById('impactAngle');
const latValue = document.getElementById('latValue');
const lonValue = document.getElementById('lonValue');
const angleValue = document.getElementById('angleValue');

latSlider.addEventListener('input', (e) => {
    latValue.textContent = e.target.value + '°';
    if (selectedAsteroid) updateImpactVisualization();
});

lonSlider.addEventListener('input', (e) => {
    lonValue.textContent = e.target.value + '°';
    if (selectedAsteroid) updateImpactVisualization();
});

angleSlider.addEventListener('input', (e) => {
    angleValue.textContent = e.target.value + '°';
    if (selectedAsteroid) updateImpactVisualization();
});

// ============================================
// SEARCH FUNCTIONALITY
// ============================================

const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');
const simulateBtn = document.getElementById('simulateBtn');

searchInput.addEventListener('input', async (e) => {
    const query = e.target.value.trim();
    if (query.length < 2) {
        searchResults.innerHTML = '';
        simulateBtn.disabled = true;
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
        simulateBtn.disabled = false;
        
    } catch (err) {
        console.error('Error loading asteroid:', err);
    }
}

// ============================================
// SIMULATE IMPACT
// ============================================

simulateBtn.addEventListener('click', async () => {
    if (!selectedAsteroid) return;
    
    simulateBtn.textContent = 'Simulating...';
    simulateBtn.disabled = true;
    
    try {
        // Get impact assessment
        const res = await fetch(`/api/impact-assessment/${selectedAsteroid.spkid}`);
        impactData = await res.json();
        
        // Update visualization
        updateImpactVisualization();
        
        // Display results
        displayImpactResults();
        
        // Animate camera to impact point
        animateCameraToImpact();
        
    } catch (err) {
        console.error('Error simulating impact:', err);
        alert('Error loading impact data');
    } finally {
        simulateBtn.textContent = 'Simulate Impact';
        simulateBtn.disabled = false;
    }
});

function updateImpactVisualization() {
    if (!impactData) return;
    
    // Clear old visualization
    clearImpact();
    
    const lat = parseFloat(latSlider.value) * Math.PI / 180;
    const lon = parseFloat(lonSlider.value) * Math.PI / 180;
    const angle = parseFloat(angleSlider.value);
    
    // Calculate impact point on sphere
    const x = earthRadius * Math.cos(lat) * Math.cos(lon);
    const y = earthRadius * Math.sin(lat);
    const z = earthRadius * Math.cos(lat) * Math.sin(lon);
    
    // Create impact point marker
    const pointGeometry = new THREE.SphereGeometry(0.1, 16, 16);
    const pointMaterial = new THREE.MeshBasicMaterial({
        color: 0xff0000,
        emissive: 0xff0000
    });
    impactPoint = new THREE.Mesh(pointGeometry, pointMaterial);
    impactPoint.position.set(x, y, z);
    scene.add(impactPoint);
    
    // Create damage zones (circles on sphere surface)
    const zones = [
        { radius: impactData.damage_radii.total_destruction || 0, color: 0xff0000, opacity: 0.6 },
        { radius: impactData.damage_radii.severe_damage || 0, color: 0xff6600, opacity: 0.4 },
        { radius: impactData.damage_radii.moderate_damage || 0, color: 0xffaa00, opacity: 0.3 },
        { radius: impactData.damage_radii.light_damage || 0, color: 0xffff00, opacity: 0.2 }
    ];
    
    zones.forEach(zone => {
        if (zone.radius > 0) {
            const circle = createDamageCircle(lat, lon, zone.radius, zone.color, zone.opacity);
            damageZones.push(circle);
            scene.add(circle);
        }
    });
    
    // Create impact trajectory
    const trajectoryPoints = [];
    const impactVector = new THREE.Vector3(x, y, z).normalize();
    
    // Create trajectory from space to impact point
    for (let i = 10; i >= 0; i--) {
        const distance = earthRadius + i * 0.5;
        const point = impactVector.clone().multiplyScalar(distance);
        trajectoryPoints.push(point);
    }
    
    const trajectoryGeometry = new THREE.BufferGeometry().setFromPoints(trajectoryPoints);
    const trajectoryMaterial = new THREE.LineBasicMaterial({
        color: 0xff00ff,
        linewidth: 2
    });
    trajectoryLine = new THREE.Line(trajectoryGeometry, trajectoryMaterial);
    scene.add(trajectoryLine);
}

function createDamageCircle(centerLat, centerLon, radiusKm, color, opacity) {
    // Convert radius from km to radians on Earth's surface
    const earthRadiusKm = 6371;
    const angularRadius = radiusKm / earthRadiusKm;
    
    const points = [];
    const segments = 64;
    
    for (let i = 0; i <= segments; i++) {
        const theta = (i / segments) * Math.PI * 2;
        
        // Calculate point on circle
        const lat = Math.asin(
            Math.sin(centerLat) * Math.cos(angularRadius) +
            Math.cos(centerLat) * Math.sin(angularRadius) * Math.cos(theta)
        );
        
        const lon = centerLon + Math.atan2(
            Math.sin(theta) * Math.sin(angularRadius) * Math.cos(centerLat),
            Math.cos(angularRadius) - Math.sin(centerLat) * Math.sin(lat)
        );
        
        const x = earthRadius * Math.cos(lat) * Math.cos(lon);
        const y = earthRadius * Math.sin(lat);
        const z = earthRadius * Math.cos(lat) * Math.sin(lon);
        
        points.push(new THREE.Vector3(x, y, z));
    }
    
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({ color, opacity, transparent: true, linewidth: 2 });
    
    return new THREE.Line(geometry, material);
}

function displayImpactResults() {
    document.getElementById('impactResults').style.display = 'block';
    
    document.getElementById('impactName').textContent = selectedAsteroid.name || `SPKID ${selectedAsteroid.spkid}`;
    document.getElementById('impactDiameter').textContent = impactData.estimated_diameter_km.toFixed(2) + ' km';
    document.getElementById('impactVelocity').textContent = impactData.impact_velocity_km_s.toFixed(1) + ' km/s';
    document.getElementById('impactEnergy').textContent = impactData.impact_energy_megatons.toFixed(1) + ' MT';
    document.getElementById('craterDiameter').textContent = impactData.crater_diameter_km.toFixed(1) + ' km';
    document.getElementById('earthquakeMag').textContent = impactData.earthquake_magnitude.toFixed(1) + ' Mw';
    
    document.getElementById('zoneTotal').textContent = impactData.damage_radii.total_destruction.toFixed(1) + ' km';
    document.getElementById('zoneSevere').textContent = impactData.damage_radii.severe_damage.toFixed(1) + ' km';
    document.getElementById('zoneModerate').textContent = impactData.damage_radii.moderate_damage.toFixed(1) + ' km';
    document.getElementById('zoneLight').textContent = impactData.damage_radii.light_damage.toFixed(1) + ' km';
    
    document.getElementById('comparisonText').textContent = impactData.historical_comparison;
}

function clearImpact() {
    if (impactPoint) {
        scene.remove(impactPoint);
        impactPoint.geometry.dispose();
        impactPoint.material.dispose();
        impactPoint = null;
    }
    
    damageZones.forEach(zone => {
        scene.remove(zone);
        zone.geometry.dispose();
        zone.material.dispose();
    });
    damageZones = [];
    
    if (trajectoryLine) {
        scene.remove(trajectoryLine);
        trajectoryLine.geometry.dispose();
        trajectoryLine.material.dispose();
        trajectoryLine = null;
    }
}

document.getElementById('clearBtn').addEventListener('click', () => {
    clearImpact();
    document.getElementById('impactResults').style.display = 'none';
    searchInput.value = '';
    selectedAsteroid = null;
    impactData = null;
    simulateBtn.disabled = true;
    camera.position.set(0, 0, 15);
    camera.lookAt(0, 0, 0);
});

// ============================================
// CAMERA ANIMATION
// ============================================

function animateCameraToImpact() {
    const lat = parseFloat(latSlider.value) * Math.PI / 180;
    const lon = parseFloat(lonSlider.value) * Math.PI / 180;
    
    const distance = 8;
    const targetX = distance * Math.cos(lat) * Math.cos(lon);
    const targetY = distance * Math.sin(lat);
    const targetZ = distance * Math.cos(lat) * Math.sin(lon);
    
    animateCameraTo(new THREE.Vector3(targetX, targetY, targetZ), new THREE.Vector3(
        earthRadius * Math.cos(lat) * Math.cos(lon),
        earthRadius * Math.sin(lat),
        earthRadius * Math.cos(lat) * Math.sin(lon)
    ));
}

let cameraTarget = null;
let cameraAnimating = false;

function animateCameraTo(position, lookAt) {
    cameraTarget = {
        position,
        lookAt,
        progress: 0
    };
    cameraAnimating = true;
}

// ============================================
// ANIMATION LOOP
// ============================================

function animate() {
    requestAnimationFrame(animate);
    
    // Camera animation
    if (cameraAnimating && cameraTarget) {
        cameraTarget.progress += 0.02;
        
        camera.position.lerp(cameraTarget.position, 0.05);
        
        const currentLookAt = new THREE.Vector3();
        camera.getWorldDirection(currentLookAt);
        currentLookAt.multiplyScalar(10).add(camera.position);
        currentLookAt.lerp(cameraTarget.lookAt, 0.05);
        camera.lookAt(currentLookAt);
        
        if (cameraTarget.progress >= 1) {
            cameraAnimating = false;
            cameraTarget = null;
        }
    }
    
    // Rotate Earth slowly
    earth.rotation.y += 0.001;
    clouds.rotation.y += 0.0012;
    atmosphere.rotation.y += 0.001;
    
    // Pulse impact point
    if (impactPoint) {
        const scale = 1 + Math.sin(Date.now() * 0.005) * 0.3;
        impactPoint.scale.set(scale, scale, scale);
    }
    
    // Rotate star field
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
    cameraAnimating = false;
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
    const zoomSpeed = 0.3;
    const currentDistance = camera.position.length();
    const newDistance = currentDistance + (e.deltaY > 0 ? zoomSpeed : -zoomSpeed);
    
    camera.position.normalize().multiplyScalar(Math.max(6, Math.min(50, newDistance)));
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
