# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This project is hosted on [Codeberg](https://codeberg.org/orpheus497/allsorted.git).

## [1.0.0] - 2025-11-03

### Features

#### Core Organization
- Intelligent file classification by extension into 13 top-level categories (Docs, Audio, Pics, Vids, Programs, Code, Archives, System, Apps, Web, Misc)
- Managed directory system with `all_` prefix for all created directories (e.g., `all_Docs`, `all_Pics`, `all_Folders`)
- Non-recursive scanning of current directory with recursive organization of managed (`all_*`) directories
- Automatic subdirectory organization into `all_Folders` directory
- Smart cleanup that only removes empty directories within managed directories
- Multiple organization strategies: by-extension, by-date, by-size, hybrid
- Custom classification rule system via YAML rule files
- Only creates category directories that actually contain files

#### Duplicate Detection & Management
- SHA256 content-based duplicate file detection
- Intelligent primary file selection (shortest path + oldest modification time)
- Complete directory structure preservation in `all_Duplicates` folder
- Configurable duplicate isolation

#### Safety & Validation
- Dry-run mode for previewing operations without executing via `--dry-run` flag
- Pre-flight validation system checking disk space, permissions, and potential conflicts
- Atomic file operations with rollback capability
- Path traversal validation to prevent operations outside target directory
- Symlink detection and safe handling to prevent infinite loops
- Permission validation for all target directories
- Disk space validation before moving large files
- File conflict detection before operations begin
- Comprehensive error recovery with transaction logging

#### User Interface & Reporting
- Real-time progress reporting with progress bars and file counts using rich library
- JSON and human-readable summary report generation after organization completion
- Statistics dashboard showing files processed, duplicates found, and storage space saved
- Enhanced preview showing both file and directory operations separately
- Detailed logging system with multiple output levels
- Click-based CLI with subcommands: organize, preview, undo, validate, config

#### Configuration & Customization
- YAML configuration file support at `~/.config/allsorted/config.yaml`
- Configurable file conflict resolution strategies (rename, skip, overwrite)
- Include/exclude pattern matching for selective file processing via glob patterns
- Directory prefix configuration (`directory_prefix`) for managed directories
- Configuration validation and merging system

#### Undo & Recovery
- Undo functionality with operation log persistence in JSON format
- Complete operation history with timestamps
- Safe rollback of all file operations

#### Developer Experience
- Modular package structure separating library functionality from CLI interface
- Type hints throughout codebase for improved IDE support and type safety
- Comprehensive test suite with pytest achieving 80%+ code coverage
- Developer tooling configuration for black, mypy, and ruff
- Dataclasses for type safety and validation
- Structured logging with contextual information

#### Installation & Setup
- pip installation support with editable mode
- Installation scripts for Linux/macOS and Windows
- Python version checks (3.8+) and dependency validation
- pyproject.toml following PEP 517/518 standards

### Documentation
- Comprehensive README with examples, troubleshooting guide, and feature documentation
- Detailed command reference for all CLI subcommands
- Configuration guide with example YAML files
- Step-by-step usage examples including multi-run scenarios
- Visual directory structure examples showing `all_` prefix system
- CHANGELOG following Keep a Changelog format
- MIT License with proper attribution

### Dependencies
- Python 3.8+
- rich - Terminal UI and progress reporting
- click - CLI framework
- PyYAML - Configuration file handling

### Changed
- Refactored monolithic main.py into modular package structure with clear separation of concerns
- Improved error handling with specific exception types and detailed error messages
- Enhanced installation scripts with Python version checks (3.8+) and dependency validation
- Updated README with comprehensive documentation, examples, troubleshooting guide, and FAQ
- Modernized project structure with pyproject.toml following PEP 517/518 standards
- Replaced dictionary-based data structures with dataclasses for type safety and validation
- Enhanced logging with structured messages, log levels, and contextual information
- Improved progress reporting from simple counts to detailed progress bars with ETA
- Installation now supports both pip and manual installation methods
- Classification rules now support case-insensitive matching and wildcard patterns
- Duplicate detection now preserves complete directory structure in Duplicates folder
- Empty directory cleanup now provides detailed logging of removed directories

### Removed
- Non-functional phase2_processor.py with hardcoded paths
- Non-functional phase2_largefile_processor.py with incomplete implementation
- Non-functional phase2_unclassified_processor.py with manual manifest editing
- Non-functional phase2_finalizer.py with hardcoded paths
- Non-functional phase3_planner.py duplicate of main.py functionality
- Non-functional phase3_executor.py with hardcoded paths
- Non-functional phase3_cleanup.py duplicate implementation
- organizer_v2.py duplicate analyzer implementation with hardcoded paths
- folder_organizer.py functionality integrated into main executor
- Hardcoded `/home/orpheus497/Downloads` paths throughout codebase
- Manual JSON manifest editing workflow
- CONTRIBUTING.md file to streamline project structure

### Fixed
- Ignore list not properly excluding nested paths in subdirectories during analysis
- Path manipulation inconsistencies between Windows and Unix-like systems
- Missing handling of symbolic links causing potential infinite loops during traversal
- Empty Misc/Unsorted category with empty list never matching classification intent
- Potential filename collisions in Duplicates folder when multiple files share names
- Silent failures during file operations now properly logged and reported
- Missing disk space validation before operations causing failures mid-execution
- Missing permission validation causing cryptic error messages
- Incomplete error messages not providing actionable troubleshooting information
- Race conditions when multiple instances run simultaneously
- Improper handling of files with Unicode characters in names
- Incorrect relative path calculation for duplicate file preservation

### Security
- Added path traversal validation to prevent operations outside target directory
- Implemented symlink attack vector mitigation with resolution validation
- Added input sanitization for all filesystem paths from user input
- Added permission validation before all file operations to prevent unauthorized access
- Implemented secure temporary file handling for operation logs

## [Unreleased]

*No unreleased changes*
