# Contributing to arr-tagsync

Thank you for your interest in contributing to arr-tagsync! This document provides guidelines and information for developers who want to contribute to the project.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git

### Setup Development Environment

1. **Clone the repository**:

   ```bash
   git clone https://github.com/your-username/arr-tagsync.git
   cd arr-tagsync
   ```

2. **Create virtual environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Verify setup**:
   ```bash
   python -m pytest --version
   python main.py --help
   ```

## Project Structure

```
arr-tagsync/
├── arr_tagsync/           # Main package
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
├── main.py                # Entry point
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── Dockerfile             # Docker image definition
├── pyproject.toml         # Project configuration and test settings
└── README.md              # User documentation
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=arr_tagsync --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x
```

### Code Quality

We use several tools to maintain code quality:

1. **pytest** for testing
2. **coverage** for test coverage reporting
3. **pydantic** for configuration validation

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

   - Write code following existing patterns
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**:

   ```bash
   # Run tests
   pytest

   # Test CLI functionality
   python main.py --help
   python main.py test  # (requires valid config)
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

- Follow PEP 8 Python style guidelines
- Use type hints where possible
- Write descriptive docstrings for functions and classes
- Keep functions focused and single-purpose
- Use meaningful variable and function names

### Adding New Features

#### Adding a New Media Server

1. Create a new client class (e.g., `jellyfin_client.py`)
2. Implement the same interface as `EmbyClient`
3. Add configuration options
4. Write comprehensive tests
5. Update documentation

#### Adding New Configuration Options

1. Add the field to `config.py`
2. Add validation if needed
3. Update environment variable handling
4. Add tests for the new configuration
5. Update documentation

## Testing

### Running Integration Tests

For integration tests that require actual services:

```bash
# Set up test environment variables
export TAGSYNC_ARR_TYPE="radarr"
export TAGSYNC_ARR_URL="http://localhost:7878"
export TAGSYNC_ARR_API_KEY="your_test_key"
export TAGSYNC_EMBY_URL="http://localhost:8096"
export TAGSYNC_EMBY_API_KEY="your_test_key"

# Run integration tests
python main.py test
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
export TAGSYNC_LOG_LEVEL=DEBUG
python main.py sync --dry-run
```

### Common Development Issues

1. **Import Errors**: Ensure virtual environment is activated
2. **Test Failures**: Check that test dependencies are installed
3. **API Errors**: Verify test services are running and accessible
4. **Configuration Issues**: Check environment variable syntax

## Release Process

### Version Numbering

We follow semantic versioning (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version in `arr_tagsync/__init__.py`
2. Update CHANGELOG.md
3. Run full test suite
4. Test Docker build
5. Create release PR
6. Tag release after merge

## Docker Development

### Building Docker Image

```bash
# Build development image
docker build -t arr-tagsync:dev .

# Test Docker image
docker run --rm arr-tagsync:dev --help
```

### Docker Compose Development

```bash
# Create override file for development
cp docker-compose.yml docker-compose.override.yml

# Edit with your development settings
# Then run:
docker-compose run --rm arr-tagsync test
```

## Need Help?

- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub discussions for questions and ideas
- **Code Review**: All PRs require review before merging

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Follow the project's technical standards

Thank you for contributing to arr-tagsync!
