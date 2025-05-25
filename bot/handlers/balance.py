from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services.blockchain import get_token_balance
from bot.services.database import get_user_wallet
from bot.services.cache import cache_balance, get_cached_balance

# Initialize router
router = Router()

@router.message(Command("balance"))
async def command_balance(message: Message, _: callable):
    """Handle /balance command to show user's token balance."""
    user_id = message.from_user.id
    
    # Check if user has a wallet
    wallet_address = await get_user_wallet(user_id)
    if not wallet_address:
        await message.answer(
            _("no_wallet").format(command="/register"),
            parse_mode="HTML"
        )
        return
    
    # Try to get balance from cache first
    cached_balance = await get_cached_balance(user_id)
    
    if cached_balance is not None:
        # We have a cached balance, use it
        await message.answer(
            _("balance_info").format(
                balance=cached_balance,
                refresh_command="/balance refresh"
            ),
            parse_mode="HTML"
        )
        return
    
    # No cached balance, get fresh balance from blockchain
    try:
        # Send "checking balance" message
        checking_msg = await message.answer(_("checking_balance"))
        
        # Get balance from blockchain
        balance = await get_token_balance(wallet_address)
        
        # Cache the balance
        await cache_balance(user_id, balance)
        
        # Edit the message with the balance
        await checking_msg.edit_text(
            _("balance_info").format(
                balance=balance,
                refresh_command="/balance refresh"
            ),
            parse_mode="HTML"
        )
    
    except Exception as e:
        await message.answer(_("balance_error"))
