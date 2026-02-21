// ML Performance Dashboard JavaScript

// Load performance metrics on page load
window.addEventListener('DOMContentLoaded', loadPerformanceMetrics);

async function loadPerformanceMetrics() {
    try {
        const response = await fetch('/api/ml-performance');
        const data = await response.json();
        
        // Update metric cards
        document.getElementById('accuracy').textContent = (data.metrics.accuracy * 100).toFixed(1) + '%';
        document.getElementById('precision').textContent = (data.metrics.precision * 100).toFixed(1) + '%';
        document.getElementById('recall').textContent = (data.metrics.recall * 100).toFixed(1) + '%';
        document.getElementById('f1').textContent = (data.metrics.f1_score * 100).toFixed(1) + '%';
        document.getElementById('roc_auc').textContent = data.metrics.roc_auc.toFixed(3);
        
        // Render charts
        renderROCCurve(data.roc_curve);
        renderPRCurve(data.pr_curve);
        renderConfusionMatrix(data.confusion_matrix);
        renderThreatDistribution(data.threat_distribution);
        
    } catch (error) {
        console.error('Error loading performance metrics:', error);
    }
}

function renderROCCurve(rocData) {
    const trace = {
        x: rocData.fpr,
        y: rocData.tpr,
        mode: 'lines',
        name: 'ROC Curve',
        line: {
            color: '#00d4ff',
            width: 3
        }
    };
    
    // Diagonal reference line (random classifier)
    const diagonalTrace = {
        x: [0, 1],
        y: [0, 1],
        mode: 'lines',
        name: 'Random Classifier',
        line: {
            color: 'rgba(255, 255, 255, 0.3)',
            width: 2,
            dash: 'dash'
        }
    };
    
    const layout = {
        xaxis: { 
            title: 'False Positive Rate',
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            color: 'white'
        },
        yaxis: { 
            title: 'True Positive Rate',
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            color: 'white'
        },
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
        plot_bgcolor: 'rgba(0, 0, 0, 0.3)',
        font: { family: 'Orbitron, monospace', color: 'white' },
        showlegend: true,
        legend: { x: 0.6, y: 0.1 },
        margin: { t: 30, r: 30, b: 50, l: 60 }
    };
    
    Plotly.newPlot('rocChart', [trace, diagonalTrace], layout, {responsive: true});
}

function renderPRCurve(prData) {
    const trace = {
        x: prData.recall,
        y: prData.precision,
        mode: 'lines',
        name: 'PR Curve',
        line: {
            color: '#ff00ff',
            width: 3
        }
    };
    
    const layout = {
        xaxis: { 
            title: 'Recall',
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            color: 'white'
        },
        yaxis: { 
            title: 'Precision',
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            color: 'white'
        },
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
        plot_bgcolor: 'rgba(0, 0, 0, 0.3)',
        font: { family: 'Orbitron, monospace', color: 'white' },
        showlegend: true,
        margin: { t: 30, r: 30, b: 50, l: 60 }
    };
    
    Plotly.newPlot('prChart', [trace], layout, {responsive: true});
}

function renderConfusionMatrix(cm) {
    const z = [
        [cm.true_negative, cm.false_positive],
        [cm.false_negative, cm.true_positive]
    ];
    
    const trace = {
        z: z,
        x: ['Predicted Negative', 'Predicted Positive'],
        y: ['Actual Negative', 'Actual Positive'],
        type: 'heatmap',
        colorscale: [
            [0, '#0a0a2e'],
            [0.5, '#ff00ff'],
            [1, '#00d4ff']
        ],
        text: z.map(row => row.map(val => val.toString())),
        texttemplate: '%{text}',
        textfont: {
            size: 20,
            color: 'white',
            family: 'Orbitron, monospace'
        },
        showscale: false
    };
    
    const layout = {
        xaxis: { 
            side: 'bottom',
            color: 'white'
        },
        yaxis: { 
            autorange: 'reversed',
            color: 'white'
        },
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
        plot_bgcolor: 'rgba(0, 0, 0, 0.3)',
        font: { family: 'Orbitron, monospace', color: 'white' },
        margin: { t: 30, r: 30, b: 80, l: 120 }
    };
    
    Plotly.newPlot('confusionMatrix', [trace], layout, {responsive: true});
}

function renderThreatDistribution(dist) {
    const trace = {
        values: [dist.high, dist.medium, dist.low],
        labels: ['High Threat', 'Medium Threat', 'Low Threat'],
        type: 'pie',
        marker: {
            colors: ['#ff3333', '#ffa500', '#00ff00']
        },
        textinfo: 'label+percent+value',
        textfont: {
            color: 'white',
            family: 'Orbitron, monospace'
        },
        hole: 0.4
    };
    
    const layout = {
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
        font: { family: 'Orbitron, monospace', color: 'white' },
        showlegend: true,
        legend: { x: 0, y: 0 },
        margin: { t: 30, r: 30, b: 30, l: 30 }
    };
    
    Plotly.newPlot('threatDistribution', [trace], layout, {responsive: true});
}

// Explainability Functions
async function explainPrediction() {
    const searchInput = document.getElementById('explainSearch').value.trim();
    if (!searchInput) {
        alert('Please enter an asteroid ID or name');
        return;
    }
    
    try {
        const response = await fetch(`/api/ml-explain/${encodeURIComponent(searchInput)}`);
        if (!response.ok) {
            throw new Error('Asteroid not found');
        }
        
        const data = await response.json();
        
        // Show results section
        document.getElementById('explainResults').style.display = 'block';
        
        // Update header
        document.getElementById('explainAsteroidName').textContent = `${data.asteroid_name || data.asteroid_id}`;
        
        // Update metrics
        document.getElementById('explainPrediction').textContent = (data.prediction * 100).toFixed(1) + '%';
        document.getElementById('explainLabel').textContent = data.prediction_label;
        document.getElementById('explainConfidence').textContent = (data.confidence * 100).toFixed(1) + '%';
        
        // Update explanation text
        document.getElementById('explainText').textContent = data.explanation_text;
        
        // Render feature importance chart
        renderFeatureImportance(data.feature_importance);
        
        // Render SHAP values chart
        renderSHAPValues(data.shap_values);
        
    } catch (error) {
        alert('Error: ' + error.message);
        console.error('Error explaining prediction:', error);
    }
}

function renderFeatureImportance(importance) {
    // Sort by importance
    const sorted = Object.entries(importance)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);  // Top 10
    
    const trace = {
        x: sorted.map(([_, val]) => val),
        y: sorted.map(([name, _]) => name.replace(/_/g, ' ')),
        type: 'bar',
        orientation: 'h',
        marker: {
            color: sorted.map(([_, val]) => val),
            colorscale: 'Inferno',
            showscale: false
        }
    };
    
    const layout = {
        xaxis: { 
            title: 'Importance (%)',
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            color: 'white'
        },
        yaxis: { 
            autorange: 'reversed',
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            color: 'white'
        },
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
        plot_bgcolor: 'rgba(0, 0, 0, 0.3)',
        font: { family: 'Orbitron, monospace', color: 'white', size: 10 },
        margin: { t: 20, r: 30, b: 50, l: 150 }
    };
    
    Plotly.newPlot('featureImportanceChart', [trace], layout, {responsive: true});
}

function renderSHAPValues(shapValues) {
    // Sort by absolute SHAP value
    const sorted = Object.entries(shapValues)
        .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
        .slice(0, 10);  // Top 10
    
    const trace = {
        x: sorted.map(([_, val]) => val),
        y: sorted.map(([name, _]) => name.replace(/_/g, ' ')),
        type: 'bar',
        orientation: 'h',
        marker: {
            color: sorted.map(([_, val]) => val > 0 ? '#ff3333' : '#00d4ff'),
        }
    };
    
    const layout = {
        xaxis: { 
            title: 'SHAP Value',
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            color: 'white'
        },
        yaxis: { 
            autorange: 'reversed',
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            color: 'white'
        },
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
        plot_bgcolor: 'rgba(0, 0, 0, 0.3)',
        font: { family: 'Orbitron, monospace', color: 'white', size: 10 },
        margin: { t: 20, r: 30, b: 50, l: 150 },
        annotations: [{
            text: 'Red = increases threat, Blue = decreases threat',
            xref: 'paper',
            yref: 'paper',
            x: 0.5,
            y: -0.15,
            xanchor: 'center',
            showarrow: false,
            font: { size: 10, color: 'rgba(255, 255, 255, 0.6)' }
        }]
    };
    
    Plotly.newPlot('shapValuesChart', [trace], layout, {responsive: true});
}

// Ensemble Prediction Functions
async function getEnsemblePrediction() {
    const searchInput = document.getElementById('ensembleSearch').value.trim();
    if (!searchInput) {
        alert('Please enter an asteroid ID or name');
        return;
    }
    
    try {
        const response = await fetch(`/api/ensemble-predict/${encodeURIComponent(searchInput)}`);
        if (!response.ok) {
            throw new Error('Asteroid not found');
        }
        
        const data = await response.json();
        
        // Show results section
        document.getElementById('ensembleResults').style.display = 'block';
        
        // Update header
        document.getElementById('ensembleAsteroidName').textContent = `${data.asteroid_name || data.asteroid_id}`;
        
        // Update metrics
        document.getElementById('ensembleScore').textContent = (data.ensemble_score * 100).toFixed(1) + '%';
        document.getElementById('ensembleAgreement').textContent = (data.agreement * 100).toFixed(1) + '%';
        document.getElementById('ensembleConfidence').textContent = (data.confidence * 100).toFixed(1) + '%';
        
        // Update recommendation
        document.getElementById('ensembleRecommendation').textContent = data.recommendation;
        
        // Render model predictions chart
        renderModelPredictions(data.individual_predictions, data.ensemble_score, data.outlier_models);
        
    } catch (error) {
        alert('Error: ' + error.message);
        console.error('Error getting ensemble prediction:', error);
    }
}

function renderModelPredictions(predictions, ensembleScore, outliers) {
    const models = Object.keys(predictions);
    const values = Object.values(predictions);
    
    const trace = {
        x: models.map(m => m.replace(/_/g, ' ').toUpperCase()),
        y: values,
        type: 'bar',
        marker: {
            color: models.map(m => outliers.includes(m) ? '#ffa500' : '#00d4ff'),
        },
        text: values.map(v => (v * 100).toFixed(1) + '%'),
        textposition: 'outside'
    };
    
    // Ensemble line
    const ensembleLine = {
        x: models.map(m => m.replace(/_/g, ' ').toUpperCase()),
        y: Array(models.length).fill(ensembleScore),
        mode: 'lines',
        name: 'Ensemble Score',
        line: {
            color: '#ff00ff',
            width: 3,
            dash: 'dash'
        }
    };
    
    const layout = {
        title: {
            text: 'Individual Model Predictions',
            font: { color: 'white', family: 'Orbitron, monospace' }
        },
        xaxis: { 
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            color: 'white'
        },
        yaxis: { 
            title: 'Threat Score',
            range: [0, 1],
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            color: 'white'
        },
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
        plot_bgcolor: 'rgba(0, 0, 0, 0.3)',
        font: { family: 'Orbitron, monospace', color: 'white' },
        showlegend: true,
        margin: { t: 60, r: 30, b: 80, l: 60 },
        annotations: [{
            text: 'Orange bars indicate outlier models',
            xref: 'paper',
            yref: 'paper',
            x: 0.5,
            y: -0.2,
            xanchor: 'center',
            showarrow: false,
            font: { size: 10, color: 'rgba(255, 255, 255, 0.6)' }
        }]
    };
    
    Plotly.newPlot('modelPredictionsChart', [trace, ensembleLine], layout, {responsive: true});
}

// Anomaly Detection Functions
async function detectAnomaly() {
    const searchInput = document.getElementById('anomalySearch').value.trim();
    if (!searchInput) {
        alert('Please enter an asteroid ID or name');
        return;
    }
    
    try {
        const response = await fetch(`/api/anomaly-score/${encodeURIComponent(searchInput)}`);
        if (!response.ok) {
            throw new Error('Asteroid not found');
        }
        
        const data = await response.json();
        
        // Show results section
        document.getElementById('anomalyResults').style.display = 'block';
        
        // Update header
        document.getElementById('anomalyAsteroidName').textContent = `${data.asteroid_name || data.asteroid_id}`;
        
        // Update metrics
        document.getElementById('anomalyScore').textContent = (data.anomaly_score * 100).toFixed(1) + '%';
        document.getElementById('anomalySeverity').textContent = data.severity;
        document.getElementById('isAnomalous').textContent = data.is_anomalous ? '⚠️ YES' : '✓ NO';
        
        // Color code based on severity
        const scoreEl = document.getElementById('anomalyScore');
        if (data.severity === 'EXTREME') {
            scoreEl.style.color = '#ff3333';
        } else if (data.severity === 'HIGH') {
            scoreEl.style.color = '#ffa500';
        } else {
            scoreEl.style.color = '#00ff00';
        }
        
        // Update explanation
        document.getElementById('anomalyExplanation').textContent = data.explanation;
        
        // Render anomalous features table
        renderAnomalousFeaturesTable(data.anomalous_features);
        
        // Update recommendations
        const recommendationsList = document.getElementById('anomalyRecommendations');
        recommendationsList.innerHTML = '';
        data.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.textContent = rec;
            li.style.marginBottom = '0.5rem';
            recommendationsList.appendChild(li);
        });
        
    } catch (error) {
        alert('Error: ' + error.message);
        console.error('Error detecting anomaly:', error);
    }
}

function renderAnomalousFeaturesTable(features) {
    const container = document.getElementById('anomalyFeaturesTable');
    
    if (!features || features.length === 0) {
        container.innerHTML = '<p style="color: rgba(255, 255, 255, 0.6);">No anomalous features detected.</p>';
        return;
    }
    
    let html = '<h4 style="color: #ffa500; margin-bottom: 1rem;">Anomalous Features:</h4>';
    html += '<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse;">';
    html += '<thead><tr style="background: rgba(255, 165, 0, 0.2); border-bottom: 2px solid #ffa500;">';
    html += '<th style="padding: 0.75rem; text-align: left;">Feature</th>';
    html += '<th style="padding: 0.75rem; text-align: right;">Value</th>';
    html += '<th style="padding: 0.75rem; text-align: right;">Z-Score</th>';
    html += '<th style="padding: 0.75rem; text-align: left;">Direction</th>';
    html += '<th style="padding: 0.75rem; text-align: left;">Comparison</th>';
    html += '</tr></thead><tbody>';
    
    features.forEach((f, i) => {
        const bgColor = i % 2 === 0 ? 'rgba(0, 0, 0, 0.2)' : 'rgba(0, 0, 0, 0.1)';
        html += `<tr style="background: ${bgColor}; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">`;
        html += `<td style="padding: 0.75rem;">${f.feature.replace(/_/g, ' ')}</td>`;
        html += `<td style="padding: 0.75rem; text-align: right; font-family: monospace;">${f.value.toFixed(4)}</td>`;
        html += `<td style="padding: 0.75rem; text-align: right; font-family: monospace; color: ${f.z_score > 3 ? '#ff3333' : '#ffa500'};">${f.z_score.toFixed(2)}</td>`;
        html += `<td style="padding: 0.75rem;"><span style="color: ${f.direction === 'high' ? '#ff3333' : '#00d4ff'};">▲ ${f.direction.toUpperCase()}</span></td>`;
        html += `<td style="padding: 0.75rem; font-size: 0.9em;">${f.comparison}</td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

// Auto-complete support (reuse from other pages if needed)
// Could add autocomplete functionality here for asteroid search
