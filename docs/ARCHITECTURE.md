# allsorted Architecture

**Created by orpheus497**

This document describes the architectural design of allsorted, an intelligent file organization tool.

## Table of Contents

- [Overview](#overview)
- [Design Principles](#design-principles)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Extension Points](#extension-points)
- [Dependencies](#dependencies)

## Overview

allsorted is designed as a modular, extensible file organization system with a clear separation of concerns:

```
User Input → CLI → Planner → Validator → Executor → Reporter
                       ↓
                   Analyzer
                       ↓
                   Classifier
```

## Design Principles

1. **Safety First**: All operations are validated before execution, with dry-run mode and undo capability
2. **Modularity**: Each component has a single, well-defined responsibility
3. **Extensibility**: Plugin architecture allows custom classifiers and strategies
4. **Performance**: Async I/O and parallel processing for large-scale operations
5. **Type Safety**: Comprehensive type annotations for IDE support and correctness
6. **Testing**: 80%+ test coverage with unit and integration tests

## Core Components

### 1. Configuration (`config.py`)

- Manages all user settings and classification rules
- Loads from YAML files with fallback to defaults
- Validates configuration values
- Provides default classification rules for 13 categories

**Key Classes:**
- `Config`: Main configuration dataclass
- `DEFAULT_CLASSIFICATION_RULES`: Extension-to-category mappings

### 2. Models (`models.py`)

- Defines data structures used throughout the application
- Uses dataclasses for type safety and validation
- Immutable where appropriate

**Key Classes:**
- `FileInfo`: Represents a single file with metadata
- `DuplicateSet`: Group of files with identical content
- `MoveOperation`: Single file move operation
- `OrganizationPlan`: Complete plan for organizing a directory
- `OrganizationResult`: Results after plan execution

### 3. Analyzer (`analyzer.py`)

- Scans directories to identify files
- Calculates file hashes for duplicate detection
- Respects ignore patterns and managed directories
- Supports both SHA256 and xxHash algorithms

**Features:**
- Non-recursive scanning of root directory
- Recursive scanning of managed (`all_*`) directories
- Efficient hash calculation with configurable block size
- Progress callback support

### 4. Classifier (`classifier.py`)

- Determines destination for each file
- Supports multiple organization strategies
- Integrates with metadata extractors and magic classifiers

**Strategies:**
- `BY_EXTENSION`: Organize by file extension (default)
- `BY_DATE`: Organize by modification date
- `BY_SIZE`: Organize by file size categories
- `HYBRID`: Combine extension and date

### 5. Planner (`planner.py`)

- Creates organization plans from analyzed files
- Generates move operations for files and directories
- Handles duplicate detection and isolation
- Optimizes plans to remove redundant operations

### 6. Validator (`validator.py`)

- Validates plans before execution
- Checks disk space, permissions, and conflicts
- Detects circular dependencies and symlink loops
- Provides detailed error messages

**Validations:**
- Root directory accessibility
- Sufficient disk space
- Write permissions
- No circular dependencies
- No file overwrites
- Source files exist

### 7. Executor (`executor.py`)

- Executes organization plans safely
- Supports dry-run mode
- Logs all operations for undo capability
- Cleans up empty directories

**Features:**
- Atomic file operations
- Conflict resolution (rename, skip, overwrite)
- Progress reporting
- Operation logging for undo
- Empty directory cleanup

### 8. Reporter (`reporter.py`)

- Generates human-readable summaries
- Creates JSON reports for programmatic access
- Displays statistics and progress

**Outputs:**
- Console summary with Rich formatting
- Statistics tables
- JSON reports
- Text reports

### 9. CLI (`cli.py`)

- Command-line interface using Click
- Subcommands for different operations
- Progress bars and rich output

**Commands:**
- `organize`: Main organization command
- `preview`: Show what would be organized
- `validate`: Check if directory can be organized
- `undo`: Reverse operations
- `config`: Configuration management

## Advanced Components

### Magic Classifier (`magic_classifier.py`)

- Content-based file type detection using libmagic
- More accurate than extension-based classification
- Handles files with missing or incorrect extensions

### Metadata Extractor (`metadata_extractor.py`)

- Extracts EXIF from images (using Pillow)
- Extracts ID3 tags from audio (using mutagen)
- Enables organization by photo date, artist, album, etc.

### Checkpoint Manager (`checkpoint.py`)

- Saves progress during long operations
- Enables resume after interruption
- Tracks completed operations

### Directory Watcher (`watcher.py`)

- Monitors directory for new files
- Automatically organizes files as they appear
- Uses watchdog for efficient file system monitoring

## Data Flow

1. **Input**: User specifies directory and options
2. **Analysis**: FileAnalyzer scans directory, calculates hashes
3. **Classification**: FileClassifier determines destination for each file
4. **Planning**: OrganizationPlanner creates complete move plan
5. **Validation**: OperationValidator checks for issues
6. **Execution**: OrganizationExecutor performs moves
7. **Cleanup**: Empty directories removed
8. **Reporting**: Results displayed to user

## Extension Points

### Custom Classifiers

Implement custom classification logic by extending `FileClassifier`:

```python
class MyClassifier(FileClassifier):
    def classify_file(self, file_info: FileInfo) -> Tuple[str, str]:
        # Custom logic
        return ("Category", "Subcategory")
```

### Custom Strategies

Add new organization strategies in `OrganizationStrategy` enum and implement in `FileClassifier`.

### Plugin System

Future: Entry point-based plugin system for custom classifiers, validators, and reporters.

## Dependencies

### Runtime Dependencies

- **rich**: Terminal UI and progress bars
- **click**: CLI framework
- **PyYAML**: Configuration file handling
- **python-magic**: Content-based file type detection
- **Pillow**: Image processing and EXIF extraction
- **mutagen**: Audio metadata extraction
- **imagehash**: Perceptual image hashing
- **aiofiles**: Async file I/O
- **xxhash**: Fast hashing
- **watchdog**: File system monitoring
- **typing-extensions**: Python 3.8 typing backports

### Development Dependencies

- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async testing
- **pytest-mock**: Mocking
- **black**: Code formatting
- **mypy**: Type checking
- **ruff**: Linting
- **pre-commit**: Git hooks

## Performance Considerations

1. **Hash Calculation**: Most expensive operation
   - Use xxHash for 3-5x speedup over SHA256
   - Configurable block size (default 64KB)
   - Future: Parallel hashing

2. **File I/O**: Second most expensive
   - Use async I/O for network paths
   - Batch operations where possible

3. **Directory Traversal**: Optimized with os.scandir()
   - Non-recursive for unmanaged directories
   - Recursive only for managed directories

## Security

1. **Path Validation**: All paths validated to prevent directory traversal
2. **Symlink Safety**: Symlink targets validated to prevent escapes
3. **Log Injection Prevention**: Filenames sanitized before logging
4. **Permission Checks**: Validate write permissions before operations

## Testing Strategy

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test complete workflows
3. **Fixtures**: Reusable test data and configurations
4. **Mocking**: Isolate external dependencies
5. **Coverage**: Maintain 80%+ coverage

---

**For more information:**
- [Contributing Guide](CONTRIBUTING.md)
- [Repository](https://codeberg.org/orpheus497/allsorted)
- [Changelog](../CHANGELOG.md)
