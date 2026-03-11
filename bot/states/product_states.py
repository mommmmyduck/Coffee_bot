#states/product_states.py
from aiogram.fsm.state import State, StatesGroup

class AddProductStates(StatesGroup):
    """Состояния для добавления товара"""
    choose_category = State()
    enter_name = State()
    enter_description = State()
    enter_price = State()
    enter_volume = State()
    enter_weight = State()
    enter_calories = State()
    upload_photo = State()


class EditProductStates(StatesGroup):
    """Состояния для редактирования товара"""
    choose_product = State()
    choose_field = State()
    enter_new_value = State()
    upload_new_photo = State()