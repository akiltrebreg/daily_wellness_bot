from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import requests
from datetime import datetime
from config import WEATHER_API_KEY
from states import ProfileForm

router = Router()

# Сохранение данных о пользователях
users = {}


def reset_daily_stats(user_id):
    today = datetime.now().date()
    user = users[user_id]
    if user.get("last_date") != today:
        # Сохранение статистики за предыдущий день
        if "last_date" in user:
            previous_date = user["last_date"]
            user["daily_stats"].setdefault(previous_date,
                                           {"water": user["logged_water"], "calories": user["logged_calories"]})

        # Сброс ежедневной статистики
        user["last_date"] = today
        user["logged_water"] = 0
        user["logged_calories"] = 0


# Команда /start
@router.message(Command("start"))
async def send_welcome(message: Message):
    await message.reply("Добро пожаловать! Введите /help для просмотра списка команд.")


# Команда /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/set_profile - Настройка профиля\n"
        "/log_water - Внести показатели воды\n"
        "/log_food - Внести показатели калорий\n"
        "/check_progress - Посмотреть прогресс\n"
    )


# Настройка профиля пользователя
@router.message(Command("set_profile"))
async def set_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {
            "weight": None,
            "height": None,
            "age": None,
            "activity": None,
            "city": None,
            "water_goal": None,
            "calorie_goal": None,
            "logged_water": 0,
            "logged_calories": 0,
            "burned_calories": 0,
            "last_date": datetime.now().date(),
            "daily_stats": {}
        }
    await message.reply("Сколько вы весите? (в килограммах)")
    await state.set_state(ProfileForm.weight)


@router.message(ProfileForm.weight)
async def handle_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        user_id = message.from_user.id
        users[user_id]["weight"] = weight
        await message.reply("Какой у вас рост? (в сантиметрах)")
        await state.set_state(ProfileForm.height)
    except ValueError:
        await message.reply("Введите корректное значение веса (число).")


@router.message(ProfileForm.height)
async def handle_height(message: Message, state: FSMContext):
    try:
        height = float(message.text)
        user_id = message.from_user.id
        users[user_id]["height"] = height
        await message.reply("Сколько вам полных лет?")
        await state.set_state(ProfileForm.age)
    except ValueError:
        await message.reply("Введите корректное значение роста (число).")


@router.message(ProfileForm.age)
async def handle_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        user_id = message.from_user.id
        users[user_id]["age"] = age
        await message.reply("Сколько минут в день вы уделяете физической активности?")
        await state.set_state(ProfileForm.activity)
    except ValueError:
        await message.reply("Введите корректное значение возраста (целое число).")


@router.message(ProfileForm.activity)
async def handle_activity(message: Message, state: FSMContext):
    try:
        activity = int(message.text)
        user_id = message.from_user.id
        users[user_id]["activity"] = activity
        await message.reply("Введите ваш город (на английском языке):")
        await state.set_state(ProfileForm.city)
    except ValueError:
        await message.reply("Введите корректное значение физической активности (целое число).")


@router.message(ProfileForm.city)
async def handle_city(message: Message, state: FSMContext):
    user_id = message.from_user.id
    city = message.text
    users[user_id]["city"] = city

    # Запрос данных о погоде
    response = requests.get(
        f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    ).json()

    temperature = response.get("main", {}).get("temp", 20)  # По умолчанию: 20°С
    weather_adjustment = 500 if temperature > 25 else 0

    weight = users[user_id]["weight"]
    activity = users[user_id]["activity"]

    # Расчет суточной нормы воды и калорий
    users[user_id]["water_goal"] = weight * 30 + (activity // 30) * 500 + weather_adjustment
    bmr = 10 * weight + 6.25 * users[user_id]["height"] - 5 * users[user_id]["age"]
    users[user_id]["calorie_goal"] = bmr + (activity * 5)

    await message.reply(
        f"Профиль настроен!\n\n"
        f"Норма воды: {users[user_id]['water_goal']} мл\n"
        f"Норма калорий: {users[user_id]['calorie_goal']} ккал"
    )
    await state.clear()


# Внесение воды
@router.message(Command("log_water"))
async def log_water(message: Message):
    user_id = message.from_user.id
    if user_id not in users:
        await message.reply("Настройте свой профиль с помощью /set_profile.")
        return

    reset_daily_stats(user_id)

    try:
        amount = int(message.text.split()[1])
        users[user_id]["logged_water"] += amount
        remaining = max(0, users[user_id]["water_goal"] - users[user_id]["logged_water"])

        # Сохранение статистики
        today = datetime.now().date()
        users[user_id]["daily_stats"].setdefault(today, {"water": 0, "calories": 0})
        users[user_id]["daily_stats"][today]["water"] += amount

        await message.reply(f"Внесено {amount} мл воды. Осталось: {remaining} мл до нормы.")
    except (IndexError, ValueError):
        await message.reply("Отправьте: /log_water <количество воды в мл>.")


# Проверка прогресса
@router.message(Command("check_progress"))
async def check_progress(message: Message):
    user_id = message.from_user.id
    if user_id not in users:
        await message.reply("Настройте свой профиль с помощью /set_profile.")
        return

    reset_daily_stats(user_id)

    user = users[user_id]
    water_progress = f"Вода: {user['logged_water']} из {user['water_goal']} мл"
    calorie_progress = f"Калории: {user['logged_calories']} из {user['calorie_goal']} ккал"

    await message.reply(f"Ваш прогресс:\n{water_progress}\n{calorie_progress}")