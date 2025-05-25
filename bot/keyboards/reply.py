from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard(_) -> ReplyKeyboardMarkup:
    """Create main reply keyboard."""
    keyboard = [
        [
            KeyboardButton(text=_("balance_button")),
            KeyboardButton(text=_("wallet_button"))
        ],
        [
            KeyboardButton(text=_("tip_button")),
            KeyboardButton(text=_("referral_button"))
        ],
        [
            KeyboardButton(text=_("transactions_button")),
            KeyboardButton(text=_("help_button"))
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=_("select_action")
    )

def get_help_keyboard(_) -> ReplyKeyboardMarkup:
    """Create help reply keyboard."""
    keyboard = [
        [
            KeyboardButton(text=_("balance_button")),
            KeyboardButton(text=_("wallet_button"))
        ],
        [
            KeyboardButton(text=_("tip_button")),
            KeyboardButton(text=_("referral_button"))
        ],
        [
            KeyboardButton(text=_("back_button"))
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=_("select_action")
    )
