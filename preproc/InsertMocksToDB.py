import asyncio
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from db.session import AsyncSessionLocal
from db.models.training import TrainingStatus
from services.UserService import UserService
from services.BaseService import BaseService
from services.PredictionService import PredictionService
from services.TrainingService import TrainingService
from db.schemas.user import UserCreate
from db.schemas.lbase import BaseCreate
from db.schemas.prediction import PredictionCreate
from db.schemas.training import TrainingCreate
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio


async def create_user_with_data(db: AsyncSession) -> dict:    
    user_data = UserCreate(
        name="user1",
        email="test@test.com",
        password="test123"
    )
    user = await UserService.create_user(db, user_data)
    
    api_key = await UserService.generate_and_set_api_key(db, user.id)
    print(f"API ключ: {api_key}")
    
    base1_data = BaseCreate(
        name="BaseJSON",
        N=100,
        nY=2,
        error=[0.001, 0.005],
        nX=2,
        dimension=[400, 60],
        labelsX=["FID", "T1"],
        labelsY=["cryst", "eth"],
        user_path="C:/Users/user/Desktop/original_base.txt",
        static_path="/static/bases/base1_content.txt"
    )
    base1 = await BaseService.create_base(db, user.id, base1_data)
    
    base2_data = BaseCreate(
        name="BaseJSON 2",
        N=200,
        nY=2,
        error=[0.002, 0.003],
        nX=3,
        dimension=[500, 80, 120],
        labelsX=["feature1", "feature2", "feature3"],
        labelsY=["target1", "target2"],
        user_path="C:/Users/user/Desktop/original_base2.txt",
        static_path="/static/bases/base2_content.txt"
    )
    base2 = await BaseService.create_base(db, user.id, base2_data)
    
    pred1_data = PredictionCreate(
        input_file="C:/Users/user/Desktop/test_samples.txt",
        model="CNN",
        results_path="/static/predictions/pred1_results.txt",
        base_id=base1.id
    )
    pred1 = await PredictionService.create_prediction(db, user.id, pred1_data)
    
    pred2_data = PredictionCreate(
        input_file="C:/Users/user/Desktop/test_samples2.txt",
        model="SVR",
        results_path="/static/predictions/pred2_results.txt",
        base_id=base2.id
    )
    pred2 = await PredictionService.create_prediction(db, user.id, pred2_data)
    
    training1_data = TrainingCreate(
        model="CNN",
        base_id=base1.id
    )
    training1 = await TrainingService.create_training(db, user.id, training1_data)
    await TrainingService.update_training_status(db, training1.id, TrainingStatus.COMPLETED)
    
    training2_data = TrainingCreate(
        model="Linear Regression",
        base_id=base2.id
    )
    training2 = await TrainingService.create_training(db, user.id, training2_data)
    
    return {
        "user": user,
        "bases": [base1, base2],
        "predictions": [pred1, pred2],
        "trainings": [training1, training2]
    }


async def create_empty_user(db: AsyncSession) -> dict:    
    user_data = UserCreate(
        name="User2",
        email="empty@example.com",
        password="empty123"
    )
    user = await UserService.create_user(db, user_data)
    
    return {"user": user}


async def main():
    print("=" * 50)
    
    async with AsyncSessionLocal() as db:
        try:
            user_with_data = await create_user_with_data(db)
            empty_user = await create_empty_user(db)
            print("\nБД заполнена (moked data)")
            
        except Exception as e:
            print(f"\nОшибка при заполнении БД: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())