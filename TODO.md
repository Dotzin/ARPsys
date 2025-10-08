# Refactoring TODO List

## Security
- [x] Move hardcoded session tokens to environment variables in relatorio_routes.py and periodic_report_task.py
- [x] Add .env file and python-dotenv to requirements

## Code Quality
- [x] Add type hints to all functions and classes
- [x] Replace print statements with logging in train.py
- [x] Standardize language to English (remove Portuguese comments/variables)
- [x] Add comprehensive docstrings to all modules, classes, and functions

## Structure
- [x] Break long functions in report_service.py into smaller methods
- [x] Refactor dependency injection to use FastAPI's Depends properly instead of app.state overrides
- [x] Extract constants and magic numbers to config files
- [x] Remove code duplication in data processing

## Error Handling
- [x] Add proper input validation using Pydantic models
- [x] Improve exception handling with specific exception types
- [x] Add retry logic for external API calls

## Configuration
- [x] Implement proper configuration management using Pydantic settings
- [x] Move database path and other configs to settings

## Performance
- [x] Optimize database queries and pandas operations
- [x] Add caching where appropriate
- [x] Use async database operations if possible

## Testing
- [x] Add unit tests for all services
- [x] Add integration tests
- [x] Ensure test coverage > 80%

## Tools
- [x] Add pre-commit hooks for linting
- [x] Configure black, flake8, mypy
- [x] Add Makefile targets for linting and testing

## Documentation
- [x] Add README.md with setup and usage instructions
- [x] Add API documentation
- [x] Document configuration options
