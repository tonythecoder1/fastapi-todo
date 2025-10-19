from typing import Annotated
from fastapi import APIRouter, Request
from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import AsyncSessionLocal
import models as md
from schema import TodoRequest
from .auth import get_current_user
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import pathlib


BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(
    prefix="/todos",
    tags=['todos']
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
        
        
user_dependency = Annotated[dict, Depends(get_current_user)]

### Pages ###
@router.get("/todo-page", name="todos_page")
async def render_todo_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = getattr(request.state, "user", None)
    if not user:
        return RedirectResponse("/auth/login-page", status_code=303)
    
    result = await db.execute(
        select(md.Todos).where(md.Todos.owner_id == user["id"])   # confere o nome da coluna!
    )
    todos = result.scalars().all()
    
    if not user:
        return RedirectResponse("/auth/login-page", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("todo.html", {"request": request, "user": user, "todos": todos})


### Endpoints ###
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(md.Todos))
    return result.scalars().all()

@router.get("/get-all", status_code=status.HTTP_200_OK)
async def read_all_todos_from_user_id(user: user_dependency, db: AsyncSession = Depends(get_db)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not logged in")
    
    result = await db.execute(select(md.Todos).where(md.Todos.owner_id == user.get("id")))
    todos_scalar = result.scalars().all()

    return todos_scalar

@router.get("/get-todo-id/{todo_id}", status_code=status.HTTP_200_OK)
async def get_todo_by_todoid(user: user_dependency,db: AsyncSession = Depends(get_db), todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not logged in")
    
    result = await db.execute(select(md.Todos).where(md.Todos.id == todo_id))
    result_scalar = result.scalar_one_or_none()
    
    return result_scalar
    

@router.get("/get-id/{todo_id}", status_code=status.HTTP_200_OK)
async def read_id(todo_id: int = Path(gt=0), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(md.Todos).where(md.Todos.id == todo_id))
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="TODO NOT FOUND")
    return todo

@router.post("/create-todo", name="todo_create", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, todo_request: TodoRequest, db: AsyncSession = Depends(get_db)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    
    # 1) todo_request.model_dump() -> devolve um dict com os campos válidos (ex.: {"title":..., "description":..., "priority":..., "complete":...})
    # 2) ** (desempacotamento) -> envia cada par chave/valor como argumento nomeado do construtor md.Todos(...)
    #3) owner_id=user["id"] -> força/define o dono da tarefa com o id do utilizador autenticado;
    #se viesse um 'owner_id' no body, seria ignorado porque este argumento vem por último (sobrepõe).
    
    todo = md.Todos(**todo_request.model_dump(), owner_id=user["id"])
    try:
        db.add(todo)
        await db.commit()
        await db.refresh(todo)
        return todo
    except Exception as e:
        await db.rollback()
        print("CREATE_TODO ERROR:", type(e).__name__, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="ERROR 500")
        
@router.delete("/del-todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency,todo_id: int, db: AsyncSession = Depends(get_db)):
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    
    result = await db.execute(select(md.Todos).where(md.Todos.id == todo_id, md.Todos.owner_id == user.get('id')))
    todo_model = result.scalar_one_or_none()
    
    if todo_model is None:
        raise HTTPException(status_code=404,detail="NOT FOUND")
        
    await db.delete(todo_model)
    await db.commit()
        
    return None

@router.put("/update-todos/{todo_id}")
async def update_todo(user: user_dependency,
                        todo_id: int, 
                        todo_request: TodoRequest, 
                        db: AsyncSession = Depends(get_db)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    
    todo: md.Todos = md.Todos(**todo_request.model_dump())
    result = await db.execute(select(md.Todos).where(md.Todos.id == todo_id, md.Todos.owner_id == user["id"]))
    todo_model = result.scalar_one_or_none()
    
    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo Not found")
        
    if result is not None:
        todo_model.title = todo_request.title
        todo_model.description = todo.description
        todo_model.priority = todo.priority
        todo_model.complete = todo.complete

        await db.commit()
        await db.refresh(todo_model)
        
        return todo_model
    else:
        raise HTTPException(status_code=404, detail="NOT FOUND TO UPDATE")