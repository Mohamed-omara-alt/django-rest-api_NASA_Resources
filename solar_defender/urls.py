from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlayerViewSet, GameSessionViewSet, SolarFlareViewSet,
    MissionViewSet, LeaderboardViewSet, StatsViewSet, ChartViewSet
)
from .views import UnifiedDataView


router = DefaultRouter()
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'sessions', GameSessionViewSet, basename='session')
router.register(r'flares', SolarFlareViewSet, basename='flare')
router.register(r'missions', MissionViewSet, basename='mission')
router.register(r'leaderboard', LeaderboardViewSet, basename='leaderboard')
router.register(r'stats', StatsViewSet, basename='stats')
router.register(r'charts', ChartViewSet, basename='charts')


urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns = [
    path('unified/', UnifiedDataView.as_view(), name='unified-data'),
]
