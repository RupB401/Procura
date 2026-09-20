from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.domain import User
from app.schemas.user import UserCreate, UserResponse, LoginRequest, Token
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.errors import ValidationException, AuthException
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise ValidationException("Email already registered")
        
    if user_in.role not in ["BUYER", "VENDOR"]:
        raise ValidationException("Role must be BUYER or VENDOR")
        
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        company_name=user_in.company_name,
        role=user_in.role
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # In a real app we might also audit log USER_REGISTERED here
    return new_user

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        # We use a generic error message as requested in stage 8
        raise AuthException("Incorrect email or password")
        
    access_token = create_access_token(subject=user.id, role=user.role)
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
