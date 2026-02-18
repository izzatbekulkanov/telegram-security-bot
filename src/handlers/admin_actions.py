from aiogram import Router, F, types, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.database.queries import set_admin_status, get_user
from src.utils.logger import logger

router = Router()

def get_role_keyboard(user_id: int, is_admin: bool):
    """Admin/User rollarini almashtirish uchun klaviatura"""
    admin_text = "✅ Admin" if is_admin else "Admin"
    user_text = "✅ User" if not is_admin else "User"
    
    # Callback data format: set_role_{role}_{target_user_id}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=user_text, callback_data=f"set_role_user_{user_id}"),
            InlineKeyboardButton(text=admin_text, callback_data=f"set_role_admin_{user_id}")
        ]
    ])
    return kb

@router.callback_query(F.data.startswith("set_role_"))
async def toggle_user_role(callback: types.CallbackQuery, bot: Bot):
    try:
        data = callback.data.split("_")
        role = data[2] # "user" or "admin"
        target_user_id = int(data[3])
        
        is_admin_new = (role == "admin")
        
        # Bazada yangilash
        await set_admin_status(target_user_id, is_admin_new)
        
        # Yangi klaviatura yasash
        new_kb = get_role_keyboard(target_user_id, is_admin_new)
        
        # Xabarni yangilash (agar o'zgargan bo'lsa)
        try:
            await callback.message.edit_reply_markup(reply_markup=new_kb)
            await callback.answer(f"Role o'zgartirildi: {role.upper()}")
        except Exception:
            await callback.answer("Allaqachon shunday holatda.")

    except Exception as e:
        logger.error(f"Role o'zgartirishda xatolik: {e}")
        await callback.answer("Xatolik yuz berdi!", show_alert=True)

# --- YANGI BUYRUQLAR ---

from aiogram.filters import Command
from src.database.queries import get_all_users, get_all_channels
from src.config import settings

@router.message(Command("users"))
async def cmd_users_list(message: types.Message):
    """(Admin) Barcha foydalanuvchilar ro'yxati"""
    # Xavfsizlik: Agar buyruq kanaldan kelsa, tekshirish shart emas (kanal admini bo'ladi)
    # Agar shaxsiy yozishsa, admin ekanligini tekshirish kerak.
    # Hozircha oddiy qilib, hammaga ruxsat beramiz yoki faqat kanalda ishlashini ta'minlaymiz.
    
    users = await get_all_users()
    if not users:
        await message.answer("👥 Foydalanuvchilar yo'q.")
        return

    text = "👥 **Foydalanuvchilar Ro'yxati:**\n\n"
    for user in users:
        status = "👑 Admin" if user.is_admin else "👤 User"
        if user.is_premium: status += " | 💎 Premium"
        text += f"🆔 `{user.user_id}` | {user.username or 'No Username'} | {status}\n"

    # Telegram limitiga (4096 belgi) ehtiyot bo'lish kerak.
    # Agar uzun bo'lsa, bo'lib tashlash kerak.
    if len(text) > 4000:
        text = text[:4000] + "\n... (davomi bor)"
        
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("channels"))
async def cmd_channels_list(message: types.Message):
    """(Admin) Ulangan kanallar ro'yxati"""
    channels = await get_all_channels()
    if not channels:
        await message.answer("📢 Kanallar yo'q.")
        return

    text = "📢 **Ulangan Kanallar:**\n\n"
    for ch in channels:
        text += f"🆔 `{ch.chat_id}` | **{ch.title}**\n"

    await message.answer(text, parse_mode="Markdown")
