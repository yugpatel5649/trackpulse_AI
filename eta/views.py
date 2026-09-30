import json
from django.shortcuts import render
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import datetime

from eta.services.data_provider import MockRailwayDataProvider
from eta.services.eta_engine import DynamicEtaEngine
from eta.models import EtaSimulationLog


def get_provider():
    return MockRailwayDataProvider()


def eta_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Renders the primary TrackPulse AI Dynamic Train ETA Forecasting Dashboard (SIH 2026 PS 26028).
    """
    provider = get_provider()
    trains_raw = provider.get_active_trains()
    evaluations = [DynamicEtaEngine.calculate_train_forecast(t) for t in trains_raw]

    context = {
        'page_title': 'TrackPulse AI — Dynamic Train ETA Forecasting',
        'data_source_label': 'SIMULATED LIVE DATA',
        'active_trains_count': len(evaluations),
        'avg_delay_minutes': round(sum(e['current_delay_minutes'] for e in evaluations) / max(1, len(evaluations)), 1),
        'trains': evaluations,
        'selected_train': evaluations[0] if evaluations else None,
        'engine_name': DynamicEtaEngine.MODEL_NAME,
        'engine_type': DynamicEtaEngine.MODEL_TYPE,
        'last_updated': datetime.datetime.now().strftime('%H:%M:%S'),
    }
    return render(request, 'eta/dashboard.html', context)


def api_eta_summary(request: HttpRequest) -> JsonResponse:
    """
    GET /api/eta/
    Returns live summary of all monitored coaching trains and dynamic ETA predictions.
    """
    try:
        provider = get_provider()
        trains_raw = provider.get_active_trains()
        evaluations = [DynamicEtaEngine.calculate_train_forecast(t) for t in trains_raw]

        avg_delay = round(sum(e['current_delay_minutes'] for e in evaluations) / max(1, len(evaluations)), 1)

        data = {
            "status": "success",
            "sih_problem_statement": "SIH 2026 PS 26028",
            "project_name": "TrackPulse AI",
            "data_source": "SIMULATED LIVE DATA",
            "is_simulated_live_feed": True,
            "architecture_note": "Mock provider can be replaced with real-time Indian Railways API (NTES/COA) without UI refactoring.",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "kpi_metrics": {
                "active_trains_count": len(evaluations),
                "avg_system_delay_minutes": avg_delay,
                "engine_status": "ONLINE • Multi-Factor Statistical ML",
                "refresh_interval_sec": 10,
            },
            "trains": evaluations
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Server error generating ETA summary: {str(e)}"
        }, status=500)


def api_eta_train_detail(request: HttpRequest, train_number: str) -> JsonResponse:
    """
    GET /api/eta/train/<train_number>/
    Returns detailed station-wise dynamic ETA prediction for a single train.
    Handles invalid train numbers with a clean 404 JSON response.
    """
    try:
        provider = get_provider()
        train_raw = provider.get_train_by_number(train_number)

        if not train_raw:
            return JsonResponse({
                "status": "error",
                "error_code": "TRAIN_NOT_FOUND",
                "message": f"Train number '{train_number}' was not found in active corridor simulation.",
                "available_trains": [t["train_number"] for t in provider.get_active_trains()]
            }, status=404)

        forecast = DynamicEtaEngine.calculate_train_forecast(train_raw)

        return JsonResponse({
            "status": "success",
            "data_source": "SIMULATED LIVE DATA",
            "train_detail": forecast
        })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Error fetching train forecast: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_simulate_event(request: HttpRequest) -> JsonResponse:
    """
    POST /api/eta/simulate-event/
    Allows judges and users to trigger live dynamic operational events:
    - Add +10 min delay
    - Signal hold / heavy congestion
    - Unscheduled stop
    - Fog / Weather impact
    - Clear track
    """
    try:
        if request.content_type == "application/json" and request.body:
            body = json.loads(request.body.decode('utf-8'))
        else:
            body = request.POST

        train_number = str(body.get("train_number", "12931")).strip()
        event_type = str(body.get("event_type", "ADD_DELAY")).strip()
        delay_minutes = int(body.get("delay_minutes", 10))
        remarks = str(body.get("remarks", "Judge event trigger simulation")).strip()

        provider = get_provider()
        result = provider.simulate_event(
            train_number=train_number,
            event_type=event_type,
            delay_minutes=delay_minutes,
            remarks=remarks
        )

        # Log event in database model
        try:
            EtaSimulationLog.objects.create(
                train_number=train_number,
                event_type=event_type,
                delay_delta_minutes=delay_minutes,
                remarks=remarks
            )
        except Exception:
            pass  # Non-blocking if db is in read-only mode

        # Fetch updated forecast
        trains_raw = provider.get_active_trains()
        evaluations = [DynamicEtaEngine.calculate_train_forecast(t) for t in trains_raw]
        updated_selected = next((e for e in evaluations if e["train_number"] == train_number), evaluations[0] if evaluations else None)

        return JsonResponse({
            "status": "success",
            "result": result,
            "updated_forecast": updated_selected,
            "all_trains": evaluations
        })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Simulation failed: {str(e)}"
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_reset_simulation(request: HttpRequest) -> JsonResponse:
    """
    POST /api/eta/reset/
    Resets mock live data back to default timetable baseline.
    """
    try:
        provider = get_provider()
        provider.reset_simulation()
        trains_raw = provider.get_active_trains()
        evaluations = [DynamicEtaEngine.calculate_train_forecast(t) for t in trains_raw]

        return JsonResponse({
            "status": "success",
            "message": "Simulation feed successfully reset to initial corridor timetable baseline.",
            "trains": evaluations
        })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Reset failed: {str(e)}"
        }, status=500)
