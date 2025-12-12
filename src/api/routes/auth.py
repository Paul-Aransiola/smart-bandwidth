"""
Authentication API routes for user registration and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from src.core.database import get_db
from src.models.user import User, UserRole
from sqlalchemy.future import select
import jwt
import os
from fastapi.security import OAuth2PasswordBearer
from fastapi import Header
from src.api.dependencies.auth import get_current_user, require_admin

router = APIRouter(prefix="/auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordChangeRequest(BaseModel):
    token: str
    new_password: str


# In-memory token store for demo (replace with DB in production)
password_reset_tokens = {}


@router.post("/register", status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar():
        raise HTTPException(status_code=400, detail="Username already exists")
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar():
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(
        username=data.username,
        email=data.email,
        password_hash=pwd_context.hash(data.password),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"id": user.id, "username": user.username, "email": user.email}


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode(
        {"sub": str(user.id), "role": user.role}, JWT_SECRET, algorithm=JWT_ALGORITHM
    )

    return TokenResponse(access_token=token)


@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }


class ProfileUpdateRequest(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None


@router.put("/profile")
async def update_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.username:
        current_user.username = data.username
    if data.email:
        current_user.email = data.email
    if data.password:
        current_user.password_hash = pwd_context.hash(data.password)
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return {"message": "Profile updated"}


@router.post("/reset-password")
async def reset_password(data: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
    # Generate token (insecure demo, use random/uuid in production)
    token = jwt.encode({"sub": user.id, "purpose": "reset"}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    password_reset_tokens[token] = user.id
    # TODO: Send token via email
    return {"message": "Password reset token generated", "token": token}


@router.post("/change-password")
async def change_password(data: PasswordChangeRequest, db: AsyncSession = Depends(get_db)):
    user_id = password_reset_tokens.get(data.token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = pwd_context.hash(data.new_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    del password_reset_tokens[data.token]

    return {"message": "Password changed successfully"}
