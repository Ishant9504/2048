from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction # Import for atomic transactions
from django.shortcuts import get_object_or_404 # Efficient object retrieval
from .models import AIModel, UserUnlocked, Game # Assuming these models are defined
from .serializers import AISerializer, UserUnlockedSerializer, GameSerializer # Assuming these serializers are defined
from django.contrib.auth import logout
from django.conf import settings
from django.http import JsonResponse

# --- CSRF DIAGNOSTIC IMPORTS ---
from django.views.decorators.csrf import csrf_exempt 
from django.utils.decorators import method_decorator
# -------------------------------

# ----------------------------------------------------------------------
# Session Debug View
# ----------------------------------------------------------------------
class SessionDebugView(APIView):
    """Debug view to check session functionality"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Force session creation if it doesn't exist
        if not request.session.session_key:
            request.session.create()
            request.session.save()
        
        # Get session data for debugging
        session_data = {}
        for key in request.session.keys():
            # Don't include sensitive data like passwords
            if key not in ['password']:
                session_data[key] = request.session[key]
        
        # Check if _auth_user_id is in session which indicates Django auth
        auth_user_id = None
        if '_auth_user_id' in request.session:
            auth_user_id = request.session['_auth_user_id']
        
        # Return detailed session info
        return JsonResponse({
            'session_key': request.session.session_key,
            'is_authenticated': request.user.is_authenticated,
            'username': request.user.username if request.user.is_authenticated else None,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'auth_user_id_in_session': auth_user_id,
            'csrf_token': request.META.get('CSRF_COOKIE', None),
            'session_keys': list(request.session.keys()),
            'session_data': session_data,
            'cookies': {k: request.COOKIES[k] for k in request.COOKIES 
                       if k not in ['password', 'csrftoken']}
        })



# ----------------------------------------------------------------------
# 1. AIModelListView 
# ----------------------------------------------------------------------

class AIModelListView(generics.ListAPIView):
    """
    List all available AI models.
    """
    queryset = AIModel.objects.all()
    serializer_class = AISerializer
    permission_classes = [permissions.AllowAny]

# ----------------------------------------------------------------------
# 2. PurchaseView (CRITICAL REVISIONS for security and atomicity + CSRF Diagnostic)
# ----------------------------------------------------------------------

# NOTE: This decorator is TEMPORARILY applied for diagnosis. 

class PurchaseView(APIView):
    """
    Handles the purchase and unlocking of an AI model using user points.
    Uses atomic transaction for data integrity.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic # Ensures all DB operations succeed or fail together
    def post(self, request):
        user = request.user
        ai_id = request.data.get('ai_model_id')

        # --- DIAGNOSTIC LOG (Server-Side) ---
        print(f">>> PURCHASE ATTEMPT BY USER: {user.username if not user.is_anonymous else 'Anonymous'} (Is Anon: {user.is_anonymous})") 
        # -------------------------------------

        # 1. Input Validation and Retrieval
        if not ai_id:
            return Response({"error": "AI model ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use get_object_or_404 for cleaner error handling
        ai_model = get_object_or_404(AIModel, id=ai_id)

        # 2. Ensure Profile exists and lock it for update, then check points first
        from users.models import Profile

        try:
            # Lock the profile row to prevent race conditions on concurrent purchases
            profile = Profile.objects.select_for_update().get(user=user)
            created = False
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=user)
            created = True

        if created:
            print(f">>> Created missing profile for user {user.username}. Points set to default {profile.points}.")

        # Check insufficient points BEFORE creating or checking unlock record
        if profile.points < ai_model.cost:
            return Response({"error": "Not enough points."}, status=status.HTTP_402_PAYMENT_REQUIRED)

        # 3. Check if already unlocked (improves UX)
        if UserUnlocked.objects.filter(user=user, ai_model=ai_model).exists():
            return Response({"error": f"You have already unlocked {ai_model.name}."}, status=status.HTTP_409_CONFLICT)

        
        # 4. Atomic Update and Creation
        
        # Deduct points
        profile.points -= ai_model.cost
        profile.save()
        
        # Create unlock record
        UserUnlocked.objects.create(user=user, ai_model=ai_model)
        
        return Response({"success": f"Unlocked {ai_model.name} for {ai_model.cost} points."}, 
                        status=status.HTTP_200_OK)

# ----------------------------------------------------------------------
# 3. RecordGameView
# ----------------------------------------------------------------------

class RecordGameView(APIView):
    """
    Records a completed game score and updates user points.
    Uses atomic transaction to ensure score is recorded and points are added together.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = GameSerializer(data=request.data)
        
        if serializer.is_valid():
            # Save the Game instance, linking it to the authenticated user
            game_instance = serializer.save(user=request.user)
            
            # Use the saved instance's score for safety and clarity
            score = game_instance.score 
            
            # Add points (assuming user.profile exists and has a 'points' field)
            try:
                profile = request.user.profile
                profile.points += score
                profile.save()
            except AttributeError:
                 # Should be handled defensively if profile is not guaranteed
                 print(f">>> WARNING: Failed to update points for user {request.user.username}. Profile missing.")

            return Response({"message": f"Game recorded. Added {score} points.", 
                             "game": serializer.data}, 
                            status=status.HTTP_201_CREATED)
                            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ----------------------------------------------------------------------
# 4. LeaderboardView (UPDATED for Profile-based stats)
# ----------------------------------------------------------------------

class LeaderboardView(APIView):
    """Get top players by high score or total points."""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        from users.models import Profile
        
        sort_by = request.query_params.get('sort_by', 'high_score')
        limit = request.query_params.get('limit', 10)
        
        try:
            limit = min(int(limit), 50)
        except ValueError:
            limit = 10
        
        if sort_by == 'points':
            # Leaderboard by total points
            top_profiles = Profile.objects.select_related('user').order_by('-points')[:limit]
            leaderboard = [
                {
                    'rank': idx + 1,
                    'user': profile.user.username,
                    'points': profile.points,
                    'high_score': profile.high_score,
                    'games_played': profile.games_played
                }
                for idx, profile in enumerate(top_profiles)
            ]
        else:
            # Leaderboard by high score (default)
            top_profiles = Profile.objects.select_related('user').order_by('-high_score')[:limit]
            leaderboard = [
                {
                    'rank': idx + 1,
                    'user': profile.user.username,
                    'high_score': profile.high_score,
                    'score': profile.high_score,  # For compatibility with old frontend
                    'points': profile.points,
                    'games_played': profile.games_played
                }
                for idx, profile in enumerate(top_profiles)
            ]
        
        return Response({
            "success": True,
            "data": leaderboard
        }, status=status.HTTP_200_OK)
# ----------------------------------------------------------------------
# 5. LogoutView (CRITICAL FIX FOR PERSISTENT SESSION TOKEN)
# ----------------------------------------------------------------------

class LogoutView(APIView):
    """
    Invalidates the server-side session and explicitly deletes 
    client-side session and CSRF cookies for proper logout in SPAs.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # 1. Invalidate the server-side session (clears data from DB/cache)
        logout(request)
        
        # 2. Prepare the success response
        response = Response(
            {"message": "Successfully logged out. Session terminated."}, 
            status=status.HTTP_200_OK
        )

        # 3. *** CRITICAL FIX: Delete Cookies on the Client-Side ***
        # The key is to match the parameters (path, domain, samesite) 
        # used when the cookie was originally SET by Django.

        # Delete the main session cookie (e.g., 'sessionid')
        response.delete_cookie(
            settings.SESSION_COOKIE_NAME, 
            path=settings.SESSION_COOKIE_PATH, 
            samesite=settings.SESSION_COOKIE_SAMESITE # Typically 'Lax' or 'None'
        )
        
        # Delete the CSRF token cookie (e.g., 'csrftoken')
        # Deleting the CSRF cookie ensures new requests require a new token.
        response.delete_cookie(
            settings.CSRF_COOKIE_NAME, 
            path=settings.CSRF_COOKIE_PATH,
            samesite=settings.CSRF_COOKIE_SAMESITE # Typically 'Lax' or 'None'
        )
        
        return response
class CompleteGameView(APIView):
    """
    Save a completed game and award points to the user.
    Called when the game ends (game over).
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        score = request.data.get('score')
        mode = request.data.get('mode', 'manual')
        ai_model_id = request.data.get('ai_model_id')
        board_state = request.data.get('board_state', [])
        
        if score is None or score < 0:
            return Response(
                {"error": "Valid score is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            profile, created = Profile.objects.get_or_create(user=user)
            
            game = Game.objects.create(
                user=user,
                score=score,
                mode=mode,
                ai_model_id=ai_model_id if ai_model_id else None,
                replay_json={'board': board_state}
            )
            
            points_earned = profile.add_game_score(score)
            
            print(f"✓ Game completed for {user.username}: score={score}, points_earned={points_earned}")
            
            return Response({
                "success": True,
                "message": f"Game saved! Earned {points_earned} points.",
                "points_earned": points_earned,
                "new_total_points": profile.points,
                "games_played": profile.games_played,
                "high_score": profile.high_score,
                "game_id": game.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"❌ Error completing game: {e}")
            return Response(
                {"error": f"Failed to save game: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserStatsView(APIView):
    """Get current user's statistics and points."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        try:
            profile = Profile.objects.get(user=user)
            recent_games = Game.objects.filter(user=user).order_by('-created_at')[:5]
            recent_games_data = [
                {
                    'score': game.score,
                    'mode': game.mode,
                    'date': game.created_at.isoformat()
                }
                for game in recent_games
            ]
            
            return Response({
                "username": user.username,
                "points": profile.points,
                "lifetime_points": profile.lifetime_points,
                "games_played": profile.games_played,
                "high_score": profile.high_score,
                "average_score": profile.average_score,
                "recent_games": recent_games_data
            }, status=status.HTTP_200_OK)
            
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=user)
            return Response({
                "username": user.username,
                "points": profile.points,
                "lifetime_points": 0,
                "games_played": 0,
                "high_score": 0,
                "average_score": 0,
                "recent_games": []
            }, status=status.HTTP_200_OK)