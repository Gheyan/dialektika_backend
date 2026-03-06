from fastapi import HTTPException, status
from sqlalchemy import select
from database.models import User, Post, Comments
from database.database import AsyncSessionLocal

async def post_comment(current_user: User, post_id: int, comment: str):
    async with AsyncSessionLocal() as db:
        post_query = select(Post).where(Post.id == post_id)
        post_result = (await db.execute(post_query)).scalar_one_or_none()

        if post_result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")

        user_query = select(User.id).where(User.email == current_user.email)
        user_result = (await db.execute(user_query)).scalar_one_or_none()

        if user_result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")

        new_comment = Comments(post_id=post_id,user_id=user_result,comment=comment)

        db.add(new_comment)
        await db.commit()
        await db.refresh(new_comment)
        return new_comment


async def edit_comment(current_user: User, comment_id: int, new_comment: str):
    async with AsyncSessionLocal() as db:
        user_query = select(User.id).where(User.email == current_user.email)
        user_result = (await db.execute(user_query)).scalar_one_or_none()

        if user_result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")

        comment_query = select(Comments).where(Comments.id == comment_id)
        comment_result = (await db.execute(comment_query)).scalar_one_or_none()

        if comment_result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Comment not found")

        if comment_result.user_id != user_result:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You can only edit your own comment")

        comment_result.comment = new_comment

        await db.commit()
        await db.refresh(comment_result)
        return comment_result


async def delete_comment(current_user: User, comment_id: int):
    async with AsyncSessionLocal() as db:
        user_query = select(User.id).where(User.email == current_user.email)
        user_result = (await db.execute(user_query)).scalar_one_or_none()

        if user_result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")

        comment_query = select(Comments).where(Comments.id == comment_id)
        comment_result = (await db.execute(comment_query)).scalar_one_or_none()

        if comment_result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Comment not found")

        if comment_result.user_id != user_result:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You can only delete your own comment")

        await db.delete(comment_result)
        await db.commit()

        return {"message": "Comment deleted successfully"}
    
async def get_comments_per_post(post_id: int):
    async with AsyncSessionLocal() as db:
        post_query = select(Post).where(Post.id == post_id)
        post_result = (await db.execute(post_query)).scalar_one_or_none()

        if post_result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")

        comments_query = (
            select(Comments.id,Comments.post_id,Comments.user_id,Comments.comment,Comments.date_created,User.username,User.firstname,User.lastname)
            .join(User, User.id == Comments.user_id)
            .where(Comments.post_id == post_id)
            .order_by(Comments.date_created.desc(), Comments.id.desc())
        )
        comments_result = (await db.execute(comments_query)).all()

        return [
            {
                "id": row.id,
                "post_id": row.post_id,
                "user_id": row.user_id,
                "username": row.username,
                "firstname": row.firstname,
                "lastname": row.lastname,
                "comment": row.comment,
                "date_created": row.date_created
            }
            for row in comments_result
        ]