// ML Performance Dashboard — Full Featured
// Auto-loads metrics, supports dropdown-based asteroid search

const DARK_LAYOUT = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(15,15,30,0.9)",
    font: { family: "Orbitron, monospace", color: "#00d4ff", size: 11 },
    xaxis: { gridcolor: "rgba(0,212,255,0.1)", color: "#fff", zerolinecolor: "rgba(0,212,255,0.2)" },
    yaxis: { gridcolor: "rgba(0,212,255,0.1)", color: "#fff", zerolinecolor: "rgba(0,212,255,0.2)" },
    margin: { l: 60, r: 30, t: 40, b: 60 }
};

let ALL_ASTEROIDS = [];

async function loadAsteroidList() {
    try {
        const res = await fetch("/api/asteroids-list");
        const data = await res.json();
        ALL_ASTEROIDS = data.asteroids || [];
    } catch (e) { console.warn("Could not pre-load asteroid list:", e); }
}

function initDropdown(inputId, dropdownId, onSelect) {
    const input = document.getElementById(inputId);
    const dropdown = document.getElementById(dropdownId);
    if (!input || !dropdown) return;
    input.addEventListener("input", () => {
        const q = input.value.toLowerCase().trim();
        dropdown.innerHTML = "";
        if (q.length < 2) { dropdown.style.display = "none"; return; }
        const matches = ALL_ASTEROIDS.filter(a =>
            a.spkid.includes(q) || a.name.toLowerCase().includes(q)
        ).slice(0, 15);
        if (matches.length === 0) { dropdown.style.display = "none"; return; }
        matches.forEach(a => {
            const div = document.createElement("div");
            const tc = a.threat > 0.7 ? "#ff3333" : a.threat > 0.4 ? "#ffa500" : "#00ff7f";
            div.innerHTML = `<span>${a.name} (${a.spkid})</span>
                <span style="color:${tc};font-size:.8em;float:right">Threat ${(a.threat*100).toFixed(1)}% | MOID ${a.moid.toFixed(4)} AU</span>`;
            div.style.cssText = "padding:.6rem 1rem;cursor:pointer;border-bottom:1px solid rgba(255,255,255,.08)";
            div.addEventListener("mouseenter", () => div.style.background = "rgba(0,212,255,.15)");
            div.addEventListener("mouseleave", () => div.style.background = "");
            div.addEventListener("click", () => {
                input.value = a.spkid;
                dropdown.style.display = "none";
                onSelect(a.spkid);
            });
            dropdown.appendChild(div);
        });
        dropdown.style.display = "block";
    });
    document.addEventListener("click", e => {
        if (!input.contains(e.target) && !dropdown.contains(e.target))
            dropdown.style.display = "none";
    });
}

function injectDropdownStyles() {
    if (document.getElementById("ml-dd-style")) return;
    const s = document.createElement("style");
    s.id = "ml-dd-style";
    s.textContent = `
        .search-wrapper{position:relative;display:inline-block;width:100%;max-width:500px}
        .asteroid-dropdown{position:absolute;top:100%;left:0;right:0;z-index:999;
            background:#0d0d2b;border:1px solid rgba(0,212,255,.4);border-radius:0 0 6px 6px;
            max-height:280px;overflow-y:auto;display:none;box-shadow:0 8px 20px rgba(0,0,0,.6)}
    `;
    document.head.appendChild(s);
}

window.addEventListener("DOMContentLoaded", async () => {
    injectDropdownStyles();
    loadPerformanceMetrics();
    await loadAsteroidList();
    initDropdown("explainSearch", "explainDropdown", explainPrediction);
    initDropdown("ensembleSearch", "ensembleDropdown", getEnsemblePrediction);
    initDropdown("anomalySearch", "anomalyDropdown", detectAnomaly);
});

async function loadPerformanceMetrics() {
    try {
        const response = await fetch("/api/ml-performance");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        const m = data.metrics;
        document.getElementById("accuracy").textContent = (m.accuracy*100).toFixed(1)+"%";
        document.getElementById("precision").textContent = (m.precision*100).toFixed(1)+"%";
        document.getElementById("recall").textContent = (m.recall*100).toFixed(1)+"%";
        document.getElementById("f1").textContent = (m.f1_score*100).toFixed(1)+"%";
        document.getElementById("roc_auc").textContent = m.roc_auc.toFixed(3);
        if (m.optimal_threshold !== undefined) {
            const accEl = document.getElementById("accuracy");
            accEl.insertAdjacentHTML("afterend",
                `<div style="font-size:.7em;color:rgba(0,212,255,.7);margin-top:.3rem">Optimal threshold: ${m.optimal_threshold.toFixed(3)}</div>`);
        }
        renderROCCurve(data.roc_curve);
        renderPRCurve(data.pr_curve);
        renderConfusionMatrix(data.confusion_matrix);
        renderThreatDistribution(data.threat_distribution);
        if (data.feature_importance) renderGlobalFeatureImportance(data.feature_importance);
    } catch (err) {
        console.error("Error loading performance metrics:", err);
        ["accuracy","precision","recall","f1","roc_auc"].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = "Error";
        });
    }
}

function renderROCCurve(d) {
    const lay = {...DARK_LAYOUT, showlegend:true, legend:{x:.6,y:.1},
        xaxis:{...DARK_LAYOUT.xaxis, title:"False Positive Rate"},
        yaxis:{...DARK_LAYOUT.yaxis, title:"True Positive Rate"}};
    Plotly.newPlot("rocChart",[
        {x:d.fpr,y:d.tpr,mode:"lines",name:"ROC",line:{color:"#00d4ff",width:3},
         fill:"tozeroy",fillcolor:"rgba(0,212,255,.07)"},
        {x:[0,1],y:[0,1],mode:"lines",name:"Random",line:{color:"rgba(255,255,255,.3)",width:2,dash:"dash"}}
    ],lay,{responsive:true});
}
function renderPRCurve(d) {
    const lay = {...DARK_LAYOUT, showlegend:true,
        xaxis:{...DARK_LAYOUT.xaxis,title:"Recall"},
        yaxis:{...DARK_LAYOUT.yaxis,title:"Precision"}};
    Plotly.newPlot("prChart",[{x:d.recall,y:d.precision,mode:"lines",name:"PR",
        line:{color:"#ff00ff",width:3},fill:"tozeroy",fillcolor:"rgba(255,0,255,.07)"}],lay,{responsive:true});
}
function renderConfusionMatrix(cm) {
    const z=[[cm.true_negative,cm.false_positive],[cm.false_negative,cm.true_positive]];
    const t=cm.true_negative+cm.false_positive+cm.false_negative+cm.true_positive;
    Plotly.newPlot("confusionMatrix",[{z,type:"heatmap",
        x:["Pred Negative","Pred Positive"],y:["Actual Negative","Actual Positive"],
        colorscale:[[0,"#0a0a2e"],[.5,"#ff00ff"],[1,"#00d4ff"]],showscale:false,
        text:z.map(r=>r.map(v=>`${v}\n${(v/t*100).toFixed(1)}%`)),texttemplate:"%{text}",
        textfont:{size:16,color:"white",family:"Orbitron, monospace"}
    }],{...DARK_LAYOUT,xaxis:{side:"bottom",color:"#fff",title:"Predicted"},
        yaxis:{autorange:"reversed",color:"#fff",title:"Actual"}},{responsive:true});
}
function renderThreatDistribution(d) {
    Plotly.newPlot("threatDistribution",[{
        values:[d.high,d.medium,d.low],
        labels:["High Threat (>70%)","Medium Threat (40-70%)","Low Threat (<40%)"],
        type:"pie",hole:.45,marker:{colors:["#ff3333","#ffa500","#00ff7f"]},
        textinfo:"label+percent+value",textfont:{color:"white",family:"Orbitron, monospace",size:10}
    }],{...DARK_LAYOUT,showlegend:true,legend:{x:-.1,y:0}},{responsive:true});
}
function renderGlobalFeatureImportance(importance) {
    const el=document.getElementById("globalFeatureImportance");
    if (!el) return;
    const sorted=Object.entries(importance).sort((a,b)=>b[1]-a[1]).slice(0,12);
    Plotly.newPlot("globalFeatureImportance",[{
        x:sorted.map(([,v])=>v),y:sorted.map(([k])=>k.replace(/_/g," ")),
        type:"bar",orientation:"h",
        marker:{color:sorted.map(([,v])=>`rgba(0,${Math.round(v*212)},255,.85)`)}
    }],{...DARK_LAYOUT,
        xaxis:{...DARK_LAYOUT.xaxis,title:"Correlation |r|"},
        yaxis:{...DARK_LAYOUT.yaxis,autorange:"reversed"},
        margin:{l:180,r:30,t:30,b:50}},{responsive:true});
}

// ---- Explainability ----------------------------------------------------------
async function explainPrediction(asteroidId) {
    const id = asteroidId || document.getElementById("explainSearch").value.trim();
    if (!id) return;
    setLoading("explainResults","explainLoader",true);
    try {
        const res = await fetch(`/api/ml-explain/${encodeURIComponent(id)}`);
        if (!res.ok) { const e=await res.json(); throw new Error(e.detail||"Not found"); }
        const d = await res.json();
        setLoading("explainResults","explainLoader",false);
        document.getElementById("explainResults").style.display="block";
        document.getElementById("explainAsteroidName").textContent=d.asteroid_name||id;
        document.getElementById("explainPrediction").textContent=(d.prediction*100).toFixed(1)+"%";
        document.getElementById("explainLabel").textContent=d.prediction_label;
        document.getElementById("explainConfidence").textContent=(d.confidence*100).toFixed(1)+"%";
        document.getElementById("explainText").textContent=d.explanation_text;
        document.getElementById("explainPrediction").style.color=
            d.prediction>0.7?"#ff3333":d.prediction>0.4?"#ffa500":"#00ff7f";
        renderFIChart(d.feature_importance,"featureImportanceChart");
        renderSHAPChart(d.shap_values,"shapValuesChart");
    } catch(err) {
        setLoading("explainResults","explainLoader",false);
        showErr("explainErrMsg",err.message);
    }
}
function renderFIChart(imp,divId) {
    if (!imp) return;
    const s=Object.entries(imp).sort((a,b)=>b[1]-a[1]).slice(0,10);
    Plotly.newPlot(divId,[{x:s.map(([,v])=>v),y:s.map(([k])=>k.replace(/_/g," ")),
        type:"bar",orientation:"h",
        marker:{color:s.map(([,v])=>`rgba(255,${Math.round((1-v)*165)},0,.85)`)}}],
        {...DARK_LAYOUT,xaxis:{...DARK_LAYOUT.xaxis,title:"Importance"},
         yaxis:{...DARK_LAYOUT.yaxis,autorange:"reversed"},margin:{l:160,r:30,t:20,b:50}},{responsive:true});
}
function renderSHAPChart(shap,divId) {
    if (!shap) return;
    const s=Object.entries(shap).sort((a,b)=>Math.abs(b[1])-Math.abs(a[1])).slice(0,10);
    Plotly.newPlot(divId,[{x:s.map(([,v])=>v),y:s.map(([k])=>k.replace(/_/g," ")),
        type:"bar",orientation:"h",
        marker:{color:s.map(([,v])=>v>0?"#ff3333":"#00d4ff")}}],
        {...DARK_LAYOUT,xaxis:{...DARK_LAYOUT.xaxis,title:"SHAP (+ raises threat, - lowers)"},
         yaxis:{...DARK_LAYOUT.yaxis,autorange:"reversed"},margin:{l:160,r:30,t:20,b:50}},{responsive:true});
}

// ---- Ensemble ---------------------------------------------------------------
async function getEnsemblePrediction(asteroidId) {
    const id = asteroidId || document.getElementById("ensembleSearch").value.trim();
    if (!id) return;
    setLoading("ensembleResults","ensembleLoader",true);
    try {
        const res = await fetch(`/api/ensemble-predict/${encodeURIComponent(id)}`);
        if (!res.ok) { const e=await res.json(); throw new Error(e.detail||"Not found"); }
        const d = await res.json();
        setLoading("ensembleResults","ensembleLoader",false);
        document.getElementById("ensembleResults").style.display="block";
        document.getElementById("ensembleAsteroidName").textContent=d.asteroid_name||id;
        document.getElementById("ensembleScore").textContent=(d.ensemble_score*100).toFixed(1)+"%";
        document.getElementById("ensembleAgreement").textContent=(d.agreement*100).toFixed(1)+"%";
        document.getElementById("ensembleConfidence").textContent=(d.confidence*100).toFixed(1)+"%";
        document.getElementById("ensembleRecommendation").textContent=d.recommendation;
        document.getElementById("ensembleScore").style.color=
            d.ensemble_score>0.7?"#ff3333":d.ensemble_score>0.4?"#ffa500":"#00ff7f";
        renderEnsembleChart(d.individual_predictions,d.ensemble_score,d.outlier_models||[]);
    } catch(err) {
        setLoading("ensembleResults","ensembleLoader",false);
        showErr("ensembleErrMsg",err.message);
    }
}
function renderEnsembleChart(preds,ensemble,outliers) {
    const models=Object.keys(preds), vals=Object.values(preds);
    Plotly.newPlot("modelPredictionsChart",[
        {x:models.map(m=>m.replace(/_/g," ").toUpperCase()),y:vals,type:"bar",
         name:"Individual",marker:{color:models.map(m=>outliers.includes(m)?"#ffa500":"#00d4ff")},
         text:vals.map(v=>(v*100).toFixed(1)+"%"),textposition:"outside"},
        {x:models.map(m=>m.replace(/_/g," ").toUpperCase()),y:vals.map(()=>ensemble),
         mode:"lines",name:"Ensemble",line:{color:"#ff00ff",width:3,dash:"dash"}}
    ],{...DARK_LAYOUT,yaxis:{...DARK_LAYOUT.yaxis,title:"Threat Score",range:[0,1.1]},showlegend:true},
    {responsive:true});
}

// ---- Anomaly ----------------------------------------------------------------
async function detectAnomaly(asteroidId) {
    const id = asteroidId || document.getElementById("anomalySearch").value.trim();
    if (!id) return;
    setLoading("anomalyResults","anomalyLoader",true);
    try {
        const res = await fetch(`/api/anomaly-score/${encodeURIComponent(id)}`);
        if (!res.ok) { const e=await res.json(); throw new Error(e.detail||"Not found"); }
        const d = await res.json();
        setLoading("anomalyResults","anomalyLoader",false);
        document.getElementById("anomalyResults").style.display="block";
        document.getElementById("anomalyAsteroidName").textContent=d.asteroid_name||id;
        document.getElementById("anomalyScore").textContent=(d.anomaly_score*100).toFixed(1)+"%";
        document.getElementById("anomalySeverity").textContent=d.severity;
        document.getElementById("isAnomalous").textContent=d.is_anomalous?" YES":" NO";
        const sc={EXTREME:"#ff3333",HIGH:"#ffa500",MEDIUM:"#ffff00",LOW:"#00ff7f"};
        document.getElementById("anomalySeverity").style.color=sc[d.severity]||"#00ff7f";
        document.getElementById("anomalyExplanation").textContent=d.explanation;
        renderAnomalyFeatTable(d.anomalous_features);
        document.getElementById("anomalyRecommendations").innerHTML=
            (d.recommendations||[]).map(r=>`<li style="margin-bottom:.5rem">${r}</li>`).join("");
    } catch(err) {
        setLoading("anomalyResults","anomalyLoader",false);
        showErr("anomalyErrMsg",err.message);
    }
}
function renderAnomalyFeatTable(features) {
    const c=document.getElementById("anomalyFeaturesTable");
    if (!features||!features.length) { c.innerHTML="<p style='color:rgba(255,255,255,.5)'>No anomalous features.</p>"; return; }
    let h=`<h4 style="color:#ffa500;margin-bottom:1rem">Anomalous Features</h4><div style="overflow-x:auto">
        <table style="width:100%;border-collapse:collapse">
        <thead><tr style="background:rgba(255,165,0,.2);border-bottom:2px solid #ffa500">
        <th style="padding:.6rem;text-align:left">Feature</th><th style="padding:.6rem;text-align:right">Value</th>
        <th style="padding:.6rem;text-align:right">Z-Score</th><th style="padding:.6rem">Direction</th>
        <th style="padding:.6rem">Note</th></tr></thead><tbody>`;
    features.forEach((f,i)=>{
        const bg=i%2===0?"rgba(0,0,0,.2)":"rgba(0,0,0,.1)";
        const zc=Math.abs(f.z_score)>3?"#ff3333":"#ffa500";
        const dc=f.direction==="high"?"#ff5555":"#55aaff";
        h+=`<tr style="background:${bg};border-bottom:1px solid rgba(255,255,255,.08)">
            <td style="padding:.6rem">${f.feature.replace(/_/g," ")}</td>
            <td style="padding:.6rem;text-align:right;font-family:monospace">${Number(f.value).toFixed(4)}</td>
            <td style="padding:.6rem;text-align:right;color:${zc};font-family:monospace">${Number(f.z_score).toFixed(2)}σ</td>
            <td style="padding:.6rem;color:${dc}"> ${f.direction.toUpperCase()}</td>
            <td style="padding:.6rem;font-size:.85em;color:rgba(255,255,255,.7)">${f.comparison}</td></tr>`;
    });
    c.innerHTML=h+"</tbody></table></div>";
}

// ---- UI helpers -------------------------------------------------------------
function setLoading(sectionId, loaderId, on) {
    let l = document.getElementById(loaderId);
    if (!l) {
        l = document.createElement("div");
        l.id = loaderId;
        l.style.cssText = "padding:2rem;text-align:center;color:#00d4ff;display:none";
        l.innerHTML = "<div style='font-size:2rem;animation:spin 1s linear infinite'></div><p>Analysing...</p>";
        const s = document.getElementById(sectionId);
        if (s) s.parentNode.insertBefore(l, s);
    }
    l.style.display = on ? "block" : "none";
    const s = document.getElementById(sectionId);
    if (s && on) s.style.display = "none";
}
function showErr(errId, msg) {
    let e = document.getElementById(errId);
    if (!e) {
        e = document.createElement("div");
        e.id = errId;
        e.style.cssText = "padding:1rem;background:rgba(255,50,50,.1);border:1px solid #ff3333;border-radius:6px;color:#ff8888;margin-top:1rem";
        document.querySelector(".section") && document.querySelector(".section").appendChild(e);
    }
    e.textContent = " "+msg;
    e.style.display = "block";
}
