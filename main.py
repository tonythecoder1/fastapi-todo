# main.py
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.params import Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from routers.auth import SECRET_KEY, ALGORITHM
from fastapi.responses import RedirectResponse
from fastapi import status
from jose import JWTError, jwt
from routers.auth import get_current_user_silent


from database import engine, Base
from routers import auth, todos, admin, users

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

LOGIN_PATH = "/auth/login-page"
PUBLIC_PREFIXES = ("/static", "/docs", "/redoc")
PUBLIC_EXACT = {
    LOGIN_PATH,
    "/auth/login",
    "/auth/register",        # <- podes manter se existir
    "/auth/register-page",   # <- ADICIONA ESTE
    "/auth/create", 
    "/openapi.json",
    "/favicon.ico",
}

def is_public(path: str) -> bool:
    if path in PUBLIC_EXACT:
        return True
    return any(path.startswith(pfx + "/") or path == pfx for pfx in PUBLIC_PREFIXES)

@app.middleware("http")
async def auth_guard(request: Request, call_next):
    path = request.url.path

    # 1) Libera rotas públicas SEM QUALQUER VERIFICAÇÃO
    if is_public(path):
        return await call_next(request)

    #Authorization: Bearer 
    token = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        token = request.cookies.get("access_token")

    # Sem token -> redireciona para login
    if not token:
        if path != LOGIN_PATH:  # proteção extra contra loop
            return RedirectResponse(LOGIN_PATH, status_code=status.HTTP_303_SEE_OTHER)
        # se por algum motivo cair aqui no próprio login, apenas segue
        return await call_next(request)

    # com token valida
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        request.state.user = {
            "id": payload.get("id") or payload.get("sub"),
            "username": payload.get("sub"),
            "role": payload.get("role"),
        }
    except JWTError:
        # token inválido/expirado → manda para login (sem loop)
        if path != LOGIN_PATH:
            return RedirectResponse(LOGIN_PATH, status_code=status.HTTP_303_SEE_OTHER)
        return await call_next(request)

    # 5) OK → segue
    return await call_next(request)
        
    
@app.get("/", name="index")
async def home(request: Request, current_user: Optional[dict]  = Depends(get_current_user_silent)):
    if current_user:
        return templates.TemplateResponse("index.html", {"request": request, "user": current_user})
    return RedirectResponse(url="/auth/login-page", status_code=status.HTTP_303_SEE_OTHER)

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
