from aiogram.fsm.state import State, StatesGroup

class BroadcastStates(StatesGroup):
    """Состояния для рассылки акций"""
    enter_text = State()      # Ввод текста акции
    upload_image = State()    # Загрузка картинки
    confirm = State()         # Подтверждение рассылки