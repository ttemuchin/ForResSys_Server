import secrets
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.user import User

class ApiKeyService:
    @staticmethod
    def generate() -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(16))
    
    @staticmethod
    async def generate_unique(db: AsyncSession) -> str:
        """Генерация уникального API ключа длиной 16 символов"""
        max_attempts = 5
        for _ in range(max_attempts):
            api_key = ApiKeyService.generate()
            result = await db.execute(
                select(User).where(User.apiKey == api_key)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                return api_key
        
        raise Exception("Failed to generate unique API key after 5 attempts")