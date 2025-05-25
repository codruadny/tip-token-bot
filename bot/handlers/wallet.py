import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import settings
from bot.services.blockchain import check_wallet_exists, get_token_balance
from bot.services.database import get_user_wallet
from bot.keyboards.inline import get_wallet_menu_keyboard

# Initialize router
router = Router()

# Define FSM states
class WalletStates(StatesGroup):
    waiting_for_withdraw_address = State()
    waiting_for_withdraw_amount = State()
    waiting_for_withdraw_confirmation = State()

@router.message(Command("wallet"))
async def command_wallet(message: Message, _: callable, state: FSMContext):
    """Handle /wallet command to display wallet info and options."""
    user_id = message.from_user.id
    
    # Check if user has a wallet
    wallet_address = await get_user_wallet(user_id)
    if not wallet_address or not await check_wallet_exists(wallet_address):
        await message.answer(
            _("no_wallet").format(command="/register"),
            parse_mode="HTML"
        )
        return
    
    # Get token balance
    balance = await get_token_balance(wallet_address)
    
    # Format wallet address for display (first 6 and last 4 chars)
    formatted_address = f"{wallet_address[:6]}...{wallet_address[-4:]}"
    
    # Send wallet info with options
    await message.answer(
        _("wallet_info").format(
            address=formatted_address,
            full_address=wallet_address,
            balance=balance
        ),
        reply_markup=get_wallet_menu_keyboard(_),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "wallet_deposit")
async def wallet_deposit(callback: CallbackQuery, _: callable):
    """Handle deposit option."""
    user_id = callback.from_user.id
    
    # Get user's wallet address
    wallet_address = await get_user_wallet(user_id)
    if not wallet_address:
        await callback.message.edit_text(_("no_wallet_found"))
        await callback.answer()
        return
    
    # Send deposit instructions
    await callback.message.edit_text(
        _("deposit_instructions").format(
            address=wallet_address,
            token_address=settings.TIP_TOKEN_ADDRESS
        ),
        parse_mode="HTML"
    )
    
    await callback.answer()

@router.callback_query(F.data == "wallet_withdraw")
async def wallet_withdraw(callback: CallbackQuery, _: callable, state: FSMContext):
    """Handle withdraw option."""
    user_id = callback.from_user.id
    
    # Get user's wallet address
    wallet_address = await get_user_wallet(user_id)
    if not wallet_address:
        await callback.message.edit_text(_("no_wallet_found"))
        await callback.answer()
        return
    
    # Get token balance
    balance = await get_token_balance(wallet_address)
    
    if balance <= 0:
        await callback.message.edit_text(_("insufficient_balance_withdraw").format(balance=balance))
        await callback.answer()
        return
    
    # Ask for destination address
    await callback.message.edit_text(
        _("withdraw_address_prompt"),
        parse_mode="HTML"
    )
    
    # Set state
    await state.set_state(WalletStates.waiting_for_withdraw_address)
    await state.update_data(balance=str(balance))
    
    await callback.answer()

@router.message(WalletStates.waiting_for_withdraw_address)
async def process_withdraw_address(message: Message, _: callable, state: FSMContext):
    """Process withdrawal destination address."""
    destination_address = message.text.strip()
    
    # Basic validation of address format
    if not destination_address.startswith("0x") or len(destination_address) != 42:
        await message.answer(_("invalid_address_format"))
        return
    
    # Save address to state
    await state.update_data(destination_address=destination_address)
    
    # Get balance from state
    data = await state.get_data()
    balance = data.get("balance")
    
    # Ask for amount
    await message.answer(
        _("withdraw_amount_prompt").format(
            balance=balance
        ),
        parse_mode="HTML"
    )
    
    # Update state
    await state.set_state(WalletStates.waiting_for_withdraw_amount)

@router.message(WalletStates.waiting_for_withdraw_amount)
async def process_withdraw_amount(message: Message, _: callable, state: FSMContext):
    """Process withdrawal amount."""
    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer(_("invalid_amount"))
        return
    
    # Get data from state
    data = await state.get_data()
    balance = float(data.get("balance", "0"))
    destination_address = data.get("destination_address")
    
    # Validate amount
    if amount <= 0:
        await message.answer(_("amount_must_be_positive"))
        return
    
    if amount > balance:
        await message.answer(_("insufficient_balance_withdraw").format(balance=balance))
        return
    
    # Save amount to state
    await state.update_data(amount=str(amount))
    
    # Ask for confirmation
    await message.answer(
        _("withdraw_confirmation").format(
            amount=amount,
            destination=destination_address
        ),
        reply_markup=get_withdraw_confirmation_keyboard(_),
        parse_mode="HTML"
    )
    
    # Update state
    await state.set_state(WalletStates.waiting_for_withdraw_confirmation)

@router.callback_query(F.data == "confirm_withdraw", WalletStates.waiting_for_withdraw_confirmation)
async def confirm_withdraw(callback: CallbackQuery, _: callable, state: FSMContext):
    """Handle withdrawal confirmation."""
    user_id = callback.from_user.id
    
    # Get data from state
    data = await state.get_data()
    amount = data.get("amount")
    destination_address = data.get("destination_address")
    
    # Show processing message
    await callback.message.edit_text(_("processing_withdraw"), reply_markup=None)
    
    try:
        # Get user's wallet
        wallet_address = await get_user_wallet(user_id)
        
        # Perform withdrawal (implementation in blockchain.py)
        from bot.services.blockchain import withdraw_tokens
        tx_hash = await withdraw_tokens(
            wallet_address=wallet_address,
            destination_address=destination_address,
            amount=float(amount)
        )
        
        # Save transaction to database
        from bot.services.database import save_transaction
        await save_transaction(
            sender_id=user_id,
            recipient_id=None,  # External withdrawal
            amount=float(amount),
            tx_hash=tx_hash,
            tx_type="withdraw"
        )
        
        # Send success message
        await callback.message.edit_text(
            _("withdraw_success").format(
                amount=amount,
                destination=destination_address,
                tx_hash=tx_hash
            ),
            parse_mode="HTML"
        )
    
    except Exception as e:
        logging.error(f"Error processing withdrawal for user {user_id}: {e}")
        await callback.message.edit_text(
            _("withdraw_error"),
            reply_markup=None
        )
    
    # Reset state
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "cancel_withdraw", WalletStates.waiting_for_withdraw_confirmation)
async def cancel_withdraw(callback: CallbackQuery, _: callable, state: FSMContext):
    """Handle withdrawal cancellation."""
    await callback.message.edit_text(
        _("withdraw_cancelled"),
        reply_markup=None
    )
    
    # Reset state
    await state.clear()
    await callback.answer()

def get_withdraw_confirmation_keyboard(_):
    """Create inline keyboard for withdrawal confirmation."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("confirm"), callback_data="confirm_withdraw"),
                InlineKeyboardButton(text=_("cancel"), callback_data="cancel_withdraw")
            ]
        ]
    )
    
    return keyboard
