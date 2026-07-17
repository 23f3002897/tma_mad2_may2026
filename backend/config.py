import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # General App Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'tma-secret-jwt-key-2026')
    
    # SQLite Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "tma.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Token Expiry (24 hours)
    JWT_EXPIRATION_DELTA = timedelta(hours=24)
    
    # Redis Caching Configuration
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
    CACHE_REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    CACHE_REDIS_DB = int(os.environ.get('REDIS_CACHE_DB', 0))
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes default cache timeout
    
    # Celery Background Jobs Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/1')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/1')
    CELERY_TIMEZONE = 'Asia/Kolkata'
