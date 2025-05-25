import os
import json
import logging
from typing import Dict, Optional

from bot.config import settings

# Cache for translations
_translations_cache = {}

def get_translation_for_language(lang_code: str) -> callable:
    """Get translation function for a specific language."""
    # Load translations if not cached
    if lang_code not in _translations_cache:
        _load_translation(lang_code)
    
    # Get translations dictionary
    translations = _translations_cache.get(lang_code, {})
    
    # Return translation function
    def translate(key: str) -> str:
        return translations.get(key, key)
    
    return translate

def _load_translation(lang_code: str) -> None:
    """Load translations for a language from file."""
    try:
        # Construct path to translation file
        locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
        file_path = os.path.join(locales_dir, f"{lang_code}.json")
        
        # Load translations from file
        with open(file_path, "r", encoding="utf-8") as f:
            translations = json.load(f)
        
        # Cache translations
        _translations_cache[lang_code] = translations
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading translations for {lang_code}: {e}")
        # Use empty dict as fallback
        _translations_cache[lang_code] = {}

def get_language_name(lang_code: str) -> str:
    """Get human-readable language name."""
    language_names = {
        "en": "English 🇬🇧",
        "ru": "Русский 🇷🇺",
        "cn": "中文 🇨🇳",
        "es": "Español 🇪🇸"
    }
    
    return language_names.get(lang_code, lang_code)
