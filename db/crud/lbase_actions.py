from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.lbase import BaseEntity
from typing import Optional, List

class BaseCRUD:
    async def create(self, db: AsyncSession, **kwargs) -> BaseEntity:
        # kwargs['trainedModels'] = []
        kwargs.setdefault('trainedModels', [])
        kwargs.setdefault('labelsX', [])
        kwargs.setdefault('labelsY', [])
        base = BaseEntity(**kwargs)
        db.add(base)
        await db.commit()
        await db.refresh(base)
        return base
    
    async def get_by_id(self, db: AsyncSession, base_id: int) -> Optional[BaseEntity]:
        """Получение базы по ID"""
        result = await db.execute(select(BaseEntity).where(BaseEntity.id == base_id))
        return result.scalar_one_or_none()
    
    async def get_by_user(self, db: AsyncSession, user_id: int) -> List[BaseEntity]:
        """Получение всех баз пользователя с полными данными)"""
        result = await db.execute(
            select(BaseEntity).where(BaseEntity.user_id == user_id)
        )
        return result.scalars().all()
    
    async def get_names_by_user(self, db: AsyncSession, user_id: int) -> List[dict]:
        """Получение id и названий баз пользователя"""
        result = await db.execute(
            select(BaseEntity.id, BaseEntity.name).where(BaseEntity.user_id == user_id)
        )
        return [{"id": row[0], "name": row[1]} for row in result.all()]
    
    async def update(self, db: AsyncSession, base_id: int, **kwargs) -> Optional[BaseEntity]:
        """Обновление конфига базы"""
        base = await self.get_by_id(db, base_id)
        if base:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(base, key, value)
            await db.commit()
            await db.refresh(base)
        return base
    
    async def delete(self, db: AsyncSession, base_id: int) -> bool:
        base = await self.get_by_id(db, base_id)
        if base:
            await db.delete(base)
            await db.commit()
            return True
        return False