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
    const elActive = document.getElementById("kpiActiveTrains");
    const elDelay = document.getElementById("kpiAvgDelay");
    const elOnTime = document.getElementById("kpiOnTime");
    const elUpdated = document.getElementById("lastUpdatedLabel");

    if (elActive) elActive.textContent = kpi.active_trains_count || 0;
    if (elDelay) elDelay.textContent = `+${kpi.avg_system_delay_minutes || 0} min`;
    if (elOnTime) elOnTime.textContent = `${kpi.on_time_count || 0} / ${kpi.active_trains_count || 0} Trains`;
    if (elUpdated) {
        const timePart = lastUpdated ? (lastUpdated.includes(' ') ? lastUpdated.split(' ')[1] : lastUpdated) : '';
        elUpdated.textContent = `Live Sync: ${timePart}`;
    }
}

/**
 * Updates the Live Coaching Train Telemetry Table
 */
function updateTrainTable(trains) {
    const tbody = document.getElementById("trainsTableBody");
    if (!tbody || !trains) return;

    tbody.innerHTML = trains.map(t => {
        const isSelected = t.train_number === selectedTrainNumber;
        const delayClass = t.current_delay_minutes > 10 
            ? 'background-color: #FCE8E6; color: #D9534F; border: 1px solid #D9534F;' 
            : (t.current_delay_minutes > 0 
                ? 'background-color: #FFF4D6; color: #5A4200; border: 1px solid #B7791F;' 
                : 'background-color: #E3F3EA; color: #16845B; border: 1px solid #16845B;');
        const delayText = t.current_delay_minutes > 0 ? `+${t.current_delay_minutes} min` : 'ON TIME';

        return `
            <tr class="train-row ${isSelected ? 'selected-row' : ''}" data-train-number="${t.train_number}" onclick="selectTrain('${t.train_number}')" style="border-bottom: 1px solid var(--border-mid); cursor: pointer; ${isSelected ? 'background-color: #E6EFFB;' : ''}">
                <td style="padding: 8px;">
                    <strong style="color: var(--blue-primary); font-family: monospace; font-size: 13px;">${t.train_number}</strong><br>
                    <span style="font-size: 11px; color: var(--text-muted);">${t.train_name}</span>
                </td>
                <td style="padding: 8px;">
                    <strong>${t.current_station}</strong><br>
                    <span style="font-size: 11px; color: var(--text-muted);">➔ ${t.next_station}</span>
                </td>
                <td style="padding: 8px; font-family: monospace; font-weight: 700;">
                    ${Math.round(t.current_speed_kmh)} km/h
                </td>
                <td style="padding: 8px;">
                    <span class="badge" style="${delayClass} font-weight: 800;">${delayText}</span>
                </td>
                <td style="padding: 8px; font-family: monospace;">
                    <strong style="color: var(--blue-primary); font-size: 13px;">${t.destination_predicted_eta}</strong><br>
                    <span style="font-size: 10px; color: var(--text-dim);">Sched: ${t.destination_scheduled_eta}</span>
                </td>
                <td style="padding: 8px; font-weight: 800; color: var(--smms-green); font-family: monospace;">
                    ${t.overall_confidence_score}%
                </td>
                <td style="padding: 8px; text-align: center;">
                    <button class="btn btn-outline btn-sm" style="padding: 2px 8px; font-size: 11px;" onclick="event.stopPropagation(); selectTrain('${t.train_number}')">Inspect</button>
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
        const isTarget = row.getAttribute("data-train-number") === trainNumber;
        row.style.backgroundColor = isTarget ? "#E6EFFB" : "";
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
    const elTitle = document.getElementById("selectedTrainTitle");
    const elType = document.getElementById("selectedTrainType");

    if (elTitle) elTitle.innerHTML = `<span>🎯</span> Train Forecast: ${train.train_number} — ${train.train_name}`;
    if (elType) elType.textContent = train.train_type;

    const elSched = document.getElementById("cmpSchedEta");
    const elDest = document.getElementById("cmpDestName");
    const elDynamic = document.getElementById("cmpDynamicEta");
    const elDiff = document.getElementById("cmpDiffBadge");
    const elConf = document.getElementById("cmpConfidence");

    if (elSched) elSched.textContent = train.destination_scheduled_eta;
    if (elDest) elDest.textContent = train.destination_name;
    if (elDynamic) elDynamic.textContent = train.destination_predicted_eta;
    if (elDiff) elDiff.textContent = `+${train.destination_delay_minutes} MIN DELAY`;
    if (elConf) elConf.textContent = `${train.overall_confidence_score}%`;

    // Operational Context Bar
    const elLoc = document.getElementById("opLocation");
    const elSpeed = document.getElementById("opSpeed");
    const elCond = document.getElementById("opCondition");

    if (elLoc) elLoc.textContent = train.current_location;
    if (elSpeed) elSpeed.textContent = `${Math.round(train.current_speed_kmh)} km/h (Max: ${train.max_speed_kmh} km/h)`;
    if (elCond) elCond.textContent = train.operational_condition;

    // Station Forecast Table
    const stBody = document.getElementById("stationForecastBody");
    if (stBody && train.stations_forecast) {
        stBody.innerHTML = train.stations_forecast.map(st => {
            const delaySpan = st.delay_minutes > 0 ? `<span style="color: var(--red-secondary);">+${st.delay_minutes} min</span>` : `<span style="color: var(--signal-clear);">0 min</span>`;
            
            let statusBadge = `<span class="badge" style="background-color: #F1F5F9; color: #475569;">UPCOMING</span>`;
            if (st.status === 'PASSED') {
                statusBadge = `<span class="badge" style="background-color: #E2E8F0; color: #64748B;">PASSED</span>`;
            } else if (st.status === 'NEXT') {
                statusBadge = `<span class="badge" style="background-color: #E6EFFB; color: var(--blue-primary); border: 1px solid var(--blue-primary);">NEXT</span>`;
            }

            return `
                <tr style="border-bottom: 1px solid var(--border-mid);">
                    <td style="padding: 6px;">
                        <strong>${st.name}</strong> <span style="color: var(--text-muted); font-family: monospace;">(${st.code})</span>
                    </td>
                    <td style="padding: 6px;">${st.distance_km} km</td>
                    <td style="padding: 6px;">${st.scheduled_eta}</td>
                    <td style="padding: 6px; font-family: monospace;"><strong style="color: var(--blue-primary);">${st.predicted_eta}</strong></td>
                    <td style="padding: 6px; font-weight: 700;">${delaySpan}</td>
                    <td style="padding: 6px; font-family: monospace; font-weight: 700; color: var(--smms-green);">${st.confidence_score}%</td>
                    <td style="padding: 6px; text-align: center;">${statusBadge}</td>
                </tr>
            `;
        }).join('');
    }

    // Feature Weights
    const featContainer = document.getElementById("featureWeightsContainer");
    if (featContainer && train.feature_weights) {
        featContainer.innerHTML = train.feature_weights.map(f => `
            <div style="background-color: var(--bg-input); border: 1px solid var(--border-mid); padding: 8px 10px;">
                <div style="font-size: 10px; color: var(--text-muted); font-weight: 700;">${f.feature}</div>
                <div style="font-size: 10px; font-weight: 800; color: var(--blue-primary);">${f.weight} Weight</div>
                <div style="font-size: 12px; font-weight: 800; color: var(--text-bright); margin-top: 2px;">${f.value}</div>
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
                        label: 'Scheduled ETA',
                        data: schedMinutes,
                        borderColor: '#64748B',
                        borderDash: [4, 4],
                        backgroundColor: 'transparent',
                        tension: 0.1
                    },
                    {
                        label: 'Dynamic AI ETA',
                        data: predMinutes,
                        borderColor: '#2563EB',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        fill: true,
                        tension: 0.2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#334155', font: { size: 10 } } }
                },
                scales: {
                    x: { ticks: { color: '#64748B', font: { size: 9 } } },
                    y: { 
                        ticks: { 
                            color: '#64748B',
                            font: { size: 9 },
                            callback: function(val) {
                                const h = Math.floor(val / 60) % 24;
                                const m = val % 60;
                                return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
                            }
                        }
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
                    label: 'Section Delay (Min)',
                    data: delays,
                    backgroundColor: delays.map(d => d > 10 ? '#D9534F' : (d > 0 ? '#B7791F' : '#168B78')),
                    borderColor: delays.map(d => d > 10 ? '#D9534F' : (d > 0 ? '#B7791F' : '#168B78')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#334155', font: { size: 10 } } }
                },
                scales: {
                    x: { ticks: { color: '#64748B', font: { size: 9 } } },
                    y: { ticks: { color: '#64748B', font: { size: 9 } } }
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
                if (notice) notice.textContent = `✓ Simulated ${eventType}: Saved to database & ETA recalculated!`;
                
                if (resultData.all_trains) {
                    updateTrainTable(resultData.all_trains);
                }

                if (resultData.updated_forecast) {
                    renderTrainDetails(resultData.updated_forecast);
                } else {
                    fetchEtaSummary();
                }
            } else {
                if (notice) notice.textContent = `Error: ${resultData.message || 'Simulation failed.'}`;
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
    if (notice) notice.textContent = "Resetting database to timetable baseline...";

    try {
        const response = await fetch('/api/eta/reset/', { method: 'POST' });
        if (response.ok) {
            const data = await response.json();
            if (data.status === "success") {
                if (notice) notice.textContent = "✓ Timetable reset to baseline!";
                fetchEtaSummary();
            }
        }
    } catch (err) {
        console.error("Reset failed:", err);
    }
}
