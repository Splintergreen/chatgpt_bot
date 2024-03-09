from aiogram.enums import ParseMode
from openai import OpenAI
import os
from aiogram import Router
from aiogram.filters import CommandStart, StateFilter, Text, BaseFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from database import messages
from keyboards import (another_question, back_button, bottom_menu,
                       start_keyboard, choose_model)
from utils import num_tokens_from_messages, get_balance
from dotenv import load_dotenv


load_dotenv()

OPENAI_KEY: str = os.getenv('OPENAI_KEY')

client = OpenAI(
    api_key=OPENAI_KEY,
    base_url="https://api.proxyapi.ru/openai/v1",
)


class TokenLimitError(Exception):
    pass


token_limit = 4096


router: Router = Router()


class FSMMessages(StatesGroup):
    message = State()
    model = State()


admin_id: int = int(os.getenv('admin_ids'))


class IsAdmin(BaseFilter):
    def __init__(self, admin_id: int) -> None:
        self.admin_id = admin_id

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == self.admin_id


router.message.filter(IsAdmin(admin_id))
router.callback_query.filter(IsAdmin(admin_id))


@router.message(CommandStart(), StateFilter(default_state))
async def start_command(message: Message, state: FSMContext):
    message_state = await state.get_data()
    model = message_state.get('model')
    if model is None:
        text = 'Выберите необходимую модель ChatGPT.'
        await state.set_state(FSMMessages.model)
        await message.answer(text, reply_markup=choose_model())
    else:
        await state.clear()
        text = (f'Здравствуйте {message.from_user.full_name}\n'
                'Вас приветствует ChatGPT bot')
        await message.answer(text, reply_markup=start_keyboard)
        # await state.set_state(FSMMessages.message)
        await state.update_data(model=model)


@router.callback_query(Text(text='main_menu'))
async def main_menu_call(call: CallbackQuery, state: FSMContext):
    message_state = await state.get_data()
    model = message_state.get('model')
    if model is None:
        text = 'Выберите необходимую модель ChatGPT.'
        await state.set_state(FSMMessages.model)
        await call.message.answer(text, reply_markup=choose_model())
        await call.answer()
    else:
        text = (f'Здравствуйте {call.message.from_user.full_name}\n'
                'Вас приветствует ChatGPT bot')
        await call.message.answer(text, reply_markup=start_keyboard)
        await call.answer()
        # await state.set_state(FSMMessages.message)
        await state.clear()
        await state.update_data(model=model)


@router.callback_query(Text(text='model_select'))
async def select_model(call: CallbackQuery, state: FSMContext):
    text = 'Выберите модель.'
    await state.set_state(FSMMessages.model)
    await call.message.answer(text, reply_markup=choose_model())
    await call.answer()


@router.callback_query(
        Text(startswith='selectedmodel_'), StateFilter(FSMMessages.model)
        )
async def chose_model(call: CallbackQuery, state: FSMContext):
    model = call.data.split('_')[1]
    text = ('💬 Задайте вопрос — после ответа можно '
            'дать уточняющие правки и скорректировать ответ.')
    await call.message.answer(
        f'Выбрана модель {model}\n {text}', reply_markup=back_button
        )
    await state.update_data(model=model)
    await state.set_state(FSMMessages.message)
    await call.answer()


@router.callback_query(Text(text='start_chat'), StateFilter(default_state))
async def start_chat_call(call: CallbackQuery, state: FSMContext):
    text = ('💬 Задайте вопрос — после ответа можно '
            'дать уточняющие правки и скорректировать ответ.')
    await call.message.answer(text, reply_markup=back_button)
    await call.answer()
    await state.set_state(FSMMessages.message)


@router.callback_query(Text(text='about'), StateFilter(default_state))
async def about_call(call: CallbackQuery, state: FSMContext):
    message_state = await state.get_data()
    model = message_state.get('model')
    text = (
        f'ChatGPT bot, выбрана модель - "{model}".\n'
        f'Баланс Proxyapi: {get_balance()}')
    await call.message.answer(text, reply_markup=back_button)
    await call.answer()


@router.message(StateFilter(FSMMessages.message))
async def bot_dialog(message: Message, state: FSMContext):
    await message.answer('Подождите, загружаю ответ...')
    await state.update_data(message=message)
    message_state = await state.get_data()
    model = message_state.get('model')
    # image_generate_model = model.startswith('dall-e-')
    try:
        messages.append({'role': 'user', 'content': message.text})
        token_in_message = num_tokens_from_messages(messages)
        if token_in_message >= token_limit:
            raise TokenLimitError
        # elif image_generate_model:
        #     response = client.images.generate(
        #         model=model,
        #         prompt=message.text,
        #         n=1,
        #         size="1024x1024",
        #         )
        else:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.5,
                max_tokens=token_limit-num_tokens_from_messages(messages)
            )
            total_token = response.usage.total_tokens
            if total_token >= token_limit:
                raise TokenLimitError
    except TokenLimitError:
        text = (
            'Использовано максимум токенов в контексте!\n'
            'Контекст будет очищен!'
             )
        messages.clear()
        await message.answer(
            text,
            reply_markup=another_question
            )
    except Exception as ex:
        text = f'Ошибка - {ex}'
        await message.answer(text, reply_markup=back_button)
    # if image_generate_model:
        # message.answer_photo(photo=response.data[0].url)
    else:
        text = response.choices[0].message.content
        await message.answer(
            text, reply_markup=bottom_menu, parse_mode=ParseMode.MARKDOWN
            )
        await state.update_data(message=message)


@router.callback_query(Text(text='another_question'))
async def another_question_call(call: CallbackQuery, state: FSMContext):
    messages.clear()
    # await state.clear()
    await state.update_data(message=None)
    text = 'Задайте новый вопрос 💬'
    await call.message.answer(text, reply_markup=back_button)
    await call.answer()
    await state.set_state(FSMMessages.message)


@router.callback_query(Text(text='new_answer'))
async def new_answer_call(call: CallbackQuery, state: FSMContext):
    message_state = await state.get_data()
    message = message_state.get('message')
    await call.answer()
    await bot_dialog(message, state)
