from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.logger import logger

async def get_count(db: AsyncSession, model):
    model_name = model.__name__
    logger.info(f"Starting count query for {model_name}")
    try:
        result = await db.execute(select(func.count()).select_from(model))
        count = result.scalar() or 0
        logger.info(f"Completed count for {model_name}: {count}")
        return count 
    except Exception as e:
        logger.error(f"Error counting {model_name}: {str(e)}")
        return 0