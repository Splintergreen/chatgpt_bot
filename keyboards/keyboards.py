from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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
                text='Основное меню', callback_data='main_menu'
            )
        ]
    ]
)

back_button: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='main_menu')]
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
