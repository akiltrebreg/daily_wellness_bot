from aiogram.fsm.state import State, StatesGroup

class ProfileForm(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()

class FoodState(StatesGroup):
    waiting_for_grams = State()