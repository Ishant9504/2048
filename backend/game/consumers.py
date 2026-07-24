import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .game_engine import Game2048
import asyncio

# Try to import AGENTS, but continue without them if not available
try:
    from game.ai_agents import AGENTS
    print(f"✓ Loaded {len(AGENTS)} AI agents: {list(AGENTS.keys())}")
except ImportError as e:
    print(f"Warning: AI agents not found - {e}")
    print("AI functionality disabled")
    AGENTS = {}

active_games = {}  # In-memory cache

class GameConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_task = None
        self.group_name = None
        self.game_key = None 
        self.game = None
        self.authenticated_username = None

    @database_sync_to_async
    def save_game_state(self, user_id, board, score, is_over):
        """Save current game state to database"""
        from django.contrib.auth.models import User
        from .models import GameState
        
        try:
            print(f"🔵 Attempting to save game state for user_id={user_id}")
            user = User.objects.get(id=user_id)
            print(f"🔵 Found user: {user.username}")
            
            game_state, created = GameState.objects.update_or_create(
                user=user,
                defaults={
                    'board_state': json.dumps(board),
                    'score': score,
                    'is_over': is_over
                }
            )
            
            if created:
                print(f"✓ CREATED new game state for {user.username}: score={score}")
            else:
                print(f"✓ UPDATED game state for {user.username}: score={score}")
                
            # Verify it was saved
            verify = GameState.objects.filter(user=user).first()
            if verify:
                print(f"✓ Verified in database: score={verify.score}")
            
            return True
        except Exception as e:
            import traceback
            print(f"❌ ERROR saving game state: {e}")
            traceback.print_exc()
            return False

    @database_sync_to_async
    def load_game_state(self, user_id):
        """Load game state from database"""
        from django.contrib.auth.models import User
        from .models import GameState
        
        try:
            print(f"🔵 Attempting to load game state for user_id={user_id}")
            user = User.objects.get(id=user_id)
            print(f"🔵 Found user: {user.username}")
            
            game_state = GameState.objects.filter(user=user).first()
            
            if game_state:
                board = json.loads(game_state.board_state)
                print(f"✓ LOADED game state for {user.username}: score={game_state.score}, over={game_state.is_over}")
                print(f"✓ Board preview: {board[0]}")  # Show first row
                return {
                    'board': board,
                    'score': game_state.score,
                    'over': game_state.is_over
                }
            else:
                print(f"ℹ️ No saved game state found for {user.username}")
                return None
        except Exception as e:
            import traceback
            print(f"❌ ERROR loading game state: {e}")
            traceback.print_exc()
            return None

    async def run_ai(self, game, agent_name):
        agent_cls = AGENTS.get(agent_name.lower())
        if not agent_cls:
            return

        agent = agent_cls()
        try:
            while not game.over:
                await asyncio.sleep(0.3)
                move = agent.get_move(game.board)
                moved = game.move(move)

                if moved:
                    try:
                        if hasattr(self, 'channel_layer'):
                            await self.channel_layer.group_send(
                                self.group_name,
                                {
                                    "type": "broadcast_state",
                                    "board": game.board,
                                    "score": game.score,
                                    "over": game.over
                                }
                            )
                        else:
                            await self.send(text_data=json.dumps({
                                "type": "update",
                                "board": game.board,
                                "score": game.score,
                                "over": game.over
                            }))
                    except Exception as e:
                        print(f"Error sending AI move update: {str(e)}")
        except asyncio.CancelledError:
            pass
        finally:
            self.ai_task = None

    async def connect(self):
        try:
            print("\n" + "="*50)
            print(">>> WebSocket Connection Attempt <<<")
            print("="*50)
            
            user = self.scope.get("user", None)
            session = self.scope.get("session", None)
            headers = dict(self.scope.get('headers', []))
            query_string = self.scope.get('query_string', b'').decode('utf-8')
            
            query_params = {}
            if query_string:
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        query_params[key] = value
            
            # Determine authentication
            authenticated_username = None
            authenticated_user = None
            user_id = None
            
            # Try Django scope
            if user and not user.is_anonymous:
                authenticated_username = user.username
                authenticated_user = user
                user_id = user.id
                print(f"✓ Authenticated via Django scope: {authenticated_username} (ID: {user_id})")
            
            # Try session
            elif session:
                try:
                    session_dict = dict(session) if hasattr(session, 'items') else session.get_decoded() if hasattr(session, 'get_decoded') else {}
                    
                    if '_auth_user_id' in session_dict:
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        user_id = session_dict.get('_auth_user_id')
                        auth_user = User.objects.get(pk=user_id)
                        authenticated_username = auth_user.username
                        authenticated_user = auth_user
                        print(f"✓ Authenticated via session: {authenticated_username} (ID: {user_id})")
                except Exception as e:
                    print(f"Session auth failed: {e}")
            
            # Try cookies
            if not authenticated_username and b'cookie' in headers:
                try:
                    cookie_str = headers[b'cookie'].decode()
                    cookies = {}
                    for cookie_part in cookie_str.split(';'):
                        if '=' in cookie_part:
                            name, value = cookie_part.strip().split('=', 1)
                            cookies[name] = value
                    
                    if 'sessionid' in cookies:
                        from django.contrib.sessions.models import Session
                        from django.contrib.auth.models import User
                        
                        session_key = cookies['sessionid']
                        session_obj = Session.objects.get(session_key=session_key)
                        session_data = session_obj.get_decoded()
                        
                        if '_auth_user_id' in session_data:
                            user_id = session_data.get('_auth_user_id')
                            auth_user = User.objects.get(pk=user_id)
                            authenticated_username = auth_user.username
                            authenticated_user = auth_user
                            print(f"✓ Authenticated via cookie: {authenticated_username} (ID: {user_id})")
                except Exception as e:
                    print(f"Cookie auth failed: {e}")
            
            print(f"Final authentication: username={authenticated_username}, user_id={user_id}")
            
            # Generate game key - ALWAYS use user_id for authenticated users
            if user_id:
                self.game_key = f"user_{user_id}"  # Use ID, not username!
                self.authenticated_username = authenticated_username
                self.user_id = user_id
                print(f"Using game key: {self.game_key}")
            elif 'session' in query_params and query_params['session'] != 'anonymous':
                session_id = query_params['session']
                self.game_key = f"session_{session_id}"
                self.authenticated_username = None
                self.user_id = None
            elif session and session.session_key:
                self.game_key = f"anon_{session.session_key}"
                self.authenticated_username = None
                self.user_id = None
            else:
                self.game_key = f"temp_{self.channel_name}"
                self.authenticated_username = None
                self.user_id = None
            
            self.group_name = f"game_{self.game_key}"
            
            # Accept connection
            await self.accept()
            print("Connection accepted")
            
            # Load or create game
            game_loaded = False
            
            # For authenticated users, try to load from database first
            if self.user_id:
                print(f"Attempting to load saved game for user_id={self.user_id}")
                saved_state = await self.load_game_state(self.user_id)
                
                if saved_state:
                    # Create game and restore state
                    self.game = Game2048()
                    self.game.board = saved_state['board']
                    self.game.score = saved_state['score']
                    self.game.over = saved_state['over']
                    active_games[self.game_key] = self.game
                    game_loaded = True
                    print(f"✓ Restored game from database: score={saved_state['score']}")
            
            # If no saved state, check memory or create new
            if not game_loaded:
                if self.game_key in active_games:
                    print(f"Found existing game in memory for {self.game_key}")
                    self.game = active_games[self.game_key]
                else:
                    print(f"Creating new game for {self.game_key}")
                    self.game = Game2048()
                    active_games[self.game_key] = self.game
            
            # Add to channel group
            if hasattr(self, 'channel_layer'):
                await self.channel_layer.group_add(self.group_name, self.channel_name)
                print(f"Added to group {self.group_name}")
            
            # Send initial state
            await self.send(text_data=json.dumps({
                "type": "init",
                "board": self.game.board,
                "score": self.game.score,
                "over": self.game.over,
                "username": self.authenticated_username
            }))
            print(f"Sent initial game state for {self.game_key}")
            
        except Exception as e:
            import traceback
            print(f"ERROR IN CONNECT: {str(e)}")
            traceback.print_exc()
            await self.close(code=1011)

    async def disconnect(self, close_code):
        try:
            print(f"WebSocket disconnect: code={close_code}, game_key={self.game_key}")
            
            # Cancel AI task
            if self.ai_task:
                self.ai_task.cancel()
            
            # Remove from channel group
            if hasattr(self, 'group_name') and self.group_name:
                await self.channel_layer.group_discard(self.group_name, self.channel_name)
            
            # CRITICAL: Save game state for authenticated users
            if self.user_id and self.game:
                print(f"Saving game state for user_id={self.user_id}")
                await self.save_game_state(
                    self.user_id,
                    self.game.board,
                    self.game.score,
                    self.game.over
                )
                print(f"✓ Game state saved to database")
                
                # Keep in memory for quick reconnection
                print(f"Keeping game in memory for potential reconnection")
            else:
                # Remove anonymous games on normal close
                if close_code == 1000 and self.game_key and self.game_key in active_games:
                    if not self.game_key.startswith("user_"):
                        print(f"Removing anonymous game: {self.game_key}")
                        active_games.pop(self.game_key, None)
            
            print(f"WebSocket disconnected")
        except Exception as e:
            print(f"ERROR IN DISCONNECT: {str(e)}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            
            if data.get("type") == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
                return
            
            if not self.game:
                await self.send(text_data=json.dumps({"type": "error", "message": "No active game"}))
                return 
            
            if data.get("type") == "move":
                direction = data.get("direction")
                if direction in ["up", "down", "left", "right"]:
                    moved = self.game.move(direction)
                    
                    if moved:
                        # Save to database after each move for authenticated users
                        if self.user_id:
                            await self.save_game_state(
                                self.user_id,
                                self.game.board,
                                self.game.score,
                                self.game.over
                            )
                        
                        if hasattr(self, 'channel_layer'):
                            await self.channel_layer.group_send(
                                self.group_name,
                                {
                                    "type": "broadcast_state",
                                    "board": self.game.board,
                                    "score": self.game.score,
                                    "over": self.game.over,
                                    "username": self.authenticated_username
                                }
                            )
                        else:
                            await self.send(text_data=json.dumps({
                                "type": "update",
                                "board": self.game.board,
                                "score": self.game.score,
                                "over": self.game.over,
                                "username": self.authenticated_username
                            }))
                        
            elif data.get("type") == "ai":
                agent_name = data.get("agent")
                if agent_name:
                    if self.ai_task: 
                        self.ai_task.cancel()
                    self.ai_task = asyncio.create_task(self.run_ai(self.game, agent_name))
                    
            elif data.get("type") == "restart":
                if self.ai_task: 
                    self.ai_task.cancel()
                    self.ai_task = None
                
                # Create new game
                self.game = Game2048()
                active_games[self.game_key] = self.game
                print(f"Game restarted for {self.game_key}")
                
                # Save new game state
                if self.user_id:
                    await self.save_game_state(
                        self.user_id,
                        self.game.board,
                        self.game.score,
                        self.game.over
                    )
                
                if hasattr(self, 'channel_layer'):
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            "type": "broadcast_state",
                            "board": self.game.board,
                            "score": self.game.score,
                            "over": self.game.over,
                            "username": self.authenticated_username
                        }
                    )
                else:
                    await self.send(text_data=json.dumps({
                        "type": "update",
                        "board": self.game.board,
                        "score": self.game.score,
                        "over": self.game.over,
                        "username": self.authenticated_username
                    }))
        
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            import traceback
            traceback.print_exc()

    async def broadcast_state(self, event):
        try:
            await self.send(text_data=json.dumps({
                "type": "update", 
                "board": event["board"], 
                "score": event["score"], 
                "over": event["over"],
                "username": event.get("username")
            }))
        except Exception as e:
            print(f"Error in broadcast_state: {str(e)}")