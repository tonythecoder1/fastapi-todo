from typing import Annotated
from fastapi import APIRouter
from fastapi import Depends, HTTPException, Path, status
from pydantic import Field, BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import AsyncSessionLocal
import models as md
from schema import TodoRequest
from .auth import get_current_user
from database import get_db   
from passlib.context import CryptContext

router = APIRouter(prefix="/users", tags=["users"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=5)
    

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@router.get("/get_user",status_code=status.HTTP_200_OK)
async def get_logged_user(user: user_dependency, db: db_dependency):
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unhoutorized Login")
    
    return {"user_id": user.get('id'), "username": user.get('username'), "user_role": user.get('role')}

@router.put("/change-password", status_code=status.HTTP_202_ACCEPTED)
async def change_user_password(user: user_dependency, db: db_dependency, user_verify: UserVerification):
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unhoutorized Login")
    
    result = await db.execute(select(md.Users).where(md.Users.id == user.get('id')))
    user_logged_in: md.Users = result.scalar_one_or_none()
    
    if not bcrypt_context.verify(user_verify.password, user_logged_in.hashed_password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PASSWORD VERIFICATION FAILED")
    
    user_logged_in.hashed_password = bcrypt_context.hash(user_verify.new_password)
    
    await db.commit()
    await db.refresh(user_logged_in)
    
    return {"detail": "Password changed with success"}