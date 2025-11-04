from rest_framework import serializers
from .models import AIModel, UserUnlocked, Game

class AISerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = [
            'id', 
            'name', 
            'agent_class', 
            'tier', 
            'cost', 
            'description',
            'base_params',    
            'tunable_params'  
        ]

class UserUnlockedSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserUnlocked
        fields = ['user', 'ai_model', 'purchased_at']


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ['user', 'score', 'mode', 'ai_model', 'replay_json', 'created_at']
        