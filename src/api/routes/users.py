"""
Admin user management API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.core.database import get_db
from src.models.user import User, UserRole
from src.api.dependencies.auth import require_admin

router = APIRouter(prefix="/users")


@router.get("/", response_model=list)
async def list_users(current_user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
        }
        for u in users
    ]


@router.put("/{user_id}/role")
async def change_role(
    user_id: int,
    role: UserRole,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"message": "Role updated"}


@router.put("/{user_id}/activate")
async def activate_user(
    user_id: int,
    is_active: bool,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = is_active
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"message": "User activation updated"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int, current_user=Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()

    return {"message": "User deleted"}
