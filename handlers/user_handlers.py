import os
from aiogram import Router
from aiogram.filters import CommandStart, StateFilter, Text, BaseFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from database import messages
from keyboards import back_button, start_keyboard, choose_model
from utils import (get_balance, get_text, process_message,
                   handle_general_error, handle_token_limit_error)


class TokenLimitError(Exception):
    pass


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
        text = ('Выберите модель "gpt" для работы с текстом, '
                '"dall-e" или "kandinsky" для генерации изображений.')
        await state.set_state(FSMMessages.model)
        await message.answer(text, reply_markup=choose_model())
    else:
        await state.clear()
        text = (f'Здравствуйте {message.from_user.full_name}\n'
                'Вас приветствует ChatGPT bot')
        await message.answer(text, reply_markup=start_keyboard)
        await state.update_data(model=model)


@router.callback_query(Text(text='main_menu'))
async def main_menu_call(call: CallbackQuery, state: FSMContext):
    message_state = await state.get_data()
    model = message_state.get('model')
    if model is None:
        text = ('Выберите модель "gpt" для работы с текстом, '
                '"dall-e" или "kandinsky" для генерации изображений.')
        await state.set_state(FSMMessages.model)
        await call.message.answer(text, reply_markup=choose_model())
        await call.answer()
    else:
        text = (f'Здравствуйте {call.message.from_user.full_name}\n'
                'Вас приветствует ChatGPT bot')
        await call.message.answer(text, reply_markup=start_keyboard)
        await call.answer()
        await state.clear()
        await state.update_data(model=model)


@router.callback_query(Text(text='model_select'))
async def select_model(call: CallbackQuery, state: FSMContext):
    text = ('Выберите модель "gpt" для работы с текстом, '
            '"dall-e" или "kandinsky" для генерации изображений.')
    await state.set_state(FSMMessages.model)
    await call.message.answer(text, reply_markup=choose_model())
    await call.answer()


@router.callback_query(
        Text(startswith='selectedmodel_'), StateFilter(FSMMessages.model)
        )
async def chose_model(call: CallbackQuery, state: FSMContext):
    model = call.data.split('_')[1]
    text = get_text(model)
    await call.message.answer(
        f'Выбрана модель "{model}"\n {text}', reply_markup=back_button
        )
    await state.update_data(model=model)
    await state.set_state(FSMMessages.message)
    await call.answer()


@router.callback_query(Text(text='start_chat'), StateFilter(default_state))
async def start_chat_call(call: CallbackQuery, state: FSMContext):
    message_state = await state.get_data()
    model = message_state.get('model')
    text = get_text(model)
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

    try:
        await process_message(model, message, state)
    except TokenLimitError:
        await handle_token_limit_error(message)
    except Exception as err:
        await handle_general_error(message, err)


@router.callback_query(Text(text='another_question'))
async def another_question_call(call: CallbackQuery, state: FSMContext):
    messages.clear()
    await state.update_data(message=None)
    text = 'Напишите новый запрос 💬'
    await call.message.answer(text, reply_markup=back_button)
    await call.answer()
    await state.set_state(FSMMessages.message)


@router.callback_query(Text(text='new_answer'))
async def new_answer_call(call: CallbackQuery, state: FSMContext):
    message_state = await state.get_data()
    message = message_state.get('message')
    await call.answer()
    await bot_dialog(message, state)
