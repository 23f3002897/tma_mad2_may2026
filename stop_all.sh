#!/usr/bin/env bash
# TMA - Stop All Services Script

echo "Stopping Trekking Management Application services..."

# Kill Flask
pkill -f "python app.py" && echo "  Stopped Flask Backend API" || echo "  Flask was not running"

# Kill Celery Worker & Beat
pkill -f "celery -A celery_worker.celery" && echo "  Stopped Celery Worker & Beat" || echo "  Celery was not running"

# Kill Vite Frontend
pkill -f "vite" && echo "  Stopped Vite Frontend Server" || echo "  Vite was not running"

echo "All TMA services stopped cleanly."
