# game/urls.py - REPLACE YOUR ENTIRE FILE

from django.urls import path
from .views import (
    AIModelListView, 
    PurchaseView, 
    RecordGameView, 
    SessionDebugView,
    CompleteGameView,
    UserStatsView,
    LeaderboardView,
    UserAIProfileView
)

urlpatterns = [
    path("ai-models/", AIModelListView.as_view(), name="ai-models"),
    path("purchase-ai/", PurchaseView.as_view(), name="purchase-ai"),
    path("record-game/", RecordGameView.as_view(), name="record-game"),
    path('debug-session/', SessionDebugView.as_view(), name='debug-session'),
    
    # NEW ENDPOINTS
    path('complete-game/', CompleteGameView.as_view(), name='complete-game'),
    path('user-stats/', UserStatsView.as_view(), name='user-stats'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    
    path('user-ai-profile/', UserAIProfileView.as_view(), name='user-ai-profile'),
]