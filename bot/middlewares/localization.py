import json
import os
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User, Message, CallbackQuery

from bot.config import settings
from bot.services.database import get_user_language

class I18nMiddleware(BaseMiddleware):
    """Middleware for handling internationalization (i18n)."""
    
    def __init__(self):
        self.i18n_data = {}
        self._load_translations()
    
    def _load_translations(self):
        """Load all translation files."""
        locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
        for lang in settings.AVAILABLE_LANGUAGES:
            try:
                with open(os.path.join(locales_dir, f"{lang}.json"), "r", encoding="utf-8") as f:
                    self.i18n_data[lang] = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error loading {lang} translations: {e}")
                # Fallback to empty dict
                self.i18n_data[lang] = {}
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process middleware logic."""
        # Extract user from different event types
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        
        if user:
            # Get user's language from database or use default
            lang_code = await get_user_language(user.id) or settings.DEFAULT_LANGUAGE
            
            # Ensure the language is supported
            if lang_code not in settings.AVAILABLE_LANGUAGES:
                lang_code = settings.DEFAULT_LANGUAGE
            
            # Add translation function to the data
            data["_"] = lambda key: self.i18n_data.get(lang_code, {}).get(key, key)
            data["user_lang"] = lang_code
        
        return await handler(event, data)
