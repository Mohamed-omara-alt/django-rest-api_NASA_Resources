import requests
from datetime import datetime, timedelta
from django.utils import timezone
from .models import SolarFlare, SpaceWeatherReport
import logging

logger = logging.getLogger(__name__)


class NASASpaceWeatherService:
    """خدمة للتعامل مع NASA API"""
    
    def __init__(self):
        self.api_key = 'DEMO_KEY'  # استبدلها بمفتاح حقيقي
        self.base_url = 'https://api.nasa.gov/DONKI/FLR'
    
    def fetch_solar_flares(self, start_date=None, end_date=None):
        """جلب الانفجارات الشمسية من NASA"""
        
        if not start_date:
            start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = timezone.now().strftime('%Y-%m-%d')
        
        params = {
            'startDate': start_date,
            'endDate': end_date,
            'api_key': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"NASA API returned status {response.status_code}")
                return self.generate_sample_data()
                
        except Exception as e:
            logger.error(f"Error fetching NASA data: {e}")
            return self.generate_sample_data()
    
    def generate_sample_data(self):
        """توليد بيانات تجريبية"""
        
        sample_flares = []
        classes = ['C2.5', 'M1.0', 'B7.2', 'X1.5', 'C8.1']
        
        for i in range(5):
            sample_flares.append({
                'flareID': f'SOLAR-BLAST-{i+1}',
                'classType': classes[i],
                'beginTime': (timezone.now() - timedelta(hours=i*6)).isoformat(),
                'peakTime': (timezone.now() - timedelta(hours=i*6, minutes=30)).isoformat(),
                'endTime': (timezone.now() - timedelta(hours=i*6-1)).isoformat(),
            })
        
        return sample_flares
    
    def calculate_impact(self, class_type):
        """حساب التأثير بناءً على نوع الانفجار"""
        
        flare_class = class_type[0] if class_type else 'B'
        
        impact_map = {
            'A': {
                'risk': 'LOW',
                'color': '#00FF00',
                'effects': ['Minimal impact']
            },
            'B': {
                'risk': 'LOW-MEDIUM',
                'color': '#7CFC00',
                'effects': ['Radio static']
            },
            'C': {
                'risk': 'MEDIUM',
                'color': '#FFD700',
                'effects': ['GPS errors', 'Radio blackouts']
            },
            'M': {
                'risk': 'HIGH',
                'color': '#FF8C00',
                'effects': ['Power grid fluctuations', 'Astronaut risk']
            },
            'X': {
                'risk': 'EXTREME',
                'color': '#FF0000',
                'effects': ['Satellite damage', 'Global blackouts']
            }
        }
        
        return impact_map.get(flare_class, impact_map['B'])
    
    def save_flares_to_db(self, flares_data):
        """حفظ الانفجارات في قاعدة البيانات"""
        
        saved_flares = []
        
        for flare in flares_data:
            class_type = flare.get('classType', 'B1.0')
            flare_class = class_type[0]
            intensity = float(class_type[1:]) if len(class_type) > 1 else 1.0
            
            impact = self.calculate_impact(class_type)
            
            flare_obj, created = SolarFlare.objects.update_or_create(
                flare_id=flare.get('flareID', f'UNKNOWN-{timezone.now().timestamp()}'),
                defaults={
                    'class_type': class_type,
                    'flare_class': flare_class,
                    'intensity': intensity,
                    'begin_time': flare.get('beginTime'),
                    'peak_time': flare.get('peakTime'),
                    'end_time': flare.get('endTime'),
                    'risk_level': impact['risk'],
                    'risk_color': impact['color'],
                    'impact_effects': impact['effects'],
                }
            )
            
            saved_flares.append(flare_obj)
        
        return saved_flares
    
    def generate_report(self):
        """توليد تقرير شامل"""
        
        recent_flares = SolarFlare.objects.filter(
            begin_time__gte=timezone.now() - timedelta(days=7)
        )
        
        total_flares = recent_flares.count()
        
        if total_flares > 0:
            strongest = recent_flares.order_by('-intensity').first()
            
            risk_sum = sum(
                3 if f.flare_class == 'X' else
                2 if f.flare_class == 'M' else 1
                for f in recent_flares
            )
            risk_percentage = (risk_sum / (total_flares * 3)) * 100
        else:
            strongest = None
            risk_percentage = 0.0
        
        report = SpaceWeatherReport.objects.create(
            total_flares=total_flares,
            strongest_flare=strongest,
            risk_percentage=risk_percentage
        )
        
        return report