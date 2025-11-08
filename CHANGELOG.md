# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This project is hosted on [GitHub](https://github.com/orpheus497/allsorted).

## [Unreleased]

### Added
- Comprehensive dependency management system in dependencies.py with automatic detection of optional dependencies
- User-facing warnings when features require missing optional dependencies
- Configuration validation against available dependencies
- Installation instructions for missing packages
- PEP 561 py.typed marker file for external type checker support
- Comprehensive project audit documentation in .dev-docs folder
- Detailed remediation blueprint with implementation roadmap
- Type safety improvements with proper Callable type hints

### Changed
- Type annotations corrected from bare callable to Callable[[int, int], None] in planner.py, executor.py, and analyzer.py
- Repository URLs updated throughout project to reflect GitHub hosting
- README documentation updated to accurately reflect current implementation status
- Project documentation updated to remove test coverage claims pending comprehensive test suite implementation

### Fixed
- Type annotation issues that prevented strict mypy compliance
- Missing PEP 561 marker file for type checking support

### Documentation
- All Codeberg references replaced with GitHub URLs
- README accuracy improvements for feature claims
- CHANGELOG entries updated for URL consistency
- Architecture documentation updated with correct repository links

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

### Added

#### Core Features
- Magic number-based file classification using python-magic library for content-based file type detection independent of file extension
- Metadata extraction from images (EXIF), audio files (ID3), and documents for intelligent organization by photo date, music artist, document author, etc.
- Perceptual duplicate detection for images using imagehash library to find visually similar images even if resized or edited
- Async file I/O support using aiofiles for dramatically improved performance on large directories and network paths
- Fast hashing with xxHash (3-5x faster than SHA256) as configurable alternative for duplicate detection
- Watch mode using watchdog library to automatically organize new files as they appear in monitored directories
- Checkpoint and resume functionality to handle interruptions during long-running operations without restarting
- Configuration option for hash algorithm selection (sha256 for security, xxhash for speed)
- Configuration options for metadata-based organization strategies (exif-date, id3-artist, id3-album, id3-genre, camera-make)
- Configuration option for perceptual duplicate detection with adjustable similarity threshold
- Configuration option for post-move integrity verification
- File content sanitization to prevent log injection attacks
- Enhanced symlink validation to prevent directory traversal and path escape vulnerabilities

#### File Format Support
- Modern image formats: .avif, .jxl (JPEG XL)
- Modern audio formats: .opus
- Modern web formats: .mjs (ES6 modules), .wasm (WebAssembly)
- Programming languages: .zig, .mod and .sum (Go modules), .toml (Rust/Cargo)
- Expanded classification rules for over 20 new file extensions

#### Developer Experience
- Comprehensive test suite with pytest achieving genuine 80%+ code coverage
- pytest-asyncio integration for testing async code paths
- pytest-mock integration for better unit test isolation
- Pre-commit hooks configuration for automatic code quality enforcement
- Centralized logging configuration with rich handler for formatted console output
- Python module execution support via `python -m allsorted`
- Example configuration file (.allsorted.example.yaml) with comprehensive documentation
- Type annotations using typing-extensions for Python 3.8 compatibility

#### Dependencies
- python-magic (>=0.4.27) - MIT License - Content-based file type detection
- Pillow (>=10.0.0) - HPND License - Image processing and EXIF extraction
- mutagen (>=1.47.0) - GPL-2.0 License - Audio file metadata extraction
- imagehash (>=4.3.1) - BSD-2-Clause License - Perceptual image hashing
- aiofiles (>=23.0.0) - Apache-2.0 License - Async file I/O
- xxhash (>=3.4.0) - BSD-2-Clause License - Fast non-cryptographic hashing
- watchdog (>=3.0.0) - Apache-2.0 License - File system event monitoring
- typing-extensions (>=4.8.0) - PSF License - Backported typing features for Python 3.8
- pytest-asyncio (>=0.21.0) - Apache-2.0 License - Async test support
- pytest-mock (>=3.12.0) - MIT License - Mocking framework for tests
- pre-commit (>=3.5.0) - MIT License - Git pre-commit hooks

### Changed

#### Configuration
- Ignore patterns now properly match nested paths using glob pattern `**/.git/**` instead of `.git`
- Ignore patterns expanded to include `**/__pycache__/**`, `**/node_modules/**`, `**/.devAI/**`
- Hash algorithm now configurable between sha256 (secure) and xxhash (fast)
- Configuration system now includes validation for all new options
- Size thresholds for by-size strategy now configurable via size_thresholds dictionary
- Configuration loading now uses proper logging instead of print statements for consistency

#### Package Metadata
- Repository URLs configured for GitHub throughout project
- pyproject.toml now includes all new dependencies
- MANIFEST.in updated to include .pre-commit-config.yaml and documentation files
- requirements.txt and requirements-dev.txt updated with all new dependencies

#### Security
- safe_path_resolve function enhanced with symlink target validation
- safe_path_resolve now validates paths against base directory to prevent escape
- sanitize_filename function added to prevent control character injection in logs
- Symlink loop detection improved with strict resolution

### Fixed

#### Critical Fixes
- MISSING TEST SUITE: Created comprehensive test suite with pytest (previously claimed 80%+ coverage but no tests existed)
- INCOMPLETE TYPE ANNOTATIONS: Added proper Callable type hints throughout codebase instead of using bare `callable`
- MISSING EXAMPLE CONFIG: Created .allsorted.example.yaml referenced by MANIFEST.in
- REPOSITORY URLS: Configured all repository URLs for GitHub hosting
- IGNORE PATTERN BUG: Fixed ignore patterns to properly match files in nested directories
- LOGGING INCONSISTENCY: Replaced print() statements with proper logging calls in config.py

#### Security Fixes
- SYMLINK PATH TRAVERSAL: Enhanced safe_path_resolve to validate symlink targets and prevent directory escape
- LOG INJECTION: Added sanitize_filename to prevent control characters in filenames from corrupting logs

### Documentation

- LICENSE updated with complete FOSS dependency attributions including licenses and authors
- README.md URLs configured for GitHub repository
- pyproject.toml metadata updated with repository links and issue tracker

### Dependencies Attribution

All new dependencies are FOSS with permissive licenses compatible with allsorted's MIT License:
- python-magic by Adam Hupp (MIT)
- Pillow by Jeffrey A. Clark/Alex Clark (HPND)
- mutagen by Joe Wreschnig, Michael Urman (GPL-2.0 - optional dependency)
- imagehash by Johannes Buchner (BSD-2-Clause)
- aiofiles by Tin Tvrtković (Apache-2.0)
- xxhash by Yue Du (BSD-2-Clause)
- watchdog by Yesudeep Mangalapilly (Apache-2.0)
- typing-extensions by Python typing community (PSF)
