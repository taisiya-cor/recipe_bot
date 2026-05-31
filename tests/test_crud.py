import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select

from database.connection import Base
from database.models import User, Category, Recipe
from database.crud import register_user, seed_categories, get_all_categories, search_recipes_by_keyword

# Переводим базу в оперативную память для исключения блокировок файлов в Windows
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Фикстура для создания чистой структуры таблиц в памяти перед каждым тестом"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_user_registration(monkeypatch):
    """Тест корректной регистрации нового пользователя в системе"""
    monkeypatch.setattr("database.crud.async_session", TestSessionLocal)

    await register_user(user_id=99999, username="test_cook")

    async with TestSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == 99999))
        db_user = result.scalar_one_or_none()

        assert db_user is not None
        assert db_user.username == "test_cook"


@pytest.mark.asyncio
async def test_user_registration_duplicate(monkeypatch):
    """Тест защиты от дублирования пользователей при повторном нажатии /start"""
    monkeypatch.setattr("database.crud.async_session", TestSessionLocal)

    # Регистрируем пользователя дважды
    await register_user(user_id=777, username="chef")
    await register_user(user_id=777, username="chef_new_nic")

    async with TestSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == 777))
        users = result.scalars().all()

        assert len(users) == 1
        assert users[0].username == "chef"


@pytest.mark.asyncio
async def test_categories_seeding(monkeypatch):
    """Тест автоматического наполнения таблицы категорий пресетами"""
    monkeypatch.setattr("database.crud.async_session", TestSessionLocal)

    await seed_categories()
    categories = await get_all_categories()

    assert len(categories) == 5
    assert categories[0].name == "🌅 Завтраки"
    assert categories[-1].name == "🥗 Салаты"


@pytest.mark.asyncio
async def test_search_recipes_by_keyword(monkeypatch):
    """Тест работы глобального поиска по ключевым словам (название/описание)"""
    monkeypatch.setattr("database.crud.async_session", TestSessionLocal)

    await seed_categories()
    await register_user(user_id=111, username="test_author")

    # Добавляем тестовый рецепт напрямую в сессию
    async with TestSessionLocal() as session:
        async with session.begin():
            test_recipe = Recipe(
                id=1,
                user_id=111,
                category_id=1,
                title="Домашние Блины",
                description="Вкусный завтрак на молоке",
                cooking_time=20,
                instructions="Смешать муку, молоко и яйца, пожарить."
            )
            session.add(test_recipe)
            await session.commit()

    # Поиск по названию в разном регистре
    results_by_title = await search_recipes_by_keyword("БЛИН")
    assert len(results_by_title) == 1
    assert results_by_title[0].title == "Домашние Блины"

    # Поиск по описанию
    results_by_desc = await search_recipes_by_keyword("завтрак")
    assert len(results_by_desc) == 1

    # Поиск несуществующего слова
    results_empty = await search_recipes_by_keyword("суп")
    assert len(results_empty) == 0
