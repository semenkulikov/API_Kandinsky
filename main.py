import os
import json
import time
import requests
import base64
from config import API_URL, API_KEY, SECRET_KEY


class FusionBrainAPI:
    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}'
        }

    def get_pipeline(self):
        """ Метод для выбора модели ИИ """
        response = requests.get(self.URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS)
        data = response.json()
        # Выбираем первую модель (на данный момент только Kandinsky доступен)
        return data[0]['id']

    def generate(self, prompt, pipeline, images=1, width=1024, height=1024, style=None, negative_prompt=None):
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": prompt
            }
        }
        if style:
            params["style"] = style
        if negative_prompt:
            params["negativePromptDecoder"] = negative_prompt

        data = {
            'pipeline_id': (None, pipeline),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/pipeline/run', headers=self.AUTH_HEADERS, files=data)
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + f'key/api/v1/pipeline/status/{request_id}', headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['result']['files']
            elif data['status'] == 'FAIL':
                raise Exception(f"Ошибка генерации: {data.get('errorDescription')}")
            attempts -= 1
            time.sleep(delay)
        raise TimeoutError("Время ожидания генерации изображения истекло")


def save_image(base64_data, file_path):
    """
    Функция для сохранения изображения
    :param base64_data: бинарные данные файла
    :param file_path: путь, куда надо сохранить
    :return:
    """
    image_data = base64.b64decode(base64_data)
    with open(file_path, 'wb') as f:
        f.write(image_data)

def get_user_choice():
    """Выбор источника промпта"""
    print("\nВыберите источник промпта:")
    print("1. Ввести текст вручную")
    print("2. Загрузить из файла input.txt")
    while True:
        choice = input("Ваш выбор (1/2): ").strip()
        if choice in ['1', '2']:
            return choice
        print("Ошибка: введите 1 или 2")

def get_prompt_from_user():
    """Многострочный ввод от пользователя"""
    return input("Введите описание изображения: ")

def get_prompt_from_file():
    """Чтение промпта из файла"""
    try:
        with open("input.txt", "r", encoding="utf-8") as f:
            prompts = f.readlines()
            prompts = [i.strip("\n") for i in prompts]
            if not prompts:
                raise ValueError("Файл input.txt пуст")
            return prompts
    except FileNotFoundError:
        print("Ошибка: файл input.txt не найден")
    except Exception as e:
        print(f"Ошибка чтения файла: {str(e)}")
    return None


def get_user_input():
    """Ввод количества изображений"""
    while True:
        try:
            num = int(input("Сколько изображений сгенерировать для каждого промта? (1-1000): "))
            if 1 <= num <= 1000:
                return num
            print("Число должно быть от 1 до 1000!")
        except ValueError:
            print("Введите целое число!")


def main():

    print("Получение промтов из файла...")
    prompts = get_prompt_from_file()

    # Создание папки photos, если она не существует
    os.makedirs("photos", exist_ok=True)

    # Инициализация API
    api = FusionBrainAPI(API_URL, API_KEY, SECRET_KEY)
    pipeline_id = api.get_pipeline()
    print("Используемая модель (pipeline):", pipeline_id)

    num_images = get_user_input()  # Получаем количество через интерактивный ввод

    for index, prompt in enumerate(prompts):
        print(f"\nОбработка промта {index + 1}/{len(prompts)}")
        for i in range(num_images):
            print(f"\n\tГенерация изображения {i + 1}/{num_images}")
            uuid = api.generate(prompt, pipeline_id)
            print("\tUUID запроса:", uuid)

            # Проверка статуса и получение сгенерированного изображения
            print("\tОжидание генерации изображения...")
            files = api.check_generation(uuid)

            timestamp = int(time.time())
            for file_data in files:
                file_name = os.path.join("photos", f"image_{timestamp}_{index + 1}_{i + 1}.png")
                save_image(file_data, file_name)
                print(f"\tИзображение сохранено: {file_name}")


if __name__ == '__main__':
    main()
