import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# Токен Telegram-бота
API_TOKEN = os.getenv("BOT_TOKEN")

# API для погоды (OpenWeatherMap)
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

# API для продуктов питания (OpenFoodFacts)
FOOD_API_URL = "https://world.openfoodfacts.org/cgi/search.pl"

# API для расчета сожженных калорий после тренировок
CALORIES_BURNED_API_KEY = os.getenv("CALORIES_BURNED_API_KEY")
CALORIES_BURNED_API_URL="https://api.api-ninjas.com/v1/caloriesburned"

if not API_TOKEN or not WEATHER_API_KEY or not WGER_API_KEY:
    raise ValueError("Необходимо указать BOT_TOKEN и WEATHER_API_KEY и WGER_API_KEY в .env файле.")