# https://fusionbrain.ai/docs/doc/api-dokumentaciya/
import json
import time

import requests
from dotenv import load_dotenv
import os
import base64


load_dotenv()


KANDINSKY_API = os.getenv('KANDINSKY_API')
KANDINSKY_SECRET_KEY = os.getenv('KANDINSKY_SECRET_KEY')


class Text2ImageAPI:

    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_model(self):
        response = requests.get(
            self.URL + 'key/api/v1/models',
            headers=self.AUTH_HEADERS
            )
        data = response.json()
        return data[0]['id']

    def generate(
            self, prompt, model, images=1, width=1024, height=1024, style='UHD'
            ):
        # styles = ['KANDINSKY', 'UHD', 'ANIME', 'DEFAULT']
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "style": f'{style}',
            "generateParams": {
                "query": f"{prompt}"
            }
        }

        data = {
            'model_id': (None, model),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(
            self.URL + 'key/api/v1/text2image/run',
            headers=self.AUTH_HEADERS, files=data
            )
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(
                self.URL + 'key/api/v1/text2image/status/' + request_id,
                headers=self.AUTH_HEADERS
                )
            data = response.json()
            if data['status'] == 'DONE':
                return data['images']

            attempts -= 1
            time.sleep(delay)


if __name__ == '__main__':
    kandinsky_api = Text2ImageAPI(
        'https://api-key.fusionbrain.ai/',
        KANDINSKY_API,
        KANDINSKY_SECRET_KEY
        )
    model_id = kandinsky_api.get_model()
    uuid = kandinsky_api.generate("океан в лучах заката", model_id)
    images = kandinsky_api.check_generation(uuid)
    image_base64 = images[0]
    image_data = base64.b64decode(image_base64)
    with open("image.jpg", "wb") as file:
        file.write(image_data)
