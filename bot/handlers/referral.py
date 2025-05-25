from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.services.database import get_user_referrals, get_user_by_id
from bot.keyboards.inline import get_referral_keyboard

# Initialize router
router = Router()

@router.message(Command("referral"))
async def command_referral(message: Message, _: callable):
    """Handle /referral command to show referral info."""
    user_id = message.from_user.id
    bot_username = (await message.bot.get_me()).username
    
    # Generate referral link
    referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    
    # Get referral stats
    referral_count, referral_users = await get_user_referrals(user_id)
    
    # Create referral message
    referral_message = _("referral_info").format(
        link=referral_link,
        count=referral_count,
        bonus=referral_count * 10  # 10 TIP per referral
    )
    
    # Add referral list if there are any
    if referral_count > 0:
        referral_list = "\n\n" + _("referral_list") + "\n"
        for i, ref_id in enumerate(referral_users, 1):
            user_data = await get_user_by_id(ref_id)
            if user_data:
                username = user_data.get("username", "")
                name = user_data.get("first_name", "")
                display_name = f"@{username}" if username else name or f"User {ref_id}"
                referral_list += f"{i}. {display_name}\n"
        
        referral_message += referral_list
    
    # Send message with inline keyboard
    await message.answer(
        referral_message,
        reply_markup=get_referral_keyboard(_, referral_link),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

@router.callback_query(F.data == "refresh_referrals")
async def refresh_referrals(callback: CallbackQuery, _: callable):
    """Handle referral stats refresh."""
    user_id = callback.from_user.id
    bot_username = (await callback.bot.get_me()).username
    
    # Generate referral link
    referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    
    # Get updated referral stats
    referral_count, referral_users = await get_user_referrals(user_id)
    
    # Create updated referral message
    referral_message = _("referral_info").format(
        link=referral_link,
        count=referral_count,
        bonus=referral_count * 10  # 10 TIP per referral
    )
    
    # Add referral list if there are any
    if referral_count > 0:
        referral_list = "\n\n" + _("referral_list") + "\n"
        for i, ref_id in enumerate(referral_users, 1):
            user_data = await get_user_by_id(ref_id)
            if user_data:
                username = user_data.get("username", "")
                name = user_data.get("first_name", "")
                display_name = f"@{username}" if username else name or f"User {ref_id}"
                referral_list += f"{i}. {display_name}\n"
        
        referral_message += referral_list
    
    # Update message with new data
    await callback.message.edit_text(
        referral_message,
        reply_markup=get_referral_keyboard(_, referral_link),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    await callback.answer(_("referrals_refreshed"))
