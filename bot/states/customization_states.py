#bot/states/customization_states.py
from aiogram.fsm.state import State, StatesGroup

class CustomizationStates(StatesGroup):
    """Состояния для кастомизации напитка"""
    choose_milk = State()        # Выбор молока
    choose_sugar = State()       # Количество сахара
    choose_temperature = State() # Температура
    choose_toppings = State()    # Добавки (сливки, корица и т.д.)