from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

#Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🗂 Категории"), KeyboardButton(text="🔍 Поиск")],
        [KeyboardButton(text="➕ Добавить рецепт"), KeyboardButton(text="📋 Мои рецепты")],
        [KeyboardButton(text="💡 Помощь")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие..."
)
