import asyncio
from aiogram import Bot, Dispatcher
from config import API_TOKEN
from handlers import router
from middlewares import LoggingMiddleware

async def main():
    # Создание бота и диспетчера
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    # Подключение роутеров и middlewares
    dp.include_router(router)
    dp.message.middleware(LoggingMiddleware())

    print("Бот запущен.")

    # Запуск polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
