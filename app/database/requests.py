from app.database.models import async_session
from app.database.models import User, Photo, Location, Winner
from sqlalchemy import distinct, func, select
from sqlalchemy import update, delete


async def set_user(tg_id, username=None, name=None, second_name=None):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            session.add(User(tg_id=tg_id, username=username,name=name))
        else:
            if name is not None:
                user.name = name
            if second_name is not None:
                user.second_name = second_name
            if username is not None:
                user.username = username
        await session.commit()

async def user_in_bd(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            return True
        return False


async def get_all_locations():
    async with async_session() as session:
        result = await session.execute(select(Location))
        return result.scalars().all()

async def get_location(location_id):
    async with async_session() as session:
        return await session.scalar(select(Location).where(Location.id == location_id))

async def get_task(location_id):
    async with async_session() as session:
        return await session.scalar(select(Location.task).where(Location.id == location_id))

async def get_task_photo(location_id):
    async with async_session() as session:
        return await session.scalar(select(Location.task_photo).where(Location.id == location_id))

async def get_descreption_photo(location_id):
    async with async_session() as session:
        return await session.scalar(select(Location.descreption_photo).where(Location.id == location_id))

async def save_photo_to_db(tg_id,  file_path, location_id, sent_at):
    await set_user(tg_id)
    async with async_session() as session:
        new_photo = Photo(
            user_tg_id=tg_id,
            photo=file_path,
            location_id=location_id,
            sent_at=sent_at
        )
        session.add(new_photo)
        await session.commit()

async def get_photos_from_db_with_location(id_location, user_id):
    async with async_session() as session:
        photo_info = await session.execute(
        select(Photo.id, Photo.photo).where(
            Photo.location_id == id_location, Photo.user_tg_id == user_id)
        )
        return photo_info.fetchone()

async def get_photo_tg_id(photo_id):
    async with async_session() as session:
        return await session.scalar(select(Photo.photo).where(Photo.id == photo_id))


# админ
async def get_photos_from_db(admin_true: int):
    async with async_session() as session:
        stmt = (
            select(Photo, Location.name, User)
            .join(Location, Photo.location_id == Location.id)
            .join(User, Photo.user_tg_id == User.tg_id)
            .where(Photo.admin_true == admin_true)
            .order_by(Photo.sent_at.asc())
            .limit(1)
        )
        result = await session.execute(stmt)
        row = result.first()
        if row:
            photo, location_name, user = row
            return {
                "id": photo.id,
                "name": user.name,
                "username": user.username,
                "photo": photo.photo,
                "location_name": location_name,
            }
        return None


async def delete_photo_from_db(photo_id: int):
    async with async_session() as session:
        async with session.begin():
            await session.execute(delete(Photo).where(Photo.id == photo_id))


async def update_photo_status(photo_id: int, admin_true: int):
    async with async_session() as session:
        async with session.begin():
            stmt = (
                update(Photo)
                .where(Photo.id == photo_id)
                .values(admin_true=admin_true)
            )
            await session.execute(stmt)



async def check_winner(user_id):
    async with async_session() as session:
        async with session.begin():
            if await session.scalar(select(Winner).where(Winner.user_id == user_id)):
                return False
            
            total_locations = await session.scalar(select(func.count(Location.id)))
            
            approved_locations_count = await session.scalar(
                select(func.count(distinct(Photo.location_id)))
                .where(Photo.user_tg_id == user_id, Photo.admin_true == 1)
            )
            
            if approved_locations_count == total_locations:
                current_place = await session.scalar(select(func.count(Winner.id))) + 1
                session.add(Winner(user_id=user_id, place=current_place))
                return current_place
            return False

# async def answer_admin_win():
#     async with async_session() as session:
#         winners_query = (
#             select(Winner, User.name, User.username)
#             .join(User, Winner.user_id == User.id)
#             .order_by(Winner.place)
#         )
        
#         winners_rows = await session.execute(winners_query)
#         return [
#             f"Место: {winner.place}, Имя: {name}, Username: @{username}"
#             for winner, name, username in winners_rows
#         ]
async def answer_admin_win():
    async with async_session() as session:
        winners_query = (
            select(
                User.name,
                User.username,
                func.count(Photo.id).label('photo_count'),
                func.max(Photo.sent_at).label('last_photo_time')
            )
            .join(Photo, Photo.user_tg_id == User.tg_id)
            .filter(Photo.admin_true == 1)
            .group_by(User.id)
            .order_by(func.count(Photo.id).desc(), func.max(Photo.sent_at))
        )
        
        winners_rows = await session.execute(winners_query)
        return [
            f"Имя: {name}, Username: @{username}, Подтвержденные фотографии: {photo_count}, Время последней фотографии: {last_photo_time}"
            for name, username, photo_count, last_photo_time in winners_rows
        ]

async def get_all_photos():
    async with async_session() as session:
        photos_query = (
            select(
                Photo.photo,
                User.name,
                User.username,
                Location.name.label('location_name'),
                Photo.sent_at
            )
            .join(User, Photo.user_tg_id == User.tg_id)
            .join(Location, Photo.location_id == Location.id)
            .order_by(Photo.sent_at)
        )
        
        photos_rows = await session.execute(photos_query)
        return [
            {
                "photo": photo,
                "name": name,
                "username": username,
                "location_name": location_name,
                "sent_at": sent_at
            }
            for photo, name, username, location_name, sent_at in photos_rows
        ]

async def get_user_id_by_photo_id(photo_id):
    async with async_session() as session:
        return await session.scalar(select(Photo.user_tg_id).where(Photo.id == photo_id))
