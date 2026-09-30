from django.db import models
from django.utils import timezone


class EtaSimulationLog(models.Model):
    """
    Log of simulated operational events and ETA calculations.
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
