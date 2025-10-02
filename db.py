from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, select

# === Настройка БД ===
DATABASE_URL = "sqlite+aiosqlite:///database.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


# === Модель твита ===
class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String, unique=True, nullable=False)

class TwitterProfile(Base):
    __tablename__ = "twitter_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_urls = Column(String, unique=True, nullable=False)

class Channels(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, unique=True, nullable=False)
    
class InstagramProfile(Base):
    __tablename__ = "instagram"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_urls = Column(String, unique=True, nullable=False)

class InstagramPost(Base):
    __tablename__ = "instagram_post"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_urls = Column(String, unique=True, nullable=False)

# === Инициализация БД (создание таблицы) ===
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



# === Телеграм ===
async def save_channel(channel_name: str):
    try:
        async with async_session() as session:
            channel = Channels(channel_name=channel_name)
            session.add(channel)
            await session.commit()
            return True
    except Exception as e:
        print(f"❌ Ошибка сохранения канала: {e}")
        return False
        
async def get_channels() -> list[str]:
    async with async_session() as session:
        result = await session.execute(select(Channels.channel_name))
        return result.scalars().all()



# === Твиттер===
async def tweet_exists(text: str) -> bool:
    async with async_session() as session:
        result = await session.execute(select(Tweet).where(Tweet.text == text))
        return result.scalars().first() is not None
    
async def save_tweet(text: str):
    async with async_session() as session:
        tweet = Tweet(text=text)
        session.add(tweet)
        await session.commit()

async def save_twitter_profile(profile_url: str):
    try:
        async with async_session() as session:
            twitter_profile = TwitterProfile(profile_urls=profile_url)
            session.add(twitter_profile)
            await session.commit()
            return True
    except Exception as e:
        print(f"❌ Ошибка сохранения профиля: {e}")
        return False

async def get_twitter_profile() -> list[str]:
    async with async_session() as session:
        result = await session.execute(select(TwitterProfile.profile_urls))
        return result.scalars().all()
    



# === Инстаграм ===
async def get_instagram_profile() -> list[str]:
    async with async_session() as session:
        result = await session.execute(select(InstagramProfile.profile_urls))
        return result.scalars().all()

async def post_exists(post_url: str) -> bool:
    async with async_session() as session:
        result = await session.execute(select(InstagramPost.post_urls).where(InstagramPost.post_urls == post_url))
        return result.scalars().first() is not None

async def save_instagram_profile(profile_url: str):
    try:
        async with async_session() as session:
            instagram_profile = InstagramProfile(profile_urls=profile_url)
            session.add(instagram_profile)
            await session.commit()
            return True
    except Exception as e:
            print(f"❌ Ошибка сохранения профиля: {e}")
            return False
        
async def save_instagram_post(post_url: str):
    try:
        async with async_session() as session:
            instagram_post = InstagramPost(post_urls=post_url)
            session.add(instagram_post)
            await session.commit()
            return True
    except Exception as e:
            print(f"❌ Ошибка сохранения поста: {e}")
            return False