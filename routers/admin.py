from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import AsyncSessionLocal
import models as md
from schema import TodoRequest
from .auth import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


db_dependency = Annotated[AsyncSession, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/todo", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ONLY ADMIN PAGE... UNHOUTORIZED LOGIN")
    
    result = await db.execute(select(md.Todos))
    return result.scalars().all()

@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo_by_id(user: user_dependency, db: db_dependency, todo_id: int):
    
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ONLY ADMIN PAGE... UNHOUTORIZED LOGIN")
    
    result = await db.execute(select(md.Todos).where(md.Todos.id == todo_id))
    result_scalar = result.scalar_one_or_none()
    
    if result_scalar is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND TOOD")
    
    await db.delete(result_scalar)
    await db.commit()
