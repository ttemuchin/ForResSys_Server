from .user_actions import UserCRUD
from .lbase_actions import BaseCRUD
from .prediction_actions import PredictionCRUD
from .training_actions import TrainingCRUD

user_crud = UserCRUD()
base_crud = BaseCRUD()
prediction_crud = PredictionCRUD()
training_crud = TrainingCRUD()