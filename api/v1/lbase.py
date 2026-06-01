from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os
import shutil
from pathlib import Path

from db.session import get_db
from services.BaseService import BaseService
from services.UserService import UserService
from db.schemas.lbase import BaseCreate, BaseUpdate, BaseResponse, BaseNameResponse
from core.jwt import get_current_user_jwt
from db.schemas.user import UserResponse
from config import config

router = APIRouter()

@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_base(
    name: str = Form(...),
    N: int = Form(...),
    nY: int = Form(...),
    error: str = Form(...),  # JSON строка
    nX: int = Form(...),
    dimension: str = Form(...),  # JSON строка
    labelsX: str = Form(...),  # JSON строка
    labelsY: str = Form(...),  # JSON строка
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Создание новой обучающей базы с загрузкой файла"""
    import json
    
    try:
        error_list = json.loads(error)
        dimension_list = json.loads(dimension)
        labelsX_list = json.loads(labelsX)
        labelsY_list = json.loads(labelsY)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format: {str(e)}"
        )
    
    user_static_dir = Path(config.STATIC_DIR) / "bases" / str(current_user.id)
    user_static_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = user_static_dir / f"{name}.txt"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    base_data = BaseCreate(
        name=name,
        N=N,
        nY=nY,
        error=error_list,
        nX=nX,
        dimension=dimension_list,
        labelsX=labelsX_list,
        labelsY=labelsY_list,
        user_path=file.filename,
        static_path=str(file_path)
    )
    
    base = await BaseService.create_base(db, current_user.id, base_data)
    return base

@router.get("/", response_model=List[BaseResponse])
async def get_user_bases(
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех баз текущего пользователя"""
    bases = await BaseService.get_bases_by_user(db, current_user.id)
    return bases


@router.get("/names", response_model=List[BaseNameResponse])
async def get_user_base_names(
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Получение названий всех баз текущего пользователя"""
    # для селекторов
    names = await BaseService.get_base_names_by_user(db, current_user.id)
    return names

@router.get("/{base_id}", response_model=BaseResponse)
async def get_base(
    base_id: int,
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Получение конкретной базы по ID"""
    base = await BaseService.get_base_by_id(db, base_id)
    if not base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base not found"
        )
    
    if base.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return base

@router.get("/{base_id}/content")
async def get_base_content(
    base_id: int,
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Получение текстового содержимого файла базы"""
    base = await BaseService.get_base_by_id(db, base_id)
    if not base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base not found"
        )
    
    if base.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        with open(base.static_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content, "filename": base.name}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}"
        )
    

# содержимое редактора - Blob - File - FormData - сервер
@router.put("/{base_id}")
async def update_base_full(
    base_id: int,
    config: Optional[str] = Form(None),  # JSON строка с конфигурацией
    file: Optional[UploadFile] = File(None),  # Новый файл для замены содержимого
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Обновление конфигурации И/ИЛИ содержимого файла"""
    import json
    
    existing_base = await BaseService.get_base_by_id(db, base_id)
    if not existing_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base not found"
        )
    
    if existing_base.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if config:
        try:
            config_data = json.loads(config)
            base_update = BaseUpdate(**config_data)
            await BaseService.update_base(db, base_id, base_update)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid config JSON: {str(e)}"
            )
    
    # Обновляем содержимое файла, если передан новый файл
    if file:
        file_path = Path(existing_base.static_path)
        try:
            content = await file.read()
            with open(file_path, 'wb') as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update file: {str(e)}"
            )
    
    updated_base = await BaseService.get_base_by_id(db, base_id)
    return updated_base


@router.patch("/{base_id}/config", response_model=BaseResponse)
async def update_base_config(
    base_id: int,
    base_data: BaseUpdate,
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Обновление только конфигурации базы"""
    existing_base = await BaseService.get_base_by_id(db, base_id)
    if not existing_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base not found"
        )
    
    if existing_base.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    updated_base = await BaseService.update_base(db, base_id, base_data)
    return updated_base


@router.put("/{base_id}/content")
async def update_base_content(
    base_id: int,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Обновление только содержимого файла базы (замена файла)"""
    base = await BaseService.get_base_by_id(db, base_id)
    if not base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base not found"
        )
    
    if base.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # новый файл поверх старого
    file_path = Path(base.static_path)
    try:
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return {"message": "File content updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update file: {str(e)}"
        )



@router.delete("/{base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_base(
    base_id: int,
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Удаление базы и связанного файла"""
    base = await BaseService.get_base_by_id(db, base_id)
    if not base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base not found"
        )
    
    if base.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # файл
    try:
        if os.path.exists(base.static_path):
            os.remove(base.static_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )
    
    deleted = await BaseService.delete_base(db, base_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base not found"
        )
    
    return None