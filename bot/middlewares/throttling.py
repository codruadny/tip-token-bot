import time
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from cachetools import TTLCache

from bot.config import settings

class ThrottlingMiddleware(BaseMiddleware):
    """Middleware for rate limiting user requests."""
    
    def __init__(self):
        # Use TTLCache to automatically expire old entries
        # The cache stores (user_id, command) keys with timestamps as values
        self.cache = TTLCache(maxsize=10000, ttl=settings.COMMAND_COOLDOWN)
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process middleware logic."""
        # Skip throttling for admins
        user_id = None
        command = None
        
        # Extract user_id and command from different event types
        if isinstance(event, Message) and event.text:
            user_id = event.from_user.id
            command = event.text.split()[0] if event.text.startswith('/') else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            command = event.data if event.data else None
        
        # Skip if not a command or user_id not found
        if not user_id or not command or user_id in settings.ADMINS:
            return await handler(event, data)
        
        # Create a unique key for this user and command
        key = (user_id, command)
        
        # Check if user is throttled
        current_time = time.time()
        if key in self.cache:
            last_time = self.cache[key]
            remaining = settings.COMMAND_COOLDOWN - (current_time - last_time)
            
            if remaining > 0:
                # If throttled, notify the user
                if isinstance(event, Message):
                    _ = data.get("_", lambda x: x)
                    await event.answer(_("throttling_message").format(seconds=int(remaining)))
                return None
        
        # Update the cache with the current time
        self.cache[key] = current_time
        
        # Continue processing
        return await handler(event, data)
