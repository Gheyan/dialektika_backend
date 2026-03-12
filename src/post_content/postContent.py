import uuid
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select
from database.database import AsyncSessionLocal
from database.models import Post, User
from storage.storage_type import SUPABASE_BUCKET, SUPABASE_URL, StorageDep
from config import ATTACHMENT_URL
import urllib.parse

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

async def create_post(current_user: User, title: str, description: str | None = None, file: UploadFile | None = None, storage: StorageDep = None):
    attachment_url = None

    async with AsyncSessionLocal() as db:
        current_user_query = select(User.id).where(User.email == current_user.email)
        result = (await db.execute(current_user_query)).scalar_one_or_none()

        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if file:
            try:
                unique_filename = f"{uuid.uuid4()}_{file.filename}"
                # Upload the file and get the response
                uploaded_url = await storage.upload(file, unique_filename)

                # Generate the correct public URL using the full path from Supabase
                attachment_url = f"{uploaded_url}"

                # Print for debugging
                print(f"Uploaded File URL: {attachment_url}")

            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}")

        new_post = Post(user_id=result, title=title, description=description, attachment=attachment_url)

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
        # Fetch current user's ID to ensure ownership
        current_user_query = select(User.id).where(User.email == current_user.email)
        user_id = (await db.execute(current_user_query)).scalar_one_or_none()

        if user_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Fetch the post to edit
        post_query = select(Post).where(Post.id == post_id)
        post = (await db.execute(post_query)).scalar_one_or_none()

        if post is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

        # Check if the current user owns the post
        if post.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to edit this post")

        # Update title and description if provided
        if title is not None:
            post.title = title

        if description is not None:
            post.description = description

        # Handle file upload if a file is provided
        if file:
            try:
                # Generate a unique filename for the file
                unique_filename = f"{uuid.uuid4()}_{file.filename}"

                # Upload the file using the storage provider
                uploaded_url = await storage.upload(file, unique_filename)

                # Update the attachment URL
                attachment_url = uploaded_url  # The upload method already returns the public URL
                post.attachment = attachment_url  # Save the new URL in the post's attachment field

                # Debugging: Print the uploaded file URL
                print(f"Uploaded File URL: {attachment_url}")

            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}")

        # Commit changes to the database
        await db.commit()
        await db.refresh(post)  # Refresh the post to reflect the changes

        return post  # Return the updated post
    
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