"""
Authentication dependencies for API routes.
TODO: Implement proper authentication when auth system is restored.
"""

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.services.auth_service import decode_access_token, get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        print(f"[AUTH] Received token: {token[:20]}...")
        payload = decode_access_token(token)
        print(f"[AUTH] Decoded payload: {payload}")
        user_id = payload.get("sub")
        print(f"[AUTH] User ID from token: {user_id}, type: {type(user_id)}")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        # Convert string user_id to int
        user = await get_user_by_id(db, int(user_id))
        print(f"[AUTH] User from DB: {user}")
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception as e:
        print(f"[AUTH] Exception: {type(e).__name__}: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


async def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
