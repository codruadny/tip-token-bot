import re
import logging
from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import settings
from bot.services.blockchain import send_tip, get_token_balance
from bot.services.database import get_user_wallet, save_transaction, get_user_by_username
from bot.utils.idempotency import generate_idempotency_key, check_idempotency
from bot.keyboards.inline import get_tip_confirmation_keyboard

# Initialize router
router = Router()

# Define FSM states
class TipStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_confirmation = State()

# Regex patterns for tip commands
TIP_COMMAND_PATTERN = r"^/tip(?:@\w+)?\s+(@\w+|\d+)\s+(\d+(?:\.\d+)?)\s*$"
TIP_REPLY_PATTERN = r"^/tip(?:@\w+)?\s+(\d+(?:\.\d+)?)\s*$"

@router.message(Command("tip"))
async def command_tip(message: Message, _: callable, state: FSMContext):
    """Handle /tip command to send TIP tokens to another user."""
    user_id = message.from_user.id
    
    # Check if user has a wallet
    sender_wallet = await get_user_wallet(user_id)
    if not sender_wallet:
        await message.answer(
            _("no_wallet_tip"),
            parse_mode="HTML"
        )
        return
    
    # Check if message is a reply or contains recipient and amount
    if message.reply_to_message:
        # Process reply-based tip
        match = re.match(TIP_REPLY_PATTERN, message.text)
        if match:
            amount_str = match.group(1)
            recipient_id = message.reply_to_message.from_user.id
            
            # Don't allow tipping yourself
            if recipient_id == user_id:
                await message.answer(_("cannot_tip_yourself"))
                return
            
            # Don't allow tipping the bot
            if recipient_id == message.bot.id:
                await message.answer(_("cannot_tip_bot"))
                return
            
            # Process the tip
            await process_tip(message, _, state, user_id, recipient_id, amount_str)
            return
        else:
            # Ask for amount if not provided
            await message.answer(_("tip_amount_prompt"))
            await state.set_state(TipStates.waiting_for_amount)
            await state.update_data(recipient_id=message.reply_to_message.from_user.id)
            return
    else:
        # Process direct command with username/user_id and amount
        match = re.match(TIP_COMMAND_PATTERN, message.text)
        if match:
            recipient_identifier = match.group(1)
            amount_str = match.group(2)
            
            # Extract recipient ID from username or direct ID
            if recipient_identifier.startswith('@'):
                # It's a username
                username = recipient_identifier[1:]  # Remove @ symbol
                recipient_data = await get_user_by_username(username)
                if not recipient_data:
                    await message.answer(_("user_not_found"))
                    return
                recipient_id = recipient_data["user_id"]
            else:
                # It's a user ID
                try:
                    recipient_id = int(recipient_identifier)
                except ValueError:
                    await message.answer(_("invalid_user_id"))
                    return
            
            # Don't allow tipping yourself
            if recipient_id == user_id:
                await message.answer(_("cannot_tip_yourself"))
                return
            
            # Process the tip
            await process_tip(message, _, state, user_id, recipient_id, amount_str)
            return
    
    # If we get here, the command format was invalid
    await message.answer(
        _("tip_usage"),
        parse_mode="HTML"
    )

async def process_tip(message, _, state, sender_id, recipient_id, amount_str):
    """Process the tip operation with validation."""
    try:
        amount = Decimal(amount_str)
    except (ValueError, TypeError):
        await message.answer(_("invalid_amount"))
        return
    
    # Validate amount
    if amount < Decimal(str(settings.MIN_TIP_AMOUNT)):
        await message.answer(_("tip_amount_too_low").format(
            min_amount=settings.MIN_TIP_AMOUNT
        ))
        return
    
    if amount > Decimal(str(settings.MAX_TIP_AMOUNT)):
        await message.answer(_("tip_amount_too_high").format(
            max_amount=settings.MAX_TIP_AMOUNT
        ))
        return
    
    # Check if recipient has a wallet
    recipient_wallet = await get_user_wallet(recipient_id)
    if not recipient_wallet:
        await message.answer(_("recipient_no_wallet"))
        return
    
    # Check sender's balance
    sender_wallet = await get_user_wallet(sender_id)
    balance = await get_token_balance(sender_wallet)
    
    if balance < amount:
        await message.answer(_("insufficient_balance").format(
            balance=balance
        ))
        return
    
    # Store data for confirmation
    await state.set_state(TipStates.waiting_for_confirmation)
    await state.update_data(
        recipient_id=recipient_id,
        recipient_wallet=recipient_wallet,
        amount=str(amount),
        idempotency_key=generate_idempotency_key()
    )
    
    # Ask for confirmation
    await message.answer(
        _("confirm_tip").format(
            amount=amount,
            recipient_id=recipient_id
        ),
        reply_markup=get_tip_confirmation_keyboard(_)
    )

@router.message(TipStates.waiting_for_amount)
async def process_tip_amount(message: Message, _: callable, state: FSMContext):
    """Process tip amount when replying to a message."""
    try:
        amount = Decimal(message.text.strip())
    except (ValueError, TypeError):
        await message.answer(_("invalid_amount"))
        return
    
    # Get data from state
    data = await state.get_data()
    recipient_id = data.get("recipient_id")
    
    # Process the tip with the provided amount
    await process_tip(message, _, state, message.from_user.id, recipient_id, str(amount))

@router.callback_query(F.data == "confirm_tip", TipStates.waiting_for_confirmation)
async def confirm_tip(callback: CallbackQuery, _: callable, state: FSMContext):
    """Handle tip confirmation."""
    data = await state.get_data()
    sender_id = callback.from_user.id
    recipient_id = data.get("recipient_id")
    recipient_wallet = data.get("recipient_wallet")
    amount_str = data.get("amount")
    idempotency_key = data.get("idempotency_key")
    
    # Check idempotency to prevent double-spending
    if await check_idempotency(idempotency_key):
        await callback.message.edit_text(_("transaction_already_processed"))
        await state.clear()
        await callback.answer()
        return
    
    # Show processing message
    await callback.message.edit_text(_("processing_tip"), reply_markup=None)
    
    try:
        # Get sender's wallet
        sender_wallet = await get_user_wallet(sender_id)
        
        # Send the tip
        tx_hash = await send_tip(
            sender_wallet_address=sender_wallet,
            recipient_wallet_address=recipient_wallet,
            amount=Decimal(amount_str)
        )
        
        # Save transaction to database
        await save_transaction(
            sender_id=sender_id,
            recipient_id=recipient_id,
            amount=Decimal(amount_str),
            tx_hash=tx_hash,
            tx_type="tip",
            idempotency_key=idempotency_key
        )
        
        # Send success message
        await callback.message.edit_text(
            _("tip_success").format(
                amount=amount_str,
                recipient_id=recipient_id,
                tx_hash=tx_hash
            ),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logging.error(f"Error sending tip from {sender_id} to {recipient_id}: {e}")
        await callback.message.edit_text(
            _("tip_error"),
            reply_markup=None
        )
    
    # Reset state
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "cancel_tip", TipStates.waiting_for_confirmation)
async def cancel_tip(callback: CallbackQuery, _: callable, state: FSMContext):
    """Handle tip cancellation."""
    await callback.message.edit_text(
        _("tip_cancelled"),
        reply_markup=None
    )
    
    # Reset state
    await state.clear()
    await callback.answer()
