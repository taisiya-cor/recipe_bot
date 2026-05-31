import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import config
from database.connection import engine, Base
from database.crud import seed_categories
from handlers import start, help, list_recipes, add_recipe, search, edit_recipe


async def main():
    # Настраиваем вывод логов в консоль PyCharm
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # 1. Автоматическая генерация таблиц в SQLite при их отсутствии
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logging.info("База данных успешно инициализирована.")

    # 2. Проверка и наполнение таблицы категорий базовыми пресетами
    await seed_categories()
    logging.info("Базовые категории успешно проверены/добавлены.")

    # 3. Инициализация объектов Bot и Dispatcher
    bot = Bot(token=config.bot_token.get_secret_value())
    dp = Dispatcher()

    # 4. Регистрация обработчиков команд
    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(list_recipes.router)
    dp.include_router(add_recipe.router)
    dp.include_router(edit_recipe.router)
    dp.include_router(search.router)

    # 5. Запуск бесконечного процесса опроса серверов Telegram
    logging.info("Бот полностью настроен и готов к обработке сообщений!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот успешно остановлен разработчиком.")
