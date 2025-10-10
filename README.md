# ARPsys

A FastAPI-based application for managing orders, generating reports, and handling SKU niches with real-time updates via WebSocket.

## Features

- Order management and insertion from external APIs
- Daily and flexible reports with ML predictions
- SKU niche management
- Real-time updates via WebSocket
- Background tasks for periodic data updates
- RESTful API with comprehensive endpoints

## Quick Start

### Using Make (Recommended)

```bash
# Install all dependencies
make install-all

# Run the entire system (backend + frontend)
make run-all

# Or run individual components
make run-backend    # Run only backend
make run-frontend   # Run only frontend
```

### Manual Setup

1. **Install Dependencies:**
   ```bash
   # Backend
   cd backend && pip install -r requirements.txt

   # Frontend
   cd frontend && npm install
   ```

2. **Run the System:**
   ```bash
   # Option 1: Run both servers with script
   ./run_all.sh

   # Option 2: Run manually in separate terminals
   # Terminal 1 - Backend
   cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

   # Terminal 2 - Frontend
   cd frontend && npm run dev
   ```

## Available Commands

```bash
make help              # Show all available commands
make install-all       # Install all dependencies
make run-all          # Run both servers
make test-backend     # Run backend tests
make lint-frontend    # Run frontend linting
make clean            # Clean up generated files
make stop             # Stop all running servers
```

## Configuration

The application uses Pydantic settings for configuration. All settings can be overridden via environment variables.

Create a `.env` file in the backend directory:

```
API_SESSION_TOKEN=your_session_token_here
DATABASE_PATH=database.db
DEBUG=false
LOG_LEVEL=INFO
REPORT_UPDATE_INTERVAL=3600
```

## API Documentation

Once the application is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Development

- Use `black` for code formatting
- Use `flake8` for linting
- Use `mypy` for type checking
- Run tests with `pytest`

## License

[Add license information]
