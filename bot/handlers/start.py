import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from bot.services.database import create_user_if_not_exists, increment_referral_count
from bot.keyboards.inline import get_language_keyboard, get_start_keyboard
from bot.keyboards.reply import get_main_keyboard
from bot.utils.i18n import get_language_name

# Initialize router
router = Router()

@router.message(CommandStart())
async def command_start(message: Message, _: callable, state: FSMContext, user_lang: str):
    """Handle /start command and process referral if exists."""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Extract referral parameter if exists
    start_params = message.text.split(maxsplit=1)
    referrer_id = None
    if len(start_params) > 1:
        try:
            # Format: /start ref123456
            referrer_param = start_params[1]
            if referrer_param.startswith('ref'):
                referrer_id = int(referrer_param[3:])
                logging.info(f"User {user_id} joined with referral from {referrer_id}")
        except (ValueError, IndexError):
            pass
    
    # Create user in database if not exists
    user_created = await create_user_if_not_exists(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        language=user_lang,
        referrer_id=referrer_id
    )
    
    # Process referral if it's a new user
    if user_created and referrer_id:
        await increment_referral_count(referrer_id)
    
    # Send welcome message with language selection
    await message.answer(
        _("welcome_message").format(name=first_name or username or "there"),
        reply_markup=get_language_keyboard()
    )
    
    # Reset any active state
    await state.clear()

@router.callback_query(F.data.startswith("language_"))
async def select_language(callback: CallbackQuery, _: callable, state: FSMContext):
    """Handle language selection."""
    language = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    # Update user language in database
    from bot.services.database import update_user_language
    await update_user_language(user_id, language)
    
    # Get the updated translation function
    from bot.utils.i18n import get_translation_for_language
    new_translate = get_translation_for_language(language)
    
    # Show main onboarding message
    await callback.message.edit_text(
        new_translate("language_selected").format(
            language=get_language_name(language)
        ) + "\n\n" + new_translate("onboarding_message"),
        reply_markup=get_start_keyboard(language)
    )
    
    # Notify of success (don't show alert)
    await callback.answer()

@router.callback_query(F.data == "start_using")
async def start_using_bot(callback: CallbackQuery, _: callable):
    """Handle the 'Start Using' button click."""
    # Show main menu with reply keyboard
    await callback.message.edit_text(
        _("start_using_message"),
        reply_markup=None
    )
    
    await callback.message.answer(
        _("main_menu_message"),
        reply_markup=get_main_keyboard(_)
    )
    
    await callback.answer()
