from django.contrib import admin
from .models import Player, GameSession, SolarFlare, Mission, Leaderboard

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'total_score', 'games_played', 'created_at']
    search_fields = ['name', 'user__username']
    list_filter = ['created_at']
    readonly_fields = ['created_at']

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'player', 'score', 'earth_health', 
        'rank', 'completed', 'created_at'
    ]
    list_filter = ['completed', 'rank', 'created_at']
    search_fields = ['player__name']
    readonly_fields = ['created_at', 'completed_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('player', 'score', 'rank', 'completed')
        }),
        ('Earth Systems', {
            'fields': ('earth_health', 'power_grid', 'satellites', 'communications')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(SolarFlare)
class SolarFlareAdmin(admin.ModelAdmin):
    list_display = [
        'flare_id', 'class_type', 'flare_class', 
        'intensity', 'begin_time', 'is_simulation'
    ]
    list_filter = ['flare_class', 'is_simulation', 'begin_time']
    search_fields = ['flare_id', 'class_type']
    readonly_fields = ['created_at']
    date_hierarchy = 'begin_time'

@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'session', 'phase_number', 'flare', 
        'defense_choice', 'success', 'points_earned'
    ]
    list_filter = ['success', 'defense_choice', 'created_at']
    search_fields = ['session__player__name', 'flare__flare_id']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Mission Info', {
            'fields': ('session', 'flare', 'phase_number', 'defense_choice', 'success')
        }),
        ('Results', {
            'fields': (
                'power_grid_after', 'satellites_after', 
                'communications_after', 'earth_health_after', 'points_earned'
            )
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['rank_position', 'player', 'session', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['player__name']
    readonly_fields = ['updated_at']
    ordering = ['rank_position']