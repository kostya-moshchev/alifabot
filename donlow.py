import csv
import asyncio
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.database.models import Base, Location  # Импортируем модель Location из models.py

# Создаем асинхронный engine SQLAlchemy для работы с SQLite
engine = create_async_engine('sqlite+aiosqlite:///db.sqlite3')

# Функция для инициализации базы данных
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Функция для загрузки данных из CSV в базу данных
async def load_data():
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        with open('bd.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter='|')
            for row in reader:
                location = Location(
                    name=row['name'],
                    description=row['description'],
                    task=row['task'],
                    locations=row['locations'],
                    photo=row['photo'],
                    task_photo=row['task_photo']
                )
                session.add(location)
            await session.commit()

# Основная функция для запуска инициализации базы и загрузки данных
async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await load_data()

if __name__ == '__main__':
    asyncio.run(main())