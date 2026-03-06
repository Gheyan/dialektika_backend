import uuid
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select
from database.database import AsyncSessionLocal
from database.models import Post, User
from storage.storage_type import StorageDep
from config import ATTACHMENT_URL

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
                attachment_url = f"{ATTACHMENT_URL}/{unique_filename}"

            except Exception as e:raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Upload failed: {str(e)}")

        new_post = Post(user_id=result,title=title,description=description,attachment=attachment_url)

        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)

        return new_post
async def edit_post(
    post_id: int,
    current_user: User,
    title: str | None = None,
    description: str | None = None,
    file: UploadFile | None = None,
    storage: StorageDep = None
):
    attachment_url = None

    async with AsyncSessionLocal() as db:
        current_user_query = select(User.id).where(User.email == current_user.email)
        user_id = (await db.execute(current_user_query)).scalar_one_or_none()

        if user_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")

        post_query = select(Post).where(Post.id == post_id)
        post = (await db.execute(post_query)).scalar_one_or_none()

        if post is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")

        if post.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to edit this post")

        if title is not None:
            post.title = title

        if description is not None:
            post.description = description

        if file:
            try:
                unique_filename = f"{uuid.uuid4()}_{file.filename}"
                await storage.upload(file, unique_filename)
                attachment_url = f"{ATTACHMENT_URL}/{unique_filename}"
                post.attachment = attachment_url
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Upload failed: {str(e)}")

        await db.commit()
        await db.refresh(post)

        return post

async def delete_post(post_id: int, current_user: User):
    async with AsyncSessionLocal() as db:
        current_user_query = select(User.id).where(User.email == current_user.email)
        user_id = (await db.execute(current_user_query)).scalar_one_or_none()

        if user_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")

        post_query = select(Post).where(Post.id == post_id)
        post = (await db.execute(post_query)).scalar_one_or_none()

        if post is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")

        if post.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to delete this post")

        await db.delete(post)
        await db.commit()

        return {"message": "Post deleted successfully"}