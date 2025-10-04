from django.db import models
from django.utils import timezone

class SolarFlare(models.Model):
    """موديل لتخزين بيانات الانفجارات الشمسية"""
    
    FLARE_CLASSES = [
        ('A', 'Class A'),
        ('B', 'Class B'),
        ('C', 'Class C'),
        ('M', 'Class M'),
        ('X', 'Class X'),
    ]
    
    flare_id = models.CharField(max_length=100, unique=True)
    class_type = models.CharField(max_length=10)
    flare_class = models.CharField(max_length=1, choices=FLARE_CLASSES)
    intensity = models.FloatField()
    begin_time = models.DateTimeField()
    peak_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    # معلومات إضافية
    risk_level = models.CharField(max_length=20)
    risk_color = models.CharField(max_length=7)
    impact_effects = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-begin_time']
        verbose_name = 'Solar Flare'
        verbose_name_plural = 'Solar Flares'
    
    def __str__(self):
        return f"{self.flare_id} - {self.class_type}"


class SpaceWeatherReport(models.Model):
    """موديل لتخزين التقارير الدورية"""
    
    report_date = models.DateTimeField(default=timezone.now)
    total_flares = models.IntegerField(default=0)
    strongest_flare = models.ForeignKey(
        SolarFlare, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='strongest_reports'
    )
    risk_percentage = models.FloatField(default=0.0)
    prediction_confidence = models.FloatField(default=92.7)
    
    class Meta:
        ordering = ['-report_date']
    
    def __str__(self):
        return f"Report {self.report_date.strftime('%Y-%m-%d %H:%M')}"