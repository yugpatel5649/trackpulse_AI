from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import datetime

from eta.models import SimulatedTrain, SimulatedStation, EtaSimulationLog


class BaseRailwayDataProvider(ABC):
    """
    Abstract interface for Railway Data Providers.
    Designed so that Mock/Simulated feed can later be seamlessly replaced by an actual
    Indian Railways live API (e.g. NTES / COA / ICMS REST endpoints).
    """

    @abstractmethod
    def get_active_trains(self) -> List[Dict[str, Any]]:
        """Return list of all monitored active coaching trains."""
        pass

    @abstractmethod
    def get_train_by_number(self, train_number: str) -> Optional[Dict[str, Any]]:
        """Return full live status for a specific train."""
        pass

    @abstractmethod
    def simulate_event(self, train_number: str, event_type: str, delay_minutes: int = 0, remarks: str = "") -> Dict[str, Any]:
        """Trigger dynamic event simulation for hackathon demonstration."""
        pass

    @abstractmethod
    def reset_simulation(self) -> bool:
        """Reset simulation back to corridor timetable baseline."""
        pass


class DatabaseRailwayDataProvider(BaseRailwayDataProvider):
    """
    Database-backed Railway Data Provider.
    Persists simulated live train state in Django database models to ensure state survives
    across multiple API calls, page refreshes, and multi-process server restarts.
    Labeled as: SIMULATED LIVE DATA.
    """

    def __init__(self):
        self.data_source_name = "PROTOTYPE SIMULATED LIVE FEED (WR-ADI CORRIDOR)"
        self.is_simulated = True
        self._ensure_database_seeded()

    def _ensure_database_seeded(self):
        """Seed initial corridor timetable data into database if empty."""
        try:
            if not SimulatedTrain.objects.exists():
                self.reset_simulation()
        except Exception:
            pass  # Fail gracefully if tables are mid-migration

    def _to_dict(self, train: SimulatedTrain) -> Dict[str, Any]:
        """Convert a SimulatedTrain DB instance to dictionary format."""
        stations_qs = train.stations.all().order_by('order')
        stations_list = [
            {
                "code": s.code,
                "name": s.name,
                "distance_km": s.distance_km,
                "sched_arr": s.sched_arr,
                "sched_dep": s.sched_dep,
                "dwell_min": s.dwell_min,
                "status": s.status,
            }
            for s in stations_qs
        ]

        return {
            "train_number": train.train_number,
            "train_name": train.train_name,
            "train_type": train.train_type,
            "origin": train.origin,
            "destination": train.destination,
            "total_distance_km": train.total_distance_km,
            "current_station_code": train.current_station_code,
            "current_station_name": train.current_station_name,
            "next_station_code": train.next_station_code,
            "next_station_name": train.next_station_name,
            "current_location_desc": train.current_location_desc,
            "current_speed_kmh": train.current_speed_kmh,
            "max_speed_kmh": train.max_speed_kmh,
            "current_delay_minutes": train.current_delay_minutes,
            "congestion_level": train.congestion_level,
            "signal_status": train.signal_status,
            "operational_condition": train.operational_condition,
            "weather_condition": train.weather_condition,
            "unscheduled_stop": train.unscheduled_stop,
            "historical_delay_trend_min": train.historical_delay_trend or [train.current_delay_minutes],
            "updated_at": train.updated_at.strftime("%H:%M:%S") if train.updated_at else "",
            "stations": stations_list,
        }

    def get_active_trains(self) -> List[Dict[str, Any]]:
        self._ensure_database_seeded()
        trains_qs = SimulatedTrain.objects.all().prefetch_related('stations')
        return [self._to_dict(t) for t in trains_qs]

    def get_train_by_number(self, train_number: str) -> Optional[Dict[str, Any]]:
        self._ensure_database_seeded()
        train = SimulatedTrain.objects.filter(train_number=str(train_number).strip()).prefetch_related('stations').first()
        if train:
            return self._to_dict(train)
        return None

    def simulate_event(self, train_number: str, event_type: str, delay_minutes: int = 0, remarks: str = "") -> Dict[str, Any]:
        """
        Dynamically mutate database-stored train parameters to simulate real-world operational changes.
        Persists updated delay, speed, congestion, signal, weather, or unscheduled stop state in database.
        """
        self._ensure_database_seeded()
        t_no = str(train_number).strip()

        if t_no.upper() == "ALL":
            trains = list(SimulatedTrain.objects.all())
            if not trains:
                return {"success": False, "message": "No active trains found in database."}
            for t in trains:
                self._apply_event(t, event_type, delay_minutes)
            
            # Log event
            try:
                EtaSimulationLog.objects.create(
                    train_number="ALL",
                    event_type=event_type,
                    delay_delta_minutes=delay_minutes,
                    remarks=remarks or f"Applied {event_type} to all trains"
                )
            except Exception:
                pass

            return {"success": True, "message": f"Applied simulation event '{event_type}' to all active trains."}

        train = SimulatedTrain.objects.filter(train_number=t_no).first()
        if not train:
            return {"success": False, "message": f"Train {train_number} not found."}

        self._apply_event(train, event_type, delay_minutes)

        try:
            EtaSimulationLog.objects.create(
                train_number=train.train_number,
                event_type=event_type,
                delay_delta_minutes=delay_minutes,
                remarks=remarks or f"Applied {event_type} to train {train.train_number}"
            )
        except Exception:
            pass

        return {
            "success": True,
            "train_number": train.train_number,
            "event_type": event_type,
            "new_delay_minutes": train.current_delay_minutes,
            "new_speed_kmh": train.current_speed_kmh,
            "operational_condition": train.operational_condition,
            "message": f"Updated train {train.train_number}: {event_type} (Delay: +{train.current_delay_minutes} min, Speed: {train.current_speed_kmh:.0f} km/h)"
        }

    def _apply_event(self, train: SimulatedTrain, event_type: str, delay_minutes: int):
        event_upper = str(event_type).upper()

        if event_upper in ["ADD_DELAY", "DELAY"]:
            add_val = delay_minutes if delay_minutes != 0 else 10
            train.current_delay_minutes = max(0, train.current_delay_minutes + add_val)
            train.operational_condition = f"CASCADE_DELAY (+{train.current_delay_minutes}m)"
            trend = list(train.historical_delay_trend or [])
            trend.append(train.current_delay_minutes)
            if len(trend) > 6:
                trend.pop(0)
            train.historical_delay_trend = trend

        elif event_upper in ["CONGESTION", "SIGNAL_HOLD", "HEAVY_CONGESTION"]:
            train.congestion_level = "HEAVY"
            train.signal_status = "CAUTION_YELLOW"
            train.current_speed_kmh = max(25.0, round(train.current_speed_kmh * 0.45, 1))
            train.operational_condition = "SECTIONAL_CONGESTION_HOLD"
            train.current_delay_minutes += 8

        elif event_upper in ["UNSCHEDULED_STOP", "STOP"]:
            train.unscheduled_stop = True
            train.signal_status = "STOP_RED"
            train.current_speed_kmh = 0.0
            train.current_delay_minutes += 12
            train.operational_condition = "UNSCHEDULED_SIGNAL_HALT"

        elif event_upper in ["SPEED_RESTRICTION", "SPEED_REDUCE"]:
            train.current_speed_kmh = min(train.current_speed_kmh, 45.0)
            train.operational_condition = "CAUTION_SPEED_RESTRICTION (45 KM/H)"
            train.current_delay_minutes += 6

        elif event_upper in ["WEATHER_FOG", "FOG"]:
            train.weather_condition = "FOG"
            train.current_speed_kmh = min(train.current_speed_kmh, 60.0)
            train.operational_condition = "FOG_FOGFUG_RESTRICTION"
            train.current_delay_minutes += 15

        elif event_upper in ["CLEAR", "CLEAR_TRACK", "RESET_NORMAL", "NORMAL"]:
            train.unscheduled_stop = False
            train.congestion_level = "NORMAL"
            train.signal_status = "PROCEED_GREEN"
            train.weather_condition = "CLEAR"
            train.current_speed_kmh = train.max_speed_kmh - 10.0
            train.operational_condition = "NORMAL_RUNNING"

        train.save()

    def reset_simulation(self) -> bool:
        """Reset all simulated train states in database back to corridor timetable baseline."""
        SimulatedStation.objects.all().delete()
        SimulatedTrain.objects.all().delete()

        # Seed 1: 12931 Double Decker
        t1 = SimulatedTrain.objects.create(
            train_number="12931",
            train_name="Ahmedabad Double Decker Express",
            train_type="Superfast Express",
            origin="Mumbai Central (MMCT)",
            destination="Ahmedabad Junction (ADI)",
            total_distance_km=493,
            current_station_code="ST",
            current_station_name="Surat",
            next_station_code="BH",
            next_station_name="Bharuch Junction",
            current_location_desc="Approaching Bharuch Junction (KM 298)",
            current_speed_kmh=105.0,
            max_speed_kmh=130.0,
            current_delay_minutes=8,
            congestion_level="MODERATE",
            signal_status="PROCEED_GREEN",
            operational_condition="NORMAL_RUNNING",
            weather_condition="CLEAR",
            unscheduled_stop=False,
            historical_delay_trend=[2, 4, 6, 8, 8]
        )
        st1 = [
            ("MMCT", "Mumbai Central", 0, "14:30", "14:30", 0, "PASSED"),
            ("BVI", "Borivali", 30, "15:02", "15:05", 3, "PASSED"),
            ("VAPI", "Vapi", 168, "16:40", "16:42", 2, "PASSED"),
            ("ST", "Surat", 263, "17:52", "17:57", 5, "PASSED"),
            ("BH", "Bharuch Junction", 322, "18:42", "18:44", 2, "NEXT"),
            ("BRC", "Vadodara Junction", 393, "19:40", "19:45", 5, "UPCOMING"),
            ("ANND", "Anand Junction", 428, "20:16", "20:18", 2, "UPCOMING"),
            ("ADI", "Ahmedabad Junction", 493, "21:25", "21:25", 0, "UPCOMING"),
        ]
        for idx, (code, name, dist, arr, dep, dwell, status) in enumerate(st1):
            SimulatedStation.objects.create(train=t1, order=idx, code=code, name=name, distance_km=dist, sched_arr=arr, sched_dep=dep, dwell_min=dwell, status=status)

        # Seed 2: 12009 Shatabdi Express
        t2 = SimulatedTrain.objects.create(
            train_number="12009",
            train_name="Mumbai Central - Ahmedabad Shatabdi Express",
            train_type="Shatabdi Express",
            origin="Mumbai Central (MMCT)",
            destination="Ahmedabad Junction (ADI)",
            total_distance_km=493,
            current_station_code="VAPI",
            current_station_name="Vapi",
            next_station_code="ST",
            next_station_name="Surat",
            current_location_desc="Cruising between Vapi & Surat (KM 215)",
            current_speed_kmh=120.0,
            max_speed_kmh=130.0,
            current_delay_minutes=2,
            congestion_level="NORMAL",
            signal_status="PROCEED_GREEN",
            operational_condition="OPTIMAL_SPEED",
            weather_condition="CLEAR",
            unscheduled_stop=False,
            historical_delay_trend=[0, 1, 2, 2, 2]
        )
        st2 = [
            ("MMCT", "Mumbai Central", 0, "06:10", "06:10", 0, "PASSED"),
            ("BVI", "Borivali", 30, "06:43", "06:45", 2, "PASSED"),
            ("VAPI", "Vapi", 168, "08:09", "08:11", 2, "PASSED"),
            ("ST", "Surat", 263, "09:18", "09:23", 5, "NEXT"),
            ("BH", "Bharuch Junction", 322, "10:04", "10:06", 2, "UPCOMING"),
            ("BRC", "Vadodara Junction", 393, "10:59", "11:04", 5, "UPCOMING"),
            ("ANND", "Anand Junction", 428, "11:33", "11:35", 2, "UPCOMING"),
            ("ND", "Nadiad Junction", 447, "11:51", "11:53", 2, "UPCOMING"),
            ("ADI", "Ahmedabad Junction", 493, "12:45", "12:45", 0, "UPCOMING"),
        ]
        for idx, (code, name, dist, arr, dep, dwell, status) in enumerate(st2):
            SimulatedStation.objects.create(train=t2, order=idx, code=code, name=name, distance_km=dist, sched_arr=arr, sched_dep=dep, dwell_min=dwell, status=status)

        # Seed 3: 12902 Gujarat Mail
        t3 = SimulatedTrain.objects.create(
            train_number="12902",
            train_name="Gujarat Mail Express",
            train_type="Superfast Mail",
            origin="Ahmedabad Junction (ADI)",
            destination="Mumbai Central (MMCT)",
            total_distance_km=493,
            current_station_code="BRC",
            current_station_name="Vadodara Junction",
            next_station_code="BH",
            next_station_name="Bharuch Junction",
            current_location_desc="Departing Vadodara Junction Yard (KM 393)",
            current_speed_kmh=65.0,
            max_speed_kmh=110.0,
            current_delay_minutes=15,
            congestion_level="HEAVY",
            signal_status="CAUTION_YELLOW",
            operational_condition="YARD_CONGESTION",
            weather_condition="CLEAR",
            unscheduled_stop=False,
            historical_delay_trend=[5, 8, 12, 15, 15]
        )
        st3 = [
            ("ADI", "Ahmedabad Junction", 0, "22:50", "22:50", 0, "PASSED"),
            ("ND", "Nadiad Junction", 46, "23:35", "23:37", 2, "PASSED"),
            ("ANND", "Anand Junction", 65, "23:54", "23:56", 2, "PASSED"),
            ("BRC", "Vadodara Junction", 100, "00:33", "00:38", 5, "PASSED"),
            ("BH", "Bharuch Junction", 171, "01:32", "01:34", 2, "NEXT"),
            ("ST", "Surat", 230, "02:29", "02:34", 5, "UPCOMING"),
            ("NVS", "Navsari", 259, "03:00", "03:02", 2, "UPCOMING"),
            ("BL", "Valsad", 299, "03:40", "03:42", 2, "UPCOMING"),
            ("VAPI", "Vapi", 325, "04:04", "04:06", 2, "UPCOMING"),
            ("BVI", "Borivali", 463, "05:37", "05:40", 3, "UPCOMING"),
            ("MMCT", "Mumbai Central", 493, "06:15", "06:15", 0, "UPCOMING"),
        ]
        for idx, (code, name, dist, arr, dep, dwell, status) in enumerate(st3):
            SimulatedStation.objects.create(train=t3, order=idx, code=code, name=name, distance_km=dist, sched_arr=arr, sched_dep=dep, dwell_min=dwell, status=status)

        # Seed 4: 20901 Vande Bharat Express
        t4 = SimulatedTrain.objects.create(
            train_number="20901",
            train_name="Mumbai Central - Gandhinagar Vande Bharat Express",
            train_type="Vande Bharat Express",
            origin="Mumbai Central (MMCT)",
            destination="Gandhinagar Capital (GNC)",
            total_distance_km=522,
            current_station_code="BRC",
            current_station_name="Vadodara Junction",
            next_station_code="ADI",
            next_station_name="Ahmedabad Junction",
            current_location_desc="Accelerating past Vadodara North (KM 405)",
            current_speed_kmh=128.0,
            max_speed_kmh=160.0,
            current_delay_minutes=0,
            congestion_level="NORMAL",
            signal_status="PROCEED_GREEN",
            operational_condition="PRIORITY_GREEN_CORRIDOR",
            weather_condition="CLEAR",
            unscheduled_stop=False,
            historical_delay_trend=[0, 0, 0, 0, 0]
        )
        st4 = [
            ("MMCT", "Mumbai Central", 0, "06:00", "06:00", 0, "PASSED"),
            ("BVI", "Borivali", 30, "06:23", "06:25", 2, "PASSED"),
            ("VAPI", "Vapi", 168, "07:56", "07:58", 2, "PASSED"),
            ("ST", "Surat", 263, "08:55", "08:58", 3, "PASSED"),
            ("BRC", "Vadodara Junction", 393, "10:13", "10:16", 3, "PASSED"),
            ("ADI", "Ahmedabad Junction", 493, "11:25", "11:30", 5, "NEXT"),
            ("GNC", "Gandhinagar Capital", 522, "12:25", "12:25", 0, "UPCOMING"),
        ]
        for idx, (code, name, dist, arr, dep, dwell, status) in enumerate(st4):
            SimulatedStation.objects.create(train=t4, order=idx, code=code, name=name, distance_km=dist, sched_arr=arr, sched_dep=dep, dwell_min=dwell, status=status)

        return True


# Alias for backward compatibility
MockRailwayDataProvider = DatabaseRailwayDataProvider
