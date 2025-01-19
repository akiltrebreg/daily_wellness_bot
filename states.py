from aiogram.fsm.state import State, StatesGroup

# Состояние для логирования информации о пользователе
class ProfileForm(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()

# Состояние для логирования потребления пищи
class FoodState(StatesGroup):
    waiting_for_grams = State()

# Состояния для логирования тренировки
class WorkoutState(StatesGroup):
    waiting_for_workout_type = State()
    waiting_for_duration = State()