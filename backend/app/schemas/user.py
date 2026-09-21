from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    company_name: str
    role: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    company_name: str | None = None
    password: str | None = None

class PasswordResetRequest(BaseModel):
    email: EmailStr
    new_password: str

class UserResponse(UserBase):
    id: UUID
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str | None = None
    role: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleLoginRequest(BaseModel):
    id_token: str
