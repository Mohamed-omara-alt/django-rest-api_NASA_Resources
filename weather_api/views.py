from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Q
from django.db import models
import numpy as np

from .models import SolarFlare, SpaceWeatherReport
from .serializers import (
    SolarFlareSerializer, 
    SpaceWeatherReportSerializer,
    SolarFlareStatsSerializer
)
from .services import NASASpaceWeatherService


class StandardResultsSetPagination(PageNumberPagination):
    """إعدادات الـ Pagination"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class SolarFlareViewSet(viewsets.ModelViewSet):
    """
    ViewSet للتعامل مع الانفجارات الشمسية
    """
    queryset = SolarFlare.objects.all()
    serializer_class = SolarFlareSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """تصفية البيانات حسب المعاملات"""
        queryset = SolarFlare.objects.all()
        
        # تصفية حسب نوع الانفجار
        flare_class = self.request.query_params.get('class', None)
        if flare_class:
            queryset = queryset.filter(flare_class=flare_class.upper())
        
        # تصفية حسب مستوى الخطورة
        risk_level = self.request.query_params.get('risk', None)
        if risk_level:
            queryset = queryset.filter(risk_level__icontains=risk_level)
        
        # تصفية حسب التاريخ
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(begin_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(begin_time__lte=end_date)
        
        # تصفية حسب الأيام الماضية
        days = self.request.query_params.get('days', None)
        if days:
            try:
                days_int = int(days)
                start_date = timezone.now() - timedelta(days=days_int)
                queryset = queryset.filter(begin_time__gte=start_date)
            except ValueError:
                pass
        
        return queryset.order_by('-begin_time')
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """الحصول على آخر الانفجارات"""
        limit = int(request.query_params.get('limit', 10))
        recent_flares = self.get_queryset()[:limit]
        serializer = self.get_serializer(recent_flares, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """تصنيف الانفجارات حسب النوع"""
        flares_by_class = {}
        for flare_class in ['A', 'B', 'C', 'M', 'X']:
            flares = self.get_queryset().filter(flare_class=flare_class)
            flares_by_class[flare_class] = {
                'count': flares.count(),
                'flares': SolarFlareSerializer(flares[:5], many=True).data
            }
        
        return Response(flares_by_class)
    
    @action(detail=False, methods=['get'])
    def strongest(self, request):
        """الحصول على أقوى انفجار"""
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        strongest = self.get_queryset().filter(
            begin_time__gte=start_date
        ).order_by('-intensity').first()
        
        if strongest:
            serializer = self.get_serializer(strongest)
            return Response(serializer.data)
        
        return Response(
            {'message': 'No flares found'},
            status=status.HTTP_404_NOT_FOUND
        )


class SpaceWeatherReportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet للتقارير (قراءة فقط)"""
    queryset = SpaceWeatherReport.objects.all()
    serializer_class = SpaceWeatherReportSerializer
    pagination_class = StandardResultsSetPagination
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """الحصول على آخر تقرير"""
        latest_report = self.get_queryset().first()
        if latest_report:
            serializer = self.get_serializer(latest_report)
            return Response(serializer.data)
        
        return Response(
            {'message': 'No reports available'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def fetch_nasa_data(request):
    """جلب البيانات من NASA وحفظها"""
    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)
    
    service = NASASpaceWeatherService()
    
    # جلب البيانات من NASA
    flares_data = service.fetch_solar_flares(start_date, end_date)
    
    # حفظ في قاعدة البيانات
    saved_flares = service.save_flares_to_db(flares_data)
    
    # توليد تقرير
    report = service.generate_report()
    
    return Response({
        'success': True,
        'message': f'تم جلب وحفظ {len(saved_flares)} انفجار شمسي',
        'flares_count': len(saved_flares),
        'report': SpaceWeatherReportSerializer(report).data
    })


@api_view(['GET'])
def statistics(request):
    """إحصائيات شاملة"""
    days = int(request.query_params.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    flares = SolarFlare.objects.filter(begin_time__gte=start_date)
    
    # إحصائيات حسب النوع
    flares_by_class = {}
    for flare_class in ['A', 'B', 'C', 'M', 'X']:
        flares_by_class[flare_class] = flares.filter(
            flare_class=flare_class
        ).count()
    
    # متوسط الشدة
    avg_intensity = flares.aggregate(Avg('intensity'))['intensity__avg'] or 0
    
    # توزيع الخطورة
    risk_distribution = {
        'LOW': flares.filter(risk_level__icontains='LOW').count(),
        'MEDIUM': flares.filter(risk_level='MEDIUM').count(),
        'HIGH': flares.filter(risk_level='HIGH').count(),
        'EXTREME': flares.filter(risk_level='EXTREME').count(),
    }
    
    # بيانات الخط الزمني
    timeline_data = []
    for flare in flares.order_by('begin_time')[:20]:
        timeline_data.append({
            'date': flare.begin_time.isoformat(),
            'intensity': flare.intensity,
            'class': flare.class_type,
            'risk': flare.risk_level
        })
    
    stats = {
        'total_flares': flares.count(),
        'flares_by_class': flares_by_class,
        'average_intensity': round(avg_intensity, 2),
        'risk_distribution': risk_distribution,
        'timeline_data': timeline_data
    }
    
    serializer = SolarFlareStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
def health_check(request):
    """فحص صحة الـ API"""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'total_flares': SolarFlare.objects.count(),
        'total_reports': SpaceWeatherReport.objects.count()
    })


@api_view(['GET'])
def dashboard_summary(request):
    """ملخص شامل للوحة التحكم"""
    week_ago = timezone.now() - timedelta(days=7)
    recent_flares = SolarFlare.objects.filter(begin_time__gte=week_ago)
    
    strongest = recent_flares.order_by('-intensity').first()
    
    summary = {
        'total_flares': recent_flares.count(),
        'strongest_flare': SolarFlareSerializer(strongest).data if strongest else None,
        'flares_by_class': {
            'A': recent_flares.filter(flare_class='A').count(),
            'B': recent_flares.filter(flare_class='B').count(),
            'C': recent_flares.filter(flare_class='C').count(),
            'M': recent_flares.filter(flare_class='M').count(),
            'X': recent_flares.filter(flare_class='X').count(),
        },
        'high_risk_count': recent_flares.filter(
            Q(risk_level='HIGH') | Q(risk_level='EXTREME')
        ).count(),
        'latest_report': None
    }
    
    latest_report = SpaceWeatherReport.objects.first()
    if latest_report:
        summary['latest_report'] = SpaceWeatherReportSerializer(latest_report).data
    
    return Response(summary)


# ====================================================================
# 🚀 FULL VISUALIZATION DATA - البيانات الكاملة
# ====================================================================

@api_view(['GET'])
def full_visualization_data(request):
    """
    🚀 إرجاع كل البيانات بنفس تفاصيل الكود الأصلي
    GET /api/full-visualization-data/?days=30
    """
    days = int(request.query_params.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    flares = SolarFlare.objects.filter(begin_time__gte=start_date).order_by('-begin_time')
    
    # 1️⃣ معالجة البيانات الأساسية
    flares_data = []
    for flare in flares[:50]:
        impact = predict_impacts_with_flair(flare.class_type)
        flares_data.append({
            'flareID': flare.flare_id,
            'classType': flare.class_type,
            'flareClass': flare.flare_class,
            'intensity': float(flare.intensity),
            'beginTime': flare.begin_time.isoformat(),
            'peakTime': flare.peak_time.isoformat() if flare.peak_time else None,
            'endTime': flare.end_time.isoformat() if flare.end_time else None,
            'riskLevel': impact['risk'],
            'riskColor': impact['color'],
            'impactEffects': impact['effects'],
            'icon': impact['icon']
        })
    
    # 2️⃣ Solar Activity Spectrum
    categories = ['A', 'B', 'C', 'M', 'X']
    solar_spectrum = []
    for cat in categories:
        count = flares.filter(flare_class=cat).count()
        solar_spectrum.append({
            'category': cat,
            'count': count,
            'color': get_category_color(cat),
            'risk_level': get_risk_by_category(cat)
        })
    
    # 3️⃣ Real-Time Impact Radar
    impact_radar = calculate_detailed_impact_radar(flares)
    
    # 4️⃣ Cosmic Risk Meter
    risk_meter = calculate_cosmic_risk_meter(flares)
    
    # 5️⃣ Cosmic Event Timeline
    timeline_events = []
    for flare in flares[:30]:
        timeline_events.append({
            'time': flare.begin_time.isoformat(),
            'intensity': float(flare.intensity),
            'classType': flare.class_type,
            'flareID': flare.flare_id,
            'color': flare.risk_color,
            'size': int(flare.intensity * 50),
            'riskLevel': flare.risk_level
        })
    
    # 6️⃣ Magnetic Storm Simulation
    storm_simulation = generate_magnetic_storm_data()
    
    # 7️⃣ Planetary Impact Zones
    impact_zones = calculate_planetary_impact_zones(flares)
    
    # 8️⃣ Cosmic Activity Summary
    strongest_flare = flares.order_by('-intensity').first()
    activity_summary = {
        'totalEvents': flares.count(),
        'strongestFlare': {
            'flareID': strongest_flare.flare_id,
            'classType': strongest_flare.class_type,
            'intensity': float(strongest_flare.intensity),
            'time': strongest_flare.begin_time.isoformat()
        } if strongest_flare else None,
        'monitoringPeriod': f'Last {days} days',
        'startDate': start_date.isoformat(),
        'endDate': timezone.now().isoformat()
    }
    
    # 9️⃣ Impact Assessment
    impact_assessment = []
    for flare in flares[:10]:
        impact = predict_impacts_with_flair(flare.class_type)
        impact_assessment.append({
            'flareID': flare.flare_id,
            'classType': flare.class_type,
            'icon': impact['icon'],
            'risk': impact['risk'],
            'effects': impact['effects'],
            'color': impact['color']
        })
    
    # 🔟 Recommendations
    recommendations = generate_defense_recommendations(flares)
    
    # 1️⃣1️⃣ Prediction Stats
    prediction_stats = {
        'confidence': 92.7,
        'nextUpdate': '3 hours',
        'dataSource': 'NASA DONKI + AI Analysis',
        'lastSync': timezone.now().isoformat()
    }
    
    # 1️⃣2️⃣ Flares by Class Detailed
    flares_by_class_detailed = {}
    for cat in ['A', 'B', 'C', 'M', 'X']:
        class_flares = flares.filter(flare_class=cat)
        flares_by_class_detailed[cat] = {
            'count': class_flares.count(),
            'percentage': round((class_flares.count() / flares.count() * 100), 1) if flares.count() > 0 else 0,
            'avgIntensity': round(class_flares.aggregate(avg=models.Avg('intensity'))['avg'] or 0, 2),
            'color': get_category_color(cat),
            'riskLevel': get_risk_by_category(cat)
        }
    
    # 1️⃣3️⃣ Risk Distribution
    risk_distribution = {
        'LOW': flares.filter(risk_level__icontains='LOW').exclude(risk_level__icontains='MEDIUM').count(),
        'LOW-MEDIUM': flares.filter(risk_level='LOW-MEDIUM').count(),
        'MEDIUM': flares.filter(risk_level='MEDIUM').count(),
        'HIGH': flares.filter(risk_level='HIGH').count(),
        'EXTREME': flares.filter(risk_level='EXTREME').count()
    }
    
    return Response({
        'flares': flares_data,
        'totalFlares': flares.count(),
        'solarSpectrum': solar_spectrum,
        'impactRadar': impact_radar,
        'riskMeter': risk_meter,
        'timeline': timeline_events,
        'stormSimulation': storm_simulation,
        'impactZones': impact_zones,
        'activitySummary': activity_summary,
        'impactAssessment': impact_assessment,
        'flaresByClass': flares_by_class_detailed,
        'riskDistribution': risk_distribution,
        'recommendations': recommendations,
        'predictionStats': prediction_stats,
        'metadata': {
            'queryDays': days,
            'generatedAt': timezone.now().isoformat(),
            'dataCount': len(flares_data)
        }
    })


# ====================================================================
# Helper Functions
# ====================================================================

def predict_impacts_with_flair(flare_class):
    """Enhanced impact prediction"""
    impact_levels = {
        'A': {'risk': '🌱 LOW', 'color': '#00FF00', 'effects': ['Minimal impact'], 'icon': '🌤️'},
        'B': {'risk': '💚 LOW-MEDIUM', 'color': '#7CFC00', 'effects': ['Radio static'], 'icon': '📻'},
        'C': {'risk': '🟡 MEDIUM', 'color': '#FFD700', 'effects': ['GPS errors', 'Radio blackouts'], 'icon': '📡'},
        'M': {'risk': '🟠 HIGH', 'color': '#FF8C00', 'effects': ['Power grid fluctuations', 'Astronaut risk'], 'icon': '⚡'},
        'X': {'risk': '🔴 EXTREME', 'color': '#FF0000', 'effects': ['Satellite damage', 'Global blackouts'], 'icon': '💥'}
    }
    flare_category = flare_class[0] if flare_class else 'B'
    return impact_levels.get(flare_category, impact_levels['B'])


def calculate_detailed_impact_radar(flares):
    """حساب بيانات الـ Radar"""
    total = flares.count()
    if total == 0:
        return {
            'categories': ['Radio', 'GPS', 'Power', 'Satellites', 'Astronauts'],
            'values': [0, 0, 0, 0, 0]
        }
    
    high_risk = flares.filter(flare_class__in=['M', 'X']).count()
    medium_risk = flares.filter(flare_class='C').count()
    low_risk = flares.filter(flare_class__in=['A', 'B']).count()
    
    radio_impact = min(100, (high_risk * 15 + medium_risk * 8 + low_risk * 2))
    gps_impact = min(100, (high_risk * 12 + medium_risk * 10 + low_risk * 3))
    power_impact = min(100, (high_risk * 18 + medium_risk * 5))
    satellite_impact = min(100, (high_risk * 20 + medium_risk * 7))
    astronaut_impact = min(100, (high_risk * 16 + medium_risk * 4))
    
    return {
        'categories': ['Radio', 'GPS', 'Power', 'Satellites', 'Astronauts'],
        'values': [radio_impact, gps_impact, power_impact, satellite_impact, astronaut_impact],
        'maxValue': 100,
        'currentRisk': 'HIGH' if high_risk > 5 else 'MEDIUM' if medium_risk > 10 else 'LOW'
    }


def calculate_cosmic_risk_meter(flares):
    """حساب مقياس الخطورة"""
    total = flares.count()
    if total == 0:
        return {'percentage': 0, 'level': 'SAFE', 'color': '#00FF00', 'message': 'No active threats'}
    
    risk_level = sum(
        3 if f.flare_class == 'X' else
        2 if f.flare_class == 'M' else
        1 if f.flare_class == 'C' else
        0.5 for f in flares
    )
    max_risk = total * 3
    risk_percent = (risk_level / max_risk) * 100 if max_risk > 0 else 0
    
    if risk_percent < 20:
        level, color, message = 'SAFE', '#00FF00', 'Minimal cosmic activity'
    elif risk_percent < 40:
        level, color, message = 'LOW', '#7CFC00', 'Low-level solar activity detected'
    elif risk_percent < 60:
        level, color, message = 'MEDIUM', '#FFD700', 'Moderate solar storm activity'
    elif risk_percent < 80:
        level, color, message = 'HIGH', '#FF8C00', 'High solar activity - caution advised'
    else:
        level, color, message = 'EXTREME', '#FF0000', 'EXTREME solar storm activity!'
    
    return {
        'percentage': round(risk_percent, 1),
        'level': level,
        'color': color,
        'message': message,
        'threat_level': 'CRITICAL' if risk_percent > 80 else 'WARNING' if risk_percent > 60 else 'NORMAL'
    }


def generate_magnetic_storm_data():
    """توليد بيانات العاصفة المغناطيسية"""
    t = np.linspace(0, 4 * np.pi, 100)
    x = np.sin(t) * (1 + 0.5 * np.sin(5 * t))
    y = np.cos(t) * (1 + 0.5 * np.sin(5 * t))
    
    points = []
    for i in range(len(t)):
        color_value = i / len(t)
        points.append({
            'x': float(x[i]),
            'y': float(y[i]),
            'colorValue': color_value,
            'intensity': float(1 + 0.5 * np.sin(5 * t[i]))
        })
    
    return {'points': points, 'type': 'magnetic_storm', 'intensity': 'ACTIVE'}


def calculate_planetary_impact_zones(flares):
    """حساب مناطق التأثير"""
    zones = []
    earth_data = {'planet': 'Earth', 'radius': 1.0, 'protected': True}
    
    aurora_zones = []
    high_risk_flares = flares.filter(flare_class__in=['M', 'X'])
    
    for flare in high_risk_flares[:5]:
        intensity_factor = flare.intensity / 10
        aurora_zones.append({
            'flareID': flare.flare_id,
            'classType': flare.class_type,
            'latitude_min': 60 + (intensity_factor * 10),
            'latitude_max': 80 + (intensity_factor * 5),
            'coverage': 'Northern Hemisphere',
            'visibility': 'HIGH' if flare.flare_class == 'X' else 'MODERATE'
        })
    
    return {
        'earth': earth_data,
        'auroraZones': aurora_zones,
        'impactLevel': 'HIGH' if high_risk_flares.count() > 3 else 'MODERATE' if high_risk_flares.count() > 0 else 'LOW',
        'affectedRegions': ['Polar Regions', 'High Latitudes'] if high_risk_flares.exists() else []
    }


def generate_defense_recommendations(flares):
    """توليد التوصيات"""
    high_risk = flares.filter(flare_class__in=['M', 'X']).count()
    medium_risk = flares.filter(flare_class='C').count()
    
    recommendations = []
    
    if high_risk > 5:
        recommendations.extend([
            {'icon': '🛰️', 'priority': 'CRITICAL', 'action': 'Stabilize satellite orbits immediately'},
            {'icon': '⚡', 'priority': 'CRITICAL', 'action': 'Reinforce power grid protocols'},
            {'icon': '👨‍🚀', 'priority': 'HIGH', 'action': 'Alert space station crew'},
            {'icon': '📡', 'priority': 'HIGH', 'action': 'Activate backup communication systems'},
            {'icon': '🌌', 'priority': 'MEDIUM', 'action': 'Monitor aurora activity zones'}
        ])
    elif high_risk > 2 or medium_risk > 10:
        recommendations.extend([
            {'icon': '🛰️', 'priority': 'HIGH', 'action': 'Check satellite system status'},
            {'icon': '📡', 'priority': 'MEDIUM', 'action': 'Monitor communication systems'},
            {'icon': '⚡', 'priority': 'MEDIUM', 'action': 'Review power grid stability'}
        ])
    else:
        recommendations.extend([
            {'icon': '✅', 'priority': 'LOW', 'action': 'Continue routine monitoring'},
            {'icon': '🛰️', 'priority': 'LOW', 'action': 'Standard satellite maintenance'}
        ])
    
    return recommendations


def get_category_color(category):
    """الحصول على اللون"""
    colors = {'A': '#00FF00', 'B': '#7CFC00', 'C': '#FFD700', 'M': '#FF8C00', 'X': '#FF0000'}
    return colors.get(category, '#FFFFFF')


def get_risk_by_category(category):
    """الحصول على مستوى الخطر"""
    risks = {'A': 'LOW', 'B': 'LOW-MEDIUM', 'C': 'MEDIUM', 'M': 'HIGH', 'X': 'EXTREME'}
    return risks.get(category, 'UNKNOWN')