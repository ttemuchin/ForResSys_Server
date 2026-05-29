from sqlalchemy.ext.asyncio import AsyncSession
from db.crud.lbase_actions import BaseCRUD
from db.schemas.lbase import BaseCreate, BaseUpdate, BaseResponse, BaseNameResponse
from typing import Optional, List

base_crud = BaseCRUD()

class BaseService:
    @staticmethod
    async def create_base(db: AsyncSession, user_id: int, base_data: BaseCreate) -> BaseResponse:
        base = await base_crud.create(
            db,
            user_id=user_id,
            name=base_data.name,
            N=base_data.N,
            nY=base_data.nY,
            error=base_data.error,
            nX=base_data.nX,
            dimension=base_data.dimension,
            user_path=base_data.user_path,
            static_path=base_data.static_path
        )
        return BaseResponse.model_validate(base)
    
    @staticmethod
    async def get_base_by_id(db: AsyncSession, base_id: int) -> Optional[BaseResponse]:
        base = await base_crud.get_by_id(db, base_id)
        return BaseResponse.model_validate(base) if base else None
    
    @staticmethod
    async def get_bases_by_user(db: AsyncSession, user_id: int) -> List[BaseResponse]:
        """Получение всех баз пользователя"""
        bases = await base_crud.get_by_user(db, user_id)
        return [BaseResponse.model_validate(b) for b in bases]
    
    @staticmethod
    async def get_base_names_by_user(db: AsyncSession, user_id: int) -> List[BaseNameResponse]:
        """Получение названий всех баз пользователя"""
        names = await base_crud.get_names_by_user(db, user_id)
        return [BaseNameResponse(id=n['id'], name=n['name']) for n in names]
    
    @staticmethod
    async def update_base(db: AsyncSession, base_id: int, base_data: BaseUpdate) -> Optional[BaseResponse]:
        update_data = base_data.model_dump(exclude_unset=True)
        base = await base_crud.update(db, base_id, **update_data)
        return BaseResponse.model_validate(base) if base else None
    
    @staticmethod
    async def delete_base(db: AsyncSession, base_id: int) -> bool:
        return await base_crud.delete(db, base_id)