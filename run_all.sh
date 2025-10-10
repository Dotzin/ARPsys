#!/bin/bash
# Script to run backend and frontend servers concurrently

# Check if dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing backend dependencies..."
    cd backend && pip install -r requirements.txt && cd ..
fi

# Set PYTHONPATH for backend
export PYTHONPATH=/home/aribas/.local/lib/python3.13/site-packages:backend

# Run backend server with PYTHONPATH
echo "Starting backend server..."
cd backend
PYTHONPATH=/home/aribas/.local/lib/python3.13/site-packages:backend uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Run frontend server
echo "Starting frontend server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "ARPsys is running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo "Press Ctrl+C to stop all servers"

# Wait for both processes
wait $BACKEND_PID
wait $FRONTEND_PID
