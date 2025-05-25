from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.services.database import get_user_transactions, get_user_by_id

# Initialize router
router = Router()

@router.message(Command("transactions"))
async def command_transactions(message: Message, _: callable):
    """Handle /transactions command to show transaction history."""
    user_id = message.from_user.id
    
    # Get transaction history
    transactions = await get_user_transactions(user_id, limit=10)
    
    if not transactions:
        await message.answer(_("no_transactions"))
        return
    
    # Create transaction list message
    tx_message = _("transaction_history") + "\n\n"
    
    for tx in transactions:
        tx_type = tx.get("tx_type", "unknown")
        amount = tx.get("amount", 0)
        tx_hash = tx.get("tx_hash", "")
        timestamp = tx.get("created_at", "")
        
        # Format timestamp
        if timestamp:
            from datetime import datetime
            try:
                # Convert timestamp to readable format
                dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = str(timestamp)
        else:
            formatted_time = _("unknown_time")
        
        # Format transaction info based on type
        if tx_type == "tip":
            sender_id = tx.get("sender_id")
            recipient_id = tx.get("recipient_id")
            
            if sender_id == user_id:
                # Outgoing tip
                recipient_data = await get_user_by_id(recipient_id)
                recipient_name = "Unknown"
                if recipient_data:
                    username = recipient_data.get("username", "")
                    name = recipient_data.get("first_name", "")
                    recipient_name = f"@{username}" if username else name or f"User {recipient_id}"
                
                tx_message += _("outgoing_tip").format(
                    amount=amount,
                    recipient=recipient_name,
                    time=formatted_time,
                    tx_hash=tx_hash[:6] + "..." + tx_hash[-4:]
                ) + "\n\n"
            else:
                # Incoming tip
                sender_data = await get_user_by_id(sender_id)
                sender_name = "Unknown"
                if sender_data:
                    username = sender_data.get("username", "")
                    name = sender_data.get("first_name", "")
                    sender_name = f"@{username}" if username else name or f"User {sender_id}"
                
                tx_message += _("incoming_tip").format(
                    amount=amount,
                    sender=sender_name,
                    time=formatted_time,
                    tx_hash=tx_hash[:6] + "..." + tx_hash[-4:]
                ) + "\n\n"
        
        elif tx_type == "deposit":
            tx_message += _("deposit_tx").format(
                amount=amount,
                time=formatted_time,
                tx_hash=tx_hash[:6] + "..." + tx_hash[-4:]
            ) + "\n\n"
        
        elif tx_type == "withdraw":
            destination = tx.get("recipient_wallet", _("external_wallet"))
            tx_message += _("withdraw_tx").format(
                amount=amount,
                destination=destination[:6] + "..." + destination[-4:] if len(destination) > 10 else destination,
                time=formatted_time,
                tx_hash=tx_hash[:6] + "..." + tx_hash[-4:]
            ) + "\n\n"
        
        else:
            # Unknown transaction type
            tx_message += _("unknown_tx").format(
                amount=amount,
                type=tx_type,
                time=formatted_time,
                tx_hash=tx_hash[:6] + "..." + tx_hash[-4:]
            ) + "\n\n"
    
    # Add view more option if there are more transactions
    total_tx_count = await get_user_transactions(user_id, count_only=True)
    if total_tx_count > 10:
        tx_message += _("more_transactions").format(
            remaining=total_tx_count - 10
        )
    
    # Send transaction history
    await message.answer(
        tx_message,
        parse_mode="HTML",
        reply_markup=get_transaction_keyboard(_) if total_tx_count > 10 else None
    )

@router.callback_query(F.data == "view_more_transactions")
async def view_more_transactions(callback: CallbackQuery, _: callable):
    """Handle view more transactions request."""
    user_id = callback.from_user.id
    
    # Get additional transactions
    transactions = await get_user_transactions(user_id, limit=10, offset=10)
    
    if not transactions:
        await callback.answer(_("no_more_transactions"))
        return
    
    # Create transaction list message
    tx_message = _("more_transaction_history") + "\n\n"
    
    for tx in transactions:
        tx_type = tx.get("tx_type", "unknown")
        amount = tx.get("amount", 0)
        tx_hash = tx.get("tx_hash", "")
        timestamp = tx.get("created_at", "")
        
        # Format timestamp
        if timestamp:
            from datetime import datetime
            try:
                # Convert timestamp to readable format
                dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = str(timestamp)
        else:
            formatted_time = _("unknown_time")
        
        # Format transaction info based on type
        if tx_type == "tip":
            sender_id = tx.get("sender_id")
            recipient_id = tx.get("recipient_id")
            
            if sender_id == user_id:
                # Outgoing tip
                recipient_data = await get_user_by_id(recipient_id)
                recipient_name = "Unknown"
                if recipient_data:
                    username = recipient_data.get("username", "")
                    name = recipient_data.get("first_name", "")
                    recipient_name = f"@{username}" if username else name or f"User {recipient_id}"
                
                tx_message += _("outgoing_tip").format(
                    amount=amount,
                    recipient=recipient_name,
                    time=formatted_time,
                    tx_hash=tx_hash[:6] + "..." + tx_hash[-4:]
                ) + "\n\n"
            else:
                # Incoming tip
                sender_data = await get_user_by_id(sender_id)
                sender_name = "Unknown"
                if sender_data:
                    username = sender_data.get("username", "")
                    name = sender_data.get("first_name", "")
                    sender_name = f"@{username}" if username else name or f"User {sender_id}"
                
                tx_message += _("incoming_tip").format(
                    amount=amount,
                    sender=sender_name,
                    time=formatted_time,
                    tx_hash=tx_hash[:6] + "..." + tx_hash[-4:]
                ) + "\n\n"
        
        elif tx_type == "deposit":
            tx_message += _("deposit_tx").format(
                amount=amount,
                time=formatted_time,
                tx_hash=tx_hash[:6] + "..." + tx_hash[-4:]
            ) + "\n\n"
        
        elif tx_type == "withdraw":
            destination = tx.get("recipient_wallet", _("external_wallet"))
            tx_message += _("withdraw_tx").format(
                amount=amount,
                destination=destination[:6] + "..." + destination[-4:] if len(destination) > 10 else destination,
                time=formatted_time,
                tx_hash=tx_hash[:6] + "..." + tx_hash[-4:]
            ) + "\n\n"
        
        else:
            # Unknown transaction type
            tx_message += _("unknown_tx").format(
                amount=amount,
                type=tx_type,
                time=formatted_time,
                tx_hash=tx_hash[:6] + "..." + tx_hash[-4:]
            ) + "\n\n"
    
    # Send additional transactions
    await callback.message.answer(
        tx_message,
        parse_mode="HTML"
    )
    
    await callback.answer()

def get_transaction_keyboard(_):
    """Create inline keyboard for transactions."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("view_more"),
                    callback_data="view_more_transactions"
                )
            ]
        ]
    )
    
    return keyboard
