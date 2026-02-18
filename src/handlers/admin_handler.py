from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.config import settings
from src.database.queries import get_user, get_all_users_count, search_user_by_username, set_admin_status

router = Router()


class AdminStates(StatesGroup):
    waiting_for_username = State()


# --- ADMIN TEKSHIRUVI (O'ZGARTIRILDI) ---
async def is_admin(user: types.User):
    """
    Foydalanuvchini admin ekanligini tekshiradi.
    1. Configdagi IDlar
    2. Bazadagi adminlar
    3. MAXSUS: @izzatbekulkanov (Doimiy Admin)
    """
    # 1. Username orqali (Siz so'ragan qism)
    if user.username and user.username.lower() == "izzatbekulkanov":
        return True

    # 2. Configdagi asosiy adminlar (ID orqali)
    if user.id in settings.ADMINS:
        return True

    # 3. Bazadagi tayinlangan adminlar
    db_user = await get_user(user.id, user.username)
    return db_user.is_admin


@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    # Tekshiruvga message.from_user (to'liq obyekt) ni beramiz
    if not await is_admin(message.from_user):
        return  # Agar admin bo'lmasa, jim turadi

    count = await get_all_users_count()

    text = (
        f"🕵️‍♂️ **KIBER-XAVFSIZLIK MARKAZI (Admin Panel)**\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"👑 **Super Admin:** @izzatbekulkanov\n"
        f"📊 **Jami Agentlar (Users):** {count} ta\n"
        f"⚙️ **Tizim holati:** Barqaror\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"Quyidagi amallardan birini tanlang:"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Foydalanuvchi qidirish", callback_data="admin_search")],
        [InlineKeyboardButton(text="📊 Statistika (To'liq)", callback_data="admin_stats")],
        [InlineKeyboardButton(text="❌ Yopish", callback_data="admin_close")]
    ])

    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == "admin_search")
async def start_search(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔍 **QIDIRUV REJIMI**\n\n"
        "Foydalanuvchi **@username** ni yuboring.\n"
        "Misol: `@shahboz_ulkanov`",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_for_username)


@router.message(AdminStates.waiting_for_username)
async def process_search(message: types.Message, state: FSMContext):
    username = message.text.strip()

    wait_msg = await message.answer(f"📡 **Ma'lumotlar bazasidan qidirilmoqda:** `{username}`...")

    user = await search_user_by_username(username)

    if not user:
        await wait_msg.edit_text("❌ **Foydalanuvchi topilmadi.**\nU botdan foydalanmagan bo'lishi mumkin.")
        await state.clear()
        return

    # Foydalanuvchi topildi
    status = "👑 ADMIN" if user.is_admin else "👤 Foydalanuvchi"
    if user.username and user.username.lower() == "izzatbekulkanov":
        status = "👑 SUPER ADMIN (Doimiy)"

    premium = "✅ VIP" if user.is_premium else "❌ Oddiy"

    text = (
        f"📂 **DOSYE TOPILDI**\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"🆔 ID: `{user.user_id}`\n"
        f"👤 Username: @{user.username}\n"
        f"🛡 Status: {status}\n"
        f"💎 Premium: {premium}\n"
        f"📅 Qo'shilgan: {user.joined_at.strftime('%Y-%m-%d')}\n"
        f"➖➖➖➖➖➖➖➖"
    )

    # Adminlik berish/olish tugmasi
    buttons = []

    # IzzatbekUlkanovni adminlikdan olib bo'lmaydi
    is_super_admin = user.username and user.username.lower() == "izzatbekulkanov"

    if not is_super_admin:
        btn_text = "⬇️ Adminlikdan olish" if user.is_admin else "⬆️ Admin qilish"
        callback_data = f"toggle_admin_{user.user_id}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=callback_data)])

    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await wait_msg.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await state.clear()


@router.callback_query(F.data.startswith("toggle_admin_"))
async def toggle_admin_rights(callback: types.CallbackQuery):
    target_id = int(callback.data.split("_")[2])

    # O'zini o'zi yoki Configdagi adminlarni o'zgartirib bo'lmaydi
    if target_id in settings.ADMINS:
        await callback.answer("⚠️ Asosiy admin huquqini o'zgartirib bo'lmaydi!", show_alert=True)
        return

    user = await get_user(target_id)
    new_status = not user.is_admin

    await set_admin_status(target_id, new_status)

    status_text = "👑 Admin qilindi" if new_status else "⬇️ Adminlikdan olindi"
    await callback.answer(f"✅ Muvaffaqiyatli: {status_text}", show_alert=True)

    await callback.message.delete()
    await callback.message.answer(f"✅ Foydalanuvchi {target_id} uchun o'zgarish kiritildi: **{status_text}**",
                                  parse_mode="Markdown")


@router.callback_query(F.data == "admin_close")
async def close_panel(callback: types.CallbackQuery):
    await callback.message.delete()


@router.callback_query(F.data == "back_to_admin")
async def back_to_main(callback: types.CallbackQuery):
    await cmd_admin(callback.message)