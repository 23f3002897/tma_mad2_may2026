"""
Database Initialization Script for Trekking Management Application (TMA) - V2.
Run this script to cleanly create/reset SQLite database tables and pre-populate default Admin & sample data.
Command: python init_db.py
"""
import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask
from config import Config
from extensions import db
from models import init_default_data

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("--> Creating SQLite database tables programmatically...")
        db.create_all()
        print("--> Tables created successfully.")
        
        print("--> Initializing default Admin, Staff, User and sample Treks...")
        init_default_data()
        print("--> Database setup completed successfully.")
