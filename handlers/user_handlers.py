import openai
import os
from aiogram import Router
from aiogram.filters import CommandStart, StateFilter, Text, BaseFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from database import messages
from keyboards import (another_question, back_button, bottom_menu,
                       start_keyboard)
from utils import num_tokens_from_messages
from dotenv import load_dotenv

load_dotenv()


class TokenLimitError(Exception):
    pass


token_limit = 4096


router: Router = Router()


class FSMMessages(StatesGroup):
    message = State()


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
    await state.clear()
    text = (f'Здравствуйте {message.from_user.full_name}\n'
            'Вас приветствует ChatGPT bot')
    await message.answer(text, reply_markup=start_keyboard)


@router.callback_query(Text(text='main_menu'))
async def main_menu_call(call: CallbackQuery, state: FSMContext):
    text = (f'Здравствуйте {call.message.from_user.full_name}\n'
            'Вас приветствует ChatGPT bot')
    await call.message.answer(text, reply_markup=start_keyboard)
    await call.answer()
    await state.clear()


@router.callback_query(Text(text='start_chat'), StateFilter(default_state))
async def start_chat_call(call: CallbackQuery, state: FSMContext):
    text = ('💬 Задайте вопрос — после ответа можно '
            'дать уточняющие правки и скорректировать ответ.')
    await call.message.answer(text, reply_markup=back_button)
    await call.answer()
    await state.set_state(FSMMessages.message)


@router.callback_query(Text(text='about'), StateFilter(default_state))
async def about_call(call: CallbackQuery):
    text = (
        'ChatGPT bot, модель "gpt-3.5-turbo".\n\n'
        'Вы можете изменить "Температуру" выдачи ответов, добавив в конце запроса - '
        '"Use a temperature of (значение от 0.1 до 78.0)"\n\n'
        'Чем больше значение тем более творческий будет ответ, чем меньше значение тем научнее будет ответ.\n'
        'По умолчанию установлено значение 0.5.')
    await call.message.answer(text, reply_markup=back_button)
    await call.answer()


@router.message(StateFilter(FSMMessages.message))
async def bot_dialog(message: Message, state: FSMContext):
    await message.answer('Подождите, загружаю ответ...')
    await state.update_data(message=message)
    try:
        messages.append({'role': 'user', 'content': message.text})
        token_in_message = num_tokens_from_messages(messages)
        if token_in_message >= token_limit:
            raise TokenLimitError
        else:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.5,
                max_tokens=token_limit-num_tokens_from_messages(messages)
            )
            total_token = response['usage']['total_tokens']
            if total_token >= token_limit:
                raise TokenLimitError
    except TokenLimitError:
        text = (
            'Использовано максимум токенов в контексте!\n'
            'Контекст будет очищен!'
             )
        messages.clear()
        await message.answer(text, reply_markup=another_question)
    except Exception as ex:
        text = f'Ошибка - {ex}'
        await message.answer(text, reply_markup=back_button)
    else:
        text = response['choices'][0]['message']['content']
        await message.answer(text, reply_markup=bottom_menu)
        await state.update_data(message=message)


@router.callback_query(Text(text='another_question'))
async def another_question_call(call: CallbackQuery, state: FSMContext):
    messages.clear()
    await state.clear()
    text = 'Задайте новый вопрос 💬'
    await call.message.answer(text, reply_markup=back_button)
    await call.answer()
    await state.set_state(FSMMessages.message)


@router.callback_query(Text(text='new_answer'))
async def new_answer_call(call: CallbackQuery, state: FSMContext):
    message_state = await state.get_data()
    message = message_state['message']
    await call.answer()
    await bot_dialog(message, state)
