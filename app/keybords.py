from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests import get_all_locations


reg = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Регистрация', callback_data='reg')]
])
main_one = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Начать игру', callback_data='main')],
    [InlineKeyboardButton(text='Отреактировать имя и фамилию', callback_data='first_name')],
])
main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Начать игру', callback_data='main')]
])

to_the_main_page = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='На главную', callback_data='main')]
])
replace_or_cancel = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Заменить", callback_data="replace"),
            InlineKeyboardButton(text="Отмена", callback_data="main"),
        ]
    ]
)
replace_or_cancel_2 = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Заменить", callback_data="replace_2"),
            InlineKeyboardButton(text="Отмена", callback_data="main"),
        ]
    ]
)

async def inline_location():
    keybord = InlineKeyboardBuilder()
    locations = await get_all_locations()
    for location in locations:
        keybord.add(InlineKeyboardButton(text=location.name, callback_data=f'location_{location.id}'))
    return keybord.adjust(1).as_markup()

def location_info(location):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Маршрут', url=location.locations)],
        [InlineKeyboardButton(text='Задание', callback_data=f'task_{location.id}')],
        [InlineKeyboardButton(text='Отправить фото', callback_data=f'my_photo_{location.id}')],
        [InlineKeyboardButton(text='👈Назад', callback_data='main')],
    ])

# админ
main_admin = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Просмотр фото')],
    [KeyboardButton(text='🏆Победители🏆')],
    [KeyboardButton(text='фото')]
], resize_keyboard=True)

async def create_admin_answer_keyboard(id_photo):
    admin_answer = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅', callback_data=f'yes_{id_photo}'), InlineKeyboardButton(text='❌', callback_data=f'no_{id_photo}')],
        [InlineKeyboardButton(text='Закрыть', callback_data='main')]
    ])
    return admin_answer
