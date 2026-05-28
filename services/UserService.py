from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from db.crud import user_actions
from db.schemas.user import UserCreate, UserResponse, UserUpdate
from services.ApiKeyService import ApiKeyService
from typing import Optional, List

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> UserResponse:
        hashed_password = UserService.hash_password(user_data.password)
        
        user = await user_actions.create(
            db,
            name=user_data.name,
            email=user_data.email,
            password=hashed_password
        )
        
        return UserResponse.model_validate(user)
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[UserResponse]:
        user = await user_actions.get_by_id(db, user_id)
        return UserResponse.model_validate(user) if user else None
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserResponse]:
        user = await user_actions.get_by_email(db, email)
        return UserResponse.model_validate(user) if user else None
    
    @staticmethod
    async def get_all_users(db: AsyncSession) -> List[UserResponse]:
        users = await user_actions.get_all(db)
        return [UserResponse.model_validate(u) for u in users]
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> Optional[UserResponse]:
        update_data = user_data.model_dump(exclude_unset=True)
        
        if 'password' in update_data and update_data['password']:
            update_data['password'] = UserService.hash_password(update_data['password'])
        
        user = await user_actions.update(db, user_id, **update_data)
        return UserResponse.model_validate(user) if user else None
    
    @staticmethod
    async def generate_and_set_api_key(db: AsyncSession, user_id: int) -> Optional[str]:
        user = await user_actions.get_by_id(db, user_id)
        if not user:
            return None
        
        api_key = await ApiKeyService.generate_unique(db)
        
        await user_actions.update_api_key(db, user_id, api_key)
        
        return api_key
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        return await user_actions.delete(db, user_id)