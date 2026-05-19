from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
from app.logger import logger

Base=declarative_base()

#For Task 2
sqlalchemy_db_url=f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
try:
    engine=create_engine(sqlalchemy_db_url)
    session_local=sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database connection established succesfully. ")
except Exception as e:
    logger.error(f'Database connection failed: {str(e)}')

def get_db():
    db=session_local()
    try:
        yield db
    finally:
        db.close()

#For Task 3
async_url = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
try:
    async_engine = create_async_engine(async_url)
    AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession)
    logger.info("Database connection established succesfully. ")
except Exception as e:
    logger.error(f'Database connection failed: {str(e)}')

async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_async_session_factory():
    return AsyncSessionLocal