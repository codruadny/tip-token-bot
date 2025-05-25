from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from bot.config import settings
from bot.middlewares.localization import I18nMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.handlers import (
    start, help, register, tip, wallet, balance, referral, transactions
)

# Initialize bot and dispatcher
bot = Bot(token=settings.BOT_TOKEN)

# Choose storage based on configuration
if settings.USE_REDIS:
    storage = RedisStorage.from_url(settings.REDIS_URL)
else:
    storage = MemoryStorage()

dp = Dispatcher(storage=storage)

# Register middlewares
dp.message.middleware(I18nMiddleware())
dp.message.middleware(ThrottlingMiddleware())
dp.callback_query.middleware(I18nMiddleware())
dp.callback_query.middleware(ThrottlingMiddleware())

# Include all routers
dp.include_router(start.router)
dp.include_router(help.router)
dp.include_router(register.router)
dp.include_router(tip.router)
dp.include_router(wallet.router)
dp.include_router(balance.router)
dp.include_router(referral.router)
dp.include_router(transactions.router)
