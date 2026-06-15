import asyncio
import os

from aiogram import Bot, Dispatcher

from .handlers import router


async def main():
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


def run():
    asyncio.run(main())
