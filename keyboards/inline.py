from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import Category, Recipe


def get_categories_keyboard(categories: list[Category]):
    """Динамически создаёт инлайн-кнопки для списка категорий"""
    builder = InlineKeyboardBuilder()

    for category in categories:
        # Кодируем в скрытую строку ID категории, чтобы знать, что именно выбрал пользователь.
        builder.button(
            text=category.name,
            callback_data=f"category_{category.id}"
        )

    # Настраиваем сетку кнопок: по 2 кнопки в ряд
    builder.adjust(2)
    return builder.as_markup()


def get_recipes_keyboard(recipes: list[Recipe], category_id: int):
    """Создает список инлайн-кнопок с названиями рецептов"""
    builder = InlineKeyboardBuilder()

    for recipe in recipes:
        builder.button(
            text=f"🍳 {recipe.title}",
            callback_data=f"recipe_{recipe.id}"
        )

    # Добавляем в самый конец кнопку возврата к списку категорий
    builder.button(text="⬅️ Назад к категориям", callback_data="back_to_categories")
    builder.adjust(1)  # Выводим строго по одному рецепту в строку
    return builder.as_markup()


def get_recipe_actions_keyboard(category_id: int, recipe_id: int, is_owner: bool):
    """Создает кнопки управления рецептом: назад, удалить и редактировать"""
    builder = InlineKeyboardBuilder()

    if is_owner:
        builder.button(text="✏️ Редактировать рецепт", callback_data=f"editchoose_{recipe_id}")
        builder.button(text="🗑 Удалить этот рецепт", callback_data=f"delrecipe_{recipe_id}")

    if category_id == 0:
        builder.button(text="⬅️ Назад к категориям", callback_data="back_to_categories")
    else:
        builder.button(text="⬅️ Назад к списку блюд", callback_data=f"category_{category_id}")

    builder.adjust(1)
    return builder.as_markup()


def get_edit_fields_keyboard(recipe_id: int):
    """Создает меню выбора поля для редактирования"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Изменить название", callback_data=f"edittitle_{recipe_id}")
    builder.button(text="📋 Изменить описание", callback_data=f"editdesc_{recipe_id}")
    builder.button(text="🛒 Изменить ингредиенты", callback_data=f"editingr_{recipe_id}")
    builder.button(text="👩‍🍳 Изменить инструкцию", callback_data=f"editinst_{recipe_id}")
    builder.button(text="❌ Отмена", callback_data=f"recipe_{recipe_id}")
    builder.adjust(1)
    return builder.as_markup()