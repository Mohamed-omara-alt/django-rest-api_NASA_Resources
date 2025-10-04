import requests
from datetime import datetime, timedelta
from django.conf import settings
from .models import SolarFlare

class NASAService:
    def __init__(self):
        self.api_key = getattr(settings, 'NASA_API_KEY', 'DEMO_KEY')
        self.base_url = "https://api.nasa.gov/DONKI/FLR"
    
    def fetch_flares(self, days=7):
        """جلب التوهجات من NASA API"""
        try:
            params = {
                'startDate': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                'endDate': datetime.now().strftime('%Y-%m-%d'),
                'api_key': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._process_nasa_data(data)
            
            return []
        
        except Exception as e:
            print(f"Error fetching NASA data: {e}")
            return []
    
    def _process_nasa_data(self, data):
        """معالجة بيانات NASA"""
        processed = []
        for flare_data in data[:7]:
            class_type = flare_data.get('classType', 'B1.0')
            
            processed.append({
                'flare_id': flare_data.get('flrID', 'Unknown'),
                'class_type': class_type,
                'flare_class': class_type[0] if class_type else 'B',
                'intensity': self._extract_intensity(class_type),
                'begin_time': self._parse_datetime(flare_data.get('beginTime')),
                'is_simulation': False
            })
        
        return processed
    
    def _extract_intensity(self, class_type):
        """استخراج شدة التوهج من النوع"""
        try:
            if len(class_type) > 1:
                return float(class_type[1:])
            return 1.0
        except:
            return 1.0
    
    def _parse_datetime(self, datetime_str):
        """تحويل النص إلى datetime"""
        try:
            if datetime_str:
                # NASA format: 2024-01-15T12:30:00Z
                return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return datetime.now()
        except:
            return datetime.now()
    
    def fetch_and_save_flares(self):
        """جلب وحفظ التوهجات في قاعدة البيانات"""
        flares_data = self.fetch_flares()
        
        if not flares_data:
            # إذا فشل الجلب، استخدم المحاكاة
            return self.create_simulation_flares()
        
        flares = []
        for flare_data in flares_data:
            flare, created = SolarFlare.objects.get_or_create(
                flare_id=flare_data['flare_id'],
                defaults=flare_data
            )
            flares.append(flare)
        
        return flares
    
    def create_simulation_flares(self):
        """إنشاء توهجات محاكاة"""
        simulation_classes = ['B3.2', 'C1.5', 'M2.1', 'B7.8', 'X1.3', 'C5.6', 'M4.2']
        flares = []
        
        for i, class_type in enumerate(simulation_classes):
            flare_data = {
                'flare_id': f'SIMULATION-FLARE-{datetime.now().timestamp()}-{i}',
                'class_type': class_type,
                'flare_class': class_type[0],
                'intensity': float(class_type[1:]) if len(class_type) > 1 else 1.0,
                'begin_time': datetime.now() - timedelta(hours=i * 6),
                'is_simulation': True
            }
            
            flare = SolarFlare.objects.create(**flare_data)
            flares.append(flare)
        
        return flares