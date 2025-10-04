from rest_framework import serializers
from .models import SolarFlare, SpaceWeatherReport

class SolarFlareSerializer(serializers.ModelSerializer):
    """Serializer للانفجارات الشمسية"""
    
    class Meta:
        model = SolarFlare
        fields = [
            'id', 'flare_id', 'class_type', 'flare_class', 
            'intensity', 'begin_time', 'peak_time', 'end_time',
            'risk_level', 'risk_color', 'impact_effects',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SpaceWeatherReportSerializer(serializers.ModelSerializer):
    """Serializer للتقارير"""
    
    strongest_flare = SolarFlareSerializer(read_only=True)
    
    class Meta:
        model = SpaceWeatherReport
        fields = [
            'id', 'report_date', 'total_flares', 
            'strongest_flare', 'risk_percentage', 
            'prediction_confidence'
        ]


class SolarFlareStatsSerializer(serializers.Serializer):
    """Serializer للإحصائيات"""
    
    total_flares = serializers.IntegerField()
    flares_by_class = serializers.DictField()
    average_intensity = serializers.FloatField()
    risk_distribution = serializers.DictField()
    timeline_data = serializers.ListField()