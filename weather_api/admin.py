from django.contrib import admin
from .models import SolarFlare, SpaceWeatherReport


@admin.register(SolarFlare)
class SolarFlareAdmin(admin.ModelAdmin):
    """واجهة إدارة الانفجارات الشمسية"""
    
    list_display = [
        'flare_id', 'class_type', 'flare_class', 
        'intensity', 'risk_level', 'begin_time'
    ]
    list_filter = ['flare_class', 'risk_level', 'begin_time']
    search_fields = ['flare_id', 'class_type']
    ordering = ['-begin_time']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('flare_id', 'class_type', 'flare_class', 'intensity')
        }),
        ('التوقيت', {
            'fields': ('begin_time', 'peak_time', 'end_time')
        }),
        ('التقييم', {
            'fields': ('risk_level', 'risk_color', 'impact_effects')
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SpaceWeatherReport)
class SpaceWeatherReportAdmin(admin.ModelAdmin):
    """واجهة إدارة التقارير"""
    
    list_display = [
        'report_date', 'total_flares', 
        'risk_percentage', 'prediction_confidence'
    ]
    list_filter = ['report_date']
    ordering = ['-report_date']
    
    fieldsets = (
        ('معلومات التقرير', {
            'fields': ('report_date', 'total_flares', 'strongest_flare')
        }),
        ('التحليل', {
            'fields': ('risk_percentage', 'prediction_confidence')
        }),
    )
