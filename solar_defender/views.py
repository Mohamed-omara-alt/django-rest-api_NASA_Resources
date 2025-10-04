from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import HttpResponse
from django.db.models import Avg, Count, Max, Q
from .visualization_service import VisualizationService
from django.utils import timezone
from datetime import timedelta

from .models import Player, GameSession, SolarFlare, Mission, Leaderboard
from .serializers import (
    PlayerSerializer, PlayerCreateSerializer, GameSessionSerializer,
    GameSessionCreateSerializer, GameSessionUpdateSerializer,
    SolarFlareSerializer, MissionSerializer, MissionCreateSerializer,
    LeaderboardSerializer, GameStatsSerializer, PlayerStatsSerializer
)
from .services import NASAService

class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PlayerCreateSerializer
        return PlayerSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'list']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """احصائيات اللاعب"""
        player = self.get_object()
        sessions = player.sessions.filter(completed=True)
        
        if not sessions.exists():
            return Response({
                'player': PlayerSerializer(player).data,
                'total_games': 0,
                'average_score': 0,
                'best_score': 0,
                'total_missions': 0,
                'defense_strategy_usage': {},
                'success_rate': 0
            })
        
        missions = Mission.objects.filter(session__player=player)
        
        # احصائيات استراتيجيات الدفاع
        defense_usage = missions.values('defense_choice').annotate(
            count=Count('id')
        ).order_by('defense_choice')
        
        defense_strategy_usage = {
            str(item['defense_choice']): item['count'] 
            for item in defense_usage
        }
        
        # معدل النجاح
        total_missions = missions.count()
        successful_missions = missions.filter(success=True).count()
        success_rate = (successful_missions / total_missions * 100) if total_missions > 0 else 0
        
        stats_data = {
            'player': PlayerSerializer(player).data,
            'total_games': sessions.count(),
            'average_score': sessions.aggregate(Avg('score'))['score__avg'] or 0,
            'best_score': sessions.aggregate(Max('score'))['score__max'] or 0,
            'total_missions': total_missions,
            'defense_strategy_usage': defense_strategy_usage,
            'success_rate': round(success_rate, 2)
        }
        
        return Response(stats_data)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """سجل جلسات اللاعب"""
        player = self.get_object()
        sessions = player.sessions.filter(completed=True).order_by('-created_at')
        
        page = self.paginate_queryset(sessions)
        if page is not None:
            serializer = GameSessionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = GameSessionSerializer(sessions, many=True)
        return Response(serializer.data)

class GameSessionViewSet(viewsets.ModelViewSet):
    queryset = GameSession.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return GameSessionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return GameSessionUpdateSerializer
        return GameSessionSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """إنهاء الجلسة وحساب الرتبة"""
        session = self.get_object()
        
        if session.completed:
            return Response(
                {'error': 'Session already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # حساب الرتبة
        session.rank = session.calculate_rank()
        session.completed = True
        session.completed_at = timezone.now()
        session.save()
        
        # تحديث إحصائيات اللاعب
        player = session.player
        player.total_score += session.score
        player.games_played += 1
        player.save()
        
        # تحديث لوحة المتصدرين
        self._update_leaderboard(session)
        
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    def _update_leaderboard(self, session):
        """تحديث لوحة المتصدرين"""
        # الحصول على أفضل 100 جلسة
        top_sessions = GameSession.objects.filter(
            completed=True
        ).order_by('-score')[:100]
        
        # حذف الإدخالات القديمة
        Leaderboard.objects.all().delete()
        
        # إنشاء إدخالات جديدة
        leaderboard_entries = []
        for position, session in enumerate(top_sessions, start=1):
            leaderboard_entries.append(
                Leaderboard(
                    player=session.player,
                    session=session,
                    rank_position=position
                )
            )
        
        Leaderboard.objects.bulk_create(leaderboard_entries)

class SolarFlareViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SolarFlare.objects.all()
    serializer_class = SolarFlareSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def fetch_nasa_data(self, request):
        """جلب بيانات جديدة من NASA"""
        nasa_service = NASAService()
        flares = nasa_service.fetch_and_save_flares()
        
        serializer = self.get_serializer(flares, many=True)
        return Response({
            'count': len(flares),
            'flares': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """الحصول على أحدث 7 توهجات"""
        days = int(request.query_params.get('days', 7))
        
        recent_flares = SolarFlare.objects.filter(
            begin_time__gte=timezone.now() - timedelta(days=days)
        ).order_by('-begin_time')[:7]
        
        # إذا لم يكن هناك توهجات حقيقية، استخدم المحاكاة
        if not recent_flares.exists():
            nasa_service = NASAService()
            recent_flares = nasa_service.create_simulation_flares()
        
        serializer = self.get_serializer(recent_flares, many=True)
        return Response(serializer.data)

class MissionViewSet(viewsets.ModelViewSet):
    queryset = Mission.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MissionCreateSerializer
        return MissionSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """إنشاء مهمة جديدة"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # حساب النجاح بناءً على الاستراتيجية
        mission = serializer.save(success=True)
        
        # تحديث جلسة اللعب
        session = mission.session
        session.score = request.data.get('session_score', session.score)
        session.power_grid = mission.power_grid_after
        session.satellites = mission.satellites_after
        session.communications = mission.communications_after
        session.earth_health = mission.earth_health_after
        session.save()
        
        return Response(
            MissionSerializer(mission).data,
            status=status.HTTP_201_CREATED
        )

class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def top(self, request):
        """أفضل 10 لاعبين"""
        top_players = self.queryset[:10]
        serializer = self.get_serializer(top_players, many=True)
        return Response(serializer.data)

class StatsViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def global_stats(self, request):
        """إحصائيات عامة للعبة"""
        total_games = GameSession.objects.filter(completed=True).count()
        total_players = Player.objects.count()
        avg_score = GameSession.objects.filter(
            completed=True
        ).aggregate(Avg('score'))['score__avg'] or 0
        highest_score = GameSession.objects.filter(
            completed=True
        ).aggregate(Max('score'))['score__max'] or 0
        total_missions = Mission.objects.count()
        
        # توزيع التوهجات حسب الفئة
        flares_by_class = SolarFlare.objects.values('flare_class').annotate(
            count=Count('id')
        ).order_by('flare_class')
        
        flares_distribution = {
            item['flare_class']: item['count'] 
            for item in flares_by_class
        }
        
        stats = {
            'total_games': total_games,
            'total_players': total_players,
            'average_score': round(avg_score, 2),
            'highest_score': highest_score,
            'total_missions': total_missions,
            'flares_by_class': flares_distribution
        }
        
        return Response(stats)
    

class ChartViewSet(viewsets.ViewSet):
    """ViewSet لتوليد الرسوم البيانية"""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'], url_path='session/(?P<session_id>[^/.]+)')
    def session_charts(self, request, session_id=None):
        """
        توليد جميع الرسوم البيانية لجلسة معينة
        
        GET /api_game/charts/session/{session_id}/
        
        Returns:
            {
                "session_id": 1,
                "player_name": "Ahmed",
                "score": 95,
                "rank": "MASTER",
                "charts": {
                    "flare_distribution": "data:image/png;base64,...",
                    "intensity_timeline": "data:image/png;base64,...",
                    "systems_status": "data:image/png;base64,...",
                    "impact_comparison": "data:image/png;base64,...",
                    "performance_gauge": "data:image/png;base64,...",
                    "earth_impact_map": "data:image/png;base64,...",
                    "mission_log": "data:image/png;base64,..."
                }
            }
        """
        try:
            session = GameSession.objects.get(id=session_id)
            
            if not session.completed:
                return Response(
                    {"error": "Session must be completed before generating charts"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # توليد الرسوم البيانية
            viz_service = VisualizationService(session)
            charts = viz_service.generate_all_charts()
            
            return Response({
                "session_id": session.id,
                "player_name": session.player.name,
                "score": session.score,
                "rank": session.rank,
                "rank_name": session.get_rank_display(),
                "charts": charts
            })
            
        except GameSession.DoesNotExist:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='session/(?P<session_id>[^/.]+)/(?P<chart_type>[^/.]+)')
    def single_chart(self, request, session_id=None, chart_type=None):
        """
        توليد رسم بياني واحد محدد
        
        GET /api_game/charts/session/{session_id}/{chart_type}/
        
        chart_types:
            - flare_distribution
            - intensity_timeline
            - systems_status
            - impact_comparison
            - performance_gauge
            - earth_impact_map
            - mission_log
        """
        try:
            session = GameSession.objects.get(id=session_id)
            
            if not session.completed:
                return Response(
                    {"error": "Session must be completed before generating charts"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            viz_service = VisualizationService(session)
            
            # استدعاء الدالة المناسبة بناءً على نوع الرسم
            chart_methods = {
                'flare_distribution': viz_service.create_flare_distribution,
                'intensity_timeline': viz_service.create_intensity_timeline,
                'systems_status': viz_service.create_systems_status,
                'impact_comparison': viz_service.create_impact_comparison,
                'performance_gauge': viz_service.create_performance_gauge,
                'earth_impact_map': viz_service.create_earth_impact_map,
                'mission_log': viz_service.create_mission_log
            }
            
            if chart_type not in chart_methods:
                return Response(
                    {"error": f"Invalid chart type. Available: {', '.join(chart_methods.keys())}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            chart_base64 = chart_methods[chart_type]()
            
            return Response({
                "session_id": session.id,
                "chart_type": chart_type,
                "chart": chart_base64
            })
            
        except GameSession.DoesNotExist:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """
        توليد تقرير كامل مع جميع الرسوم البيانية
        
        POST /api_game/charts/generate_report/
        Body: {"session_id": 1}
        
        Returns: PDF file or ZIP with images
        """
        session_id = request.data.get('session_id')
        
        if not session_id:
            return Response(
                {"error": "session_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = GameSession.objects.get(id=session_id)
            
            if not session.completed:
                return Response(
                    {"error": "Session must be completed"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            viz_service = VisualizationService(session)
            charts = viz_service.generate_all_charts()
            
            # يمكنك إنشاء PDF أو ZIP هنا
            # للتبسيط، سنرجع جميع الرسوم كـ JSON
            
            return Response({
                "session_id": session.id,
                "player": session.player.name,
                "score": session.score,
                "rank": session.get_rank_display(),
                "generated_at": session.completed_at,
                "charts": charts,
                "report_url": f"/api_game/charts/session/{session_id}/"
            })
            
        except GameSession.DoesNotExist:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        


from rest_framework.views import APIView
from .serializers import (
    PlayerSerializer, GameSessionSerializer, MissionSerializer, SolarFlareSerializer
)

class UnifiedDataView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        players = PlayerSerializer(Player.objects.all(), many=True).data
        sessions = GameSessionSerializer(GameSession.objects.all(), many=True).data
        missions = MissionSerializer(Mission.objects.all(), many=True).data
        flares = SolarFlareSerializer(SolarFlare.objects.all(), many=True).data
        leaderboard = LeaderboardSerializer(Leaderboard.objects.all(), many=True).data

        # إحصائيات عامة
        stats_view = StatsViewSet()
        stats_response = stats_view.global_stats(request)
        stats = stats_response.data

        # لو عايز آخر Session يولّد Charts
        charts = {}
        last_session = GameSession.objects.filter(completed=True).last()
        if last_session:
            viz_service = VisualizationService(last_session)
            charts = viz_service.generate_all_charts()  # بيرجع صور Base64

        return Response({
            "players": players,
            "sessions": sessions,
            "missions": missions,
            "flares": flares,
            "leaderboard": leaderboard,
            "stats": stats,
            "charts": charts
        })
