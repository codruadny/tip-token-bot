import uuid
import logging
from typing import Optional

from bot.services.database import check_transaction_exists

async def generate_idempotency_key() -> str:
    """Generate a unique idempotency key for a transaction."""
    return str(uuid.uuid4())

async def check_idempotency(idempotency_key: Optional[str]) -> bool:
    """Check if a transaction with the given idempotency key already exists.
    
    Returns:
        bool: True if the transaction already exists, False otherwise
    """
    if not idempotency_key:
        return False
    
    try:
        return await check_transaction_exists(idempotency_key)
    except Exception as e:
        logging.error(f"Error checking idempotency: {e}")
        # In case of error, assume it's a new transaction
        return False
