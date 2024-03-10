import tiktoken
import requests
import os
from dotenv import load_dotenv

load_dotenv()

AUTH_TOKEN: str = os.getenv('AUTH_TOKEN')


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
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru,en;q=0.9",
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Connection": "keep-alive",
        "Host": "local.proxyapi.ru",
        "Origin": "https://console.proxyapi.ru",
        "Referer": "https://console.proxyapi.ru",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0"
        " YaBrowser/24.1.0.0 Safari/537.36",
        "sec-ch-ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", "
        "\"YaBrowser\";v=\"24.1\", \"Yowser\";v=\"2.5\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Linux\""
    }
    responce = requests.get(
        url='https://local.proxyapi.ru/auth/me', headers=headers
        )
    return responce.json().get('balance')


def get_text(model):
    image_generate_model = (
        model.startswith('dall-e-') or model.startswith('kandinsky')
        )
    text = ('💬 Задайте вопрос — после ответа можно '
            'дать уточняющие правки и скорректировать ответ.')
    if image_generate_model:
        text = '💬 Напишите промт для генерации изображения'
    return text
