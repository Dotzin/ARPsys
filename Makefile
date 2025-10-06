.PHONY: test test-unit test-integration test-api install-test-deps clean-test

# Install test dependencies
install-test-deps:
	pip install -r requirements-test.txt

# Set PYTHONPATH for all test commands
PYTHONPATH := /workspaces/ARPsys

# Run all tests
test: test-unit test-integration test-api

# Run unit tests only
test-unit:
	PYTHONPATH=$(PYTHONPATH) pytest tests/test_services.py -v

# Run integration tests only
test-integration:
	PYTHONPATH=$(PYTHONPATH) pytest tests/test_integration.py -v

# Run API tests only
test-api:
	PYTHONPATH=$(PYTHONPATH) pytest tests/test_app.py -v

# Run tests with coverage
test-cov:
	PYTHONPATH=$(PYTHONPATH) pytest --cov=app --cov-report=html tests/

# Run tests in parallel
test-parallel:
	PYTHONPATH=$(PYTHONPATH) pytest -n auto tests/

# Clean test artifacts
clean-test:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f .coverage

# Run specific test file
test-file:
	@echo "Usage: make test-file FILE=tests/test_app.py"

# Run tests with verbose output
test-verbose:
	PYTHONPATH=$(PYTHONPATH) pytest tests/ -v -s

# Run tests and stop on first failure
test-fast:
	PYTHONPATH=$(PYTHONPATH) pytest tests/ -x
