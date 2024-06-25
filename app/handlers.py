from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from datetime import datetime
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext


import app.keybords as kd
import app.database.requests as rq
from app.database.requests import get_location, save_photo
from app.keybords import location_info


router = Router()


class Photo(StatesGroup):
    photo = State()
    replace_photo = State()

class Reg(StatesGroup):
    name = State()


@router.callback_query(F.data.in_({'reg', 'first_name'}))
async def main(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Reg.name)
    await callback.message.answer('Введите вашу фамилию и имя:')


@router.message(Reg.name)
async def main(message: Message, state: FSMContext):
    username = message.from_user.username if message.from_user.username else None
    await rq.set_user(
        tg_id=message.from_user.id, name=message.text, username=username)
    await message.answer(
        f'Спасибо, регистрация завершена.\n Ваша фамилия и имя: {message.text}',
        reply_markup=kd.main_one
    )
    await state.clear()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_in_bd = await rq.user_in_bd(message.from_user.id)
    if not user_in_bd:
        await message.answer('Привет, я бот, который поможет тебе познакомиться с памятными местями для компании Альфасигма, а если ты умпеешь сфотографирорваться первым рядом со всем местами, то ты выиграешь наш конкурс и получишь приз на конференции!!!',
                          reply_markup=kd.reg)
    else:
        await message.answer('Привет, я бот, который поможет тебе познакомиться с памятными местями для компании Альфасигма, а если ты умпеешь сфотографирорваться первым рядом со всем местами, то ты выиграешь наш конкурс и получишь приз на конференции!!!',
                          reply_markup=kd.main)
    if message.from_user.id == int('973404201'):
        await message.answer('Вы авторизовались как админ', reply_markup=kd.main_admin)

@router.message(Command('help'))
async def get_help(message: Message):
    await message.answer('Это команда /help')

@router.message(F.data =='')
async def main(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer('Выберите локацию:', reply_markup=await kd.inline_location())

@router.callback_query(F.data =='main')
async def main(callback: CallbackQuery,  state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.answer('Выберите локацию:', reply_markup=await kd.inline_location())


@router.callback_query(F.data.startswith('location_'))
async def main(callback: CallbackQuery):
    await callback.answer()
    lctn = await get_location(callback.data.split('_')[1])
    if lctn:
        await callback.message.answer_photo(caption=lctn.description, photo=lctn.photo, reply_markup=location_info(lctn))
    else:
        await callback.message.edit_text("Location not found")


@router.callback_query(F.data.startswith('task_'))
async def main(callback: CallbackQuery):
    await callback.answer()
    task = await rq.get_task(callback.data.split('_')[1])
    task_photo = await rq.get_task_photo(callback.data.split('_')[1])
    if task_photo:
        await callback.message.answer_photo(photo=task_photo, caption=task)
    else:
        await callback.message.answer(task)


@router.callback_query(F.data.startswith('my_photo_'))
async def main(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    id_location = int(callback.data.split('_')[2])

    result = await rq.get_photos_from_db_with_location(id_location, callback.from_user.id)
    await state.update_data(id_location=id_location)
    if result != None:
        photo_id, photo_exists = result
        await state.update_data(photo_id=photo_id, photo_exists=photo_exists)
        await callback.message.answer_photo(photo=photo_exists, caption='У вас уже есть фото для этой локации. Вы хотите заменить его?', reply_markup=kd.replace_or_cancel)
    else:
        await state.set_state(Photo.photo)
        await callback.message.answer('Отправьте ваше фото', reply_markup=kd.to_the_main_page)

@router.message(Photo.photo)
async def main(message: Message, state: FSMContext):
    data = await state.get_data()
    id_location = data.get('id_location')
    if message.photo:
        photo_file_id = message.photo[-1].file_id
        # print(photo_file_id) # Для получения id фотки любой
        user_tg_id = message.from_user.id
        sent_at = datetime.utcnow()
        await save_photo(user_tg_id,  photo_file_id, id_location, sent_at)
        admin_chat_id = -4240133579
        await message.bot.send_photo(admin_chat_id, photo=photo_file_id, caption=f'Photo from location ID: {id_location}')
        
        await message.answer(f'Фото отправлено администратору на проверку. Location ID: {id_location}', reply_markup=kd.to_the_main_page)
        await state.clear()
    else:
        await message.answer('Пожалуйста, отправьте фото.', reply_markup=kd.to_the_main_page)

@router.callback_query(F.data =='replace')
async def main(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('При замене старое фото будет удалено из базы и не будет учитываться в результатах игры', reply_markup=kd.replace_or_cancel_2)
    await state.update_data(replace_confirmed=True)

@router.callback_query(F.data =='replace_2')
async def main(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    if data.get('replace_confirmed'):
        data = await state.get_data()
    photo_id = data.get('photo_id')
    if photo_id:
        await rq.delete_photo_from_db(photo_id)
        await callback.message.answer('Старое фото удалено. Пожалуйста, отправьте новое фото.', reply_markup=kd.to_the_main_page)
        await state.set_state(Photo.photo)


# админ
async def send_next_photo_for_review(chat_id, bot):
    photo = await rq.get_photos_from_db(admin_true=0)
    if not photo:
        await bot.send_message(chat_id, 'Нет новых фото для проверки.')
        return
    photo_id = photo['photo']
    admin_answer_keyboard = await kd.create_admin_answer_keyboard(photo['id'])
    caption = f"Проверьте фото\nМестоположение: {photo['location_name']}\nОтправитель:{photo['name']}\nНик: @{photo['username']}"
    await bot.send_photo(chat_id, photo_id, caption=caption, reply_markup=admin_answer_keyboard)


@router.message(F.text == 'Просмотр фото')
async def answer_admin(message: Message):
    await send_next_photo_for_review(message.chat.id, message.bot)

@router.message(F.text == '🏆Победители🏆')
async def answer_admin_win(message: Message):
    winners = await rq.answer_admin_win()
    if winners:
        winners_text = "\n\n".join(winners)
        await message.answer(f"Список победителей:\n\n{winners_text}")
    else:
        await message.answer("На данный момент нет победителей.")


@router.callback_query(F.data.startswith('yes_'))
async def approve_photo(callback: CallbackQuery):
    photo_id = callback.data.split('_')[1]
    await rq.update_photo_status(photo_id, admin_true=1)
    await callback.answer('Фото одобрено.')
    await callback.message.delete()
    user_id = await rq.get_user_id_by_photo_id(photo_id)
    photo_tg_id = await rq.get_photo_tg_id(photo_id)
    await callback.bot.send_photo(user_id, photo=photo_tg_id, caption="Ваша фотография одобрена")
    is_winner = await rq.check_winner(user_id)
    if is_winner:
        await callback.bot.send_message(user_id, f"Поздравляем! Вы прошли игру и заняли {is_winner} место")
    await send_next_photo_for_review(callback.message.chat.id, callback.bot)


@router.callback_query(F.data.startswith('no_'))
async def reject_photo(callback: CallbackQuery):
    photo_id = callback.data.split('_')[1]
    user_id = await rq.get_user_id_by_photo_id(photo_id)
    if user_id:
        photo_tg_id = await rq.get_photo_tg_id(photo_id)
        await callback.bot.send_photo(user_id, photo=photo_tg_id, caption="К сожалению, ваша фотография не удовлетворяет установленным требованиям.")
    await rq.delete_photo_from_db(photo_id)
    await callback.answer('Фото отклонено.')
    await callback.message.delete()
    await send_next_photo_for_review(callback.message.chat.id, callback.bot)


@router.message()
async def handle_unknown_message(message: Message):
    await message.reply("Извините, я не понимаю этот запрос. Пожалуйста, используйте команду /help для получения списка доступных команд.")