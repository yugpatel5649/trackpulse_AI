/**
 * TrackPulse AI — Dynamic Train ETA Forecasting Application Logic
 * SIH 2026 Problem Statement 26028 | Indian Railways Prototype
 */

let selectedTrainNumber = "12931";
let etaChartInstance = null;
let delayChartInstance = null;
let autoRefreshTimer = null;

document.addEventListener("DOMContentLoaded", function () {
    // Initial data load
    fetchEtaSummary();

    // Auto-poll live feed every 10 seconds
    autoRefreshTimer = setInterval(fetchEtaSummary, 10000);
});

/**
 * Fetches overall ETA summary from GET /api/eta/
 */
async function fetchEtaSummary() {
    try {
        const response = await fetch('/api/eta/');
        if (!response.ok) {
            console.warn("ETA API returned non-200 status:", response.status);
            return;
        }

        const data = await response.json();
        if (data.status === "success") {
            updateKpiMetrics(data.kpi_metrics, data.last_updated);
            updateTrainTable(data.trains);

            // Find selected train or default to first
            let activeTrain = data.trains.find(t => t.train_number === selectedTrainNumber);
            if (!activeTrain && data.trains.length > 0) {
                activeTrain = data.trains[0];
                selectedTrainNumber = activeTrain.train_number;
            }

            if (activeTrain) {
                renderTrainDetails(activeTrain);
            }
        }
    } catch (err) {
        console.error("Error fetching live ETA summary:", err);
    }
}

/**
 * Updates top KPI metric cards
 */
function updateKpiMetrics(kpi, lastUpdated) {
    if (!kpi) return;
    document.getElementById("kpiActiveTrains").textContent = kpi.active_trains_count || 0;
    document.getElementById("kpiAvgDelay").textContent = `+${kpi.avg_system_delay_minutes || 0} min`;
    document.getElementById("lastUpdatedLabel").textContent = `Live Sync: ${lastUpdated.split(' ')[1] || lastUpdated}`;
}

/**
 * Updates the Live Coaching Train Telemetry Table
 */
function updateTrainTable(trains) {
    const tbody = document.getElementById("trainsTableBody");
    if (!tbody || !trains) return;

    tbody.innerHTML = trains.map(t => {
        const isSelected = t.train_number === selectedTrainNumber;
        const delayClass = t.current_delay_minutes > 10 ? 'delay-high' : (t.current_delay_minutes > 0 ? 'delay-medium' : 'delay-on-time');
        const delayText = t.current_delay_minutes > 0 ? `+${t.current_delay_minutes} min` : 'ON TIME';

        return `
            <tr class="train-row ${isSelected ? 'selected-row' : ''}" data-train-number="${t.train_number}" onclick="selectTrain('${t.train_number}')">
                <td>
                    <div class="train-name-cell">
                        <span class="train-no">${t.train_number}</span>
                        <span class="train-title">${t.train_name}</span>
                    </div>
                </td>
                <td>
                    <div class="location-cell">
                        <span class="current-st">${t.current_station}</span>
                        <span class="next-st">➔ ${t.next_station}</span>
                    </div>
                </td>
                <td>
                    <span class="speed-badge">${Math.round(t.current_speed_kmh)} km/h</span>
                </td>
                <td>
                    <span class="delay-badge ${delayClass}">${delayText}</span>
                </td>
                <td>
                    <div class="eta-cell">
                        <span class="pred-eta">${t.destination_predicted_eta}</span>
                        <span class="sched-eta">Sched: ${t.destination_scheduled_eta}</span>
                    </div>
                </td>
                <td>
                    <div class="confidence-pill">
                        <span class="conf-value">${t.overall_confidence_score}%</span>
                    </div>
                </td>
                <td>
                    <button class="btn-select-train" onclick="event.stopPropagation(); selectTrain('${t.train_number}')">Inspect</button>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Switches selected train and fetches detail
 */
async function selectTrain(trainNumber) {
    selectedTrainNumber = trainNumber;
    
    // Highlight table row
    document.querySelectorAll(".train-row").forEach(row => {
        row.classList.toggle("selected-row", row.getAttribute("data-train-number") === trainNumber);
    });

    try {
        const res = await fetch(`/api/eta/train/${trainNumber}/`);
        if (res.ok) {
            const data = await res.json();
            if (data.status === "success" && data.train_detail) {
                renderTrainDetails(data.train_detail);
            }
        }
    } catch (err) {
        console.error(`Error fetching train ${trainNumber} detail:`, err);
    }
}

/**
 * Renders detail view for selected train
 */
function renderTrainDetails(train) {
    if (!train) return;

    // Header & Banner
    document.getElementById("selectedTrainTitle").innerHTML = `<span class="icon">🎯</span> Train Forecast: ${train.train_number} — ${train.train_name}`;
    document.getElementById("selectedTrainType").textContent = train.train_type;

    document.getElementById("cmpSchedEta").textContent = train.destination_scheduled_eta;
    document.getElementById("cmpDestName").textContent = train.destination_name;
    document.getElementById("cmpDynamicEta").textContent = train.destination_predicted_eta;
    document.getElementById("cmpDiffBadge").textContent = `+${train.destination_delay_minutes} MIN DELAY`;
    document.getElementById("cmpConfidence").textContent = `${train.overall_confidence_score}%`;

    // Operational Context Bar
    document.getElementById("opLocation").textContent = train.current_location;
    document.getElementById("opSpeed").textContent = `${Math.round(train.current_speed_kmh)} km/h (Max: ${train.max_speed_kmh} km/h)`;
    document.getElementById("opCondition").textContent = train.operational_condition;

    // Station Forecast Table
    const stBody = document.getElementById("stationForecastBody");
    if (stBody && train.stations_forecast) {
        stBody.innerHTML = train.stations_forecast.map(st => {
            const statusLower = (st.status || 'UPCOMING').toLowerCase();
            const delaySpan = st.delay_minutes > 0 ? `<span class="text-amber">+${st.delay_minutes} min</span>` : `<span class="text-green">0 min</span>`;

            return `
                <tr class="st-row st-${statusLower}">
                    <td>
                        <strong>${st.name}</strong>
                        <span class="st-code">(${st.code})</span>
                    </td>
                    <td>${st.distance_km} km</td>
                    <td>${st.scheduled_eta}</td>
                    <td><strong class="text-cyan">${st.predicted_eta}</strong></td>
                    <td>${delaySpan}</td>
                    <td>
                        <div class="conf-bar-wrap">
                            <div class="conf-bar" style="width: ${st.confidence_score}%;"></div>
                            <span class="conf-num">${st.confidence_score}%</span>
                        </div>
                    </td>
                    <td>
                        <span class="st-status-badge st-status-${statusLower}">${st.status}</span>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // Feature Weights
    const featContainer = document.getElementById("featureWeightsContainer");
    if (featContainer && train.feature_weights) {
        featContainer.innerHTML = train.feature_weights.map(f => `
            <div class="feature-item">
                <div class="feature-name">${f.feature}</div>
                <div class="feature-weight">${f.weight} Weight</div>
                <div class="feature-val">${f.value}</div>
            </div>
        `).join('');
    }

    // Render Analytics Charts
    renderAnalyticsCharts(train);
}

/**
 * Render Chart.js Analytics for Scheduled vs Dynamic ETA & Delay Propagation
 */
function renderAnalyticsCharts(train) {
    if (!train || !train.stations_forecast) return;

    const labels = train.stations_forecast.map(s => s.code);
    
    // Convert HH:MM into arrival minutes from midnight for plotting
    const parseMins = (timeStr) => {
        try {
            const parts = timeStr.split(':');
            return parseInt(parts[0]) * 60 + parseInt(parts[1]);
        } catch (e) {
            return 0;
        }
    };

    const schedMinutes = train.stations_forecast.map(s => parseMins(s.scheduled_eta));
    const predMinutes = train.stations_forecast.map(s => parseMins(s.predicted_eta));
    const delays = train.stations_forecast.map(s => s.delay_minutes);

    // Chart 1: Scheduled vs Dynamic ETA Timeline
    const ctxEta = document.getElementById("etaTimelineChart");
    if (ctxEta) {
        if (etaChartInstance) etaChartInstance.destroy();

        etaChartInstance = new Chart(ctxEta, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Scheduled ETA (Timeline)',
                        data: schedMinutes,
                        borderColor: '#94a3b8',
                        borderDash: [5, 5],
                        backgroundColor: 'transparent',
                        tension: 0.2
                    },
                    {
                        label: 'Dynamic AI Predicted ETA',
                        data: predMinutes,
                        borderColor: '#00e5ff',
                        backgroundColor: 'rgba(0, 229, 255, 0.1)',
                        fill: true,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#94a3b8' } }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { 
                        ticks: { 
                            color: '#94a3b8',
                            callback: function(val) {
                                const h = Math.floor(val / 60) % 24;
                                const m = val % 60;
                                return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
                            }
                        }, 
                        grid: { color: 'rgba(255,255,255,0.05)' } 
                    }
                }
            }
        });
    }

    // Chart 2: Delay Propagation Across Route
    const ctxDelay = document.getElementById("delayPropagationChart");
    if (ctxDelay) {
        if (delayChartInstance) delayChartInstance.destroy();

        delayChartInstance = new Chart(ctxDelay, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Calculated Section Delay (Min)',
                    data: delays,
                    backgroundColor: delays.map(d => d > 10 ? 'rgba(239, 68, 68, 0.7)' : (d > 0 ? 'rgba(245, 158, 11, 0.7)' : 'rgba(16, 185, 129, 0.7)')),
                    borderColor: delays.map(d => d > 10 ? '#ef4444' : (d > 0 ? '#f59e0b' : '#10b981')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#94a3b8' } }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    }
}

/**
 * Triggers Dynamic Event Simulation (Hackathon Demo Feature)
 */
async function triggerSimulation(eventType, delayMinutes = 10) {
    const simSelect = document.getElementById("simTrainSelect");
    const targetTrain = simSelect ? simSelect.value : selectedTrainNumber;
    const notice = document.getElementById("simNotice");

    if (notice) notice.textContent = `Triggering ${eventType} simulation...`;

    try {
        const response = await fetch('/api/eta/simulate-event/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                train_number: targetTrain,
                event_type: eventType,
                delay_minutes: delayMinutes,
                remarks: "Interactive Hackathon Demo Event"
            })
        });

        if (response.ok) {
            const resultData = await response.json();
            if (resultData.status === "success") {
                if (notice) notice.textContent = `⚡ Simulated ${eventType}: Forecast dynamically updated!`;
                
                if (resultData.all_trains) {
                    updateTrainTable(resultData.all_trains);
                }

                if (resultData.updated_forecast) {
                    renderTrainDetails(resultData.updated_forecast);
                } else {
                    fetchEtaSummary();
                }
            }
        }
    } catch (err) {
        console.error("Simulation trigger failed:", err);
        if (notice) notice.textContent = "Error triggering simulation.";
    }
}

/**
 * Resets simulation feed back to baseline schedule
 */
async function resetSimulationFeed() {
    const notice = document.getElementById("simNotice");
    if (notice) notice.textContent = "Resetting simulation to baseline timetable...";

    try {
        const response = await fetch('/api/eta/reset/', { method: 'POST' });
        if (response.ok) {
            const data = await response.json();
            if (data.status === "success") {
                if (notice) notice.textContent = "✓ Simulation reset to corridor baseline!";
                fetchEtaSummary();
            }
        }
    } catch (err) {
        console.error("Reset failed:", err);
    }
}
