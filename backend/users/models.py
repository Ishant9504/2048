# users/models.py - REPLACE ENTIRE FILE

from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    """Extended user profile with points and statistics"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Points system
    points = models.IntegerField(default=100)  # Starting balance
    lifetime_points = models.IntegerField(default=0)  # Total points ever earned
    
    # Game statistics
    games_played = models.IntegerField(default=0)
    high_score = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)  # Sum of all game scores
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Foreign key to the equipped agents of the users
    equipped_ai = models.ForeignKey(
        'game.AIModel', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # User's custom slider settings
    ai_configs = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def average_score(self):
        """Calculate average score across all games"""
        if self.games_played == 0:
            return 0
        return self.total_score // self.games_played
    
    def add_game_score(self, score):
        """Update stats when a game is completed"""
        self.games_played += 1
        self.total_score += score
        if score > self.high_score:
            self.high_score = score
        
        # Award points (1:1 ratio - you can adjust this)
        points_earned = score
        self.points += points_earned
        self.lifetime_points += points_earned
        
        self.save()
        return points_earned