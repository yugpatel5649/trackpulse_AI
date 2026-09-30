from django.db import models
from django.utils import timezone


class SimulatedTrain(models.Model):
    """
    Database model to persist simulated train state across API requests and server restarts.
    """
    CONGESTION_CHOICES = [
        ('NORMAL', 'Normal'),
        ('MODERATE', 'Moderate'),
        ('HEAVY', 'Heavy'),
    ]

    SIGNAL_CHOICES = [
        ('PROCEED_GREEN', 'Proceed (Green)'),
        ('CAUTION_YELLOW', 'Caution (Yellow)'),
        ('STOP_RED', 'Stop (Red)'),
    ]

    train_number = models.CharField(max_length=20, primary_key=True)
    train_name = models.CharField(max_length=150)
    train_type = models.CharField(max_length=80)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    total_distance_km = models.IntegerField(default=500)
    
    current_station_code = models.CharField(max_length=20)
    current_station_name = models.CharField(max_length=100)
    next_station_code = models.CharField(max_length=20)
    next_station_name = models.CharField(max_length=100)
    current_location_desc = models.CharField(max_length=200)
    
    current_speed_kmh = models.FloatField(default=80.0)
    max_speed_kmh = models.FloatField(default=130.0)
    current_delay_minutes = models.IntegerField(default=0)
    
    congestion_level = models.CharField(max_length=20, choices=CONGESTION_CHOICES, default='NORMAL')
    signal_status = models.CharField(max_length=30, choices=SIGNAL_CHOICES, default='PROCEED_GREEN')
    operational_condition = models.CharField(max_length=120, default='NORMAL_RUNNING')
    weather_condition = models.CharField(max_length=50, default='CLEAR')
    unscheduled_stop = models.BooleanField(default=False)
    
    historical_delay_trend = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['train_number']

    def __str__(self):
        return f"{self.train_number} - {self.train_name} (+{self.current_delay_minutes}m)"


class SimulatedStation(models.Model):
    """
    Station timetable and live status for a simulated train.
    """
    STATUS_CHOICES = [
        ('PASSED', 'Passed'),
        ('NEXT', 'Next Station'),
        ('UPCOMING', 'Upcoming'),
    ]

    train = models.ForeignKey(SimulatedTrain, on_delete=models.CASCADE, related_name='stations')
    order = models.IntegerField(default=0)
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    distance_km = models.IntegerField(default=0)
    sched_arr = models.CharField(max_length=10)
    sched_dep = models.CharField(max_length=10)
    dwell_min = models.IntegerField(default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPCOMING')

    class Meta:
        ordering = ['train', 'order']

    def __str__(self):
        return f"{self.train.train_number} @ {self.name} ({self.code}) - {self.sched_arr}"


class EtaSimulationLog(models.Model):
    """
    Audit log of simulated operational events and ETA calculations.
    """
    train_number = models.CharField(max_length=20)
    event_type = models.CharField(max_length=100)
    delay_delta_minutes = models.IntegerField(default=0)
    remarks = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.train_number} - {self.event_type} ({self.delay_delta_minutes:+d}m)"
