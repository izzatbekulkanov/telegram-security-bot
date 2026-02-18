import logging
from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError
from src.database.models import User, Channel, async_session

# --- AI LOGGER SOZLAMALARI ---
# Bu logger xuddi server terminali kabi ishlaydi
logger = logging.getLogger("NeuralMemory")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


async def get_user(user_id: int, username: str = None):
    """Foydalanuvchini olish va usernameni yangilash"""
    async with async_session() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                user_id=user_id,
                username=username,  # Usernameni saqlaymiz
                check_count=0,
                is_premium=False
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # Agar username o'zgargan bo'lsa, yangilaymiz
            if user.username != username:
                user.username = username
                await session.commit()

        return user


async def increment_check(user_id: int):
    """
    Tranzaksiya: Tekshiruvlar hisoblagichini neyron tarmoqda yangilash.
    """
    try:
        async with async_session() as session:
            # Atomic update (bu eng tezkor va xavfsiz usul)
            stmt = update(User).where(User.user_id == user_id). \
                values(check_count=User.check_count + 1)

            await session.execute(stmt)
            await session.commit()

            logger.info(f"📈 [UPDATE] Hisoblagich oshirildi. User: {user_id}")

    except Exception as e:
        logger.error(f"⚠️ [SYNC_ERROR] Hisoblagichni yangilashda xato: {e}")


async def set_premium(user_id: int):
    async with async_session() as session:
        stmt = update(User).where(User.user_id == user_id).values(is_premium=True)
        await session.execute(stmt)
        await session.commit()

async def get_all_users_count():
    """Jami foydalanuvchilar soni"""
    async with async_session() as session:
        stmt = select(func.count(User.id))
        result = await session.execute(stmt)
        return result.scalar()

async def search_user_by_username(username: str):
    """Username orqali qidirish (Admin uchun)"""
    # @ belgisini olib tashlaymiz
    clean_username = username.replace("@", "")
    async with async_session() as session:
        stmt = select(User).where(User.username == clean_username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def set_admin_status(user_id: int, is_admin: bool):
    """Foydalanuvchiga adminlik berish yoki olish"""
    async with async_session() as session:
        stmt = update(User).where(User.user_id == user_id).values(is_admin=is_admin)
        await session.execute(stmt)
        await session.commit()
        logger.info(f"👮‍♂️ [ADMIN] User {user_id} admin statusi: {is_admin}")



# --- QO'SHIMCHA AI FUNKSIYASI ---

async def analyze_user_activity(user_id: int):
    """
    Foydalanuvchi haqida qisqacha 'Dosye' tayyorlaydi.
    Buni bot ichida admin panel yoki profil uchun ishlatsa bo'ladi.
    """
    user = await get_user(user_id)

    trust_level = "🟢 Ishonchli"
    if user.check_count > 100:
        trust_level = "👑 Elita"
    elif user.check_count < 5:
        trust_level = "⚪️ Yangi"

    return {
        "id": user.user_id,
        "total_scans": user.check_count,
        "status": "Premium 💎" if user.is_premium else "Bepul 👤",
        "trust_score": trust_level
    }

async def set_language(user_id: int, lang_code: str):
    """Foydalanuvchi tilini saqlash"""
    async with async_session() as session:
        stmt = update(User).where(User.user_id == user_id).values(language=lang_code)
        await session.execute(stmt)
        await session.commit()

async def increment_check(user_id: int):
    async with async_session() as session:
        stmt = update(User).where(User.user_id == user_id).values(check_count=User.check_count + 1)
        await session.execute(stmt)
        await session.commit()

async def get_all_users():
    """Barcha foydalanuvchilarni olish"""
    async with async_session() as session:
        stmt = select(User).order_by(User.joined_at.desc())
        result = await session.execute(stmt)
        return result.scalars().all()

# --- CHANNEL QUERIES ---

async def add_channel(chat_id: int, title: str):
    """Kanalni bazaga qo'shish"""
    async with async_session() as session:
        stmt = select(Channel).where(Channel.chat_id == chat_id)
        result = await session.execute(stmt)
        channel = result.scalar_one_or_none()

        if not channel:
            channel = Channel(chat_id=chat_id, title=title)
            session.add(channel)
            await session.commit()
            logger.info(f"📢 [CHANNEL] Yangi kanal qo'shildi: {title} ({chat_id})")
        else:
            # Nomini yangilaymiz
            if channel.title != title:
                channel.title = title
                await session.commit()

async def remove_channel(chat_id: int):
    """Kanalni bazadan o'chirish"""
    async with async_session() as session:
        stmt = select(Channel).where(Channel.chat_id == chat_id)
        result = await session.execute(stmt)
        channel = result.scalar_one_or_none()

        if channel:
            await session.delete(channel)
            await session.commit()
            logger.info(f"🗑 [CHANNEL] Kanal o'chirildi: {chat_id}")

async def get_all_channels():
    """Barcha kanallarni olish"""
    async with async_session() as session:
        stmt = select(Channel).order_by(Channel.added_at.desc())
        result = await session.execute(stmt)
        return result.scalars().all()

async def set_log_channel(chat_id: int):
    """Bitta kanalni log uchun belgilash (boshqalarini o'chirish)"""
    async with async_session() as session:
        # 1. Barcha kanallardan log statusini olib tashlash
        await session.execute(update(Channel).values(is_log_channel=False))
        
        # 2. Tanlangan kanalni log qilib belgilash
        stmt = update(Channel).where(Channel.chat_id == chat_id).values(is_log_channel=True)
        result = await session.execute(stmt)
        
        await session.commit()
        
        if result.rowcount == 0:
            # Kanal bazada yo'q edi, uni qo'shish kerak (lekin nomini bilmaymiz)
            # Bu holatda avval add_channel chaqirilgan bo'lishi kerak.
            # Yoki bu funksiyani chaqirishdan oldin add_channel chaqiramiz.
            return False 
        return True

async def get_log_channel_id():
    """Log kanal ID sini olish"""
    async with async_session() as session:
        stmt = select(Channel.chat_id).where(Channel.is_log_channel == True)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()