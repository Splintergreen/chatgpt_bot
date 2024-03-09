from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


start_keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='Начать общение с ChatGPT', callback_data='start_chat'
                )
        ],
        [
            InlineKeyboardButton(
                text='About', callback_data='about'
                )
        ]
    ]
)

bottom_menu: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='Задать другой вопрос', callback_data='another_question'
                )
        ],
        [
            InlineKeyboardButton(
                text='Новый ответ', callback_data='new_answer'
                )
        ],
        [
            InlineKeyboardButton(
                text='Выбрать модель', callback_data='model_select'
            )
        ],
        [
            InlineKeyboardButton(
                text='Основное меню', callback_data='main_menu'
            )
        ]
    ]
)

back_button: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text='Назад',
            callback_data='main_menu'
            )],
        [InlineKeyboardButton(
            text='Выбрать модель',
            callback_data='model_select'
            )]
    ]
)

another_question: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='Задать другой вопрос', callback_data='another_question'
                )
        ],
    ]
)


def choose_model():
    models = [
        'gpt-4-turbo-preview',
        'gpt-3.5-turbo',
        # 'dall-e-3',
        # 'dall-e-2',
        ]
    buttons = [
        InlineKeyboardButton(text=model, callback_data='selectedmodel_'+model)
        for model in models
        ]
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    kb_builder.row(*buttons, width=2)
    # print(kb_builder.as_markup())
    return kb_builder.as_markup()
