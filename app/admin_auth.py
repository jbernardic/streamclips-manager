from typing import Optional

from fastapi import Request
from sqladmin.authentication import AuthenticationBackend
from starlette.responses import RedirectResponse
from jose import JWTError, jwt
import os

from app.core import auth
from app.database.connection import get_db
from app.database import models
from app.schemas import UserLogin


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        db = next(get_db())
        try:
            data = auth.login(db, UserLogin(username=username, password=password))
            access_token = data["access_token"]
        finally:
            db.close()

        request.session.update({"token": access_token})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Optional[RedirectResponse]:
        token = request.session.get("token")
        db = next(get_db())
        try:
            auth.get_current_user(token, db)
        except:
            return False
        finally:
            db.close()
        
        return True
