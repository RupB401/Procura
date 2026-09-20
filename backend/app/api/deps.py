from typing import Generator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.security import ALGORITHM
from app.core.errors import AuthException
from app.db.session import get_db
from app.models.domain import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise AuthException("Could not validate credentials")
    except JWTError:
        raise AuthException("Could not validate credentials")
        
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise AuthException("User not found")
        
    return user

async def get_current_buyer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "BUYER":
        raise AuthException("Not enough permissions. Buyer role required.")
    return current_user

async def get_current_vendor(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "VENDOR":
        raise AuthException("Not enough permissions. Vendor role required.")
    return current_user
