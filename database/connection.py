from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Создаем движок для работы с локальной базой данных SQLite в асинхронном режиме
engine = create_async_engine("sqlite+aiosqlite:///recipes.db", echo=True)

# Фабрика сессий для выполнения запросов
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Базовый класс для всех моделей (таблиц)
class Base(DeclarativeBase):
    pass
