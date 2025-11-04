from django.contrib import admin
from .models import AIModel, UserUnlocked, Game, GameState

# This is a simple way to register the models
admin.site.register(AIModel)
admin.site.register(UserUnlocked)
admin.site.register(Game)
admin.site.register(GameState)