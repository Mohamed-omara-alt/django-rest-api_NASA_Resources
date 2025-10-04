# solar_defender/management/commands/update_leaderboard.py

from django.core.management.base import BaseCommand
from solar_defender.models import GameSession, Leaderboard

class Command(BaseCommand):
    help = 'Update leaderboard rankings'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Updating leaderboard...'))
        
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
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated leaderboard with {len(leaderboard_entries)} entries')
        )