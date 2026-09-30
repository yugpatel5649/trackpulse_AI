import time
import copy
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import datetime


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


class MockRailwayDataProvider(BaseRailwayDataProvider):
    """
    Prototype Live Railway Data Provider delivering simulated real-time telemetry.
    Labeled as: SIMULATED LIVE DATA / PROTOTYPE LIVE FEED.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MockRailwayDataProvider, cls).__new__(cls)
            cls._instance._initialize_data()
        return cls._instance

    def _initialize_data(self):
        """Build baseline timetable and live status for prototype trains."""
        self.data_source_name = "PROTOTYPE SIMULATED LIVE FEED (WR-ADI CORRIDOR)"
        self.is_simulated = True
        self.last_updated = datetime.datetime.now()

        # Prototype Trains on Mumbai Central - Ahmedabad Corridor
        self._initial_trains: Dict[str, Dict[str, Any]] = {
            "12931": {
                "train_number": "12931",
                "train_name": "Ahmedabad Double Decker Express",
                "train_type": "Superfast Express",
                "origin": "Mumbai Central (MMCT)",
                "destination": "Ahmedabad Junction (ADI)",
                "total_distance_km": 493,
                "current_station_code": "ST",
                "current_station_name": "Surat",
                "next_station_code": "BH",
                "next_station_name": "Bharuch Junction",
                "current_location_desc": "Approaching Bharuch Junction (KM 298)",
                "current_speed_kmh": 105,
                "max_speed_kmh": 130,
                "current_delay_minutes": 8,
                "congestion_level": "MODERATE",  # NORMAL, MODERATE, HEAVY
                "signal_status": "PROCEED_GREEN",  # PROCEED_GREEN, CAUTION_YELLOW, STOP_RED
                "operational_condition": "NORMAL_RUNNING",  # NORMAL_RUNNING, SPEED_RESTRICTION, SIGNAL_HOLD, UNSCHEDULED_STOP
                "weather_condition": "CLEAR",  # CLEAR, FOG, RAIN
                "unscheduled_stop": False,
                "dwell_delay_minutes": 2,
                "historical_delay_trend_min": [2, 4, 6, 8, 8],
                "stations": [
                    {"code": "MMCT", "name": "Mumbai Central", "distance_km": 0, "sched_arr": "14:30", "sched_dep": "14:30", "dwell_min": 0, "status": "PASSED"},
                    {"code": "BVI", "name": "Borivali", "distance_km": 30, "sched_arr": "15:02", "sched_dep": "15:05", "dwell_min": 3, "status": "PASSED"},
                    {"code": "VAPI", "name": "Vapi", "distance_km": 168, "sched_arr": "16:40", "sched_dep": "16:42", "dwell_min": 2, "status": "PASSED"},
                    {"code": "ST", "name": "Surat", "distance_km": 263, "sched_arr": "17:52", "sched_dep": "17:57", "dwell_min": 5, "status": "PASSED"},
                    {"code": "BH", "name": "Bharuch Junction", "distance_km": 322, "sched_arr": "18:42", "sched_dep": "18:44", "dwell_min": 2, "status": "NEXT"},
                    {"code": "BRC", "name": "Vadodara Junction", "distance_km": 393, "sched_arr": "19:40", "sched_dep": "19:45", "dwell_min": 5, "status": "UPCOMING"},
                    {"code": "ANND", "name": "Anand Junction", "distance_km": 428, "sched_arr": "20:16", "sched_dep": "20:18", "dwell_min": 2, "status": "UPCOMING"},
                    {"code": "ADI", "name": "Ahmedabad Junction", "distance_km": 493, "sched_arr": "21:25", "sched_dep": "21:25", "dwell_min": 0, "status": "UPCOMING"},
                ]
            },
            "12009": {
                "train_number": "12009",
                "train_name": "Mumbai Central - Ahmedabad Shatabdi Express",
                "train_type": "Shatabdi Express",
                "origin": "Mumbai Central (MMCT)",
                "destination": "Ahmedabad Junction (ADI)",
                "total_distance_km": 493,
                "current_station_code": "VAPI",
                "current_station_name": "Vapi",
                "next_station_code": "ST",
                "next_station_name": "Surat",
                "current_location_desc": "Cruising between Vapi & Surat (KM 215)",
                "current_speed_kmh": 120,
                "max_speed_kmh": 130,
                "current_delay_minutes": 2,
                "congestion_level": "NORMAL",
                "signal_status": "PROCEED_GREEN",
                "operational_condition": "OPTIMAL_SPEED",
                "weather_condition": "CLEAR",
                "unscheduled_stop": False,
                "dwell_delay_minutes": 0,
                "historical_delay_trend_min": [0, 1, 2, 2, 2],
                "stations": [
                    {"code": "MMCT", "name": "Mumbai Central", "distance_km": 0, "sched_arr": "06:10", "sched_dep": "06:10", "dwell_min": 0, "status": "PASSED"},
                    {"code": "BVI", "name": "Borivali", "distance_km": 30, "sched_arr": "06:43", "sched_dep": "06:45", "dwell_min": 2, "status": "PASSED"},
                    {"code": "VAPI", "name": "Vapi", "distance_km": 168, "sched_arr": "08:09", "sched_dep": "08:11", "dwell_min": 2, "status": "PASSED"},
                    {"code": "ST", "name": "Surat", "distance_km": 263, "sched_arr": "09:18", "sched_dep": "09:23", "dwell_min": 5, "status": "NEXT"},
                    {"code": "BH", "name": "Bharuch Junction", "distance_km": 322, "sched_arr": "10:04", "sched_dep": "10:06", "dwell_min": 2, "status": "UPCOMING"},
                    {"code": "BRC", "name": "Vadodara Junction", "distance_km": 393, "sched_arr": "10:59", "sched_dep": "11:04", "dwell_min": 5, "status": "UPCOMING"},
                    {"code": "ANND", "name": "Anand Junction", "distance_km": 428, "sched_arr": "11:33", "sched_dep": "11:35", "dwell_min": 2, "status": "UPCOMING"},
                    {"code": "ND", "name": "Nadiad Junction", "distance_km": 447, "sched_arr": "11:51", "sched_dep": "11:53", "dwell_min": 2, "status": "UPCOMING"},
                    {"code": "ADI", "name": "Ahmedabad Junction", "distance_km": 493, "sched_arr": "12:45", "sched_dep": "12:45", "dwell_min": 0, "status": "UPCOMING"},
                ]
            },
            "12902": {
                "train_number": "12902",
                "train_name": "Gujarat Mail Express",
                "train_type": "Superfast Mail",
                "origin": "Ahmedabad Junction (ADI)",
                "destination": "Mumbai Central (MMCT)",
                "total_distance_km": 493,
                "current_station_code": "BRC",
                "current_station_name": "Vadodara Junction",
                "next_station_code": "BH",
                "next_station_name": "Bharuch Junction",
                "current_location_desc": "Departing Vadodara Junction Yard (KM 393)",
                "current_speed_kmh": 65,
                "max_speed_kmh": 110,
                "current_delay_minutes": 15,
                "congestion_level": "HEAVY",
                "signal_status": "CAUTION_YELLOW",
                "operational_condition": "YARD_CONGESTION",
                "weather_condition": "CLEAR",
                "unscheduled_stop": False,
                "dwell_delay_minutes": 4,
                "historical_delay_trend_min": [5, 8, 12, 15, 15],
                "stations": [
                    {"code": "ADI", "name": "Ahmedabad Junction", "distance_km": 0, "sched_arr": "22:50", "sched_dep": "22:50", "dwell_min": 0, "status": "PASSED"},
                    {"code": "ND", "name": "Nadiad Junction", "distance_km": 46, "sched_arr": "23:35", "sched_dep": "23:37", "dwell_min": 2, "status": "PASSED"},
                    {"code": "ANND", "name": "Anand Junction", "distance_km": 65, "sched_arr": "23:54", "sched_dep": "23:56", "dwell_min": 2, "status": "PASSED"},
                    {"code": "BRC", "name": "Vadodara Junction", "distance_km": 100, "sched_arr": "00:33", "sched_dep": "00:38", "dwell_min": 5, "status": "PASSED"},
                    {"code": "BH", "name": "Bharuch Junction", "distance_km": 171, "sched_arr": "01:32", "sched_dep": "01:34", "dwell_min": 2, "status": "NEXT"},
                    {"code": "ST", "name": "Surat", "distance_km": 230, "sched_arr": "02:29", "sched_dep": "02:34", "dwell_min": 5, "status": "UPCOMING"},
                    {"code": "NVS", "name": "Navsari", "distance_km": 259, "sched_arr": "03:00", "sched_dep": "03:02", "dwell_min": 2, "status": "UPCOMING"},
                    {"code": "BL", "name": "Valsad", "distance_km": 299, "sched_arr": "03:40", "sched_dep": "03:42", "dwell_min": 2, "status": "UPCOMING"},
                    {"code": "VAPI", "name": "Vapi", "distance_km": 325, "sched_arr": "04:04", "sched_dep": "04:06", "dwell_min": 2, "status": "UPCOMING"},
                    {"code": "BVI", "name": "Borivali", "distance_km": 463, "sched_arr": "05:37", "sched_dep": "05:40", "dwell_min": 3, "status": "UPCOMING"},
                    {"code": "MMCT", "name": "Mumbai Central", "distance_km": 493, "sched_arr": "06:15", "sched_dep": "06:15", "dwell_min": 0, "status": "UPCOMING"},
                ]
            },
            "20901": {
                "train_number": "20901",
                "train_name": "Mumbai Central - Gandhinagar Vande Bharat Express",
                "train_type": "Vande Bharat Express",
                "origin": "Mumbai Central (MMCT)",
                "destination": "Gandhinagar Capital (GNC)",
                "total_distance_km": 522,
                "current_station_code": "BRC",
                "current_station_name": "Vadodara Junction",
                "next_station_code": "ADI",
                "next_station_name": "Ahmedabad Junction",
                "current_location_desc": "Accelerating past Vadodara North (KM 405)",
                "current_speed_kmh": 128,
                "max_speed_kmh": 160,
                "current_delay_minutes": 0,
                "congestion_level": "NORMAL",
                "signal_status": "PROCEED_GREEN",
                "operational_condition": "PRIORITY_GREEN_CORRIDOR",
                "weather_condition": "CLEAR",
                "unscheduled_stop": False,
                "dwell_delay_minutes": 0,
                "historical_delay_trend_min": [0, 0, 0, 0, 0],
                "stations": [
                    {"code": "MMCT", "name": "Mumbai Central", "distance_km": 0, "sched_arr": "06:00", "sched_dep": "06:00", "dwell_min": 0, "status": "PASSED"},
                    {"code": "BVI", "name": "Borivali", "distance_km": 30, "sched_arr": "06:23", "sched_dep": "06:25", "dwell_min": 2, "status": "PASSED"},
                    {"code": "VAPI", "name": "Vapi", "distance_km": 168, "sched_arr": "07:56", "sched_dep": "07:58", "dwell_min": 2, "status": "PASSED"},
                    {"code": "ST", "name": "Surat", "distance_km": 263, "sched_arr": "08:55", "sched_dep": "08:58", "dwell_min": 3, "status": "PASSED"},
                    {"code": "BRC", "name": "Vadodara Junction", "distance_km": 393, "sched_arr": "10:13", "sched_dep": "10:16", "dwell_min": 3, "status": "PASSED"},
                    {"code": "ADI", "name": "Ahmedabad Junction", "distance_km": 493, "sched_arr": "11:25", "sched_dep": "11:30", "dwell_min": 5, "status": "NEXT"},
                    {"code": "GNC", "name": "Gandhinagar Capital", "distance_km": 522, "sched_arr": "12:25", "sched_dep": "12:25", "dwell_min": 0, "status": "UPCOMING"},
                ]
            }
        }
        self.live_trains = copy.deepcopy(self._initial_trains)

    def get_active_trains(self) -> List[Dict[str, Any]]:
        self.last_updated = datetime.datetime.now()
        trains_list = []
        for t_no, t_data in self.live_trains.items():
            trains_list.append(copy.deepcopy(t_data))
        return trains_list

    def get_train_by_number(self, train_number: str) -> Optional[Dict[str, Any]]:
        t_data = self.live_trains.get(str(train_number).strip())
        if t_data:
            return copy.deepcopy(t_data)
        return None

    def simulate_event(self, train_number: str, event_type: str, delay_minutes: int = 0, remarks: str = "") -> Dict[str, Any]:
        """
        Dynamically mutate mock live data parameters to simulate real-world operational changes.
        Types: ADD_DELAY, SET_CONGESTION, UNSCHEDULED_STOP, CLEAR_TRACK, SPEED_CHANGE
        """
        train = self.live_trains.get(str(train_number).strip())
        if not train:
            # If train number is "ALL", apply to all trains
            if str(train_number).upper() == "ALL":
                for t in self.live_trains.values():
                    self._apply_event_to_train(t, event_type, delay_minutes, remarks)
                self.last_updated = datetime.datetime.now()
                return {"success": True, "message": f"Applied simulation event '{event_type}' to all active trains."}
            return {"success": False, "message": f"Train {train_number} not found."}

        self._apply_event_to_train(train, event_type, delay_minutes, remarks)
        self.last_updated = datetime.datetime.now()
        return {
            "success": True,
            "train_number": train["train_number"],
            "event_type": event_type,
            "new_delay_minutes": train["current_delay_minutes"],
            "new_speed_kmh": train["current_speed_kmh"],
            "operational_condition": train["operational_condition"],
            "message": f"Updated train {train['train_number']}: {event_type} (Delay: {train['current_delay_minutes']} min, Speed: {train['current_speed_kmh']} km/h)"
        }

    def _apply_event_to_train(self, train: Dict[str, Any], event_type: str, delay_minutes: int, remarks: str):
        event_upper = event_type.upper()

        if event_upper in ["ADD_DELAY", "DELAY"]:
            add_val = delay_minutes if delay_minutes != 0 else 10
            train["current_delay_minutes"] = max(0, train["current_delay_minutes"] + add_val)
            train["operational_condition"] = f"CASCADE_DELAY (+{train['current_delay_minutes']}m)"
            train["historical_delay_trend_min"].append(train["current_delay_minutes"])
            if len(train["historical_delay_trend_min"]) > 6:
                train["historical_delay_trend_min"].pop(0)

        elif event_upper in ["CONGESTION", "SIGNAL_HOLD"]:
            train["congestion_level"] = "HEAVY"
            train["signal_status"] = "CAUTION_YELLOW"
            train["current_speed_kmh"] = max(25, int(train["current_speed_kmh"] * 0.45))
            train["operational_condition"] = "SECTIONAL_CONGESTION_HOLD"
            train["current_delay_minutes"] += 8

        elif event_upper in ["UNSCHEDULED_STOP", "STOP"]:
            train["unscheduled_stop"] = True
            train["signal_status"] = "STOP_RED"
            train["current_speed_kmh"] = 0
            train["current_delay_minutes"] += 12
            train["operational_condition"] = "UNSCHEDULED_SIGNAL_HALT"

        elif event_upper in ["WEATHER_FOG", "FOG"]:
            train["weather_condition"] = "FOG"
            train["current_speed_kmh"] = min(train["current_speed_kmh"], 60)
            train["operational_condition"] = "FOG_FOGFUG_RESTRICTION"
            train["current_delay_minutes"] += 15

        elif event_upper in ["CLEAR", "RESET_NORMAL"]:
            train["unscheduled_stop"] = False
            train["congestion_level"] = "NORMAL"
            train["signal_status"] = "PROCEED_GREEN"
            train["weather_condition"] = "CLEAR"
            train["current_speed_kmh"] = train["max_speed_kmh"] - 10
            train["operational_condition"] = "NORMAL_RUNNING"

    def reset_simulation(self) -> bool:
        self.live_trains = copy.deepcopy(self._initial_trains)
        self.last_updated = datetime.datetime.now()
        return True
