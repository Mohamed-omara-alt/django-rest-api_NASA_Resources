from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    total_score = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class GameSession(models.Model):
    RANK_CHOICES = [
        ('BEGINNER', 'Space Beginner'),
        ('CADET', 'Space Cadet'),
        ('COMMANDER', 'Space Commander'),
        ('MASTER', 'Solar Defender Master'),
    ]
    
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='sessions')
    score = models.IntegerField(default=0)
    earth_health = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    power_grid = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    satellites = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    communications = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def calculate_rank(self):
        if self.score >= 80:
            return 'MASTER'
        elif self.score >= 50:
            return 'COMMANDER'
        elif self.score >= 25:
            return 'CADET'
        else:
            return 'BEGINNER'
    
    def __str__(self):
        return f"{self.player.name} - Session {self.id}"

class SolarFlare(models.Model):
    FLARE_CLASSES = [
        ('A', 'A-Class'),
        ('B', 'B-Class'),
        ('C', 'C-Class'),
        ('M', 'M-Class'),
        ('X', 'X-Class'),
    ]
    
    flare_id = models.CharField(max_length=100)
    class_type = models.CharField(max_length=10)
    flare_class = models.CharField(max_length=1, choices=FLARE_CLASSES)
    intensity = models.FloatField()
    begin_time = models.DateTimeField()
    is_simulation = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-begin_time']
    
    def calculate_impact(self):
        impacts = {
            'A': {'power': 0, 'satellites': 0, 'comm': 0, 'message': "Minimal impact"},
            'B': {'power': 5, 'satellites': 3, 'comm': 8, 'message': "Minor radio interference"},
            'C': {'power': 15, 'satellites': 10, 'comm': 20, 'message': "GPS and radio disruption"},
            'M': {'power': 30, 'satellites': 25, 'comm': 40, 'message': "Potential power grid fluctuations"},
            'X': {'power': 50, 'satellites': 40, 'comm': 60, 'message': "Critical infrastructure at risk!"}
        }
        return impacts.get(self.flare_class, impacts['B'])
    
    def __str__(self):
        return f"{self.class_type} - {self.begin_time}"

class Mission(models.Model):
    DEFENSE_STRATEGIES = [
        (1, 'Satellite Shields'),
        (2, 'Grid Protection'),
        (3, 'Communications Boost'),
        (4, 'Integrated Defense'),
    ]
    
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='missions')
    flare = models.ForeignKey(SolarFlare, on_delete=models.CASCADE)
    defense_choice = models.IntegerField(choices=DEFENSE_STRATEGIES)
    success = models.BooleanField(default=True)
    phase_number = models.IntegerField()
    power_grid_after = models.IntegerField()
    satellites_after = models.IntegerField()
    communications_after = models.IntegerField()
    earth_health_after = models.IntegerField()
    points_earned = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['phase_number']
    
    def __str__(self):
        return f"Mission {self.phase_number} - {self.session.player.name}"

class Leaderboard(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    rank_position = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['rank_position']
        unique_together = ['player', 'session']
    
    def __str__(self):
        return f"{self.rank_position}. {self.player.name} - {self.session.score}"