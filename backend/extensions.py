from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from celery import Celery

# Initialize Flask extensions (attached to app in app.py)
db = SQLAlchemy()
cache = Cache()
celery = Celery(__name__, broker='redis://127.0.0.1:6379/1', backend='redis://127.0.0.1:6379/1')
