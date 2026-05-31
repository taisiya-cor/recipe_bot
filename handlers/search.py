from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from states import SearchStates
from database.crud import search_recipes_by_keyword
from keyboards.inline import get_recipes_keyboard

router = Router()


# 1. Срабатывает при нажатии на текстовую кнопку "🔍 Поиск"
@router.message(F.text == "🔍 Поиск")
async def start_search(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название блюда, ключевое слово для поиска или название ингредиента:\n",
        parse_mode="Markdown"
    )
    # Переводим пользователя в режим ожидания текста запроса
    await state.set_state(SearchStates.waiting_for_keyword)


# 2. Ловим поисковый запрос от пользователя
@router.message(SearchStates.waiting_for_keyword, F.text)
async def process_search(message: types.Message, state: FSMContext):
    keyword = message.text

    # Ищем совпадения в базе данных SQLite
    found_recipes = await search_recipes_by_keyword(keyword)

    if not found_recipes:
        await message.answer(
            f"🔍 По запросу «{keyword}» ничего не найдено.\n"
            "Попробуйте ввести другое слово или проверьте орфографию."
        )
        # Выходим из состояния поиска, чтобы пользователь мог пользоваться меню
        await state.clear()
        return

    # Если рецепты найдены, выводим их списком инлайн-кнопок
    # Передаем id категории как 0 (так как поиск идет по всем категориям разом)
    kb = get_recipes_keyboard(found_recipes, category_id=0)

    await message.answer(
        f"🔍 Результаты поиска по запросу «{keyword}» ({len(found_recipes)}):",
        reply_markup=kb
    )

    # Сбрасываем состояние
    await state.clear()
