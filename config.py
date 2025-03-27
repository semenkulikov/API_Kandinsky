from dotenv import find_dotenv, load_dotenv
import os

if find_dotenv():
    load_dotenv()
else:
    exit("Переменные окружения не загружены, т.к. отсутствует файл .env")


API_URL = "https://api-key.fusionbrain.ai/"
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
