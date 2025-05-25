from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import settings
from bot.utils.i18n import get_language_name

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Create a keyboard with language options."""
    keyboard = []
    
    # Create rows with 2 languages per row
    row = []
    for i, lang_code in enumerate(settings.AVAILABLE_LANGUAGES):
        lang_name = get_language_name(lang_code)
        row.append(InlineKeyboardButton(
            text=lang_name,
            callback_data=f"language_{lang_code}"
        ))
        
        # Add row after every 2 buttons
        if (i + 1) % 2 == 0 or i == len(settings.AVAILABLE_LANGUAGES) - 1:
            keyboard.append(row)
            row = []
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_start_keyboard(lang_code: str) -> InlineKeyboardMarkup:
    """Create keyboard for start menu."""
    from bot.utils.i18n import get_translation_for_language
    _ = get_translation_for_language(lang_code)
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("start_using_button"),
                callback_data="start_using"
            )
        ],
        [
            InlineKeyboardButton(
                text=_("change_language"),
                callback_data="change_language"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_wallet_menu_keyboard(_) -> InlineKeyboardMarkup:
    """Create wallet menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("deposit"),
                callback_data="wallet_deposit"
            ),
            InlineKeyboardButton(
                text=_("withdraw"),
                callback_data="wallet_withdraw"
            )
        ],
        [
            InlineKeyboardButton(
                text=_("refresh_balance"),
                callback_data="refresh_balance"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_tip_confirmation_keyboard(_) -> InlineKeyboardMarkup:
    """Create tip confirmation keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("confirm"),
                callback_data="confirm_tip"
            ),
            InlineKeyboardButton(
                text=_("cancel"),
                callback_data="cancel_tip"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_referral_keyboard(_, referral_link: str) -> InlineKeyboardMarkup:
    """Create referral keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("share_referral_link"),
                url=f"https://t.me/share/url?url={referral_link}&text={_('referral_share_text')}"
            )
        ],
        [
            InlineKeyboardButton(
                text=_("refresh_referrals"),
                callback_data="refresh_referrals"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
