from typing import Annotated, Optional
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from jose import JWTError, jwt

from database import get_db
from models import Users

# templates portável (evita hardcode)
BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

logout_on = False

#Tenta buscar um token JWT no header Authorization: Bearer <token> em cada pedido.
# importante: auto_error=False para podermos cair no cookie
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

db_dependency = Annotated[AsyncSession, Depends(get_db)]

router = APIRouter(prefix="/auth", tags=["auth"])

class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

SECRET_KEY = "12345678"
ALGORITHM = "HS256"

# ---------- PAGES ----------
@router.get("/login-page", name="loginpage")
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "login_page_on": True})

@router.get("/register-page", name="register")
def render_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# ---------- HELPERS ----------
async def authenticate_user(username: str, password: str, db: AsyncSession):
    result = await db.execute(select(Users).where(Users.username == username))
    user = result.scalars().first()
    if not user:
        return False
    try:
        ok = bcrypt_context.verify(password, user.hashed_password or "")
    except Exception:
        ok = False
    return user if ok else False

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    # usar UTC
    payload = {'sub': username, 'id': user_id, 'role': role, 'exp': datetime.utcnow() + expires_delta}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ---------- CURRENT USER ----------
async def get_current_user(
    request: Request,
    token: Annotated[Optional[str], Depends(oauth2_bearer)],
):
    # tenta Authorization header; senão, tenta cookie
    if not token:
        token = request.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            token = token.split(" ", 1)[1]

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate the user")
        return {'username': username, 'id': user_id, 'role': role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate the user")

async def get_current_user_silent(
    request: Request,
    token: Annotated[Optional[str], Depends(oauth2_bearer)] = None,
):
    try:
        return await get_current_user(request, token)
    except HTTPException:
        return None

@router.get("/me")
async def get_logged_user(current_user: dict = Depends(get_current_user)):
    return current_user

# ---------- API: CRIAR USER (JSON) ----------
@router.post("/create", status_code=status.HTTP_201_CREATED, name="create_user")
async def create_user(payload: CreateUserRequest, db: AsyncSession = Depends(get_db)):
    existing_email = await db.execute(select(Users).where(Users.email == payload.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já registado")

    existing_username = await db.execute(select(Users).where(Users.username == payload.username))
    if existing_username.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username já registado")

    user = Users(
        email=payload.email,
        username=payload.username,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        hashed_password=bcrypt_context.hash(payload.password),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "username": user.username, "email": user.email, "role": user.role, "is_active": user.is_active}

# ---------- API: TOKEN PARA APPS (x-www-form-urlencoded) ----------
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user: Users = await authenticate_user(form_data.username, form_data.password, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="FAILED TO LOGIN")
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=30))
    return {'access_token': token, 'token_type': 'bearer'}

# ---------- BRIDGE: LOGIN QUE DEFINE COOKIE E REDIRECIONA ----------
@router.post("/login", name="login")
async def login_bridge(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(username, password, db=db)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=30))

    resp = RedirectResponse(url="/", status_code=303)
    #navegador que passa a enviar automaticamente o token em todos os pedidos
    resp.set_cookie(
        key="access_token",
        value=token,      # ou "Bearer " + token se preferires
        httponly=True,
        samesite="lax",
        max_age=30 * 60,
        secure=False,     # True em produção (HTTPS)
        path="/",
    )
    return resp

@router.get("/logout", name="logout")
async def user_logout(request: Request):
    logout_on = True
    response: Response = templates.TemplateResponse("login.html", {"request": request, "logout_on": logout_on})
    response.delete_cookie(key="access_token")
    return response
