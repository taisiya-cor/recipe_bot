from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from states import EditRecipeStates
from database.crud import (
    update_recipe_title,
    update_recipe_description,
    update_recipe_instructions,
    clear_recipe_ingredients
)

router = Router()

# 1. Выбор поля: ловим нажатие инлайн-кнопки "✏️ Редактировать рецепт"
from keyboards.inline import get_edit_fields_keyboard


@router.callback_query(F.data.startswith("editchoose_"))
async def process_edit_choose(callback: types.CallbackQuery):
    recipe_id = int(callback.data.split("_")[-1])
    await callback.message.edit_text(
        "Что именно вы хотите изменить в этом рецепте?",
        reply_markup=get_edit_fields_keyboard(recipe_id)
    )
    await callback.answer()


# 2. Название: переход в режим редактирования названия
@router.callback_query(F.data.startswith("edittitle_"))
async def edit_title_start(callback: types.CallbackQuery, state: FSMContext):
    recipe_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_recipe_id=recipe_id)
    await callback.message.answer("Введите новое название для этого блюда:")
    await state.set_state(EditRecipeStates.waiting_for_new_title)
    await callback.answer()


@router.message(EditRecipeStates.waiting_for_new_title, F.text)
async def edit_title_save(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await update_recipe_title(data['edit_recipe_id'], message.text)
    await message.answer(f"✅ Название рецепта успешно изменено на: «{message.text}»")
    await state.clear()


# 3. Описание: переход в режим редактирования описания
@router.callback_query(F.data.startswith("editdesc_"))
async def edit_desc_start(callback: types.CallbackQuery, state: FSMContext):
    recipe_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_recipe_id=recipe_id)
    await callback.message.answer("Введите новое краткое описание для блюда:")
    await state.set_state(EditRecipeStates.waiting_for_new_description)
    await callback.answer()


@router.message(EditRecipeStates.waiting_for_new_description, F.text)
async def edit_desc_save(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await update_recipe_description(data['edit_recipe_id'], message.text)
    await message.answer("✅ Краткое описание рецепта успешно обновлено!")
    await state.clear()


# 4. Инструкция: переход в режим редактирования пошагового текста
@router.callback_query(F.data.startswith("editinst_"))
async def edit_inst_start(callback: types.CallbackQuery, state: FSMContext):
    recipe_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_recipe_id=recipe_id)
    await callback.message.answer("Напишите новую пошаговую инструкцию по приготовлению:")
    await state.set_state(EditRecipeStates.waiting_for_new_instructions)
    await callback.answer()


@router.message(EditRecipeStates.waiting_for_new_instructions, F.text)
async def edit_inst_save(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await update_recipe_instructions(data['edit_recipe_id'], message.text)
    await message.answer("✅ Пошаговая инструкция по приготовлению успешно изменена!")
    await state.clear()


# 5. Ингредиенты: алгоритм каскадного перезаписывания состава продуктов
@router.callback_query(F.data.startswith("editingr_"))
async def edit_ingr_start(callback: types.CallbackQuery, state: FSMContext):
    recipe_id = int(callback.data.split("_")[-1])

    # Сначала полностью очищаем старый состав граммовок в SQLite
    await clear_recipe_ingredients(recipe_id)

    # Настраиваем временную память FSM для сбора новых продуктов
    await state.update_data(edit_recipe_id=recipe_id)
    await state.update_data(ingredients_list=[])

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Все новые ингредиенты добавлены", callback_data="finish_edit_ingredients")

    await callback.message.answer(
        "Старый состав рецепта очищен. Отправьте новые ингредиенты по одному.\n"
        "Формат: `Название, Количество, Единица измерения`\n"
        "Пример: `Картофель, 4, шт`",
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )
    await state.set_state(EditRecipeStates.waiting_for_new_ingredients)
    await callback.answer()


# Ловим строки продуктов в цикле FSM
@router.message(EditRecipeStates.waiting_for_new_ingredients, F.text)
async def process_new_single_ingredient(message: types.Message, state: FSMContext):
    parts = message.text.split(",")
    if len(parts) != 3:
        await message.answer("⚠️ Неверный формат! Пример: `Вода, 1.5, л`")
        return

    name = parts[0].strip()
    amount_str = parts[1].strip()
    unit = parts[2].strip()

    try:
        amount = float(amount_str)
    except ValueError:
        await message.answer("⚠️ Ошибка: количество должно быть числом.")
        return

    data = await state.get_data()
    current_list = data.get("ingredients_list", [])
    current_list.append({"name": name, "amount": amount, "unit": unit})
    await state.update_data(ingredients_list=current_list)

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Все новые ингредиенты добавлены", callback_data="finish_edit_ingredients")

    await message.answer(
        f"➕ Добавлено: {name} — {amount} {unit}.\n"
        f"Отправьте следующий ингредиент или завершите ввод:",
        reply_markup=kb.as_markup()
    )


# Фиксация нового собранного состава в базе данных SQLite
@router.callback_query(EditRecipeStates.waiting_for_new_ingredients, F.data == "finish_edit_ingredients")
async def finish_edit_ingredients_input(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    recipe_id = user_data['edit_recipe_id']

    from database.connection import async_session
    from database.models import Ingredient, RecipeIngredient
    from sqlalchemy.future import select

    async with async_session() as session:
        async with session.begin():
            for ing in user_data['ingredients_list']:
                clean_name = ing['name'].lower().strip()
                res = await session.execute(select(Ingredient).where(Ingredient.name == clean_name))
                db_ingredient = res.scalar_one_or_none()

                if not db_ingredient:
                    db_ingredient = Ingredient(name=clean_name)
                    session.add(db_ingredient)
                    await session.flush()

                recipe_ing = RecipeIngredient(
                    recipe_id=recipe_id,
                    ingredient_id=db_ingredient.id,
                    amount=ing['amount'],
                    unit=ing['unit']
                )
                session.add(recipe_ing)
            await session.commit()

    await callback.message.answer("🎉 Новый состав ингредиентов успешно привязан к рецепту!")
    await state.clear()
    await callback.answer()
