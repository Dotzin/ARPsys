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
- [ ] Refactor dependency injection to use FastAPI's Depends properly instead of app.state overrides
- [x] Extract constants and magic numbers to config files
- [x] Remove code duplication in data processing

## Error Handling
- [x] Add proper input validation using Pydantic models
- [ ] Improve exception handling with specific exception types
- [ ] Add retry logic for external API calls

## Configuration
- [ ] Implement proper configuration management using Pydantic settings
- [ ] Move database path and other configs to settings

## Performance
- [ ] Optimize database queries and pandas operations
- [ ] Add caching where appropriate
- [ ] Use async database operations if possible

## Testing
- [ ] Add unit tests for all services
- [ ] Add integration tests
- [ ] Ensure test coverage > 80%

## Tools
- [ ] Add pre-commit hooks for linting
- [x] Configure black, flake8, mypy
- [x] Add Makefile targets for linting and testing

## Documentation
- [ ] Add README.md with setup and usage instructions
- [ ] Add API documentation
- [ ] Document configuration options
