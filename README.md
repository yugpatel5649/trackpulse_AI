# TrackPulse AI — Dynamic Train ETA Forecasting

### Smart India Hackathon 2026 (SIH 2026) • Problem Statement 26028

**"Dynamic Forecast of Expected Time of Arrival (ETA) for Coaching Trains on Indian Railways"**

---

## 📌 Executive Summary

**TrackPulse AI** is an advanced dynamic Expected Time of Arrival (ETA) forecasting solution engineered for Indian Railways coaching operations. Built for **SIH 2026 Problem Statement 26028**, TrackPulse AI dynamically predicts station-by-station arrival timings and final destination ETAs by ingesting real-time train location, current delay, section speed limits, historical delay propagation patterns, track congestion index, signal aspects, and weather visibility conditions.

> [!NOTE]
> **Data Layer Transparency**: The current prototype uses **`SIMULATED LIVE DATA`** for demonstration. The system architecture uses a clean service-provider abstraction (`BaseRailwayDataProvider` / `MockRailwayDataProvider`), designed for seamless future integration with authorized real-time Indian Railways data feeds (e.g. NTES / COA / ICMS APIs) without requiring frontend or prediction engine rewrites.

---

## 🚀 Key Features & Capabilities

- **Dynamic Multi-Factor ETA Forecasting Engine**:
  Computes dynamically recalculated ETAs instead of relying on static timetable estimates. Incorporates live train location, current delay, section speed, historical section running times, congestion level, signal halts, and weather factors.
- **Station-Wise Arrival & Delay Propagation**:
  Generates detailed upcoming station forecasts with distance breakdown, scheduled ETA, dynamic AI predicted ETA, station delay, and engine confidence scores (%).
- **Baseline (Scheduled) vs Dynamic AI ETA Comparison**:
  Side-by-side visual comparison displaying scheduled timetable baseline versus AI predicted arrival time with real-time delay delta indicators.
- **Simulated Live Railway Data Layer**:
  Monitors coaching trains across Western Railway's high-density Mumbai Central – Vadodara – Ahmedabad corridor (including Vande Bharat Express, Shatabdi Express, Double Decker Express, Gujarat Mail, and Tejas Rajdhani Express).
- **Dynamic Event Simulation Console (Hackathon Demo Controller)**:
  Allows judges and evaluators to trigger real-world operational events (e.g. `+10 min delay`, `signal hold / congestion`, `unscheduled stop`, `fog impact`, or `clear line`) and observe instantaneous live re-forecasting.
- **Real-Time AJAX Auto-Polling**:
  Dashboard automatically refreshes telemetry and predictions every 10 seconds via asynchronous REST APIs without full page reloads.
- **Preserved SIH 26027 RailBlock AI Module**:
  The original SIH 2026 Problem Statement 26027 maintenance block planning application (**RailBlock AI**) remains preserved and fully functional at `/block-planning/`.

---

## 🏗️ System Architecture

```
trackpulse_ai/ (railblock_AI)
├── railblock_project/        # Core Django settings & routing configuration
│   ├── settings.py           # Includes 'eta', 'core', and 'scheduler' apps
│   └── urls.py               # Main router ('/' -> TrackPulse AI, '/block-planning/' -> RailBlock AI)
├── eta/                       # [SIH 26028] Dynamic ETA Forecasting Application
│   ├── apps.py
│   ├── urls.py               # Dashboard & REST endpoints (/api/eta/, /api/eta/train/<id>/)
│   ├── views.py              # ETA views & REST API controllers
│   ├── models.py             # Event simulation audit logs
│   └── services/
│       ├── data_provider.py  # Base & Mock Railway Data Provider abstraction
│       └── eta_engine.py     # Transparent Multi-Factor Statistical ML Engine
├── core/                      # [SIH 26027] Preserved RailBlock AI Maintenance App
│   ├── urls.py               # Preserved routes mounted under /block-planning/
│   ├── views.py
│   └── models.py
├── templates/
│   └── eta/
│       └── dashboard.html    # Control office glassmorphism dashboard UI
└── static/
    ├── css/
    │   └── eta_style.css     # TrackPulse AI dark control room CSS
    └── js/
        └── eta_app.js        # Asynchronous live polling, Chart.js analytics & event triggers
```

---

## ⚡ REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | TrackPulse AI Dynamic Train ETA Forecasting Dashboard |
| `GET` | `/api/eta/` | System-wide ETA summary, KPI metrics, and active train forecasts |
| `GET` | `/api/eta/train/<train_number>/` | Detailed station-by-station ETA forecast for a specific train |
| `POST` | `/api/eta/simulate-event/` | Triggers dynamic event simulation (+delay, congestion, stop, fog) |
| `POST` | `/api/eta/reset/` | Resets simulated live data layer back to baseline schedule |
| `GET` | `/block-planning/` | Preserved SIH 26027 RailBlock AI Maintenance Block Dashboard |

---

## 🛠️ Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Axel-032/railblock_AI.git
   cd railblock_AI
   ```

2. **Set up virtual environment (optional but recommended)**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Run Test Suite**:
   ```bash
   python manage.py test core eta
   ```

6. **Start Local Development Server**:
   ```bash
   python manage.py runserver
   ```
   Open your browser and navigate to:
   - Primary ETA System (SIH 26028): `http://127.0.0.1:8000/`
   - Preserved Block Planning System (SIH 26027): `http://127.0.0.1:8000/block-planning/`

---

## ☁️ Deployment on Render

This application is ready for production deployment on [Render](https://render.com).

- **Environment**: Python 3.12 / 3.14
- **Build Command**:
  ```bash
  pip install -r requirements.txt && python manage.py migrate
  ```
- **Start Command**:
  ```bash
  python manage.py runserver 0.0.0.0:$PORT
  ```

---

## 📜 Problem Statement Compliance

- **Problem Statement**: SIH 2026 PS 26028 — Dynamic Forecast of Expected Time of Arrival (ETA) for Coaching Trains.
- **Simulated Data**: Mock data provider layer clearly labeled as `SIMULATED LIVE DATA` / `PROTOTYPE LIVE FEED`.
- **Backward Compatibility**: Fully preserves SIH 26027 RailBlock AI at `/block-planning/`.
