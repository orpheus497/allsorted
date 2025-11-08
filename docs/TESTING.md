# Testing Guide for allsorted

**Project**: allsorted - Intelligent File Organizer
**Creator**: orpheus497

This document describes the testing philosophy, practices, and guidelines for allsorted.

---

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Coverage](#test-coverage)
6. [Testing Best Practices](#testing-best-practices)
7. [Continuous Integration](#continuous-integration)

---

## Overview

allsorted uses **pytest** as its testing framework with plugins for coverage, async testing, and mocking.

### Testing Philosophy

- **Comprehensive**: Test all critical functionality
- **Fast**: Unit tests should run in milliseconds
- **Isolated**: Tests should not depend on each other
- **Readable**: Tests should be self-documenting
- **Maintainable**: Easy to update as code evolves

### Test Types

1. **Unit Tests** (`tests/unit/`) - Test individual components in isolation
2. **Integration Tests** (`tests/integration/`) - Test component interactions
3. **Functional Tests** - Test end-to-end workflows (coming soon)

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_analyzer.py           # File analysis tests
│   ├── test_config.py             # Configuration tests
│   ├── test_models.py             # Data model tests
│   ├── test_utils.py              # Utility function tests
│   └── ...
└── integration/
    ├── __init__.py
    └── test_full_workflow.py      # End-to-end tests
```

---

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_config.py

# Run specific test function
pytest tests/unit/test_config.py::TestConfig::test_default_config

# Run tests matching a pattern
pytest -k "test_config"
```

### With Coverage

```bash
# Run tests with coverage report
pytest --cov=allsorted

# Generate HTML coverage report
pytest --cov=allsorted --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Continuous Watching

```bash
# Install pytest-watch
pip install pytest-watch

# Watch for changes and auto-run tests
ptw
```

---

## Writing Tests

### Unit Test Example

```python
"""Tests for the Config class."""

import pytest
from allsorted.config import Config
from allsorted.models import OrganizationStrategy


class TestConfig:
    """Test suite for Config class."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = Config()

        assert config.strategy == OrganizationStrategy.BY_EXTENSION
        assert config.detect_duplicates is True
        assert config.hash_algorithm == "sha256"

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = Config()
        config.detect_duplicates = False

        assert config.detect_duplicates is False
```

### Integration Test Example

```python
"""Integration tests for full workflow."""

import pytest
from pathlib import Path
from allsorted.planner import OrganizationPlanner
from allsorted.executor import OrganizationExecutor
from allsorted.config import Config


def test_complete_organization(temp_dir: Path) -> None:
    """Test complete organization workflow."""
    # Setup: Create test files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.jpg").write_text("image data")

    # Execute: Run organization
    config = Config()
    planner = OrganizationPlanner(config)
    plan = planner.create_plan(temp_dir)

    executor = OrganizationExecutor(dry_run=False, log_operations=True)
    result = executor.execute_plan(plan)

    # Verify: Check results
    assert result.files_moved >= 2
    assert result.is_complete_success
    assert (temp_dir / "all_Docs" / "Text").exists()
    assert (temp_dir / "all_Pics" / "Photos").exists()
```

### Using Fixtures

```python
# In conftest.py
import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# In test file
def test_something(temp_dir: Path) -> None:
    """Test using temporary directory."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()
```

---

## Test Coverage

### Coverage Goals

- **Overall**: Maintain ≥85% code coverage
- **Critical modules**: ≥90% coverage
  - `analyzer.py`
  - `planner.py`
  - `executor.py`
  - `validator.py`
- **Utility modules**: ≥80% coverage

### Checking Coverage

```bash
# Generate coverage report
pytest --cov=allsorted --cov-report=term-missing

# See which lines are not covered
pytest --cov=allsorted --cov-report=html
open htmlcov/index.html
```

### Coverage Configuration

Coverage settings are in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "**/__pycache__/*"]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
```

---

## Testing Best Practices

### 1. Test Organization

```python
class TestFeatureName:
    """Group related tests together."""

    def test_normal_case(self) -> None:
        """Test the typical use case."""
        pass

    def test_edge_case(self) -> None:
        """Test edge cases."""
        pass

    def test_error_case(self) -> None:
        """Test error handling."""
        pass
```

### 2. Test Naming

- Use descriptive names that explain what is tested
- Follow pattern: `test_<what>_<condition>_<expected>`
- Examples:
  - `test_config_from_dict_with_valid_data_returns_config`
  - `test_analyzer_with_invalid_path_raises_error`

### 3. Arrange-Act-Assert Pattern

```python
def test_example(self) -> None:
    """Test example following AAA pattern."""
    # Arrange: Set up test data
    config = Config()
    test_file = Path("test.txt")

    # Act: Execute the functionality
    result = config.get_category_for_extension(".txt")

    # Assert: Verify the results
    assert result == ("Docs", "Text")
```

### 4. Use Fixtures for Setup

```python
@pytest.fixture
def sample_config() -> Config:
    """Create a sample configuration for testing."""
    config = Config()
    config.detect_duplicates = False
    return config


def test_with_fixture(sample_config: Config) -> None:
    """Test using a fixture."""
    assert not sample_config.detect_duplicates
```

### 5. Test Edge Cases

```python
def test_edge_cases(self) -> None:
    """Test boundary conditions."""
    config = Config()

    # Empty string
    assert config.get_category_for_extension("") == ("Misc", "Unsorted")

    # Extension without dot
    assert config.get_category_for_extension("txt") == ("Docs", "Text")

    # Unknown extension
    assert config.get_category_for_extension(".xyz") == ("Misc", "Unsorted")
```

### 6. Test Error Handling

```python
def test_error_handling(self) -> None:
    """Test that errors are properly raised."""
    analyzer = FileAnalyzer(Config())

    with pytest.raises(ValueError, match="does not exist"):
        analyzer.analyze_directory(Path("/nonexistent"))
```

### 7. Use Parametrization for Multiple Cases

```python
@pytest.mark.parametrize("extension,expected", [
    (".txt", ("Docs", "Text")),
    (".jpg", ("Pics", "Photos")),
    (".mp3", ("Audio", "Music")),
    (".unknown", ("Misc", "Unsorted")),
])
def test_extensions(extension: str, expected: tuple) -> None:
    """Test multiple extensions."""
    config = Config()
    assert config.get_category_for_extension(extension) == expected
```

---

## Continuous Integration

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### CI Pipeline

Tests run automatically on:
- Every push to main branch
- Every pull request
- Scheduled nightly runs

**Requirements for passing CI:**
- All tests pass
- Test coverage ≥85%
- Type checking passes (mypy)
- Code formatting correct (black)
- Linting passes (ruff)

---

## Debugging Tests

### Running Single Test with Output

```bash
# Show print statements
pytest -s tests/unit/test_config.py::test_default_config

# Show detailed output
pytest -vv tests/unit/test_config.py
```

### Using pytest debugger

```python
def test_something(self) -> None:
    """Test with debugger."""
    result = some_function()

    # Drop into debugger
    import pdb; pdb.set_trace()

    assert result == expected
```

### Debugging in VS Code

Add to `.vscode/launch.json`:

```json
{
    "name": "Python: Pytest",
    "type": "python",
    "request": "launch",
    "module": "pytest",
    "args": ["tests/"]
}
```

---

## Adding New Tests

### Checklist for New Features

When adding a new feature, ensure you add tests for:

- ✅ Normal/happy path
- ✅ Edge cases (empty input, maximum values, etc.)
- ✅ Error cases (invalid input, missing files, etc.)
- ✅ Integration with existing features
- ✅ Performance (if applicable)

### Test Template

```python
"""
Tests for <module_name>.

Created by orpheus497
"""

import pytest
from pathlib import Path
from allsorted.<module> import <Class>


class Test<ClassName>:
    """Test suite for <ClassName>."""

    def test_default_behavior(self) -> None:
        """Test default behavior."""
        # Arrange
        instance = <Class>()

        # Act
        result = instance.method()

        # Assert
        assert result == expected

    def test_edge_case(self) -> None:
        """Test edge case."""
        pass

    def test_error_case(self) -> None:
        """Test error handling."""
        with pytest.raises(ExpectedException):
            # Code that should raise exception
            pass
```

---

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Python testing best practices](https://docs.python-guide.org/writing/tests/)

---

**Questions?** Open an issue on [GitHub](https://github.com/orpheus497/allsorted/issues)

**Made with ❤️ by orpheus497**
