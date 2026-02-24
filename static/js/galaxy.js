// ============================================
// ATIS - 3D Orbital Galaxy Visualization
// Advanced WebGL Rendering with Three.js
// ============================================

const canvas = document.getElementById("scene");

// Scene Setup
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x000000, 0.0008);

// Camera Setup
const camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);
camera.position.set(0, 5, 15);

// Renderer Setup
const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);

// Orbit Controls (optional enhancement)
// const controls = new THREE.OrbitControls(camera, renderer.domElement);
// controls.enableDamping = true;
// controls.dampingFactor = 0.05;

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
scene.add(ambientLight);

const sunLight = new THREE.PointLight(0xffffff, 1, 100);
sunLight.position.set(0, 0, 0);
scene.add(sunLight);

// ============================================
// EARTH VISUALIZATION
// ============================================

// Create Earth
const earthGeometry = new THREE.SphereGeometry(1, 64, 64);
const earthMaterial = new THREE.MeshPhongMaterial({
    color: 0x2233ff,
    emissive: 0x112244,
    shininess: 25,
    transparent: true,
    opacity: 0.8
});
const earth = new THREE.Mesh(earthGeometry, earthMaterial);
earth.position.set(0, 0, 0);
scene.add(earth);

// Earth Glow Effect
const glowGeometry = new THREE.SphereGeometry(1.1, 32, 32);
const glowMaterial = new THREE.MeshBasicMaterial({
    color: 0x00bfff,
    transparent: true,
    opacity: 0.2,
    side: THREE.BackSide
});
const earthGlow = new THREE.Mesh(glowGeometry, glowMaterial);
earth.add(earthGlow);

// Earth Orbit Ring
const orbitGeometry = new THREE.TorusGeometry(10, 0.02, 16, 100);
const orbitMaterial = new THREE.MeshBasicMaterial({
    color: 0x00bfff,
    transparent: true,
    opacity: 0.6
});
const earthOrbitRing = new THREE.Mesh(orbitGeometry, orbitMaterial);
earthOrbitRing.rotation.x = Math.PI / 2;
scene.add(earthOrbitRing);

// Additional Reference Rings
const ring2 = earthOrbitRing.clone();
ring2.scale.set(1.5, 1.5, 1.5);
ring2.material = orbitMaterial.clone();
ring2.material.opacity = 0.3;
scene.add(ring2);

const ring3 = earthOrbitRing.clone();
ring3.scale.set(2, 2, 2);
ring3.material = orbitMaterial.clone();
ring3.material.opacity = 0.15;
scene.add(ring3);

// ============================================
// STAR FIELD BACKGROUND
// ============================================

function createStarField() {
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
    
    const stars = new THREE.Points(starGeometry, starMaterial);
    scene.add(stars);
    
    return stars;
}

const starField = createStarField();

// ============================================
// ASTEROID CLOUD
// ============================================

let asteroidCloud = null;
let asteroidData = [];

// Color mapping function (Inferno colormap)
function getInfernoColor(value) {
    // value should be 0-1
    const colors = [
        [0, 0, 4],       // Dark purple (safe)
        [66, 10, 104],   // Purple
        [147, 38, 103],  // Magenta
        [221, 81, 58],   // Red-orange
        [252, 165, 10],  // Orange
        [252, 255, 164]  // Yellow (high threat)
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

// Fetch and render asteroid data
fetch("/api/galaxy")
.then(res => res.json())
.then(data => {
    asteroidData = data.objects;  // Store full object data with names and URLs
    
    const geometry = new THREE.BufferGeometry();
    const count = asteroidData.length;
    
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    
    for (let i = 0; i < count; i++) {
        const obj = asteroidData[i];
        
        // Position (scaled for visualization)
        positions[i * 3] = obj.x * 5;
        positions[i * 3 + 1] = obj.y * 5;
        positions[i * 3 + 2] = obj.z * 5;
        
        // Color based on threat score
        const color = getInfernoColor(obj.threat);
        colors[i * 3] = color.r;
        colors[i * 3 + 1] = color.g;
        colors[i * 3 + 2] = color.b;
        
        // Size based on threat (larger = more dangerous)
        sizes[i] = 0.05 + obj.threat * 0.15;
    }
    
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    
    const material = new THREE.PointsMaterial({
        size: 0.4,  // Much larger for better visibility
        vertexColors: true,
        transparent: true,
        opacity: 1.0,  // Full opacity
        sizeAttenuation: true,
        blending: THREE.AdditiveBlending
    });
    
    asteroidCloud = new THREE.Points(geometry, material);
    scene.add(asteroidCloud);
    
    // Update live statistics
    document.getElementById('totalCount').textContent = count.toLocaleString();
    
    console.log(`✓ Loaded ${count} real NASA asteroids from JPL SBDB`);
    console.log(`  Each point represents one asteroid with real orbital data`);
    console.log(`  Hover over any point to see asteroid details and JPL link`);
})
.catch(err => console.error("Error loading asteroid data:", err));

// ============================================
// LIVE ASTEROID UPDATES
// ============================================

let liveAsteroids = null;

let liveAsteroidData = [];

function updateLiveAsteroids(data) {
    if (data && data.length > 0) {
        liveAsteroidData = data;
        
        // Remove old live asteroids
        if (liveAsteroids) {
            scene.remove(liveAsteroids);
            liveAsteroids.geometry.dispose();
            liveAsteroids.material.dispose();
        }
        
        const geometry = new THREE.BufferGeometry();
            const count = data.objects.length;
            
            const positions = new Float32Array(count * 3);
            const colors = new Float32Array(count * 3);
            
            for (let i = 0; i < count; i++) {
                const obj = data.objects[i];
                positions[i * 3] = obj.x * 5;
                positions[i * 3 + 1] = obj.y * 5;
                positions[i * 3 + 2] = obj.z * 5;
                
                // Bright cyan for new detections
                colors[i * 3] = 0;
                colors[i * 3 + 1] = 1;
                colors[i * 3 + 2] = 1;
            }
            
            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
            
            const material = new THREE.PointsMaterial({
                size: 0.5,  // Larger for live updates
                vertexColors: true,
                transparent: true,
                opacity: 1.0,
                sizeAttenuation: true
            });
            
            liveAsteroids = new THREE.Points(geometry, material);
            scene.add(liveAsteroids);
            
            // Update live count
            document.getElementById('liveCount').textContent = liveAsteroidData.length;
            
            console.log(`✓ Live update: ${liveAsteroidData.length} new asteroids from WebSocket`);
        }
}

// Initial fetch of live data
fetch("/api/live")
    .then(res => res.json())
    .then(data => {
        if (data.objects && data.objects.length > 0) {
            updateLiveAsteroids(data.objects);
        }
    })
    .catch(err => console.error("Initial live data load error:", err));

// WebSocket event handlers for real-time updates
window.addEventListener('ws_connected', () => {
    console.log('[Galaxy] WebSocket connected, subscribing to threat updates...');
    wsClient.subscribe('threat_updates');
});

window.addEventListener('ws_threat_update', (event) => {
    console.log('[Galaxy] Received threat update:', event.detail);
    if (event.detail && event.detail.objects) {
        updateLiveAsteroids(event.detail.objects);
    }
});

// ============================================
// RAYCASTING FOR HOVER INTERACTION
// ============================================

const raycaster = new THREE.Raycaster();
raycaster.params.Points.threshold = 0.8;  // Larger threshold for easier hover detection
const mouse = new THREE.Vector2();

let tooltip = null;

function createTooltip() {
    const div = document.createElement('div');
    div.className = 'tooltip';
    div.style.position = 'absolute';
    div.style.pointerEvents = 'none';
    document.body.appendChild(div);
    return div;
}

tooltip = createTooltip();

canvas.addEventListener('mousemove', (event) => {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
    
    raycaster.setFromCamera(mouse, camera);
    
    if (asteroidCloud) {
        const intersects = raycaster.intersectObject(asteroidCloud);
        
        if (intersects.length > 0) {
            const index = intersects[0].index;
            const obj = asteroidData[index];
            
            // Clean up asteroid name (remove extra spaces)
            const cleanName = obj.name.trim();
            
            tooltip.innerHTML = `
                <div class="tooltip-title">
                    <a href="${obj.url}" target="_blank" style="color: #00bfff; text-decoration: none;">
                        ${cleanName} ↗
                    </a>
                </div>
                <div class="tooltip-data">
                    SPKID: ${obj.spkid}<br>
                    Position: (${obj.x.toFixed(2)}, ${obj.y.toFixed(2)}, ${obj.z.toFixed(2)})<br>
                    Threat Score: ${(obj.threat * 100).toFixed(1)}%<br>
                    Status: ${obj.threat > 0.7 ? '<span style="color:#ff0000">HIGH RISK</span>' : 
                              obj.threat > 0.4 ? '<span style="color:#ffa500">MODERATE</span>' : 
                              '<span style="color:#00ff7f">LOW RISK</span>'}<br>
                    <small style="color: #888; margin-top: 4px; display: block;">Click name to view on NASA JPL</small>
                </div>
            `;
            tooltip.style.left = event.clientX + 15 + 'px';
            tooltip.style.top = event.clientY + 15 + 'px';
            tooltip.classList.add('visible');
        } else {
            tooltip.classList.remove('visible');
        }
    }
});

// ============================================
// ANIMATION LOOP
// ============================================

let rotationSpeed = 0.001;
let time = 0;

function animate() {
    requestAnimationFrame(animate);
    time += 0.01;
    
    // Rotate asteroid cloud
    if (asteroidCloud) {
        asteroidCloud.rotation.y += rotationSpeed;
    }
    
    // Rotate Earth
    earth.rotation.y += 0.002;
    
    // Pulsing effect on orbit rings
    earthOrbitRing.material.opacity = 0.6 + Math.sin(time) * 0.2;
    
    // Animate live asteroids (pulsing glow)
    if (liveAsteroids) {
        liveAsteroids.material.opacity = 0.7 + Math.sin(time * 2) * 0.2;
    }
    
    // Gentle camera sway
    camera.position.x = Math.sin(time * 0.1) * 0.5;
    camera.lookAt(0, 0, 0);
    
    // Rotate starfield slowly
    starField.rotation.y += 0.0001;
    
    renderer.render(scene, camera);
}

animate();

// ============================================
// WINDOW RESIZE HANDLER
// ============================================

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// ============================================
// KEYBOARD CONTROLS
// ============================================

document.addEventListener('keydown', (event) => {
    switch(event.key) {
        case ' ':
            rotationSpeed = rotationSpeed === 0 ? 0.001 : 0;
            break;
        case '+':
        case '=':
            rotationSpeed = Math.min(rotationSpeed + 0.0005, 0.01);
            break;
        case '-':
        case '_':
            rotationSpeed = Math.max(rotationSpeed - 0.0005, -0.01);
            break;
        case 'r':
        case 'R':
            camera.position.set(0, 5, 15);
            rotationSpeed = 0.001;
            break;
    }
});
