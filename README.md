# ARPsys

A FastAPI-based application for managing orders, generating reports, and handling SKU niches with real-time updates via WebSocket.

## Features

- Order management and insertion from external APIs
- Daily and flexible reports with ML predictions
- SKU niche management
- Real-time updates via WebSocket
- Background tasks for periodic data updates
- RESTful API with comprehensive endpoints

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   API_SESSION_TOKEN=your_session_token_here
   DATABASE_PATH=database.db
   DEBUG=false
   LOG_LEVEL=INFO
   REPORT_UPDATE_INTERVAL=3600
   ```
4. Run the application:
   ```bash
   python -m app.main
   ```

## API Documentation

Once the application is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Configuration

The application uses Pydantic settings for configuration. All settings can be overridden via environment variables.

## Development

- Use `black` for code formatting
- Use `flake8` for linting
- Use `mypy` for type checking
- Run tests with `pytest`

## License

[Add license information]
