import os
import sys
import logging
import django
from django.core.asgi import get_asgi_application

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('asgi')
logger.info("Starting ASGI application")

# Setup Django BEFORE importing anything else
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
logger.info("Django setup complete")

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.security.websocket import AllowedHostsOriginValidator
from channels.exceptions import RequestAborted
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.models import Session
from game import routing as game_routing

# Custom Session-Cookie Authentication Middleware
class SessionAuthMiddleware:
    """
    Custom middleware to authenticate WebSocket connections using session cookies.
    Channels' AuthMiddlewareStack doesn't always read cookies properly,
    so we manually extract the sessionid and authenticate the user.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'websocket':
            return await self.app(scope, receive, send)
        
        session_key = None
        
        # Try to get the session key from the query string
        #    e.g., ws://.../?session=xxx
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
        session_key = query_params.get('session')

        if session_key:
            logger.info(f"🔍 Found session key in query string: {session_key}")
        
        # IF it's not in the query string, fall back to checking the cookies
        if not session_key:
            headers = dict(scope.get('headers', []))
            cookie_header = headers.get(b'cookie', b'').decode('utf-8')
            cookies = dict(cookie.split('=') for cookie in cookie_header.split(';') if '=' in cookie)
            session_key = cookies.get('sessionid')
            if session_key:
                 logger.info(f"🔍 Found sessionid in cookies: {session_key}")

        # Authenticate the user based on the session key we found
        if session_key:
            user = await self.get_user_from_session(session_key)
            if user:
                logger.info(f"✅ Authenticated user from session: {user.username} (ID: {user.id})")
                scope['user'] = user
            else:
                logger.warning(f"⚠️ Session {session_key} found but no user associated with it.")
                scope['user'] = AnonymousUser()
        else:
            logger.warning("⚠️ No session key found in query string or cookies.")
            scope['user'] = AnonymousUser()
        
        return await self.app(scope, receive, send)
    
    @database_sync_to_async
    def get_user_from_session(self, session_key):
        """Load user from session key"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Get session from database
            session = Session.objects.get(session_key=session_key)
            session_data = session.get_decoded()
            
            # Get user ID from session
            user_id = session_data.get('_auth_user_id')
            if user_id:
                user = User.objects.get(pk=user_id)
                return user
        except (Session.DoesNotExist, User.DoesNotExist, KeyError):
            pass
        
        return None


# Custom middleware for better error handling
class ErrorHandlingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            logger.info(f"New {scope['type']} connection from {scope.get('client', ['unknown'])[0]}")
            if scope['type'] == 'websocket':
                headers = dict(scope.get('headers', []))
                origin = headers.get(b'origin', b'unknown').decode()
                logger.info(f"WebSocket connection from origin: {origin}")
                
                # Debug: Log authentication status AFTER our custom middleware
                user = scope.get('user', None)
                if user and hasattr(user, 'is_authenticated') and user.is_authenticated:
                    logger.info(f"✅ WebSocket user: {user.username} (authenticated)")
                else:
                    logger.info("❌ WebSocket user: Anonymous/None")
                    
            await self.app(scope, receive, send)
        except RequestAborted:
            logger.warning("Request was aborted")
        except Exception as e:
            logger.error(f"Error in ASGI application: {str(e)}", exc_info=True)
            if scope['type'] == 'websocket':
                try:
                    await send({
                        'type': 'websocket.close',
                        'code': 1011,
                        'reason': 'Internal server error',
                    })
                except Exception:
                    pass

# Define the HTTP application first
logger.info("Initializing HTTP application")
http_application = get_asgi_application()

# Setup WebSocket routing with custom session auth
logger.info("Setting up protocol router")
application = ErrorHandlingMiddleware(
    ProtocolTypeRouter({
        "http": http_application,
        "websocket": AllowedHostsOriginValidator(
            SessionAuthMiddleware(  # ← Our custom middleware FIRST
                AuthMiddlewareStack(  # ← Then standard auth
                    URLRouter(
                        game_routing.websocket_urlpatterns
                    )
                )
            )
        ),
    })
)
logger.info("ASGI application configured and ready")