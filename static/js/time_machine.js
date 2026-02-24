// ============================================
// ATIS - Time Machine
// Temporal Asteroid Position Visualization
// ============================================

const canvas = document.getElementById("scene");

// Scene Setup
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x000000, 0.0005);

// Camera
const camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);
camera.position.set(0, 15, 25);
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
const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
scene.add(ambientLight);

const sunLight = new THREE.PointLight(0xffd700, 2, 100);
sunLight.position.set(0, 0, 0);
scene.add(sunLight);

// ============================================
// SUN
// ============================================

const sunGeometry = new THREE.SphereGeometry(0.7, 32, 32);
const sunMaterial = new THREE.MeshBasicMaterial({
    color: 0xffd700,
    emissive: 0xffd700
});
const sun = new THREE.Mesh(sunGeometry, sunMaterial);
scene.add(sun);

// ============================================
// EARTH
// ============================================

const earthGeometry = new THREE.SphereGeometry(0.3, 32, 32);
const earthMaterial = new THREE.MeshPhongMaterial({
    color: 0x2233ff,
    emissive: 0x112244
});
const earth = new THREE.Mesh(earthGeometry, earthMaterial);
scene.add(earth);

// Earth orbit ring
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
    opacity: 0.3
});
const earthOrbit = new THREE.Line(earthOrbitGeometry, earthOrbitMaterial);
scene.add(earthOrbit);

// ============================================
// STAR FIELD
// ============================================

const starGeometry = new THREE.BufferGeometry();
const starCount = 10000;
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
// ASTEROID CLOUD
// ============================================

let asteroidCloud = null;
let asteroidData = [];
let currentTimeOffset = 0;
let isPlaying = false;
let playbackSpeed = 30; // days per second

// Color mapping
function getInfernoColor(value) {
    const colors = [
        [0, 0, 4],
        [66, 10, 104],
        [147, 38, 103],
        [221, 81, 58],
        [252, 165, 10],
        [252, 255, 164]
    ];
    
    const scaledValue = Math.min(Math.max(value, 0), 1);
    const index = scaledValue * (colors.length - 1);
    const lowerIndex = Math.floor(index);
    const upperIndex = Math.ceil(index);
    const blend = index - lowerIndex;
    
    if (lowerIndex === upperIndex) {
        return new THREE.Color(
            colors[lowerIndex][0] / 255,
            colors[lowerIndex][1] / 255,
            colors[lowerIndex][2] / 255
        );
    }
    
    const r = colors[lowerIndex][0] + (colors[upperIndex][0] - colors[lowerIndex][0]) * blend;
    const g = colors[lowerIndex][1] + (colors[upperIndex][1] - colors[lowerIndex][1]) * blend;
    const b = colors[lowerIndex][2] + (colors[upperIndex][2] - colors[lowerIndex][2]) * blend;
    
    return new THREE.Color(r / 255, g / 255, b / 255);
}

function loadAsteroidPositions(timeOffsetDays) {
    fetch(`/api/time-machine?time_offset_days=${timeOffsetDays}&limit=200`)
        .then(res => res.json())
        .then(data => {
            asteroidData = data;
            
            // Remove old cloud
            if (asteroidCloud) {
                scene.remove(asteroidCloud);
                asteroidCloud.geometry.dispose();
                asteroidCloud.material.dispose();
            }
            
            // Create new cloud
            const geometry = new THREE.BufferGeometry();
            const count = data.asteroids.length;
            
            const positions = new Float32Array(count * 3);
            const colors = new Float32Array(count * 3);
            const sizes = new Float32Array(count);
            
            let closeCount = 0;
            
            for (let i = 0; i < count; i++) {
                const ast = data.asteroids[i];
                
                positions[i * 3] = ast.x * 5;
                positions[i * 3 + 1] = ast.z * 5;
                positions[i * 3 + 2] = ast.y * 5;
                
                const color = getInfernoColor(ast.threat);
                colors[i * 3] = color.r;
                colors[i * 3 + 1] = color.g;
                colors[i * 3 + 2] = color.b;
                
                sizes[i] = 0.05 + ast.threat * 0.15;
                
                // Count close approaches
                const dist = Math.sqrt(ast.x**2 + ast.y**2 + ast.z**2);
                if (Math.abs(dist - 1.0) < 0.1) closeCount++;
            }
            
            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
            geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
            
            const material = new THREE.PointsMaterial({
                size: 0.1,
                vertexColors: true,
                transparent: true,
                opacity: 0.85,
                sizeAttenuation: true
            });
            
            asteroidCloud = new THREE.Points(geometry, material);
            scene.add(asteroidCloud);
            
            // Update UI
            document.getElementById('asteroidCount').textContent = count.toString();
            document.getElementById('closeCount').textContent = closeCount.toString();
            
            // Update Earth position
            if (data.earth_position) {
                earth.position.set(
                    data.earth_position.x,
                    data.earth_position.z,
                    data.earth_position.y
                );
            }
            
            // Update date display
            const date = new Date(data.date);
            document.getElementById('currentDate').textContent = date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            
            const offsetYears = (timeOffsetDays / 365.25).toFixed(1);
            document.getElementById('timeOffset').textContent = 
                offsetYears > 0 ? `+${offsetYears} years from now` :
                offsetYears < 0 ? `${Math.abs(offsetYears)} years ago` :
                'Current time';
        })
        .catch(err => console.error("Error loading positions:", err));
}

// ============================================
// TIME CONTROLS
// ============================================

function updateTimeOffset(days) {
    currentTimeOffset = parseFloat(days);
    document.getElementById('timeSlider').value = days;
    loadAsteroidPositions(currentTimeOffset);
}

function jumpTime(deltadays) {
    currentTimeOffset += deltadays;
    currentTimeOffset = Math.max(-3650, Math.min(3650, currentTimeOffset));
    updateTimeOffset(currentTimeOffset);
}

function resetTime() {
    updateTimeOffset(0);
}

function togglePlayback() {
    isPlaying = !isPlaying;
    const button = document.getElementById('playButton');
    button.textContent = isPlaying ? '⏸ Pause' : '▶ Play';
    button.classList.toggle('btn-primary');
    button.classList.toggle('btn-secondary');
}

document.getElementById('speedSelect').addEventListener('change', (e) => {
    playbackSpeed = parseFloat(e.target.value);
});

// ============================================
// ANIMATION LOOP
// ============================================

let lastUpdate = Date.now();

function animate() {
    requestAnimationFrame(animate);
    
    // Playback
    if (isPlaying) {
        const now = Date.now();
        const delta = (now - lastUpdate) / 1000; // seconds
        lastUpdate = now;
        
        currentTimeOffset += playbackSpeed * delta;
        
        // Loop at boundaries
        if (currentTimeOffset > 3650) currentTimeOffset = -3650;
        if (currentTimeOffset < -3650) currentTimeOffset = 3650;
        
        // Update every frame during playback
        if (Math.floor(currentTimeOffset) % 5 === 0) {
            loadAsteroidPositions(currentTimeOffset);
        }
        
        document.getElementById('timeSlider').value = currentTimeOffset;
    } else {
        lastUpdate = Date.now();
    }
    
    // Rotate asteroid cloud slowly
    if (asteroidCloud) {
        asteroidCloud.rotation.y += 0.0005;
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
    const zoomSpeed = 1;
    const currentDistance = camera.position.length();
    const newDistance = currentDistance + (e.deltaY > 0 ? zoomSpeed : -zoomSpeed);
    
    camera.position.normalize().multiplyScalar(Math.max(5, Math.min(80, newDistance)));
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

// ============================================
// ASTEROID SEARCH & TRACKING
// ============================================

let trackedAsteroidId = null;
let trackedAsteroidMarker = null;
let allAsteroidsCache = [];

// Load all asteroids for search
fetch('/api/asteroids')
    .then(res => res.json())
    .then(data => {
        allAsteroidsCache = data.map(ast => ({
            spkid: ast.spkid,
            name: ast.name || `Asteroid ${ast.spkid}`,
            threat: ast.threat || 0
        }));
    })
    .catch(err => console.error('Error loading asteroid list:', err));

function searchAsteroid(event) {
    const query = event.target.value.trim().toLowerCase();
    const resultsDiv = document.getElementById('searchResults');
    
    if (query.length < 2) {
        resultsDiv.style.display = 'none';
        return;
    }
    
    const matches = allAsteroidsCache
        .filter(ast => 
            ast.name.toLowerCase().includes(query) || 
            ast.spkid.toString().includes(query)
        )
        .slice(0, 10);
    
    if (matches.length === 0) {
        resultsDiv.innerHTML = '<div style="padding: 8px; color: rgba(255,255,255,0.5);">No matches found</div>';
        resultsDiv.style.display = 'block';
        return;
    }
    
    resultsDiv.innerHTML = matches.map(ast => `
        <div onclick="selectAsteroid('${ast.spkid}', '${ast.name}')" 
             style="padding: 8px; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.1); transition: background 0.2s;"
             onmouseover="this.style.background='rgba(0,191,255,0.2)'" 
             onmouseout="this.style.background='transparent'">
            <div style="font-weight: 600; font-size: 0.875rem;">${ast.name}</div>
            <div style="font-size: 0.75rem; color: rgba(255,255,255,0.6);">SPKID: ${ast.spkid} | Threat: ${(ast.threat * 100).toFixed(1)}%</div>
        </div>
    `).join('');
    
    resultsDiv.style.display = 'block';
}

function selectAsteroid(spkid, name) {
    trackedAsteroidId = spkid;
    
    document.getElementById('searchResults').style.display = 'none';
    document.getElementById('asteroidSearch').value = '';
    document.getElementById('selectedAsteroid').style.display = 'block';
    document.getElementById('trackedName').textContent = name;
    
    // Highlight the asteroid
    highlightTrackedAsteroid();
}

function clearTracking() {
    trackedAsteroidId = null;
    
    document.getElementById('selectedAsteroid').style.display = 'none';
    
    if (trackedAsteroidMarker) {
        scene.remove(trackedAsteroidMarker);
        trackedAsteroidMarker.geometry.dispose();
        trackedAsteroidMarker.material.dispose();
        trackedAsteroidMarker = null;
    }
}

function highlightTrackedAsteroid() {
    // Remove previous marker
    if (trackedAsteroidMarker) {
        scene.remove(trackedAsteroidMarker);
        trackedAsteroidMarker.geometry.dispose();
        trackedAsteroidMarker.material.dispose();
    }
    
    // Find asteroid in current data
    const asteroid = asteroidData.asteroids?.find(ast => ast.spkid == trackedAsteroidId);
    if (!asteroid) {
        console.log('Tracked asteroid not in current time range');
        return;
    }
    
    // Create marker ring
    const ringGeometry = new THREE.TorusGeometry(0.3, 0.05, 16, 32);
    const ringMaterial = new THREE.MeshBasicMaterial({
        color: 0x00ffff,
        emissive: 0x00ffff,
        transparent: true,
        opacity: 0.8
    });
    trackedAsteroidMarker = new THREE.Mesh(ringGeometry, ringMaterial);
    trackedAsteroidMarker.position.set(asteroid.x * 5, asteroid.z * 5, asteroid.y * 5);
    trackedAsteroidMarker.rotation.x = Math.PI / 2;
    scene.add(trackedAsteroidMarker);
    
    // Animate marker
    function animateMarker() {
        if (trackedAsteroidMarker) {
            trackedAsteroidMarker.rotation.z += 0.02;
            trackedAsteroidMarker.scale.setScalar(1 + Math.sin(Date.now() * 0.003) * 0.2);
        }
    }
    setInterval(animateMarker, 16);
}

// Initial load
loadAsteroidPositions(0);

