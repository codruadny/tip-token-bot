from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.keyboards.reply import get_help_keyboard

# Initialize router
router = Router()

@router.message(Command("help"))
async def command_help(message: Message, _: callable):
    """Handle /help command and show available commands."""
    help_text = _(
        "help_message"
    ) + "\n\n" + _(
        "help_commands"
    ).format(
        start_cmd="/start - " + _("help_start"),
        help_cmd="/help - " + _("help_help"),
        register_cmd="/register - " + _("help_register"),
        tip_cmd="/tip - " + _("help_tip"),
        wallet_cmd="/wallet - " + _("help_wallet"),
        balance_cmd="/balance - " + _("help_balance"),
        referral_cmd="/referral - " + _("help_referral"),
        transactions_cmd="/transactions - " + _("help_transactions")
    )
    
    await message.answer(
        help_text,
        reply_markup=get_help_keyboard(_),
        parse_mode="HTML"
    )
