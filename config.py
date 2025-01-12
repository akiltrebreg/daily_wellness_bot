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
FOOD_API_URL = "https://world.openfoodfacts.org/api/v0/product"

if not API_TOKEN or not WEATHER_API_KEY:
    raise ValueError("Необходимо указать BOT_TOKEN и WEATHER_API_KEY в .env файле.")