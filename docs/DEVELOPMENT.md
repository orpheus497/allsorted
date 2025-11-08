# Development Guide for allsorted

**Project**: allsorted - Intelligent File Organizer
**Creator**: orpheus497

This guide will help you set up your development environment and contribute to allsorted.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Code Style](#code-style)
4. [Development Workflow](#development-workflow)
5. [Testing](#testing)
6. [Documentation](#documentation)
7. [Release Process](#release-process)
8. [Contributing](#contributing)

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- pip and virtualenv (recommended)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/orpheus497/allsorted.git
cd allsorted

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install allsorted in editable mode
pip install -e .

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest
```

---

## Development Setup

### Virtual Environment

Always use a virtual environment for development:

```bash
# Create venv
python -m venv venv

# Activate
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Verify
which python  # Should show path inside venv
```

### Installing Dependencies

```bash
# Runtime dependencies
pip install -r requirements.txt

# Development dependencies
pip install -r requirements-dev.txt

# Or install everything at once
pip install -e ".[dev]"
```

### IDE Setup

#### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Black Formatter
- Mypy Type Checker
- GitLens

Settings (`.vscode/settings.json`):
```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.ruffEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "editor.formatOnSave": true
}
```

#### PyCharm

- Enable Black as formatter
- Enable mypy inspection
- Configure pytest as test runner
- Enable PEP 8 inspections

---

## Code Style

### Python Style Guide

allsorted follows **PEP 8** with some modifications:

- **Line length**: 100 characters (configured in `pyproject.toml`)
- **Formatter**: Black
- **Import sorting**: isort (via ruff)
- **Type hints**: Required for all functions (enforced by mypy)

### Code Formatting

```bash
# Format code with black
black src/ tests/

# Check formatting without changes
black --check src/ tests/

# Sort imports
ruff check --fix src/ tests/
```

### Type Checking

```bash
# Run mypy
mypy src/

# Specific file
mypy src/allsorted/analyzer.py
```

### Linting

```bash
# Run ruff linter
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

### Running All Checks

```bash
# Format, lint, type check, and test
black src/ tests/
ruff check --fix src/ tests/
mypy src/
pytest
```

---

## Development Workflow

### Creating a New Feature

1. **Create a branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Write code with tests**
   - Implement feature
   - Add unit tests
   - Add integration tests if needed
   - Update documentation

3. **Run quality checks**
   ```bash
   black src/ tests/
   ruff check --fix src/ tests/
   mypy src/
   pytest --cov=allsorted
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/my-new-feature
   # Create pull request on GitHub
   ```

### Commit Message Guidelines

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
git commit -m "feat(analyzer): add support for xxHash algorithm"
git commit -m "fix(executor): handle file permissions correctly"
git commit -m "docs(readme): update installation instructions"
git commit -m "test(config): add tests for custom rules"
```

---

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_config.py

# Specific test
pytest tests/unit/test_config.py::TestConfig::test_default_config

# With coverage
pytest --cov=allsorted --cov-report=html
```

### Writing Tests

See [TESTING.md](TESTING.md) for comprehensive testing guide.

**Quick template:**
```python
"""Tests for new_feature."""

import pytest
from allsorted.new_module import NewClass


class TestNewClass:
    """Test suite for NewClass."""

    def test_basic_functionality(self) -> None:
        """Test basic functionality."""
        # Arrange
        instance = NewClass()

        # Act
        result = instance.method()

        # Assert
        assert result == expected
```

---

## Documentation

### Code Documentation

All functions must have docstrings:

```python
def my_function(arg1: str, arg2: int) -> bool:
    """
    Brief description of what the function does.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When and why this is raised
    """
    # Implementation
    pass
```

### Module Documentation

Every module should have a docstring:

```python
"""
Module description.

This module provides functionality for X, Y, and Z.
It is designed to be used with...

Example:
    >>> from allsorted.module import Class
    >>> instance = Class()
    >>> instance.method()
"""
```

### Updating Documentation

When adding features:
1. Update docstrings
2. Update README.md if user-facing
3. Update CHANGELOG.md
4. Add examples if appropriate
5. Update type hints

---

## Release Process

### Version Numbering

allsorted follows [Semantic Versioning](https://semver.org/):
- MAJOR.MINOR.PATCH (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Creating a Release

1. **Update version**
   ```bash
   # Update in pyproject.toml and src/allsorted/__init__.py
   version = "1.2.0"
   ```

2. **Update CHANGELOG.md**
   ```markdown
   ## [1.2.0] - 2025-11-08

   ### Added
   - New feature X

   ### Fixed
   - Bug Y
   ```

3. **Run all checks**
   ```bash
   black src/ tests/
   mypy src/
   ruff check src/
   pytest --cov=allsorted
   ```

4. **Commit and tag**
   ```bash
   git add .
   git commit -m "chore: release v1.2.0"
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push origin main --tags
   ```

5. **Build and publish** (maintainers only)
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

---

## Contributing

### Ways to Contribute

- 🐛 Report bugs via GitHub Issues
- 💡 Suggest features via GitHub Issues
- 📝 Improve documentation
- 🧪 Add tests
- 💻 Submit code fixes or features
- ⭐ Star the project on GitHub

### Contribution Checklist

Before submitting a PR:

- [ ] Code follows style guide (black, ruff, mypy pass)
- [ ] Tests added for new functionality
- [ ] Tests pass (`pytest`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow conventions
- [ ] No debugging code left in (print statements, etc.)
- [ ] Type hints added for all functions

### Code Review Process

1. Create pull request
2. Automated checks run (CI)
3. Maintainer reviews code
4. Address feedback
5. Merge when approved

### Getting Help

- 📖 Read the documentation
- 💬 Open a GitHub Discussion
- 🐛 Report issues on GitHub
- 📧 Contact maintainers

---

## Project Structure

```
allsorted/
├── .dev-docs/              # AI development documentation (gitignored)
├── docs/                   # User and developer documentation
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   └── TESTING.md
├── examples/               # Example scripts
├── scripts/                # Development scripts
├── src/allsorted/          # Main package
│   ├── __init__.py
│   ├── analyzer.py
│   ├── cli.py
│   ├── config.py
│   └── ...
├── tests/                  # Test suite
│   ├── unit/
│   └── integration/
├── .gitignore
├── .pre-commit-config.yaml
├── CHANGELOG.md
├── LICENSE
├── README.md
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

---

## Debugging

### Common Issues

**Import errors:**
```bash
# Reinstall in editable mode
pip install -e .
```

**Type checking failures:**
```bash
# Check specific file
mypy src/allsorted/analyzer.py

# Show full trace
mypy --show-traceback src/
```

**Test failures:**
```bash
# Run with verbose output
pytest -vv

# Run specific test with output
pytest -s tests/unit/test_config.py::test_name
```

### Using Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint() (Python 3.7+)
breakpoint()
```

---

## Resources

### Documentation
- [README.md](../README.md) - User documentation
- [TESTING.md](TESTING.md) - Testing guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture overview

### External Resources
- [Python Style Guide (PEP 8)](https://peps.python.org/pep-0008/)
- [Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
- [pytest documentation](https://docs.pytest.org/)
- [Black formatter](https://black.readthedocs.io/)
- [mypy documentation](https://mypy.readthedocs.io/)

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Contact

- **GitHub**: https://github.com/orpheus497/allsorted
- **Issues**: https://github.com/orpheus497/allsorted/issues

---

**Made with ❤️ by orpheus497**

Thank you for contributing to allsorted!
