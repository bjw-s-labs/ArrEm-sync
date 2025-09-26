# Contributing to ArrEm-sync

Thank you for your interest in contributing to ArrEm-sync! This document provides guidelines and information for developers who want to contribute to the project.

## Development Setup

### Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) (modern Python package manager)
- Git

### Setup Development Environment

1. **Clone the repository**:

   ```bash
   git clone https://github.com/your-username/ArrEm-sync.git
   cd ArrEm-sync
   ```

2. **Set up development environment with uv (recommended)**:

   ```bash
   # Install dependencies and create virtual environment
   uv sync --dev

   # Activate the virtual environment
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Verify setup**:
   ```bash
   python -m pytest --version
   python -m arrem_sync.cli --help
   # Or if installed as script:
   arrem-sync --help
   ```

## Project Structure

```
ArrEm-sync/
├── arrem_sync/           # Main package
│   ├── __init__.py        # Package initialization
│   ├── cli.py             # Command-line interface
│   ├── config.py          # Configuration management (Pydantic-based)
│   ├── arr_client.py      # Radarr/Sonarr API client
│   ├── emby_client.py     # Emby API client
│   └── sync_service.py    # Tag synchronization logic
├── tests/                 # Unit tests
│   ├── test_arr_client.py
│   ├── test_config.py
│   ├── test_emby_client.py
│   └── test_sync_service.py
├── pyproject.toml         # Project configuration, dependencies, and tool settings
├── uv.lock                # Dependency lock file (uv)
├── Dockerfile             # Docker image definition
└── README.md              # User documentation
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=arrem_sync --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x
```

### Code Quality

We use modern Python development tools to maintain high code quality:

1. **ruff** - Modern linter and formatter (replaces black, isort, flake8)
2. **mypy** - Static type checker
3. **pytest** - Testing framework
4. **pytest-cov** - Test coverage reporting
5. **pydantic** - Configuration validation and data modeling

#### Running Code Quality Tools

```bash
# Format code with ruff
ruff format

# Lint code with ruff
ruff check

# Fix auto-fixable issues
ruff check --fix

# Type check with mypy
mypy arrem_sync/
```

### Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test API interactions (mocked)
- **Configuration Tests**: Validate environment variable handling
- **CLI Tests**: Ensure command-line interface works correctly

#### Test Categories

- `test_arr_client.py`: Tests for Radarr/Sonarr API interactions
- `test_emby_client.py`: Tests for Emby API interactions
- `test_config.py`: Tests for configuration loading and validation
- `test_sync_service.py`: Tests for tag synchronization logic

### API Client Architecture

- **ArrClient**: Handles Radarr/Sonarr API communication
- **EmbyClient**: Handles Emby server API communication
- Both use session management and retry logic for reliability

## Making Changes

### Before You Start

1. **Check existing issues**: Look for related issues or feature requests
2. **Create an issue**: For significant changes, create an issue first to discuss
3. **Branch naming**: Use descriptive branch names (e.g., `feature/add-jellyfin-support`, `fix/connection-timeout`)

### Development Process

1. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:

   - Write code following existing patterns and type hints
   - Add tests for new functionality
   - Update documentation as needed
   - Ensure code passes ruff and mypy checks

3. **Test your changes**:

   ```bash
   # Run tests
   pytest

   # Run with coverage
   pytest --cov=arrem_sync

   # Run code quality checks
   ruff check
   ruff format --check
   mypy arrem_sync/

   # Test CLI functionality
   arrem-sync --help
   ```

4. **Commit your changes**:

   ```bash
   git add .
   git commit -m "Add detailed commit message"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style Guidelines

- Follow PEP 8 Python style guidelines (enforced by ruff)
- Use type hints for all function parameters and return values
- Write descriptive docstrings for functions and classes
- Keep functions focused and single-purpose
- Use meaningful variable and function names
- Follow the project's ruff configuration in `pyproject.toml`
- Maintain line length of 120 characters (configured in ruff)
- Use double quotes for strings (enforced by ruff formatter)

### Adding New Features

#### Adding a New Media Server

1. Create a new client class (e.g., `jellyfin_client.py`)
2. Implement the same interface as `EmbyClient` with proper type hints
3. Add configuration options to `config.py`
4. Write comprehensive tests with proper type annotations
5. Update documentation
6. Ensure all ruff and mypy checks pass

#### Adding New Configuration Options

1. Add the field to `config.py` with proper type hints and Pydantic validation
2. Add validation rules if needed using Pydantic validators
3. Update environment variable handling
4. Add tests for the new configuration with type checking
5. Update documentation
6. Ensure mypy type checking passes

## Testing

### Running Integration Tests

For integration tests that require actual services:

```bash
# Set up test environment variables
export ARREM_ARR_TYPE="radarr"
export ARREM_ARR_URL="http://localhost:7878"
export ARREM_ARR_API_KEY="your_test_key"
export ARREM_EMBY_URL="http://localhost:8096"
export ARREM_EMBY_API_KEY="your_test_key"

# Run integration tests
arrem-sync test
```

### Test Coverage

Aim for high test coverage, especially for:

- Configuration loading and validation
- API client error handling
- Tag synchronization logic
- CLI command functionality

## Debugging

### Debug Mode

Enable debug logging for development:

```bash
export ARREM_LOG_LEVEL=DEBUG
arrem-sync
```

### Common Development Issues

1. **Import Errors**: Ensure virtual environment is activated and dependencies installed with `uv sync --dev`
2. **Test Failures**: Check that test dependencies are installed
3. **API Errors**: Verify test services are running and accessible
4. **Configuration Issues**: Check environment variable syntax
5. **Type Checking Errors**: Run `mypy arrem_sync/` to see detailed type issues
6. **Linting Errors**: Run `ruff check` to see all linting issues and `ruff check --fix` for auto-fixes

## Release Process

### Version Numbering

We follow semantic versioning (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite: `pytest`
4. Run code quality checks: `ruff check && mypy arrem_sync/`
5. Test Docker build
6. Create release PR
7. Tag release after merge

## Docker Development

### Building Docker Image

```bash
# Build development image
docker build -t arrem-sync:dev .

# Test Docker image
docker run --rm arrem-sync:dev --help
```

## Modern Python Development

This project uses modern Python 3.13+ features and tooling:

### Package Management with uv

- **uv** is a fast Python package manager that replaces pip in many workflows
- Dependencies are specified in `pyproject.toml` under `[project.dependencies]` and `[project.optional-dependencies]`
- Lock file `uv.lock` ensures reproducible builds across environments
- Use `uv sync --dev` to install all dependencies including development tools

### Code Quality with ruff

- **ruff** is a fast Python linter and formatter written in Rust
- Replaces multiple tools: black (formatting), isort (import sorting), flake8 (linting)
- Configuration in `pyproject.toml` under `[tool.ruff]`
- Supports auto-fixing many issues with `ruff check --fix`

### Type Safety with mypy

- **mypy** provides static type checking for Python
- All new code should include proper type hints
- Configuration in `pyproject.toml` under `[tool.mypy]`
- Strict settings enabled for better type safety

## Need Help?

- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub discussions for questions and ideas
- **Code Review**: All PRs require review before merging

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Follow the project's technical standards

Thank you for contributing to ArrEm-sync!
