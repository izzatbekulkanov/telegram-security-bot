import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import settings
from src.database.models import init_db, engine
from src.handlers.bot_handler import router as bot_router
from src.handlers.admin_handler import router as admin_router
from src.handlers.admin_actions import router as admin_actions_router
from src.handlers.channel_handler import router as channel_router
from src.utils.logger import logger

async def main():
    try:
        await init_db()
        logger.info("Ma'lumotlar bazasi muvaffaqiyatli yuklandi.")
    except Exception as e:
        logger.error(f"Bazani yuklashda xatolik: {e}")
        return

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Routerlarni ulash
    dp.include_router(admin_actions_router) # Callbacklar va yangi admin buyruqlar
    dp.include_router(channel_router)       # Kanal kuzatuvchisi
    dp.include_router(admin_router)         # Eski admin buyruqlar
    dp.include_router(bot_router)           # Bot asosiy logikasi

    logger.info("Bot polling rejimida ishga tushdi...")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logger.info("Bot to'xtatilmoqda...")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {e}")
    finally:
        logger.info("Sessiyalar yopilmoqda...")
        await bot.session.close()
        await engine.dispose()
        logger.info("Bot butunlay to'xtatildi.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)