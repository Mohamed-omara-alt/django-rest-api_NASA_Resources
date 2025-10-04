from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

#نRouter للـ ViewSets
router = DefaultRouter()
router.register(r'flares', views.SolarFlareViewSet, basename='flare')
router.register(r'reports', views.SpaceWeatherReportViewSet, basename='report')

urlpatterns = [
    # ViewSets URLs (تلقائية)
    path('', include(router.urls)),
    
    # Custom Endpoints
    path('fetch-nasa-data/', views.fetch_nasa_data, name='fetch-nasa-data'),
    path('full-visualization-data/', views.full_visualization_data, name='full-visualization-data'),
    path('statistics/', views.statistics, name='statistics'),
    path('health/', views.health_check, name='health-check'),
    path('dashboard-summary/', views.dashboard_summary, name='dashboard-summary'),
]


