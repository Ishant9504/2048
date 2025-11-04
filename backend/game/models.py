from django.db import models
from django.contrib.auth.models import User

class AIModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    agent_class = models.CharField(max_length=50)   # Example: Expectimax agent class 
    tier = models.IntegerField(default=1)
    cost = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    base_params = models.JSONField(default=dict, blank=True)    # Parameters are "fixed" to the specific version of the agent
    tunable_params = models.JSONField(default=dict)

    
    def __str__(self):
        return self.name

class UserUnlocked(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'ai_model')

class Game(models.Model):
    MODE_CHOICES = (
        ('manual', 'Manual'),
        ('ai', 'AI')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True)
    replay_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}-{self.score}"


# NEW MODEL: Store active game state for persistence
class GameState(models.Model):
    """
    Stores the current/active game state for each user.
    This allows game state to persist across WebSocket disconnections,
    logout/login cycles, and server restarts.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='game_state',
        help_text="The user who owns this game state"
    )
    board_state = models.TextField(
        help_text="JSON-serialized 4x4 board array"
    )
    score = models.IntegerField(
        default=0,
        help_text="Current game score"
    )
    is_over = models.BooleanField(
        default=False,
        help_text="Whether the game is over"
    )
    ai_assisted = models.BooleanField(
        default=False, 
        help_text="True if an AI move has been requested for this game"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="When this game state was last modified"
    )
    
    class Meta:
        verbose_name = "Game State"
        verbose_name_plural = "Game States"
    
    def __str__(self):
        return f"{self.user.username} - Score: {self.score} ({'Game Over' if self.is_over else 'In Progress'})"