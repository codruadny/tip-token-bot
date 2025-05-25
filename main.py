import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler

import uvicorn
from fastapi import FastAPI, Request, Response
from bot.app import bot, dp
from bot.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler("bot.log", maxBytes=10485760, backupCount=5),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create FastAPI app
app = FastAPI(title="TIP Token Telegram Bot")

# Webhook URL path
WEBHOOK_PATH = f"/webhook/{settings.BOT_TOKEN}"
WEBHOOK_URL = f"{settings.WEBHOOK_HOST}{WEBHOOK_PATH}"

@app.on_event("startup")
async def on_startup():
    """Set webhook on startup."""
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(
            url=WEBHOOK_URL,
            drop_pending_updates=True
        )
        logging.info(f"Webhook set to {WEBHOOK_URL}")
    else:
        logging.info(f"Webhook already set to {WEBHOOK_URL}")

@app.post(WEBHOOK_PATH)
async def bot_webhook(request: Request):
    """Process webhook updates from Telegram."""
    update_data = await request.json()
    update = update_data
    await dp.feed_update(bot=bot, update=update)
    return Response()

@app.on_event("shutdown")
async def on_shutdown():
    """Delete webhook and close connections on shutdown."""
    await bot.delete_webhook()
    await dp.storage.close()
    await bot.session.close()

if __name__ == "__main__":
    if settings.USE_WEBHOOK:
        # Run as webhook server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=False
        )
    else:
        # Run in polling mode for development
        asyncio.run(dp.start_polling(bot))
