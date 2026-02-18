from aiogram import Router, F, types
from aiogram.filters import ChatMemberUpdatedFilter, KICKED, MEMBER, ADMINISTRATOR, LEFT, RESTRICTED, CREATOR
from src.database.queries import add_channel, remove_channel
from src.utils.logger import logger

router = Router()

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR))
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def on_channel_join(event: types.ChatMemberUpdated):
    """Bot kanalga qo'shilganda yoki admin qilinganda"""
    if event.chat.type in ["channel", "supergroup"]:
        await add_channel(event.chat.id, event.chat.title)
        logger.info(f"📢 Bot yangi kanalga qo'shildi: {event.chat.title}")

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=LEFT))
async def on_channel_leave(event: types.ChatMemberUpdated):
    """Bot kanaldan chiqarilganda"""
    await remove_channel(event.chat.id)
    logger.info(f"🗑 Bot kanaldan chiqarildi: {event.chat.title}")

from aiogram.filters import Command
from src.database.queries import set_log_channel, add_channel

@router.message(Command("setlog"))
async def cmd_set_log(message: types.Message):
    """Kanalni loglar uchun belgilash"""
    if message.chat.type not in ["channel", "supergroup"]:
        await message.answer("⚠️ Bu buyruq faqat kanallarda ishlatiladi.")
        return

    # Kanalni bazaga qo'shish (ehtiyot shart)
    await add_channel(message.chat.id, message.chat.title)
    
    # Log kanal qilib belgilash
    success = await set_log_channel(message.chat.id)
    
    if success:
        await message.answer(f"✅ **{message.chat.title}** muvaffaqiyatli loglar kanali sifatida o'rnatildi!")
    else:
        await message.answer("❌ Xatolik yuz berdi.")

@router.channel_post()
async def on_channel_post(message: types.Message):
    """Kanalda xabar yozilganda uni bazaga saqlash (Topilmay qolishini oldini olish)"""
    # Agar bot kanalda admin bo'lsa, u postlarni ko'radi.
    # Har bir postda kanalni bazaga yangilab qo'yamiz/qo'shamiz.
    await add_channel(message.chat.id, message.chat.title)
