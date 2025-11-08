# allsorted - Intelligent File Organizer

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**allsorted** is a powerful, intelligent command-line tool that brings order to chaotic directories. It automatically classifies files by type, detects and isolates duplicates, and organizes everything into a clean, logical structure—all with enterprise-grade safety features and undo capability.

**Created by orpheus497**

This project is hosted on [GitHub](https://github.com/orpheus497/allsorted).

---

## ✨ Features

- 🎯 **Intelligent Classification** - Automatically categorizes files by extension into 13 top-level categories
- 📁 **Smart Directory Handling** - Uses `all_` prefix for managed directories; recursively organizes only its own folders
- 🔍 **Duplicate Detection** - Finds identical files using SHA256 content hashing
- 🛡️ **Safety First** - Dry-run mode, pre-flight validation, and full undo capability
- 📊 **Rich Progress Reporting** - Real-time progress bars and detailed statistics
- ⚙️ **Highly Configurable** - YAML configuration files and multiple organization strategies
- 🔄 **Flexible Strategies** - Organize by extension, date, size, or hybrid approach
- 📝 **Comprehensive Logging** - Detailed operation logs and JSON reports
- 🚀 **Fast & Efficient** - Optimized file operations with smart caching
- ✅ **Production Ready** - Type-safe with comprehensive type hints, fully documented

---

## 🚀 Quick Start

### Installation

**Method 1: Using pip (recommended)**
```bash
pip install -e .
```

**Method 2: Using installation scripts**

Linux/macOS:
```bash
cd scripts
./install.sh
```

Windows:
```batch
cd scripts
install.bat
```

### Basic Usage

Organize the current directory:
```bash
allsorted organize
```

Preview what would happen (dry-run):
```bash
allsorted organize --dry-run
```

Organize a specific directory:
```bash
allsorted organize /path/to/messy/folder
```

---

## 📖 How It Works

allsorted operates in a safe, predictable workflow:

### 1. **Analysis Phase**
- Scans **only the current directory** (not recursive into non-managed subdirectories)
- **Recursively scans `all_*` directories** (directories created by allsorted)
- Calculates SHA256 hash for each file (content-based)
- Identifies duplicate files regardless of filename
- Tracks subdirectories for organization
- Respects ignore patterns (`.git`, `node_modules`, etc.)

### 2. **Planning Phase**
- Classifies files by extension (or date/size based on strategy)
- Plans to move non-managed subdirectories to the "all_Folders" directory
- Selects "primary" file for duplicates (shortest path + oldest date)
- Generates complete move plan
- Detects potential conflicts

### 3. **Validation Phase**
- Checks disk space availability
- Validates write permissions
- Detects circular dependencies
- Prevents overwrites

### 4. **Execution Phase**
- Creates destination directories with `all_` prefix (only those needed)
- Moves files atomically to category/subcategory folders
- Moves non-managed subdirectories to "all_Folders" directory
- Logs every operation for undo capability
- Reports progress in real-time

### 5. **Cleanup Phase**
- Removes empty directories **only within `all_*` managed directories**
- Generates summary reports

---

## 📁 Default Organization Structure

**All directories created by allsorted have the `all_` prefix**, making them easily identifiable and allowing the tool to manage them recursively on subsequent runs.

```
YourDirectory/
├── all_Docs/
│   ├── Word/          (.doc, .docx, .odt)
│   ├── PDFs/          (.pdf)
│   ├── Text/          (.txt, .md, .log)
│   ├── Sheets/        (.xls, .xlsx, .csv)
│   └── ...
├── all_Audio/
│   ├── Music/         (.mp3, .flac, .ogg)
│   └── VoiceMemos/    (.m4a, .aac)
├── all_Pics/
│   ├── Photos/        (.jpg, .png, .gif)
│   ├── Vector/        (.svg, .ai)
│   └── Raw/           (.cr2, .nef, .dng)
├── all_Vids/
│   ├── Movies/        (.mp4, .mkv, .avi)
│   └── Clips/         (.webm, .3gp)
├── all_Programs/
│   ├── Windows/       (.exe, .msi)
│   ├── Mac/           (.dmg, .pkg)
│   └── Linux/         (.deb, .rpm)
├── all_Code/
│   ├── Python/        (.py)
│   ├── Web/           (.html, .css, .js)
│   └── ...
├── all_Archives/      (.zip, .tar.gz, .7z)
├── all_System/        (.iso, .dll)
├── all_Apps/          (app-specific files)
├── all_Web/           (.webp, .url)
├── all_Misc/          (uncategorized)
├── all_Duplicates/    (duplicate files with preserved paths)
└── all_Folders/       (remaining non-managed directories)
```

---

## 🎮 Command Reference

### Organize Command
```bash
allsorted organize [DIRECTORY] [OPTIONS]

Options:
  -c, --config PATH       Use custom configuration file
  -n, --dry-run          Preview without making changes
  --no-duplicates        Disable duplicate detection
  --strategy STRATEGY    Organization strategy (by-extension, by-date, by-size, hybrid)
  --conflict RESOLUTION  Conflict resolution (rename, skip, overwrite)
  -r, --report PATH      Save detailed JSON report
  -v, --verbose          Enable verbose output
```

### Preview Command
```bash
allsorted preview [DIRECTORY] [OPTIONS]

# Shows what would be organized without making any changes
```

### Validate Command
```bash
allsorted validate [DIRECTORY] [OPTIONS]

# Checks if directory can be safely organized
# Validates disk space, permissions, and detects issues
```

### Undo Command
```bash
allsorted undo LOG_FILE [--dry-run]

# Reverses operations from a previous organization
```

### Config Commands
```bash
allsorted config show              # Display current configuration
allsorted config init [--path]     # Create new config file
```

---

## ⚙️ Configuration

Create a configuration file for custom behavior:

```bash
allsorted config init
```

Edit `~/.config/allsorted/config.yaml`:

```yaml
# Organization strategy
strategy: by-extension  # or: by-date, by-size, hybrid

# Duplicate handling
detect_duplicates: true
isolate_duplicates: true

# File handling
follow_symlinks: false
ignore_hidden: true
ignore_patterns:
  - .devAI
  - .git
  - node_modules
  - __pycache__

# Conflict resolution
conflict_resolution: rename  # or: skip, overwrite

# Custom classification rules (extends defaults)
classification_rules:
  Code:
    Rust:
      - .rs
      - .toml
  Docs:
    Markdown:
      - .md
      - .markdown
```

---

## 🛡️ Safety Features

### Dry-Run Mode
Always preview before executing:
```bash
allsorted organize --dry-run
```

### Pre-Flight Validation
Automatic checks for:
- Sufficient disk space
- Write permissions
- File conflicts
- Circular dependencies
- Symlink loops

### Undo Capability
Every operation is logged:
```bash
# Find operation logs
ls ~/.devAI/operations_*.json

# Undo an organization
allsorted undo ~/.devAI/operations_20250103_143022.json
```

### Non-Destructive
- Never modifies file content
- Preserves modification times
- Handles conflicts safely
- Logs all operations

---

## 💡 Examples

### Example 1: Basic Organization
```bash
cd ~/Downloads
allsorted organize --dry-run    # Preview
allsorted organize              # Execute
```

**Before:**
```
Downloads/
├── report.pdf
├── vacation.jpg
├── song.mp3
├── ProjectFiles/
│   └── code.js
└── OldDocuments/
    └── archive.zip
```

**After:**
```
Downloads/
├── all_Docs/
│   └── PDFs/
│       └── report.pdf
├── all_Pics/
│   └── Photos/
│       └── vacation.jpg
├── all_Audio/
│   └── Music/
│       └── song.mp3
└── all_Folders/
    ├── ProjectFiles/
    │   └── code.js
    └── OldDocuments/
        └── archive.zip
```

**On subsequent runs**, files within `all_*` directories are recursively reorganized:
```bash
# Add a misplaced file to all_Folders
echo "new image" > Downloads/all_Folders/ProjectFiles/photo.jpg

# Run allsorted again
allsorted organize ~/Downloads

# Result: photo.jpg is moved to all_Pics/Photos/
```

### Example 2: Organize by Date
```bash
allsorted organize ~/Photos --strategy by-date
# Creates: 2024/01-15/, 2024/01-16/, etc.
```

### Example 3: Handle Conflicts
```bash
allsorted organize ~/Documents --conflict skip
# Skips files that would conflict
```

### Example 4: Custom Configuration
```bash
allsorted organize --config ./my-rules.yaml ~/Projects
```

### Example 5: Generate Report
```bash
allsorted organize ~/Music --report ~/music-report.json
```

---

## 📊 Output Examples

### Success Summary
```
Organization Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status              COMPLETED ✓
Root Directory      /home/user/Downloads
Total Files         1,247
Operations Failed   0
Success Rate        100.0%
Duration            12.3s
Duplicate Sets      15
Duplicate Files     47
Space Recoverable   3.2 GB
```

### Statistics Table
```
Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Category     Files    Percentage
─────────────────────────────────────────
Docs         423      33.9%
Pics         312      25.0%
Audio        198      15.9%
Vids         145      11.6%
Code         89       7.1%
Archives     80       6.4%
```

---

## 🧪 Development

### Setup Development Environment
```bash
# Clone repository
git clone https://github.com/orpheus497/allsorted.git
cd allsorted

# Install dependencies
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .
```

### Run Tests
```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest --cov=allsorted         # With coverage
pytest tests/test_integration.py  # Specific file
```

### Code Quality
```bash
black src/ tests/              # Format code
mypy src/                      # Type checking
ruff check src/                # Linting
```

---

---

## 📦 Dependencies & Attribution

allsorted is built with FOSS (Free and Open Source Software) components:

### Runtime Dependencies
- **Python** (≥3.8) - [Python Software Foundation License](https://www.python.org/psf/license/)
- **rich** by Will McGugan - [MIT License](https://github.com/Textualize/rich)
- **click** by Pallets Team - [BSD-3-Clause License](https://github.com/pallets/click)
- **PyYAML** by Kirill Simonov - [MIT License](https://github.com/yaml/pyyaml)

### Development Dependencies
- **pytest** - MIT License
- **pytest-cov** - MIT License
- **black** - MIT License
- **mypy** - MIT License
- **ruff** - MIT License

All dependencies are FOSS with permissive licenses compatible with allsorted's MIT License.

---

## 🐛 Troubleshooting

### Issue: Permission Denied
```bash
# Ensure you have write permissions
ls -la /path/to/directory

# Try with proper permissions or choose a different directory
```

### Issue: Disk Space Error
```bash
# Check available space
df -h

# Free up space or use --no-duplicates to reduce operations
```

### Issue: Files Not Organizing
```bash
# Check if files are being ignored
allsorted organize --verbose

# Verify your ignore patterns in config
allsorted config show
```

### Issue: Undo Not Working
```bash
# Ensure log file exists
ls .devAI/operations_*.json

# Specify correct log file path
allsorted undo /full/path/to/operations_20250103_143022.json
```

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

```
Copyright (c) 2025 The Orpheus497 Project Contributors
```

---

## 👤 Creator

**allsorted** is designed and created by **orpheus497**.

---

## 🔗 Links

- [GitHub Repository](https://github.com/orpheus497/allsorted)
- [Changelog](CHANGELOG.md)
- [Issues](https://github.com/orpheus497/allsorted/issues)

---

**Made with ❤️ by orpheus497**

This project is hosted on [GitHub](https://github.com/orpheus497/allsorted).
