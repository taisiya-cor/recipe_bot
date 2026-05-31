from aiogram.fsm.state import StatesGroup, State

class AddRecipeStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_time = State()
    waiting_for_ingredients = State()
    waiting_for_instructions = State()
class SearchStates(StatesGroup):
    waiting_for_keyword = State()
class EditRecipeStates(StatesGroup):
    waiting_for_new_title = State()        # Ожидание нового названия
    waiting_for_new_description = State()  # Ожидание нового описания
    waiting_for_new_instructions = State() # Ожидание новой инструкции
    waiting_for_new_ingredients = State() # Ожидание новых ингредиентов