from sqlalchemy import BigInteger, String, Text, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from datetime import datetime
from sqlalchemy import DateTime


engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__='users' 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    username: Mapped[str] = mapped_column(String, nullable=True)


class Location(Base):
    __tablename__ = 'locations'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    locations: Mapped[str] = mapped_column(Text)
    photo: Mapped[str] = mapped_column(String)
    task: Mapped[str] = mapped_column(String, nullable=True)
    task_photo: Mapped[str] = mapped_column(String, nullable=True)

class Photo(Base):
    __tablename__ = 'photos'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_tg_id: Mapped[int] = mapped_column(ForeignKey('users.tg_id'))
    photo: Mapped[str] = mapped_column(String)  # URL or path to the photo
    location_id: Mapped[int] = mapped_column(ForeignKey('locations.id'))
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) #  default=datetime.utcnow
    admin_true: Mapped[int] = mapped_column(Integer, default=0, nullable=True)

class Winner(Base):
    __tablename__ = 'winners'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    place: Mapped[int] = mapped_column(Integer)
    win_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
