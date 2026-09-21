from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.db.session import get_db
from app.models.domain import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, LoginRequest, Token, GoogleLoginRequest, PasswordResetRequest
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.errors import ValidationException, AuthException
from app.api.deps import get_current_user

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

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
    
    return new_user

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise AuthException("Incorrect email or password")
        
    access_token = create_access_token(subject=user.id, role=user.role)
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/google", response_model=Token)
async def google_login(login_data: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Client ID not configured on server")
        
    try:
        idinfo = id_token.verify_oauth2_token(
            login_data.id_token, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=60
        )
        email = idinfo['email']
        name = idinfo.get('name', 'Google User')
    except ValueError as e:
        print(f"GOOGLE TOKEN VERIFICATION FAILED: {str(e)}")
        raise AuthException("Invalid Google token")

    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        # Auto-register as BUYER for showcase if doesn't exist
        user = User(
            email=email,
            hashed_password=get_password_hash("GOOGLE_AUTH_PLACEHOLDER"),
            company_name=name,
            role="BUYER"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    access_token = create_access_token(subject=user.id, role=user.role)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.delete("/me")
async def delete_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.delete(current_user)
    await db.commit()
    return Response(status_code=204)

@router.patch("/me", response_model=UserResponse)
async def update_me(update_data: UserUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if update_data.company_name is not None:
        current_user.company_name = update_data.company_name
    if update_data.password is not None:
        current_user.hashed_password = get_password_hash(update_data.password)
    
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.post("/reset-password")
async def reset_password(reset_data: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == reset_data.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise AuthException("User with this email not found")
        
    user.hashed_password = get_password_hash(reset_data.new_password)
    await db.commit()
    
    return {"message": "Password reset successfully"}
