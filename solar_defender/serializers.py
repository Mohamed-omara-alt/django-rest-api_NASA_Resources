from rest_framework import serializers
from .models import Player, GameSession, SolarFlare, Mission, Leaderboard
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class PlayerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Player
        fields = ['id', 'name', 'total_score', 'games_played', 'created_at', 'user']
        read_only_fields = ['total_score', 'games_played', 'created_at']

class PlayerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['name']

class SolarFlareSerializer(serializers.ModelSerializer):
    impact = serializers.SerializerMethodField()
    
    class Meta:
        model = SolarFlare
        fields = [
            'id', 'flare_id', 'class_type', 'flare_class', 
            'intensity', 'begin_time', 'is_simulation', 'impact'
        ]
    
    def get_impact(self, obj):
        return obj.calculate_impact()

class MissionSerializer(serializers.ModelSerializer):
    flare = SolarFlareSerializer(read_only=True)
    defense_strategy_name = serializers.CharField(source='get_defense_choice_display', read_only=True)
    
    class Meta:
        model = Mission
        fields = [
            'id', 'flare', 'defense_choice', 'defense_strategy_name',
            'success', 'phase_number', 'power_grid_after', 
            'satellites_after', 'communications_after', 
            'earth_health_after', 'points_earned', 'created_at'
        ]

class MissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mission
        fields = [
            'flare', 'defense_choice', 'phase_number',
            'power_grid_after', 'satellites_after', 
            'communications_after', 'earth_health_after', 'points_earned'
        ]

class GameSessionSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)
    missions = MissionSerializer(many=True, read_only=True)
    rank_name = serializers.CharField(source='get_rank_display', read_only=True)
    missions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GameSession
        fields = [
            'id', 'player', 'score', 'earth_health', 
            'power_grid', 'satellites', 'communications',
            'rank', 'rank_name', 'completed', 'created_at', 
            'completed_at', 'missions', 'missions_count'
        ]
        read_only_fields = ['created_at', 'rank']
    
    def get_missions_count(self, obj):
        return obj.missions.count()

class GameSessionCreateSerializer(serializers.ModelSerializer):
    player_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = GameSession
        fields = ['player_id']
    
    def create(self, validated_data):
        player = Player.objects.get(id=validated_data['player_id'])
        return GameSession.objects.create(player=player)

class GameSessionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameSession
        fields = [
            'score', 'earth_health', 'power_grid', 
            'satellites', 'communications', 'completed'
        ]

class LeaderboardSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.name', read_only=True)
    score = serializers.IntegerField(source='session.score', read_only=True)
    rank_display = serializers.CharField(source='session.get_rank_display', read_only=True)
    
    class Meta:
        model = Leaderboard
        fields = [
            'id', 'rank_position', 'player_name', 
            'score', 'rank_display', 'updated_at'
        ]

class GameStatsSerializer(serializers.Serializer):
    total_games = serializers.IntegerField()
    total_players = serializers.IntegerField()
    average_score = serializers.FloatField()
    highest_score = serializers.IntegerField()
    total_missions = serializers.IntegerField()
    flares_by_class = serializers.DictField()

class PlayerStatsSerializer(serializers.Serializer):
    player = PlayerSerializer()
    total_games = serializers.IntegerField()
    average_score = serializers.FloatField()
    best_score = serializers.IntegerField()
    total_missions = serializers.IntegerField()
    defense_strategy_usage = serializers.DictField()
    success_rate = serializers.FloatField()

class ChartResponseSerializer(serializers.Serializer):
    """Serializer لاستجابة الرسوم البيانية"""
    session_id = serializers.IntegerField()
    player_name = serializers.CharField()
    score = serializers.IntegerField()
    rank = serializers.CharField()
    rank_name = serializers.CharField()
    charts = serializers.DictField(
        child=serializers.CharField(),
        help_text="Base64 encoded images"
    )

class SingleChartResponseSerializer(serializers.Serializer):
    """Serializer لرسم بياني واحد"""
    session_id = serializers.IntegerField()
    chart_type = serializers.CharField()
    chart = serializers.CharField(help_text="Base64 encoded image")