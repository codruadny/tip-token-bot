import json
import logging
from typing import Optional, Dict, Any
from decimal import Decimal

# Use in-memory cache as a simple solution
# In production, consider using Redis or another distributed cache
_balance_cache = {}

async def cache_balance(user_id: int, balance: Decimal, ttl_seconds: int = 300) -> None:
    """Cache a user's balance for faster retrieval."""
    try:
        import time
        
        # Store balance with expiration time
        _balance_cache[user_id] = {
            "balance": str(balance),  # Convert Decimal to string for JSON compatibility
            "expires_at": time.time() + ttl_seconds
        }
    except Exception as e:
        logging.error(f"Error caching balance: {e}")

async def get_cached_balance(user_id: int) -> Optional[Decimal]:
    """Get a user's cached balance if it exists and is not expired."""
    try:
        import time
        
        # Check if balance is in cache
        if user_id not in _balance_cache:
            return None
        
        # Check if cached balance is expired
        cache_data = _balance_cache[user_id]
        if time.time() > cache_data.get("expires_at", 0):
            # Cache expired, remove it
            del _balance_cache[user_id]
            return None
        
        # Return cached balance
        return Decimal(cache_data.get("balance", "0"))
    except Exception as e:
        logging.error(f"Error getting cached balance: {e}")
        return None

async def invalidate_balance_cache(user_id: int) -> None:
    """Invalidate a user's cached balance."""
    try:
        if user_id in _balance_cache:
            del _balance_cache[user_id]
    except Exception as e:
        logging.error(f"Error invalidating balance cache: {e}")
