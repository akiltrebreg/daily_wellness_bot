from aiogram.dispatcher.filters.state import State, StatesGroup

# Состояния пользователей
class ProfileForm(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()