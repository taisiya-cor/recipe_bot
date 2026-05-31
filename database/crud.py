from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from database.connection import async_session
from database.models import User, Category, Recipe, Ingredient, RecipeIngredient


async def register_user(user_id: int, username: str):
    """Регистрирует пользователя в базе данных, если его там нет"""
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                new_user = User(id=user_id, username=username)
                session.add(new_user)
                await session.commit()


async def seed_categories():
    """Заполняет базу данных начальными категориями, если таблица пуста"""
    default_categories = ["🌅 Завтраки", "🍜 Супы", "🥩 Горячие блюда", "🍰 Десерты", "🥗 Салаты"]
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(Category))
            if not result.scalars().first():
                for cat_name in default_categories:
                    session.add(Category(name=cat_name))
                await session.commit()


async def get_all_categories():
    """Возвращает список всех категорий из базы данных"""
    async with async_session() as session:
        result = await session.execute(select(Category))
        return result.scalars().all()
async def add_new_recipe(user_id: int, category_id: int, title: str, description: str, cooking_time: int, instructions: str):
    """Добавляет новый рецепт в базу данных"""
    async with async_session() as session:
        async with session.begin():
            new_recipe = Recipe(
                user_id=user_id,
                category_id=category_id,
                title=title,
                description=description,
                cooking_time=cooking_time,
                instructions=instructions
            )
            session.add(new_recipe)
            await session.commit()
async def get_recipes_by_category(category_id: int):
    """Возвращает все рецепты, принадлежащие конкретной категории"""
    async with async_session() as session:
        result = await session.execute(
            select(Recipe).where(Recipe.category_id == category_id)
        )
        return result.scalars().all()

async def get_recipe_by_id(recipe_id: int):
    """Возвращает детальную информацию о рецепте по его уникальному ID"""
    async with async_session() as session:
        result = await session.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )
        return result.scalar_one_or_none()


async def add_ingredient_to_recipe(recipe_id: int, ingredient_name: str, amount: float, unit: str):
    """Ищет ингредиент в справочнике (или создает новый) и привязывает его к рецепту"""
    async with async_session() as session:
        async with session.begin():
            # 1. Приводим название к нижнему регистру для исключения дублей
            clean_name = ingredient_name.strip().lower()

            # Проверяем, есть ли такой продукт в глобальном справочнике
            result = await session.execute(select(Ingredient).where(Ingredient.name == clean_name))
            ingredient = result.scalar_one_or_none()

            if not ingredient:
                ingredient = Ingredient(name=clean_name)
                session.add(ingredient)
                await session.flush()  # Получаем ID нового ингредиента до commit

            # 2. Привязываем ингредиент к конкретному рецепту в промежуточной таблице
            recipe_ing = RecipeIngredient(
                recipe_id=recipe_id,
                ingredient_id=ingredient.id,
                amount=amount,
                unit=unit
            )
            session.add(recipe_ing)
            await session.commit()


async def get_recipe_with_ingredients(recipe_id: int):
    """Возвращает рецепт вместе со всеми его ингредиентами"""
    async with async_session() as session:
        # selectinload автоматически подгружает связанные данные из recipe_ingredients и далее из ingredients
        result = await session.execute(
            select(Recipe)
            .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
            .where(Recipe.id == recipe_id)
        )
        return result.scalar_one_or_none()


async def search_recipes_by_keyword(keyword: str):
    """Поиск по названию, описанию или ингредиентам"""
    async with async_session() as session:
        # 1. Загружаем из базы абсолютно все рецепты вместе с их ингредиентами
        query = select(Recipe).options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient)
        )
        result = await session.execute(query)
        all_recipes = result.scalars().all()

        # Подготавливаем поисковое слово
        search_word = keyword.lower().strip()
        found_recipes = []

        # 2. Фильтруем данные средствами самого Python
        for recipe in all_recipes:
            # Проверяем название и описание
            in_title = search_word in recipe.title.lower()
            in_desc = search_word in recipe.description.lower()

            # Проверяем ингредиенты блюда
            in_ingredients = False
            for ri in recipe.ingredients:
                if ri.ingredient and search_word in ri.ingredient.name.lower():
                    in_ingredients = True
                    break

            # Если где-то совпало — добавляем в результаты
            if in_title or in_desc or in_ingredients:
                found_recipes.append(recipe)

        return found_recipes


async def get_user_recipes(user_id: int):
    """Возвращает список всех рецептов, которые создал конкретный пользователь"""
    async with async_session() as session:
        result = await session.execute(
            select(Recipe).where(Recipe.user_id == user_id)
        )
        return result.scalars().all()


async def delete_recipe_from_db(recipe_id: int):
    """Удаляет рецепт и автоматически зачищает связанные ингредиенты в промежуточной таблице"""
    async with async_session() as session:
        async with session.begin():
            # 1. Сначала удаляем записи из связующей таблицы, чтобы не нарушать внешние ключи
            await session.execute(
                select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)
            )
            from sqlalchemy import delete
            await session.execute(delete(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id))

            # 2. Удаляем сам рецепт
            await session.execute(delete(Recipe).where(Recipe.id == recipe_id))
            await session.commit()

async def update_recipe_title(recipe_id: int, new_title: str):
    """Обновляет название рецепта в базе данных"""
    async with async_session() as session:
        async with session.begin():
            recipe = await session.get(Recipe, recipe_id)
            if recipe:
                recipe.title = new_title
                await session.commit()

async def update_recipe_description(recipe_id: int, new_description: str):
    """Обновляет краткое описание рецепта в базе данных"""
    async with async_session() as session:
        async with session.begin():
            recipe = await session.get(Recipe, recipe_id)
            if recipe:
                recipe.description = new_description
                await session.commit()

async def update_recipe_instructions(recipe_id: int, new_instructions: str):
    """Обновляет пошаговую инструкцию рецепта в базе данных"""
    async with async_session() as session:
        async with session.begin():
            recipe = await session.get(Recipe, recipe_id)
            if recipe:
                recipe.instructions = new_instructions
                await session.commit()

async def clear_recipe_ingredients(recipe_id: int):
    """Полностью удаляет все ингредиенты, привязанные к рецепту"""
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                delete(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)
            )
            await session.commit()