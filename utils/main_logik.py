import os
from dotenv import load_dotenv
from database import messages
from aiogram.enums import ParseMode
from openai import OpenAI
from aiogram.types import FSInputFile
from keyboards import (another_question, back_button,
                       bottom_menu, start_keyboard, choose_model)
from utils import num_tokens_from_messages
from .logger_config import setup_logger
from utils.kandinsky import Text2ImageAPI
import aiohttp
import base64
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup


load_dotenv()


logger = setup_logger('main_logik')


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


class FSMMessages(StatesGroup):
    message = State()
    model = State()


async def handle_model_selection(entity, state: FSMContext, is_callback=False):
    try:
        message_state = await state.get_data()
        model = message_state.get('model')
        if model is None:
            text = ('Выберите модель "gpt" для работы с текстом, '
                    '"dall-e" или "kandinsky" для генерации изображений.')
            await state.set_state(FSMMessages.model)
            if is_callback:
                await entity.message.answer(text, reply_markup=choose_model())
                await entity.answer()
            else:
                await entity.answer(text, reply_markup=choose_model())
        else:
            await state.clear()
            text = (f'Здравствуйте {entity.from_user.full_name}\n'
                    'Вас приветствует ChatGPT bot')
            if is_callback:
                await entity.message.answer(text, reply_markup=start_keyboard)
                await entity.answer()
            else:
                await entity.answer(text, reply_markup=start_keyboard)
            await state.update_data(model=model)
    except Exception as err:
        logger.error(f'Ошибка в обработке handler "/start" - {err}')


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
    try:
        style = model.split('-')[-1]
        model_id = kandinsky_api.get_model()
        uuid = kandinsky_api.generate(message.text, model_id, style=style)
        images = kandinsky_api.check_generation(uuid)
        image_data = base64.b64decode(images[0])
        await save_and_send_image(image_data, message, 'temp_kald_image.jpg')
    except Exception as err:
        logger.error(
            'Ошибка выполнения функции '
            f'"process_kandinsky_image_model" - {err}'
            )


async def process_text_model(model, message, state):
    try:
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
    except Exception as err:
        logger.error(f'Ошибка выполнения функции "process_text_model" - {err}')


async def download_and_send_image(url, message, filename):
    try:
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
    except Exception as err:
        logger.error(
            f'Ошибка выполнения функции "download_and_send_image" - {err}'
            )


async def save_and_send_image(image_data, message, filename):
    try:
        with open(filename, "wb") as file:
            file.write(image_data)
        photo = FSInputFile(filename)
        await message.answer_photo(
            photo=photo,
            caption=f'Изображение по запросу: {message.text}',
            reply_markup=bottom_menu
            )
    except Exception as err:
        logger.error(
            f'Ошибка выполнения функции "save_and_send_image" - {err}'
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
