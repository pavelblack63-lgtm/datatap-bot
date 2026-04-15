import asyncio
import logging
import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from src.config import settings
from src.utils.logger import setup_logger
from src.database.session import init_db
from src.handlers import start, tap, profile, upgrades
from src.middlewares.throttling import ThrottlingMiddleware
from src.middlewares.user_middleware import UserMiddleware
from src.services.passive_income import passive_income_worker

logger = setup_logger("datatap.main")
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


async def on_startup(dp: Dispatcher, bot: Bot):
    logger.info("🚀 DataTap Bot starting up...")
    await init_db()
    logger.info("✅ Database initialized")

    asyncio.create_task(passive_income_worker(interval_sec=60))
    logger.info("📈 Passive income worker launched")


async def on_shutdown(dp: Dispatcher, bot: Bot):
    logger.info("🛑 DataTap Bot shutting down...")
    await bot.session.close()


async def main():
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()

    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    dp.update.middleware(ThrottlingMiddleware(redis_client, limit=10, window=1))
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())

    dp.include_router(start.router)
    dp.include_router(tap.router)
    dp.include_router(profile.router)
    dp.include_router(upgrades.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    if settings.WEBHOOK_URL:
        logger.info(f"🌐 Setting Webhook to {settings.WEBHOOK_URL}")
        await bot.set_webhook(
            url=settings.WEBHOOK_URL,
            drop_pending_updates=True,
            allowed_updates=dp.resolve_used_update_types(),
        )
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler
        from aiohttp import web

        app = web.Application()
        webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_handler.register(app, path="/webhook")

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=settings.WEBHOOK_HOST, port=settings.WEBHOOK_PORT)
        await site.start()
        logger.info(f"✅ Webhook server running on {settings.WEBHOOK_HOST}:{settings.WEBHOOK_PORT}")

        try:
            while True:
                await asyncio.sleep(3600)
        finally:
            await bot.delete_webhook()
            await runner.cleanup()
    else:
        logger.info("📡 Starting Polling mode...")
        await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
    except Exception as e:
        logger.exception(f"💥 Fatal error: {e}")
