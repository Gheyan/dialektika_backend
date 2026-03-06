from typing import Optional
import datetime

from fastapi import HTTPException, status
from pydantic import BaseModel, computed_field
from sqlalchemy import select

from database import AsyncSessionLocal
from database.models import Post, User
from .storage_type import StorageDep, get_storage


class PostResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    attachment: Optional[str] = None
    date_created: datetime.date

    @computed_field
    def full_attachment_url(self) -> Optional[str]:
        if not self.attachment:
            return None

        storage = get_storage()
        return storage.get_url(self.attachment)

    class Config:
        from_attributes = True


async def upload_attachment_to_post(current_user: User,file,post_id: int,storage: StorageDep):
    async with AsyncSessionLocal() as db:
        query = select(Post).where(Post.id == post_id)
        post = (await db.execute(query)).scalar_one_or_none()

        current_user_query = select(User.id).where(current_user.email == User.email)
        result = (await db.execute(current_user_query)).scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post does not exist")

        if post.user_id != result:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to edit this post")

        old_attachment = post.attachment

        try:
            file_url = await storage.upload(file, file.filename)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Upload failed: {str(e)}")

        post.attachment = file_url

        await db.commit()
        await db.refresh(post)

        if old_attachment:
            try:
                await storage.delete(old_attachment)
            except Exception as e:
                print(f"Old file deletion failed: {e}")

        return PostResponse.model_validate(post)


async def delete_attachment_from_post(current_user: User,post_id: int,storage: StorageDep):
    async with AsyncSessionLocal() as db:
        query = select(Post).where(Post.id == post_id)
        post = (await db.execute(query)).scalar_one_or_none()

        current_user_query = select(User.id).where(current_user.email == User.email)
        result = (await db.execute(current_user_query)).scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")

        if post.user_id != result:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to edit this post")

        if not post.attachment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post has no attachment")

        attachment_to_delete = post.attachment
        post.attachment = None

        await db.commit()
        await db.refresh(post)

        try:
            await storage.delete(attachment_to_delete)
        except Exception as e:
            print(f"File deletion failed: {e}")

        return {"detail": "Attachment deleted successfully"}

