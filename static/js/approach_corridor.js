// ============================================
// ATIS - Close Approach Corridor Visualization
// 3D Uncertainty Tube During Earth Flyby
// ============================================

const canvas = document.getElementById("scene");

// Scene Setup
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x000000, 0.002);

// Camera
const camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.01,
    1000
);
camera.position.set(0, 10, 20);
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
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);

const earthLight = new THREE.PointLight(0x2233ff, 1.5, 50);
scene.add(earthLight);

// ============================================
// EARTH
// ============================================

const earthGeometry = new THREE.SphereGeometry(1, 64, 64);
const earthMaterial = new THREE.MeshPhongMaterial({
    color: 0x2233ff,
    emissive: 0x112244,
    shininess: 30
});
const earth = new THREE.Mesh(earthGeometry, earthMaterial);
scene.add(earth);

// Earth atmosphere glow
const glowGeometry = new THREE.SphereGeometry(1.1, 32, 32);
const glowMaterial = new THREE.MeshBasicMaterial({
    color: 0x00bfff,
    transparent: true,
    opacity: 0.2
});
const earthGlow = new THREE.Mesh(glowGeometry, glowMaterial);
scene.add(earthGlow);

// Earth orbit reference ring
const earthOrbitRadius = 30; // 1 AU in scaled units
const earthOrbitPoints = [];
for (let i = 0; i <= 100; i++) {
    const angle = (i / 100) * Math.PI * 2;
    earthOrbitPoints.push(new THREE.Vector3(
        Math.cos(angle) * earthOrbitRadius,
        0,
        Math.sin(angle) * earthOrbitRadius
    ));
}
const earthOrbitGeometry = new THREE.BufferGeometry().setFromPoints(earthOrbitPoints);
const earthOrbitMaterial = new THREE.LineBasicMaterial({
    color: 0x00bfff,
    transparent: true,
    opacity: 0.15
});
const earthOrbit = new THREE.Line(earthOrbitGeometry, earthOrbitMaterial);
scene.add(earthOrbit);

// ============================================
// STAR FIELD
// ============================================

const starGeometry = new THREE.BufferGeometry();
const starCount = 5000;
const positions = new Float32Array(starCount * 3);

for (let i = 0; i < starCount * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 300;
    positions[i + 1] = (Math.random() - 0.5) * 300;
    positions[i + 2] = (Math.random() - 0.5) * 300;
}

starGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
const starMaterial = new THREE.PointsMaterial({
    color: 0xffffff,
    size: 0.15,
    transparent: true,
    opacity: 0.7
});
const starField = new THREE.Points(starGeometry, starMaterial);
scene.add(starField);

// ============================================
// CORRIDOR OBJECTS
// ============================================

let trajectoryLine = null;
let uncertaintyCorridor = null;
let closestPointMarker = null;
let selectedAsteroid = null;

// ============================================
// SEARCH FUNCTIONALITY
// ============================================

const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');
const loadBtn = document.getElementById('loadCorridorBtn');

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
        
        // Update info panel
        document.getElementById('asteroidInfo').style.display = 'block';
        document.getElementById('infoName').textContent = selectedAsteroid.name || '-';
        document.getElementById('infoSpkid').textContent = selectedAsteroid.spkid;
        document.getElementById('infoThreat').textContent = (selectedAsteroid.threat * 100).toFixed(1) + '%';
        
    } catch (err) {
        console.error('Error loading asteroid:', err);
    }
}

// ============================================
// LOAD CORRIDOR
// ============================================

loadBtn.addEventListener('click', async () => {
    if (!selectedAsteroid) return;
    
    loadBtn.textContent = 'Loading...';
    loadBtn.disabled = true;
    
    try {
        // Get close approach data
        const res = await fetch(`/api/close-approaches/${selectedAsteroid.spkid}?years_ahead=10&num_samples=500`);
        const data = await res.json();
        
        if (data.approaches.length === 0) {
            alert('No close approaches found in the next 10 years');
            loadBtn.textContent = 'Load Corridor';
            loadBtn.disabled = false;
            return;
        }
        
        // Find closest approach
        const closestApproach = data.approaches.reduce((min, approach) => 
            approach.distance < min.distance ? approach : min
        );
        
        // Update info
        document.getElementById('infoMinDist').textContent = closestApproach.distance.toFixed(4);
        document.getElementById('infoDate').textContent = new Date(closestApproach.date).toLocaleDateString();
        
        // Clear old visualization
        clearCorridor();
        
        // Create trajectory line
        const trajectoryPoints = [];
        const uncertaintyWidth = closestApproach.distance * 0.1 + 0.5; // Width based on distance
        
        // Sample points around closest approach (±30 days)
        const centerIndex = data.approaches.findIndex(a => a.date === closestApproach.date);
        const sampleStart = Math.max(0, centerIndex - 15);
        const sampleEnd = Math.min(data.approaches.length - 1, centerIndex + 15);
        
        for (let i = sampleStart; i <= sampleEnd; i++) {
            const approach = data.approaches[i];
            // Convert distance to 3D position (scaled)
            const scale = 5; // Scale factor for visualization
            const t = (i - centerIndex) / 30; // Normalized time
            
            // Create a flyby trajectory arc
            const x = approach.distance * Math.cos(t * Math.PI * 0.5) * scale;
            const y = t * 2;
            const z = approach.distance * Math.sin(t * Math.PI * 0.5) * scale;
            
            trajectoryPoints.push(new THREE.Vector3(x, y, z));
        }
        
        // Create trajectory line
        const trajectoryGeometry = new THREE.BufferGeometry().setFromPoints(trajectoryPoints);
        const trajectoryMaterial = new THREE.LineBasicMaterial({
            color: 0xff00ff,
            linewidth: 2
        });
        trajectoryLine = new THREE.Line(trajectoryGeometry, trajectoryMaterial);
        scene.add(trajectoryLine);
        
        // Create uncertainty corridor (tube around trajectory)
        const tubeSegments = trajectoryPoints.length - 1;
        const radialSegments = 16;
        
        // Create tube geometry manually
        const tubeVertices = [];
        const tubeIndices = [];
        
        for (let i = 0; i < trajectoryPoints.length; i++) {
            const point = trajectoryPoints[i];
            
            // Get direction for tube orientation
            let direction;
            if (i === 0) {
                direction = new THREE.Vector3().subVectors(trajectoryPoints[1], point).normalize();
            } else if (i === trajectoryPoints.length - 1) {
                direction = new THREE.Vector3().subVectors(point, trajectoryPoints[i - 1]).normalize();
            } else {
                direction = new THREE.Vector3().subVectors(trajectoryPoints[i + 1], trajectoryPoints[i - 1]).normalize();
            }
            
            // Create perpendicular vectors
            const up = Math.abs(direction.y) < 0.99 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
            const right = new THREE.Vector3().crossVectors(up, direction).normalize();
            const forward = new THREE.Vector3().crossVectors(direction, right).normalize();
            
            // Create circle of vertices
            for (let j = 0; j < radialSegments; j++) {
                const angle = (j / radialSegments) * Math.PI * 2;
                const radius = uncertaintyWidth * (1 - Math.abs(i - centerIndex + sampleStart) / 15 * 0.5);
                
                const offset = new THREE.Vector3()
                    .addScaledVector(right, Math.cos(angle) * radius)
                    .addScaledVector(forward, Math.sin(angle) * radius);
                
                const vertex = new THREE.Vector3().addVectors(point, offset);
                tubeVertices.push(vertex.x, vertex.y, vertex.z);
            }
            
            // Create faces
            if (i < trajectoryPoints.length - 1) {
                for (let j = 0; j < radialSegments; j++) {
                    const current = i * radialSegments + j;
                    const next = i * radialSegments + ((j + 1) % radialSegments);
                    const currentNext = (i + 1) * radialSegments + j;
                    const nextNext = (i + 1) * radialSegments + ((j + 1) % radialSegments);
                    
                    tubeIndices.push(current, next, currentNext);
                    tubeIndices.push(next, nextNext, currentNext);
                }
            }
        }
        
        const tubeGeometry = new THREE.BufferGeometry();
        tubeGeometry.setAttribute('position', new THREE.Float32BufferAttribute(tubeVertices, 3));
        tubeGeometry.setIndex(tubeIndices);
        tubeGeometry.computeVertexNormals();
        
        const tubeMaterial = new THREE.MeshPhongMaterial({
            color: 0xff00ff,
            transparent: true,
            opacity: 0.2,
            side: THREE.DoubleSide
        });
        
        uncertaintyCorridor = new THREE.Mesh(tubeGeometry, tubeMaterial);
        scene.add(uncertaintyCorridor);
        
        // Mark closest approach point
        const closestPoint = trajectoryPoints[centerIndex - sampleStart];
        const markerGeometry = new THREE.SphereGeometry(0.3, 16, 16);
        const markerMaterial = new THREE.MeshBasicMaterial({
            color: 0x00ff00,
            emissive: 0x00ff00
        });
        closestPointMarker = new THREE.Mesh(markerGeometry, markerMaterial);
        closestPointMarker.position.copy(closestPoint);
        scene.add(closestPointMarker);
        
        // Animate camera to view corridor
        animateCameraTo(closestPoint);
        
    } catch (err) {
        console.error('Error loading corridor:', err);
        alert('Error loading corridor data');
    } finally {
        loadBtn.textContent = 'Load Corridor';
        loadBtn.disabled = false;
    }
});

function clearCorridor() {
    if (trajectoryLine) {
        scene.remove(trajectoryLine);
        trajectoryLine.geometry.dispose();
        trajectoryLine.material.dispose();
        trajectoryLine = null;
    }
    
    if (uncertaintyCorridor) {
        scene.remove(uncertaintyCorridor);
        uncertaintyCorridor.geometry.dispose();
        uncertaintyCorridor.material.dispose();
        uncertaintyCorridor = null;
    }
    
    if (closestPointMarker) {
        scene.remove(closestPointMarker);
        closestPointMarker.geometry.dispose();
        closestPointMarker.material.dispose();
        closestPointMarker = null;
    }
}

document.getElementById('clearBtn').addEventListener('click', () => {
    clearCorridor();
    document.getElementById('asteroidInfo').style.display = 'none';
    searchInput.value = '';
    selectedAsteroid = null;
    loadBtn.disabled = true;
});

// ============================================
// CAMERA ANIMATION
// ============================================

let cameraTarget = null;
let cameraAnimating = false;

function animateCameraTo(target) {
    const targetPos = new THREE.Vector3()
        .copy(target)
        .add(new THREE.Vector3(10, 5, 10));
    
    cameraTarget = {
        position: targetPos,
        lookAt: target,
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
    
    // Rotate Earth
    earth.rotation.y += 0.002;
    earthGlow.rotation.y += 0.002;
    
    // Pulse closest point marker
    if (closestPointMarker) {
        const scale = 1 + Math.sin(Date.now() * 0.003) * 0.2;
        closestPointMarker.scale.set(scale, scale, scale);
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
    const zoomSpeed = 0.5;
    const currentDistance = camera.position.length();
    const newDistance = currentDistance + (e.deltaY > 0 ? zoomSpeed : -zoomSpeed);
    
    camera.position.normalize().multiplyScalar(Math.max(2, Math.min(100, newDistance)));
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
