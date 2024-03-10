import os
from dotenv import load_dotenv
from database import messages
from aiogram.enums import ParseMode
from openai import OpenAI
from aiogram.types import FSInputFile
from keyboards import another_question, back_button, bottom_menu
from utils import num_tokens_from_messages
from utils.kandinsky import Text2ImageAPI
import aiohttp
import base64


load_dotenv()

OPENAI_KEY: str = os.getenv('OPENAI_KEY')
KANDINSKY_API = os.getenv('KANDINSKY_API')
KANDINSKY_SECRET_KEY = os.getenv('KANDINSKY_SECRET_KEY')

client = OpenAI(
    api_key=OPENAI_KEY,
    base_url="https://api.proxyapi.ru/openai/v1",
)


kandinsky_api = Text2ImageAPI(
    'https://api-key.fusionbrain.ai/',
    KANDINSKY_API,
    KANDINSKY_SECRET_KEY
    )


class ErrorURLToFileConvert(Exception):
    pass


token_limit = 4096


def get_text(model):
    image_generate_model = (
        model.startswith('dall-e-') or model.startswith('kandinsky')
        )
    text = ('💬 Задайте вопрос — после ответа можно '
            'дать уточняющие правки и скорректировать ответ.')
    if image_generate_model:
        text = '💬 Напишите промт для генерации изображения'
    return text


async def process_message(model, message, state):
    if is_dalle_image_model(model):
        await process_dalle_image_model(model, message)
    elif is_kandinsky_image_model(model):
        await process_kandinsky_image_model(model, message)
    else:
        await process_text_model(model, message, state)


async def process_dalle_image_model(model, message, size='1024x1024'):
    response = client.images.generate(
        model=model, prompt=message.text, n=1, size=size
        )
    image_url = response.data[0].url
    await download_and_send_image(image_url, message, 'temp_dalle_image.jpg')


async def process_kandinsky_image_model(model, message):
    style = model.split('-')[-1]
    model_id = kandinsky_api.get_model()
    uuid = kandinsky_api.generate(message.text, model_id, style=style)
    images = kandinsky_api.check_generation(uuid)
    image_data = base64.b64decode(images[0])
    await save_and_send_image(image_data, message, 'temp_kald_image.jpg')


async def process_text_model(model, message, state):
    messages.append({'role': 'user', 'content': message.text})
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.5,
        max_tokens=token_limit-num_tokens_from_messages(messages)
    )
    text = response.choices[0].message.content
    await message.answer(
        text, reply_markup=bottom_menu, parse_mode=ParseMode.MARKDOWN
        )
    await state.update_data(message=message)


async def download_and_send_image(url, message, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise ErrorURLToFileConvert
            with open(filename, "wb") as f:
                while True:
                    chunk = await resp.content.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)
    photo = FSInputFile(filename)
    await message.answer_photo(
        photo=photo,
        caption=f'Изображение по запросу: {message.text}',
        reply_markup=bottom_menu
        )


async def save_and_send_image(image_data, message, filename):
    with open(filename, "wb") as file:
        file.write(image_data)
    photo = FSInputFile(filename)
    await message.answer_photo(
        photo=photo,
        caption=f'Изображение по запросу: {message.text}',
        reply_markup=bottom_menu
        )


async def handle_token_limit_error(message):
    text = 'Использовано максимум токенов в контексте!\nКонтекст будет очищен!'
    messages.clear()
    await message.answer(text, reply_markup=another_question)


async def handle_general_error(message, err):
    text = f'Ошибка - {err}'
    await message.answer(text, reply_markup=back_button)


def is_dalle_image_model(model):
    return model.startswith('dall-e-')


def is_kandinsky_image_model(model):
    return model.startswith('kandinsky')
