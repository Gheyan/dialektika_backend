from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse

from typing import Annotated, Optional, List

from auth import login
from auth.token import Token, RefreshRequest
from auth.public_user import PublicUser

from datetime import timedelta, datetime

from manage_user import get_all_user, edit_user, add_user, delete_user

router = APIRouter(prefix="/rest")

user_dependency = Annotated[PublicUser, Depends(login.get_current_active_user)]


@router.post("/login", tags=["Authentication"])
async def login_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
        ) -> Token:
    user = await login.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=login.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = login.create_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
        token_type="access"
    )
    refresh_token = login.create_token(
        data={"sub": user.username},
        expires_delta=timedelta(days=7),
        token_type="refresh"
    )
    return Token(access_token=access_token,
                 refresh_token=refresh_token,
                 token_type="bearer")


@router.post("/refresh", tags=["Authentication"])
async def refresh_access_token(body: RefreshRequest):
    username = login.verify_refresh_token(RefreshRequest.refresh_token)

    user = await login.get_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = login.create_access_token(
        data={"sub": user.username, "type": "access"},
        expires_delta=timedelta(minutes=login.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(
        access_token=new_access_token,
        refresh_token=body.refresh_token,
        token_type="bearer"
    )

@router.get("/user", tags=["Authentication"])
async def get_public_user(current_user: user_dependency):
    return current_user



#######################MANAGEUSER####################


@router.delete("/deleteuser", tags=["User Management"])
async def delete_user_role(current_user: user_dependency,user_id:int=None):
    remove_user = await delete_user(current_user,user_id)
    return remove_user

@router.get("/loadusers", tags=["User Management"])
async def load_all_users(current_user: user_dependency):
    load_user = await get_all_user(current_user)
    return load_user

@router.put("/edituser", tags=["User Management"])
async def edit_user_info(current_user: user_dependency, user_id: int, email: str=None, role: str=None, firstname: str=None, lastname: str=None, username: str=None, password: str=None):
    edit_users = await edit_user(current_user, user_id, email, role, firstname, lastname, username, password)
    return edit_user

@router.put("/softdelete", tags=["User Management"])
async def soft_delete_user_info(current_user: user_dependency, user_id:int):
    soft_delete = await soft_delete_user(current_user, user_id)
    return soft_delete

@router.post("/adduser", tags=["User Management"])
async def add_user_instance(current_user: user_dependency, email: str, role: str, username: str, firstname: str, lastname:str, password: str):
    added_user = await add_user(current_user, email, role, username, firstname, lastname, password)
    return added_user