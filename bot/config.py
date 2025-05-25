import os
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Bot settings
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "7885838956:AAEIz5M0CW2iWbhuh9lQ0l-3HsGaelgMIIw")
    ADMINS: List[int] = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]
    
    # Webhook settings
    USE_WEBHOOK: bool = bool(os.getenv("USE_WEBHOOK", "True").lower() == "true")
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "https://your-app-url.com")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/tipbot")
    
    # Redis settings (for caching and rate limiting)
    USE_REDIS: bool = bool(os.getenv("USE_REDIS", "False").lower() == "true")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Blockchain settings
    POLYGON_RPC_URL: str = os.getenv("POLYGON_RPC_URL", "https://rpc-mumbai.maticvigil.com")
    TIP_TOKEN_ADDRESS: str = os.getenv("TIP_TOKEN_ADDRESS", "0x0000000000000000000000000000000000000000")
    
    # Thirdweb settings
    THIRDWEB_API_KEY: str = os.getenv("THIRDWEB_API_KEY", "")
    THIRDWEB_SECRET_KEY: str = os.getenv("THIRDWEB_SECRET_KEY", "")
    
    # Admin wallet
    ADMIN_WALLET_PRIVATE_KEY: str = os.getenv("ADMIN_WALLET_PRIVATE_KEY", "")
    
    # Tip settings
    MIN_TIP_AMOUNT: float = float(os.getenv("MIN_TIP_AMOUNT", "1.0"))
    MAX_TIP_AMOUNT: float = float(os.getenv("MAX_TIP_AMOUNT", "1000.0"))
    
    # Referral settings
    REFERRAL_BONUS: float = float(os.getenv("REFERRAL_BONUS", "10.0"))
    
    # Language settings
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")
    AVAILABLE_LANGUAGES: List[str] = ["en", "ru", "cn", "es"]
    
    # Command cooldown in seconds
    COMMAND_COOLDOWN: int = int(os.getenv("COMMAND_COOLDOWN", "3"))
    
    # Sentry for error tracking
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
