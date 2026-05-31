from aiogram import Router, F, types
from aiogram.filters import Command

router = Router()

# Бот ответит и на команду /help, и на нажатие новой кнопки меню
@router.message(Command("help"))
@router.message(F.text == "💡 Помощь")
async def cmd_help(message: types.Message):
    await message.answer(
        "💡 **Справка по боту «Книга рецептов»**\n\n"
        "• Нажмите **«🗂 Категории»**, чтобы искать блюда по кулинарным разделам.\n"
        "• Нажмите **«🔍 Поиск»**, чтобы найти рецепт по названию, описанию или ингредиентам.\n"
        "• Нажмите **«➕ Добавить рецепт»**, чтобы пошагово внести свое блюдо в базу данных.\n"
        "• Нажмите **«📋 Мои рецепты»**, чтобы посмотреть или удалить добавленные вами блюда.",
        parse_mode="Markdown"
    )
