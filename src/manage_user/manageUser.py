from fastapi import HTTPException, status
from sqlalchemy import select
from database.models import User
from database.database import AsyncSessionLocal
from auth.login import get_password_hash

async def soft_delete_user(current_user: User, user_id: int):
    async with AsyncSessionLocal() as db:
        if current_user.role != 'admin':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete users")
        
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)    
        user_to_delete = user_result.scalar_one_or_none()

        current_user_query = select(User).where(current_user.email == User.email)
        current_user_result = await db.execute(current_user_query)    
        current_person = current_user_result.scalar_one_or_none()

        if not user_to_delete:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")
        
        if user_to_delete.is_deleted is True:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is already in recycle bin!")
        
        user_to_delete.is_deleted=True
        await db.commit()

    return {"message": f"User {user_to_delete.username} is moved to the recycle bin."}


async def delete_user(current_user: User, user_id: int, ):
    async with AsyncSessionLocal() as db:
        if current_user.role != 'admin':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete users")
        
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)    
        user_to_delete = user_result.scalar_one_or_none()

        current_user_query = select(User).where(current_user.email == User.email)
        current_user_result = await db.execute(current_user_query)    
        current_person = current_user_result.scalar_one_or_none()

        if not user_to_delete:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")
        
        if user_to_delete.is_deleted is False:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not in the recycle bin!")

        await db.delete(user_to_delete)
        await db.commit()

    return {"message": f"User {user_to_delete.username} successfully deleted."}

async def get_all_user(current_user:User):
    async with AsyncSessionLocal() as db:
        if current_user.role != 'admin':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can load users")
        
        alluser_query = select(User).where(User.is_deleted==False)

        alluser_result = await db.execute(alluser_query)
        all_users = alluser_result.scalars().all()
        
    return all_users

async def edit_user(current_user: User, user_id: int, email: str=None, role: str=None, username: str=None, password: str=None):
     async with AsyncSessionLocal() as db:
        if current_user.role != 'admin':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can load users")

        current_user_query = select(User).where(current_user.email == User.email)
        current_user_result = await db.execute(current_user_query)    
        current_person = current_user_result.scalar_one_or_none()


        edit_query = select(User).where(User.id == user_id)
        edit_result = await db.execute(edit_query)
        user_to_edit = edit_result.scalar_one_or_none()
        check_username_query = select(User).where(User.username == username)
        check_username_result = await db.execute(check_username_query)
        username_scalar = check_username_result.scalar_one_or_none()
        check_email_query = select(User).where(User.email == email)
        check_email_result = await db.execute(check_email_query)
        email_scalar = check_email_result.scalar_one_or_none()

        if email_scalar:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

        if username_scalar:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

        if not user_to_edit:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not exist")
        if email:
            user_to_edit.email = email
        if role:
            user_to_edit.role = role
        if username:
            user_to_edit.username = username
        if password:
            user_to_edit.hash = get_password_hash(password)

        await db.merge(user_to_edit)
       
        await db.commit()
        
async def add_user(current_user: User, email: str, role: str, username: str, password: str):
     async with AsyncSessionLocal() as db:
        if current_user.role != 'admin':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can load users")   

        current_user_query = select(User).where(current_user.email == User.email)
        current_user_result = await db.execute(current_user_query)    
        current_person = current_user_result.scalar_one_or_none()

        check_username_query = select(User).where(User.username == username)
        check_username_result = await db.execute(check_username_query)
        username_scalar = check_username_result.scalar_one_or_none()
        check_email_query = select(User).where(User.email == email)
        check_email_result = await db.execute(check_email_query)
        email_scalar = check_email_result.scalar_one_or_none()

        if email_scalar:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

        if username_scalar:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        
        new_user = User(email=email,role=role, username=username, hash=get_password_hash(password))
        db.add(new_user)
        await db.commit()
