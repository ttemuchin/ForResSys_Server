import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    APP_NAME = "Resonance Systems ML API"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    DB_NAME = os.getenv("DB_NAME", "res_sys_storage")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    
    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    SECRET_KEY = os.getenv("SECRET_KEY", "jwt-key-main")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 300
    
    ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    UPLOAD_DIR = os.path.join(STATIC_DIR, "bases")
    RESULTS_DIR = os.path.join(STATIC_DIR, "predictions")
    
    MODELS_DIR = os.path.join(BASE_DIR, "ml", "saved_models")
    
config = Config()