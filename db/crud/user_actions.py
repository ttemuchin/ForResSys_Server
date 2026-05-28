from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from db.models import User
from typing import Optional, List

class UserCRUD:
    async def create(self, db: AsyncSession, name: str, email: str, password: str) -> User:
        user = User(name=name, email=email, password=password)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def get_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()
    
    async def update(self, db: AsyncSession, user_id: int, **kwargs) -> Optional[User]:
        user = await self.get_by_id(db, user_id)
        if user:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(user, key, value)
            await db.commit()
            await db.refresh(user)
        return user
    
    async def update_api_key(self, db: AsyncSession, user_id: int, api_key: str) -> Optional[User]:
        """Обновление только apiKey"""
        return await self.update(db, user_id, apiKey=api_key)
    
    async def delete(self, db: AsyncSession, user_id: int) -> bool:
        user = await self.get_by_id(db, user_id)
        if user:
            await db.delete(user)
            await db.commit()
            return True
        return False