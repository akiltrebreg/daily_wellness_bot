from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import requests
from datetime import datetime
from config import WEATHER_API_KEY, WEATHER_API_URL, CALORIES_BURNED_API_KEY, CALORIES_BURNED_API_URL, FOOD_API_URL
from states import ProfileForm, FoodState, WorkoutState
import matplotlib.pyplot as plt
import io
from datetime import datetime

router = Router()

# Сохранение данных о пользователях
users = {}

def reset_daily_stats(user_id):
    """
    Функция для сброса статистики.
    """
    today = datetime.now().date()
    user = users[user_id]

    # Если пользователь только зарегистрировался сегодня
    if "last_date" not in user:
        user["last_date"] = today
        user["logged_water"] = 0
        user["logged_calories"] = 0
        user["burned_calories"] = 0
        user["daily_stats"] = {}
        return

    # Если день сменился, сохраняем статистику и сбрасываем показатели
    if user["last_date"] != today:
        previous_date = user["last_date"]
        user["daily_stats"].setdefault(previous_date, {
            "water": user["logged_water"],
            "calories": user["logged_calories"],
            "burned_calories": user.get("burned_calories", 0),
            "water_goal": user.get("water_goal", 0),
            "calorie_goal": user.get("calorie_goal", 0)
        })
        user["last_date"] = today
        user["logged_water"] = 0
        user["logged_calories"] = 0
        user["burned_calories"] = 0

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
        "/log_workout - Логирование тренировок\n"
        "/check_progress - Посмотреть прогресс\n"
        "/plot_history - Посмотреть графики с историей прогресса\n"
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
        weight = float(message.text.strip())
        user_id = message.from_user.id
        users[user_id]["weight"] = weight
        await message.reply("Какой у вас рост? (в сантиметрах)")
        await state.set_state(ProfileForm.height)
    except ValueError:
        await message.reply("Введите корректное значение веса (число).")

@router.message(ProfileForm.height)
async def handle_height(message: Message, state: FSMContext):
    try:
        height = float(message.text.strip())
        user_id = message.from_user.id
        users[user_id]["height"] = height
        await message.reply("Сколько вам полных лет?")
        await state.set_state(ProfileForm.age)
    except ValueError:
        await message.reply("Введите корректное значение роста (число).")

@router.message(ProfileForm.age)
async def handle_age(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        user_id = message.from_user.id
        users[user_id]["age"] = age
        await message.reply("Сколько минут в день вы уделяете физической активности?")
        await state.set_state(ProfileForm.activity)
    except ValueError:
        await message.reply("Введите корректное значение возраста (целое число).")

@router.message(ProfileForm.activity)
async def handle_activity(message: Message, state: FSMContext):
    try:
        activity = int(message.text.strip())
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
        f"{WEATHER_API_URL}?q={city}&appid={WEATHER_API_KEY}&units=metric"
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
        user = users[user_id]
        users[user_id]["daily_stats"].setdefault(today, {
            "water": 0,
            "calories": 0,
            "burned_calories": 0,
            "water_goal": user.get("water_goal", 0),
            "calorie_goal": user.get("calorie_goal", 0)
        })
        users[user_id]["daily_stats"][today]["water"] += amount

        await message.reply(f"Внесено {amount} мл воды. Осталось: {remaining} мл до нормы.")
    except (IndexError, ValueError):
        await message.reply("Отправьте: /log_water <количество воды в мл>.")


# Внесение данных о съеденном продукте
@router.message(Command("log_food"))
async def log_food(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in users:
        await message.reply("Настройте свой профиль с помощью /set_profile.")
        return

    try:
        # Получаем название продукта
        food = message.text.split(maxsplit=1)[1].strip().lower()
        response = requests.get(
            f"{FOOD_API_URL}",
            params={"search_terms": food, "search_simple": "1", "action": "process", "json": "1", "page_size": 3}
        ).json()

        # Ищем продукты в ответе от API
        products = response.get("products", [])
        if not products:
            await message.reply(f"Продукт с названием '{food}' не найден.")
            return

        # Поиск наиболее подходящего продукта
        best_match = None
        for product in products:
            product_name = product.get("product_name", "").lower()
            if food in product_name:
                best_match = product
                break

        if best_match:
            calories_per_100g = best_match.get("nutriments", {}).get("energy-kcal_100g", 0)
            product_name = best_match.get("product_name", "Неизвестный продукт")
            if calories_per_100g:
                # Сохраняем данные в FSM
                await state.set_state(FoodState.waiting_for_grams)
                await state.update_data(
                    calories_per_100g=calories_per_100g,
                    product_name=product_name,
                )
                await message.reply(
                    f"{product_name} содержит {calories_per_100g} ккал на 100 г. Сколько граммов вы съели?")
            else:
                await message.reply(f"Нет данных о калориях для продукта {product_name}.")
        else:
            await message.reply(f"Продукт с названием '{food}' не найден.")

    except IndexError:
        await message.reply("Используйте: /log_food <название продукта>.")
    except Exception as e:
        await message.reply(f"Настройте профиль /set_profile")


@router.message(FoodState.waiting_for_grams)
async def calculate_calories(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    calories_per_100g = data.get("calories_per_100g")
    product_name = data.get("product_name")

    try:
        # Получаем количество съеденных граммов
        ate_gram = int(message.text)
        if ate_gram <= 0:
            await message.reply("Введите положительное число граммов.")
            return

        # Рассчитываем потребленные калории
        amount = calories_per_100g * ate_gram / 100

        # Получаем текущую дату
        today = datetime.now().date()

        # Если история для текущего пользователя еще не сохранена, создаем пустой словарь
        if user_id not in users:
            users[user_id] = {}

        # Сохранение статистики в daily_stats
        user = users[user_id]
        users[user_id]["daily_stats"].setdefault(today, {
            "water": 0,
            "calories": 0,
            "burned_calories": 0,
            "water_goal": user.get("water_goal", 0),
            "calorie_goal": user.get("calorie_goal", 0)
        })
        users[user_id]["daily_stats"][today]["calories"] += amount

        # Обновляем общий счетчик потребленных калорий
        users[user_id]["logged_calories"] = users[user_id].get("logged_calories", 0) + amount

        # Получаем текущую цель по калориям
        calorie_goal = users[user_id].get("calorie_goal", 2000)

        # Проверяем, если съели больше, чем норма - остаток должен быть 0
        remaining = max(0, calorie_goal - users[user_id]["logged_calories"])

        # Отправляем ответ
        await message.reply(
            f"Вы съели {ate_gram} г {product_name}, это {amount:.2f} ккал.\n"
            f"Всего потреблено: {users[user_id]['logged_calories']:.2f} ккал.\n"
            f"Осталось {remaining:.2f} ккал до нормы ({calorie_goal} ккал)."
        )

        # Завершаем состояние
        await state.clear()

    except ValueError:
        await message.reply("Введите корректное число граммов.")
    except Exception as e:
        await message.reply(f"Настройте профиль /set_profile")
        await state.clear()


@router.message(Command("log_workout"))
async def log_workout_start(message: Message, state: FSMContext):
    await message.reply("Введите тип тренировки.")
    await state.set_state(WorkoutState.waiting_for_workout_type)


@router.message(WorkoutState.waiting_for_workout_type)
async def get_workout_type(message: Message, state: FSMContext):
    workout_type = message.text.strip()
    await state.update_data(workout_type=workout_type)
    await message.reply("Теперь введите продолжительность тренировки в минутах.")
    await state.set_state(WorkoutState.waiting_for_duration)


@router.message(WorkoutState.waiting_for_duration)
async def log_workout(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()

    try:
        # Проверяем корректность ввода времени тренировки
        workout_time = int(message.text.strip())
        if workout_time <= 0:
            await message.reply("Введите положительное число минут.")
            return

        # Получаем тип тренировки из состояния
        workout_type = data.get("workout_type")
        if not workout_type:
            await message.reply("Произошла ошибка: тип тренировки не указан.")
            return

        # Отправляем запрос к API для расчёта калорий
        response = requests.get(
            f"{CALORIES_BURNED_API_URL}?activity={workout_type}&duration={workout_time}",
            headers={"x-api-key": f"{CALORIES_BURNED_API_KEY}"}
        ).json()

        if not response or not isinstance(response, list) or not isinstance(response[0].get("total_calories"), (int, float)):
            await message.reply(f"Тренировка '{workout_type}' не найдена в базе или произошла ошибка в расчёте.")
            return

        # Получаем сожжённые калории
        calories_burned = float(response[0]["total_calories"])

        # Рассчитываем расход воды на тренировке (200 мл за каждые 30 минут)
        water_consumed = (workout_time / 30) * 200

        # Логируем данные, приводя типы к числовым для безопасности
        users[user_id]["logged_calories"] = float(users[user_id].get("logged_calories", 0)) - calories_burned
        users[user_id]["logged_water"] = float(users[user_id].get("logged_water", 0)) - water_consumed
        users[user_id]["burned_calories"] = float(users[user_id].get("burned_calories", 0)) + calories_burned

        # Получаем текущую дату и обновляем историю
        today = datetime.now().date()
        user = users[user_id]
        users[user_id]["daily_stats"].setdefault(today, {
            "water": 0,
            "calories": 0,
            "burned_calories": 0,
            "water_goal": user.get("water_goal", 0),
            "calorie_goal": user.get("calorie_goal", 0)
        })

        users[user_id]["daily_stats"][today]["calories"] = float(users[user_id]["daily_stats"][today]["calories"]) - calories_burned
        users[user_id]["daily_stats"][today]["water"] = float(users[user_id]["daily_stats"][today]["water"]) - water_consumed
        users[user_id]["daily_stats"][today]["burned_calories"] = float(users[user_id]["daily_stats"][today]["burned_calories"]) + calories_burned

        # Отправляем пользователю ответ
        await message.reply(
            f"🏃‍♂️ {workout_type.capitalize()} {workout_time} минут — {calories_burned:.2f} ккал.\n"
            f"Дополнительно: выпейте {water_consumed} мл воды."
        )

        # Завершаем состояние
        await state.clear()

    except ValueError:
        await message.reply("Введите корректное число минут.")
    except Exception as e:
        await message.reply(f"Настройте профиль /set_profile")
        await state.clear()


# Проверка прогресса
@router.message(Command("check_progress"))
async def check_progress(message: Message):
    user_id = message.from_user.id
    if user_id not in users:
        await message.reply("Настройте свой профиль с помощью /set_profile.")
        return

    if not all([users[user_id].get(key) for key in ["age", "weight", "height", "activity", "city"]]):
        await message.reply("Профиль не завершён. Пожалуйста, завершите настройку профиля с помощью /set_profile.")
        return

    # Сброс статистики перед отображением (например, по окончании дня)
    reset_daily_stats(user_id)

    user = users[user_id]

    # Прогресс по воде и калориям
    water_progress = f"Вода: {user['logged_water']} из {user['water_goal']} мл"
    water_remain = float(user['water_goal']) - float(user['logged_water'])
    water_to_drink = f"Осталось выпить: {water_remain} мл"

    calorie_progress = f"Калории: {user['logged_calories']} из {user['calorie_goal']} ккал"
    calorie_remain = float(user['calorie_goal']) - float(user['logged_calories'])
    calorie_were_burned = f"Сожжено: {user['burned_calories']} ккал"
    calorie_to_eat = f"Осталось потребить: {calorie_remain} ккал"

    # Отправляем сообщение с прогрессом и историей
    await message.reply(f"📊 Ваш прогресс:\n{water_progress}\n{water_to_drink}\n\n{calorie_progress}\n{calorie_were_burned}\n{calorie_to_eat}")


# Графики с историей прогресса
@router.message(Command("plot_history"))
async def plot_history(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in users:
        await message.reply("Настройте свой профиль с помощью /set_profile.")
        return

    if not all([users[user_id].get(key) for key in ["age", "weight", "height", "activity", "city"]]):
        await message.reply("Профиль не завершён. Пожалуйста, завершите настройку профиля с помощью /set_profile.")
        return

    # Сброс статистики перед отображением (например, по окончании дня)
    reset_daily_stats(user_id)

    user = users[user_id]

    # Данные для графиков
    dates = list(user["daily_stats"].keys())
    calories_logged = [user["daily_stats"][date]["calories"] for date in dates]
    burned_calories = [user["daily_stats"][date]["burned_calories"] for date in dates]
    calories_goals = [user["daily_stats"][date]["calorie_goal"] for date in dates]
    water_logged = [user["daily_stats"][date]["water"] for date in dates]
    water_goals = [user["daily_stats"][date]["water_goal"] for date in dates]

    def plot_and_send(title, ylabel, data_pairs, colors, filename):
        """
        Общая функция для создания и отправки графиков.
        """
        fig, ax = plt.subplots(figsize=(8, 6))
        for data, color, label in data_pairs:
            ax.bar(dates, data, width=0.4, color=color, label=label, alpha=0.7)

        # Настройка оси X
        ax.set_xticks(dates)
        ax.set_xticklabels(dates, rotation=0)

        ax.set_xlabel("Дата")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend()

        # Сохраняем график в буфер
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        photo = BufferedInputFile(buf.read(), filename=filename)
        buf.close()
        return photo

    # Генерация и отправка графика по калориям
    photo = plot_and_send(
        title="Цель по калориям и количество потребленных калорий",
        ylabel="Калории (ккал)",
        data_pairs=[(calories_goals, 'green', 'Цель по калориям'), (calories_logged, 'salmon', 'Съеденные калории')],
        colors=['green', 'salmon'],
        filename='calories_plot.png'
    )
    await message.reply_photo(photo)

    # Генерация и отправка графика по сожженным калориям
    photo = plot_and_send(
        title="Сожженные калории по дням",
        ylabel="Калории (ккал)",
        data_pairs=[(burned_calories, 'orange', 'Сожженные калории')],
        colors=['orange'],
        filename='burned_calories_plot.png'
    )
    await message.reply_photo(photo)

    # Генерация и отправка графика по воде
    photo = plot_and_send(
        title="Цель по воде и количество выпитой воды",
        ylabel="Вода (мл)",
        data_pairs=[(water_goals, 'lightblue', 'Цель по воде'), (water_logged, 'blue', 'Выпитая вода')],
        colors=['lightblue', 'blue'],
        filename='water_plot.png'
    )
    await message.reply_photo(photo)