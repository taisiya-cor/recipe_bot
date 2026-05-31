from aiogram import Router, types
from aiogram.filters import CommandStart
from database.crud import register_user
from keyboards.reply import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    # Регистрируем пользователя в SQLite
    await register_user(user_id=message.from_user.id, username=message.from_user.username)

    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        f"Добро пожаловать в кулинарную книгу рецептов. "
        f"Используйте меню ниже для навигации.",
        reply_markup=main_menu
    )
