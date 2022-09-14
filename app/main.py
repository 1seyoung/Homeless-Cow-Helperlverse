from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from os.path import dirname, abspath
from pathlib import Path
from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from .core.models.database import db_manager
from .core.models.auth_manager import auth_manager, get_current_active_user
from .core.schemas.user_model import UserModel
from .core.schemas.token_model import Token
from .core.instance.config import MONGODB_URL, ACCESS_TOKEN_EXPIRE_MINUTES

from app.core.routers import register
from app.core.routers import page_tmp
from app.core.routers import login

BASE_DIR = dirname(abspath(__file__))

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(Path(BASE_DIR, 'static'))), name="static")
db_manager.init_manager(MONGODB_URL, "simulverse")

app.include_router(register.router, prefix="", tags=["register"])
app.include_router(page_tmp.router, prefix="", tags=["home"])
app.include_router(login.router, prefix="", tags=["login"])

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await auth_manager.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await auth_manager.create_access_token(
        data={"sub": user.userid}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=UserModel)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    print("SDFSDF")
    return current_user


@app.get("/users/me/items/")
async def read_own_items(current_user: UserModel = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.userid}]