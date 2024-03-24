import os

import requests
import tiktoken
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY: str = os.getenv('OPENAI_KEY')


def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4":
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4
        tokens_per_name = -1
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(
            f'num_tokens_from_messages() is not implemented for model {model}.'
            )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens


def get_balance():
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_KEY}',
    }
    response = requests.get(
        url='https://api.proxyapi.ru/proxyapi/balance',
        headers=headers
        )
    return response.json().get('balance')


def get_text(model):
    image_generate_model = (
        model.startswith('dall-e-') or model.startswith('kandinsky')
        )
    text = ('💬 Задайте вопрос — после ответа можно '
            'дать уточняющие правки и скорректировать ответ.')
    if image_generate_model:
        text = '💬 Напишите промт для генерации изображения'
    return text
