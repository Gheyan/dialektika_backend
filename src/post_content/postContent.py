from fastapi import HTTPException, status
from sqlalchemy import select
from database.database import AsyncSessionLocal
from database.models import Post, User

async def get_all_post(current_user:User, rows:int, offset:int):
    async with AsyncSessionLocal() as db:
        all_post_query = select(Post).limit(rows).offset(offset)
        all_post_result = await db.execute(all_post_query)
        all_post = all_post_result.scalars().all()

    return all_post



        