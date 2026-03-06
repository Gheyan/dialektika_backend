import uuid
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select
from database.database import AsyncSessionLocal
from database.models import Post, User
from storage.storage_type import StorageDep

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

        current_user_query = select(User.id).where(current_user.email == User.email)
        result = (await db.execute(current_user_query)).scalar_one_or_none()

        if not all_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No posts found for this user!")

    return all_post

BASE_URL = "http://localhost:8000/static"

async def create_post(current_user: User,title: str,description: str | None = None,file: UploadFile | None = None,storage: StorageDep = None):
    attachment_url = None

    async with AsyncSessionLocal() as db:
        current_user_query = select(User.id).where(User.email == current_user.email)
        result = (await db.execute(current_user_query)).scalar_one_or_none()

        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")

        if file:
            try:
                unique_filename = f"{uuid.uuid4()}_{file.filename}"
                await storage.upload(file, unique_filename)
                attachment_url = f"{BASE_URL}/{unique_filename}"

            except Exception as e:raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Upload failed: {str(e)}")

        new_post = Post(user_id=result,title=title,description=description,attachment=attachment_url)

        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)

        return new_post


        