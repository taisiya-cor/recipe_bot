from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from states import AddRecipeStates
from database.crud import get_all_categories

router = Router()


# 1. Начало диалога: ловим нажатие кнопки "➕ Добавить рецепт"
@router.message(F.text == "➕ Добавить рецепт")
async def start_add_recipe(message: types.Message, state: FSMContext):
    # Сбрасываем прошлые состояния на всякий случай
    await state.clear()

    categories = await get_all_categories()
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat.name, callback_data=f"addcat_{cat.id}")
    builder.adjust(2)

    await message.answer("Сначала выберите категорию для вашего рецепта:", reply_markup=builder.as_markup())
    await state.set_state(AddRecipeStates.waiting_for_category)


# 2. Ловим выбор категории
@router.callback_query(AddRecipeStates.waiting_for_category, F.data.startswith("addcat_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[1])
    await state.update_data(category_id=category_id)

    await callback.message.answer("Отлично! Теперь введите название блюда:")
    await state.set_state(AddRecipeStates.waiting_for_title)
    await callback.answer()


# 3. Ловим название рецепта
@router.message(AddRecipeStates.waiting_for_title, F.text)
async def process_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите краткое описание блюда (одно-два предложения):")
    await state.set_state(AddRecipeStates.waiting_for_description)


# 4. Ловим описание
@router.message(AddRecipeStates.waiting_for_description, F.text)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Сколько минут требуется на приготовление? Введите только число:")
    await state.set_state(AddRecipeStates.waiting_for_time)


# 5. Ловим время приготовления
@router.message(AddRecipeStates.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректное число минут цифрами:")
        return

    await state.update_data(cooking_time=int(message.text))
    await state.update_data(ingredients_list=[])

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Все ингредиенты добавлены", callback_data="finish_ingredients")

    await message.answer(
        "Теперь добавьте ингредиенты по одному.\n"
        "Отправляйте сообщения строго в формате:\n"
        "`Название, Количество, Единица измерения`\n\n"
        "Пример: `Куриное филе, 500, г`.\n\n"
        "Как только введёте всё, нажмите кнопку ниже:",
        parse_mode="Markdown",
        reply_markup=kb.as_markup()
    )
    await state.set_state(AddRecipeStates.waiting_for_ingredients)


# Ловим строки ингредиентов
@router.message(AddRecipeStates.waiting_for_ingredients, F.text)
async def process_single_ingredient(message: types.Message, state: FSMContext):
    parts = message.text.split(",")
    if len(parts) != 3:
        await message.answer(
            "⚠️ Неверный формат! Напишите строго через запятую: Название, Количество, Единица.")
        return

    name = parts[0].strip()
    amount_str = parts[1].strip()
    unit = parts[2].strip()

    try:
        amount = float(amount_str)
    except ValueError:
        await message.answer("⚠️ Ошибка: количество должно быть числом (дробные пишите через точку, например: 0.5).")
        return

    data = await state.get_data()
    current_list = data.get("ingredients_list", [])
    current_list.append({"name": name, "amount": amount, "unit": unit})
    await state.update_data(ingredients_list=current_list)

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Все ингредиенты добавлены", callback_data="finish_ingredients")

    await message.answer(
        f"➕ Добавлено: {name} — {amount} {unit}.\nОтправьте следующий ингредиент или нажмите кнопку окончания:",
        reply_markup=kb.as_markup())


# Финал по кнопке
@router.callback_query(AddRecipeStates.waiting_for_ingredients, F.data == "finish_ingredients")
async def finish_ingredients_input(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Отлично, состав сохранен! Теперь напишите подробную пошагувую инструкцию по приготовлению:")
    await state.set_state(AddRecipeStates.waiting_for_instructions)
    await callback.answer()


# Сохранение в БД
@router.message(AddRecipeStates.waiting_for_instructions, F.text)
async def process_instructions(message: types.Message, state: FSMContext):
    await state.update_data(instructions=message.text)
    user_data = await state.get_data()

    from database.connection import async_session
    from database.models import Recipe, Ingredient, RecipeIngredient
    from sqlalchemy.future import select

    async with async_session() as session:
        async with session.begin():
            new_recipe = Recipe(
                user_id=message.from_user.id,
                category_id=user_data['category_id'],
                title=user_data['title'],
                description=user_data['description'],
                cooking_time=user_data['cooking_time'],
                instructions=user_data['instructions']
            )
            session.add(new_recipe)
            await session.flush()

            for ing in user_data['ingredients_list']:
                clean_name = ing['name'].lower().strip()
                res = await session.execute(select(Ingredient).where(Ingredient.name == clean_name))
                db_ingredient = res.scalar_one_or_none()
                if not db_ingredient:
                    db_ingredient = Ingredient(name=clean_name)
                    session.add(db_ingredient)
                    await session.flush()

                recipe_ing = RecipeIngredient(
                    recipe_id=new_recipe.id,
                    ingredient_id=db_ingredient.id,
                    amount=ing['amount'],
                    unit=ing['unit']
                )
                session.add(recipe_ing)

            await session.commit()

    await message.answer(f"🎉 Рецепт «{user_data['title']}» успешно сохранён!")
    await state.clear()
