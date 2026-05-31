from aiogram import Router, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.crud import (
    get_all_categories,
    get_recipes_by_category,
    get_recipe_with_ingredients,
    get_user_recipes,
    delete_recipe_from_db
)
from keyboards.inline import (
    get_categories_keyboard,
    get_recipes_keyboard,
    get_recipe_actions_keyboard
)

router = Router()


# 1. Показ главного меню категорий (при нажатии текстовой кнопки "🗂 Категории")
@router.message(F.text == "🗂 Категории")
async def show_categories(message: types.Message):
    categories = await get_all_categories()
    if not categories:
        await message.answer("К сожалению, список категорий пуст.")
        return
    await message.answer(
        "Выберите интересующую вас категорию блюд из списка ниже:",
        reply_markup=get_categories_keyboard(categories)
    )


# 2. Показ списка рецептов внутри выбранной категории
@router.callback_query(F.data.startswith("category_"))
async def process_category_click(callback: types.CallbackQuery):
    category_id = int(callback.data.split("_")[1])

    # Получаем все рецепты этой категории из базы данных
    recipes = await get_recipes_by_category(category_id)

    if not recipes:
        # Если рецептов нет, выводим сообщение с кнопкой возврата назад
        kb = InlineKeyboardBuilder()
        kb.button(text="⬅️ Назад к категориям", callback_data="back_to_categories")
        await callback.message.edit_text(
            "В этой категории пока нет рецептов.",
            reply_markup=kb.as_markup()
        )
        await callback.answer()
        return

    # Если рецепты есть, заменяем текст меню на список блюд
    await callback.message.edit_text(
        "Выберите блюдо, чтобы посмотреть рецепт:",
        reply_markup=get_recipes_keyboard(recipes, category_id)
    )
    await callback.answer()


# 3. Детальный просмотр конкретного выбранного рецепта
@router.callback_query(F.data.startswith("recipe_"))
async def process_recipe_click(callback: types.CallbackQuery):
    recipe_id = int(callback.data.split("_")[1])

    # Извлекаем рецепт вместе со всеми связями из SQLite
    recipe = await get_recipe_with_ingredients(recipe_id)

    if not recipe:
        await callback.answer("Ошибка: рецепт не найден.", show_alert=True)
        return

    # Формируем и красиво форматируем список ингредиентов
    ingredients_text = ""
    if recipe.ingredients:
        for idx, ri in enumerate(recipe.ingredients, 1):
            if ri.ingredient:
                ingredients_text += f"{idx}. {ri.ingredient.name.capitalize()} — {ri.amount} {ri.unit}\n"
    else:
        ingredients_text = "Не указаны\n"

    # Формируем красивый текст кулинарной карточки блюда
    recipe_card = (
        f"📖 **{recipe.title}**\n\n"
        f"⏱ **Время приготовления:** {recipe.cooking_time} минут\n"
        f"📝 **Описание:** {recipe.description}\n\n"
        f"🛒 **Ингредиенты:**\n{ingredients_text}\n"
        f"👩‍🍳 **Инструкция по приготовлению:**\n{recipe.instructions}"
    )

    # Проверяем: является ли тот, кто нажал на кнопку, автором этого рецепта
    is_owner = (callback.from_user.id == recipe.user_id)

    await callback.message.edit_text(
        recipe_card,
        parse_mode="Markdown",
        reply_markup=get_recipe_actions_keyboard(recipe.category_id, recipe.id, is_owner)
    )
    await callback.answer()


# 4. Показ личного кабинета (при нажатии текстовой кнопки "📋 Мои рецепты")
@router.message(F.text == "📋 Мои рецепты")
async def show_my_recipes(message: types.Message):
    # Достаем из SQLite рецепты, где автор — текущий пользователь
    my_recipes = await get_user_recipes(message.from_user.id)

    if not my_recipes:
        await message.answer(
            "Вы еще не добавили ни одного рецепта.\n"
            "Самое время нажать кнопку «➕ Добавить рецепт»!"
        )
        return

    # Выводим список личных рецептов
    kb = get_recipes_keyboard(my_recipes, category_id=0)
    await message.answer(
        f"📋 Список добавленных вами рецептов ({len(my_recipes)}):",
        reply_markup=kb
    )


# 5. Обработка нажатия инлайн-кнопки "🗑 Удалить этот рецепт"
@router.callback_query(F.data.startswith("delrecipe_"))
async def process_delete_recipe(callback: types.CallbackQuery):
    recipe_id = int(callback.data.split("_")[1])

    # Полностью стираем рецепт и связи граммовок из SQLite
    await delete_recipe_from_db(recipe_id)

    # Выводим красивое системное уведомление в Telegram
    await callback.answer("Рецепт успешно удален из вашей книги!", show_alert=True)

    # Обновляем сообщение, возвращая пользователя к списку папок категорий
    categories = await get_all_categories()
    await callback.message.edit_text(
        "Рецепт был удален. Выберите категорию для дальнейшего поиска:",
        reply_markup=get_categories_keyboard(categories)
    )


# 6. Обработка кнопки "Назад к категориям"
@router.callback_query(F.data == "back_to_categories")
async def process_back_to_categories(callback: types.CallbackQuery):
    categories = await get_all_categories()
    await callback.message.edit_text(
        "Выберите интересующую вас категорию блюд из списка ниже:",
        reply_markup=get_categories_keyboard(categories)
    )
    await callback.answer()
