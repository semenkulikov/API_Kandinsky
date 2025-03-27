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
    image_data = base64.b64decode(base64_data)
    with open(file_path, 'wb') as f:
        f.write(image_data)


def main():
    # Чтение описания из input.txt
    with open("input.txt", "r", encoding="utf-8") as file:
        prompt = file.read().strip()

    # Создание папки photos, если она не существует
    os.makedirs("photos", exist_ok=True)

    # Инициализация API
    api = FusionBrainAPI(API_URL, API_KEY, SECRET_KEY)
    pipeline_id = api.get_pipeline()
    print("Используемая модель (pipeline):", pipeline_id)

    # Отправка запроса на генерацию
    uuid = api.generate(prompt, pipeline_id)
    print("UUID запроса:", uuid)

    # Проверка статуса и получение сгенерированного изображения
    print("Ожидание генерации изображения...")
    files = api.check_generation(uuid)

    # Сохранение изображения (в данном примере ожидается одно изображение)
    for idx, file_data in enumerate(files):
        file_name = os.path.join("photos", f"image_{idx + 1}.png")
        save_image(file_data, file_name)
        print(f"Изображение сохранено: {file_name}")


if __name__ == '__main__':
    main()
