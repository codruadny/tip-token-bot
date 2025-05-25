import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services.blockchain import create_wallet, check_wallet_exists
from bot.services.database import update_user_wallet, get_user_wallet

# Initialize router
router = Router()

# Define FSM states
class RegistrationStates(StatesGroup):
    waiting_for_confirmation = State()

@router.message(Command("register"))
async def command_register(message: Message, _: callable, state: FSMContext):
    """Handle /register command to create a new wallet."""
    user_id = message.from_user.id
    
    # Check if user already has a wallet
    existing_wallet = await get_user_wallet(user_id)
    if existing_wallet and await check_wallet_exists(existing_wallet):
        await message.answer(_("wallet_already_exists"))
        return
    
    # Ask for confirmation
    await message.answer(
        _("register_confirmation"),
        reply_markup=get_registration_confirmation_keyboard(_)
    )
    
    # Set state
    await state.set_state(RegistrationStates.waiting_for_confirmation)

@router.callback_query(F.data == "confirm_registration", RegistrationStates.waiting_for_confirmation)
async def confirm_registration(callback: CallbackQuery, _: callable, state: FSMContext):
    """Handle registration confirmation."""
    user_id = callback.from_user.id
    
    # Show processing message
    await callback.message.edit_text(_("creating_wallet"), reply_markup=None)
    
    try:
        # Create a new wallet
        wallet_address, private_key = await create_wallet()
        
        # Store wallet address in database (private key is encrypted and stored)
        await update_user_wallet(user_id, wallet_address, private_key)
        
        # Send success message
        success_text = _("wallet_created").format(
            address=wallet_address
        )
        
        # Add warning about private key
        success_text += "\n\n" + _("private_key_warning")
        
        await callback.message.edit_text(
            success_text,
            reply_markup=None,
            parse_mode="HTML"
        )
        
        # Reset state
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error creating wallet for user {user_id}: {e}")
        await callback.message.edit_text(
            _("wallet_creation_error"),
            reply_markup=None
        )
        await state.clear()
    
    await callback.answer()

@router.callback_query(F.data == "cancel_registration", RegistrationStates.waiting_for_confirmation)
async def cancel_registration(callback: CallbackQuery, _: callable, state: FSMContext):
    """Handle registration cancellation."""
    await callback.message.edit_text(
        _("registration_cancelled"),
        reply_markup=None
    )
    
    # Reset state
    await state.clear()
    
    await callback.answer()

def get_registration_confirmation_keyboard(_):
    """Create inline keyboard for registration confirmation."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("confirm"), callback_data="confirm_registration"),
                InlineKeyboardButton(text=_("cancel"), callback_data="cancel_registration")
            ]
        ]
    )
    
    return keyboard
