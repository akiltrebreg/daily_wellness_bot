import asyncio
from aiogram import Bot, Dispatcher
from aiogram.utils import executor
from config import API_TOKEN
from handlers import router
from middlewares import LoggingMiddleware


bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.include_router(router)
dp.message.middleware(LoggingMiddleware())

async def main():
    print("Бот запущен.")
    await dp.start_pollig(bot)

if __name__ == "__main__":
    asyncio.run(main())