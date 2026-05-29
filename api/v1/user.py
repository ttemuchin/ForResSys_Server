from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import timedelta

from db.session import get_db
from services.UserService import UserService
from services.ApiKeyService import ApiKeyService
from db.schemas.user import UserCreate, UserResponse, UserUpdate
from core.jwt import create_access_token
from core.jwt import get_current_user_jwt
from core.exceptions import (
    UserAlreadyExistsException,
    UserNotFoundException,
    InvalidCredentialsException
)

router = APIRouter()

# апи ключ
# админ функции
# пользовательская часть где меняем данные для входа
# логин ИЛИ почта

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # есть проверка сущ-й почты. можно возвращть токен при реге, но думаю не обязательно. на фронте сделали авто логин после реги
    existing_user = await UserService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    try:
        user = await UserService.create_user(db, user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.post("/login")
async def login(email: str, password: str, db: AsyncSession = Depends(get_db)):
    """Аутентификация, получение токена"""
    user = await UserService.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    from db.crud.user_actions import UserCRUD
    crud = UserCRUD()
    db_user = await crud.get_by_email(db, email)
    
    if not UserService.verify_password(password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Создаем JWT токен
    access_token = create_access_token(
        data={"sub": str(db_user.id), "email": db_user.email}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(db_user)
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Получение информации о текущем авторизованном пользователе"""
    return current_user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновление данных пользователя"""
    user = await UserService.update_user(db, user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/{user_id}/api-key")
async def generate_api_key(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Генерация нового API ключа для пользователя"""
    api_key = await UserService.generate_and_set_api_key(db, user_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"apiKey": api_key}

# Получение всех пользователей(адм)
@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    # потенциально проверка на администратора
):
    """Получение списка всех пользователей"""
    users = await UserService.get_all_users(db)
    return users

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    deleted = await UserService.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return None