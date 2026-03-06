from fastapi import HTTPException, status
from sqlalchemy import select
from database.database import AsyncSessionLocal
from database.models import Post, User

async def get_all_post(current_user:User, rows:int, offset:int):
    async with AsyncSessionLocal() as db:
        all_post_query = select(Post).limit(rows).offset(offset)
        all_post_result = await db.execute(all_post_query)
        all_post = all_post_result.scalars().all()

        if not all_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No posts available")

    return all_post

async def get_specific_user_post(current_user:User, user_id:int):
    async with AsyncSessionLocal() as db:
        all_post_query = select(Post).where(user_id == Post.user_id)
        all_post_result = await db.execute(all_post_query)
        all_post = all_post_result.scalars().all()

        if not all_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No posts found for this user!")

    return all_post

async def create_post(current_User:User, title:int, description:str=None, attachment:str=None):
    pass




        