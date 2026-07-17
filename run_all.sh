#!/usr/bin/env bash
# TMA - Startup Script

echo "====================================================================="
echo "Starting Trekking Management Application (TMA)"
echo "====================================================================="

# 1. Check/Start Redis Server
echo "[1/5] Checking Redis Server..."
if pgrep -x "redis-server" >/dev/null; then
    echo "  Redis server is already running."
else
    echo "  Attempting to start Redis daemonize..."
    redis-server --daemonize yes || {
        echo "  Could not start redis-server automatically. Ensure Redis is installed and running on port 6379."
    }
fi

# 2. Check/Setup Python Virtual Environment
echo "[2/5] Checking Python Virtual Environment & Dependencies..."
cd "$(dirname "$0")/backend"
if [ ! -d "venv" ]; then
    echo "  Creating Python virtual environment (venv)..."
    python3 -m venv venv || {
        echo "  Error: Failed to create virtual environment. Ensure python3-venv is installed."
        exit 1
    }
    echo "  Installing required Python dependencies from requirements.txt..."
    ./venv/bin/pip install --upgrade pip >/dev/null 2>&1
    ./venv/bin/pip install -r requirements.txt || {
        echo "  Error: Failed to install Python dependencies."
        exit 1
    }
    echo "  Python dependencies installed successfully."
else
    echo "  Python virtual environment ready."
fi

# 3. Initialize Database & Seed Default Data
echo "[3/6] Initializing Database & Seed Data..."
./venv/bin/python init_db.py

# 4. Start Flask Backend API
echo "[4/6] Launching Flask Backend API (Port 5000)..."
./venv/bin/python app.py > flask.log 2>&1 &
FLASK_PID=$!
echo "  Flask API started (PID: $FLASK_PID)"

# 5. Start Celery Worker & Beat Scheduler
echo "[5/6] Launching Celery Worker & Beat Scheduler..."
./venv/bin/celery -A celery_worker.celery worker --loglevel=info > celery_worker.log 2>&1 &
CELERY_WORKER_PID=$!
echo "  Celery Worker started (PID: $CELERY_WORKER_PID)"

./venv/bin/celery -A celery_worker.celery beat --loglevel=info > celery_beat.log 2>&1 &
CELERY_BEAT_PID=$!
echo "  Celery Beat Scheduler started (PID: $CELERY_BEAT_PID)"

# 6. Check Node Modules & Start Vite Frontend Dev Server
echo "[6/6] Checking Frontend & Launching Vue 3 Dev Server (Port 5173)..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "  Installing Node dependencies (node_modules not found)..."
    npm install || {
        echo "  Error: Failed to install Node dependencies. Ensure npm is installed."
        exit 1
    }
    echo "  Node dependencies installed successfully."
fi
npm run dev -- --host > frontend.log 2>&1 &
VITE_PID=$!
echo "  Vite Frontend started (PID: $VITE_PID)"

cd ..

echo 
echo "ALL SERVICES ARE RUNNING SUCCESSFULLY!"

echo "Frontend Web App:  http://localhost:5173"
echo "Backend REST API:  http://localhost:5000/api/treks"
echo "Log Files:         backend/flask.log, backend/celery_worker.log, frontend/frontend.log"



echo "To stop all services, run: ./stop_all.sh"

