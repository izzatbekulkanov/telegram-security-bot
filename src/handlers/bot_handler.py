import os
import time
import asyncio
import random
import aiohttp
from concurrent.futures import ProcessPoolExecutor  # <--- Parallel ishlash uchun

from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from src.config import settings
from src.database.queries import get_user, increment_check, set_premium, set_language
from src.services.analyzer import SecurityAnalyzer
from src.utils.locales import TEXTS

router = Router()

# ⚡️ CPU-og'ir vazifalar uchun alohida jarayonlar hovuzi (3 ta parallel tahlil)
process_pool = ProcessPoolExecutor(max_workers=3)


# --- YORDAMCHI FUNKSIYALAR ---

def get_text(lang, key):
    lang = lang if lang in TEXTS else "uz"
    return TEXTS[lang].get(key, "Text error")


def get_cyber_log(percent):
    """Fayl yuklanayotganda chiqadigan 'xakerlik' loglari"""
    logs = [
        f"[INFO] Verifying packet integrity... {random.randint(100, 999)}ms",
        "[WARN] Encrypted segment detected, decryption initiated...",
        f"[AI] Neural Network Activated (Nodes: {random.randint(50, 200)})",
        "[NET] Receiving bytes via Secure Gateway...",
        f"[MEM] Buffer memory flushed... {random.randint(10, 50)}MB",
        "[SEC] Comparing against Virus Signature Database...",
    ]
    if percent < 20:
        return "🚀 Establishing secure channel..."
    elif percent > 90:
        return "✅ Finalizing data assembly..."
    else:
        return random.choice(logs)


# --- COMMAND HANDLERS ---

@router.message(CommandStart())
async def cmd_start(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    # Username ni bazaga saqlash/yangilash
    user = await get_user(user_id, message.from_user.username)

    # Agar foydalanuvchi yangi bo'lsa (check_count=0) va Configda kanal sozlangan bo'lsa
    # Yoki har doim start bosganda log bormasin, faqat birinchi marta.
    # Lekin get_user har doim user qaytaradi (yaratib yoki olib).
    # Biz queries.py da get_user funksiyasini o'zgartirmadik, u userni qaytaradi.
    # Keling, oddiylik uchun har doim log qilmaymiz, faqat yangi qo'shilganda.
    # Buning uchun get_user da "created" flag qaytish kerak edi, lekin hozir u yo'q.
    # Mayli, hozircha har bir /start bosilganda log qilamiz (agar admin bo'lsa o'zi biladi).
    # Yoki check_count == 0 bo'lsa yangi deb hisoblaymiz.

    # 1. Configdan olish
    log_channel_id = settings.LOG_CHANNEL_ID
    
    # 2. Agar configda bo'lmasa, bazadan olish
    if not log_channel_id:
        from src.database.queries import get_log_channel_id
        log_channel_id = await get_log_channel_id()

    if user.check_count == 0 and log_channel_id:
        # Kanalga xabar yuborish
        from src.handlers.admin_actions import get_role_keyboard
        
        log_text = (
            f"🆕 **Yangi Foydalanuvchi!**\n\n"
            f"👤 Ism: {message.from_user.full_name}\n"
            f"🆔 ID: `{user_id}`\n"
            f"🔗 Username: @{message.from_user.username}\n"
            f"📅 Vaqt: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        try:
            await bot.send_message(
                chat_id=log_channel_id,
                text=log_text,
                reply_markup=get_role_keyboard(user_id, user.is_admin),
                parse_mode="Markdown"
            )
        except Exception as e:
            # Agar bot kanalga a'zo bo'lmasa yoki xato bo'lsa
            print(f"Log yuborishda xato: {e}")

    if not user.language:
        # Til tanlash menyusi
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
        ])
        await message.answer(TEXTS["uz"]["ask_lang"], reply_markup=kb)
        return

    await message.answer(
        get_text(user.language, "welcome"),
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )


@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    """Foydalanuvchi profilini va statusini ko'rsatish"""
    user_id = message.from_user.id
    user = await get_user(user_id, message.from_user.username)
    lang = user.language if user.language else "uz"

    # Statusni aniqlash
    status_text = get_text(lang, "premium_yes") if user.is_premium else get_text(lang, "premium_no")

    # Tekshiruvlar soni
    scan_info = f"{user.check_count}"
    if not user.is_premium:
        scan_info += "/10"
    else:
        scan_info += " (∞)"

    # Profil matni
    profile_text = (
        f"{get_text(lang, 'profile_header')}\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"{get_text(lang, 'id')} `{user.user_id}`\n"
        f"{get_text(lang, 'status')} {status_text}\n"
        f"{get_text(lang, 'scans')} {scan_info}\n"
        f"{get_text(lang, 'lang')} {lang.upper()}\n"
        f"➖➖➖➖➖➖➖➖"
    )

    # Tugmalar (Tilni o'zgartirish + Premium olish)
    buttons = []
    buttons.append([InlineKeyboardButton(text=get_text(lang, "change_lang_btn"), callback_data="change_lang_cmd")])

    if not user.is_premium:
        buttons.append([InlineKeyboardButton(text=get_text(lang, "pay_btn"), callback_data="buy_premium")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(profile_text, reply_markup=kb, parse_mode="Markdown")


@router.message(Command("lang"))
async def cmd_lang(message: types.Message):
    """Tilni o'zgartirish buyrug'i"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    await message.answer("🌐 Select Language / Tilni tanlang:", reply_markup=kb)


# --- CALLBACK HANDLERS ---

@router.callback_query(F.data == "change_lang_cmd")
async def callback_lang_switch(callback: CallbackQuery):
    """Profil ichidagi 'Tilni o'zgartirish' tugmasi bosilganda"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    await callback.message.edit_text("🌐 Select Language / Tilni tanlang:", reply_markup=kb)


@router.callback_query(F.data == "buy_premium")
async def callback_buy_premium(callback: CallbackQuery):
    """Profil ichidagi 'Premium sotib olish' tugmasi bosilganda"""
    user_id = callback.from_user.id
    # Callbackda message obyektiga to'g'ridan to'g'ri murojaat qilinmaydi, callback.from_user ishlatiladi
    user = await get_user(user_id, callback.from_user.username)
    lang = user.language if user.language else "uz"

    # Invoice yuborish
    await send_payment_invoice(callback.message, lang)
    await callback.answer()


@router.callback_query(F.data.startswith("lang_"))
async def language_selection(callback: CallbackQuery):
    """Til tanlanganda ishlaydi"""
    lang_code = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # Bazaga yozamiz
    await set_language(user_id, lang_code)

    # Xabarni o'zgartiramiz
    await callback.message.delete()
    await callback.message.answer(
        get_text(lang_code, "lang_updated"),
        parse_mode="Markdown"
    )
    # Darhol welcome xabarni ham chiqarib beramiz
    await callback.message.answer(
        get_text(lang_code, "welcome"),
        parse_mode="Markdown"
    )


# --- TO'LOV VA FAYL HANDLERLARI ---

async def send_payment_invoice(message: types.Message, lang):
    """To'lov chekini yuborish"""
    await message.answer_invoice(
        title=get_text(lang, "payment_title"),
        description=get_text(lang, "payment_desc"),
        payload="premium_access_payload",
        provider_token=settings.PAYMENT_PROVIDER_TOKEN,
        currency="UZS",
        prices=[LabeledPrice(label="Premium Access", amount=1000000)],  # 10 000 so'm
        start_parameter="premium-access",
        photo_url="https://cdn-icons-png.flaticon.com/512/2092/2092663.png",
        photo_height=512, photo_width=512, photo_size=512
    )


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id, message.from_user.username)
    await set_premium(user_id)
    await message.answer(get_text(user.language, "success"), parse_mode="Markdown")


# --- HAVOLA (URL) TEKSHIRUVI ---

@router.message(F.text.regexp(r'https?://[^\s]+'))
async def handle_link_check(message: types.Message):
    """Havolalarni tekshirish (Tezkor)"""
    user_id = message.from_user.id
    user = await get_user(user_id, message.from_user.username)
    lang = user.language if user.language else "uz"

    # Limit tekshiruvi
    if user.check_count >= 10 and not user.is_premium:
        await message.answer(get_text(lang, "limit_reached"), parse_mode="Markdown")
        await send_payment_invoice(message, lang)
        return

    url = message.text.strip()
    status_msg = await message.answer("🔍 " + get_text(lang, "analyzing"), parse_mode="Markdown")

    # Asinxron URL tahlili (Juda tez ishlaydi)
    report = await SecurityAnalyzer.analyze_url(url)

    await status_msg.edit_text(report, parse_mode="Markdown")
    await increment_check(user_id)


# --- APK FAYL TEKSHIRUVI (OPTIMALLASHTIRILGAN) ---

@router.message(F.document.file_name.endswith(".apk"))
async def handle_apk(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    user = await get_user(user_id, message.from_user.username)
    lang = user.language if user.language else "uz"

    # 1. LIMIT TEKSHIRUVI
    if user.check_count >= 10 and not user.is_premium:
        await message.answer(get_text(lang, "limit_reached"), parse_mode="Markdown")
        await send_payment_invoice(message, lang)
        return

    # 2. Jarayon boshlanishi
    status_msg = await message.answer(get_text(lang, "start_system"))

    start_time = time.time()
    last_update_time = 0
    file_id = message.document.file_id
    file_name = message.document.file_name
    file_size = message.document.file_size

    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/{user_id}_{file_name}"

    try:
        file_info = await bot.get_file(file_id)
        custom_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

        async with aiohttp.ClientSession() as session:
            async with session.get(custom_url) as response:
                if response.status != 200: raise Exception("Connection Error")

                with open(file_path, 'wb') as f:
                    downloaded = 0
                    chunk_start_time = time.time()

                    async for chunk in response.content.iter_chunked(1024 * 1024):
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = int(downloaded / file_size * 100) if file_size > 0 else 0
                        current_time = time.time()

                        if current_time - last_update_time > 2.0 or percent == 100:
                            time_diff = current_time - chunk_start_time
                            speed = (len(chunk) / 1024 / 1024) / time_diff if time_diff > 0 else 0
                            chunk_start_time = current_time
                            last_update_time = current_time

                            bar = '▰' * int(12 * percent // 100) + '▱' * (12 - int(12 * percent // 100))

                            dashboard = (
                                f"🛡 **CYBER-GUARD AI v3.0**\n"
                                f"➖➖➖➖➖➖➖➖➖➖\n"
                                f"📂 **File:** `{file_name[:15]}...`\n"
                                f"📥 **Status:** `{bar}` {percent}%\n"
                                f"⚡️ **Speed:** {speed:.1f} MB/s\n"
                                f"💾 **Size:** {downloaded // 1024 // 1024}MB / {file_size // 1024 // 1024}MB\n"
                                f"➖➖➖➖➖➖➖➖➖➖\n"
                                f"🖥 **TERMINAL:**\n`> {get_cyber_log(percent)}`"
                            )
                            try:
                                await status_msg.edit_text(dashboard, parse_mode="Markdown")
                            except TelegramBadRequest:
                                pass

        # 5. AI Tahlil (Optimallashtirilgan)
        await status_msg.edit_text(get_text(lang, "analyzing"), parse_mode="Markdown")

        # ⚡️ MUHIM: ProcessPoolExecutor orqali alohida yadroda ishlatamiz
        loop = asyncio.get_event_loop()
        report = await loop.run_in_executor(process_pool, SecurityAnalyzer.analyze_apk, file_path)

        total_time = round(time.time() - start_time, 1)
        time_text = f"\n⏱ Process time: {total_time}s"

        await status_msg.edit_text(report + time_text, parse_mode="Markdown")
        await increment_check(user_id)

    except Exception as e:
        await status_msg.edit_text(f"❌ **System Error:** {str(e)}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)