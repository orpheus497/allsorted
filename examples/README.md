# allsorted Examples

This directory contains example scripts demonstrating various ways to use allsorted.

**Created by orpheus497**

## Available Examples

### 1. Basic Organization (`basic_organize.py`)

The simplest way to use allsorted programmatically.

**Usage:**
```bash
python basic_organize.py <directory> [--dry-run]
```

**Features:**
- Default configuration
- Pre-flight validation
- Progress reporting
- Error handling

**Example:**
```bash
# Preview what would be organized
python basic_organize.py ~/Downloads --dry-run

# Actually organize the directory
python basic_organize.py ~/Downloads
```

---

### 2. Custom Classification Rules (`custom_rules.py`)

Demonstrates how to add custom file type classifications.

**Usage:**
```bash
python custom_rules.py <directory>
```

**Custom Rules Included:**
- **DataScience**: `.ipynb`, `.rmd`, `.qmd`, `.r`
- **CAD**: `.dwg`, `.dxf`, `.stl`, `.obj`, `.fbx`
- **GameDev**: `.unity`, `.unitypackage`, `.prefab`, `.mat`
- **Blockchain**: `.sol`, `.vy`
- **MLModels**: `.h5`, `.keras`, `.pkl`, `.joblib`, `.model`

**Example:**
```bash
python custom_rules.py ~/Projects
```

---

### 3. Metadata-Based Organization (`metadata_organization.py`)

Shows how to organize files using metadata (EXIF, ID3 tags).

**Usage:**
```bash
python metadata_organization.py <mode> <directory> [--live]
```

**Modes:**
- `photos` - Organize photos by EXIF date (when taken)
- `music` - Organize music by ID3 artist tag

**Options:**
- `--live` - Actually move files (default is dry-run)

**Examples:**
```bash
# Preview photo organization by date
python metadata_organization.py photos ~/Pictures

# Organize music by artist (live mode)
python metadata_organization.py music ~/Music --live
```

---

## Requirements

All examples require allsorted to be installed:

```bash
pip install -e .
```

Some examples require optional dependencies:

- **Metadata organization**: Requires `Pillow` (EXIF) and `mutagen` (ID3)
  ```bash
  pip install Pillow mutagen
  ```

---

## Creating Your Own Examples

When creating custom scripts using allsorted:

1. **Import the necessary modules:**
   ```python
   from allsorted.config import Config
   from allsorted.planner import OrganizationPlanner
   from allsorted.executor import OrganizationExecutor
   from allsorted.validator import OperationValidator
   ```

2. **Create a configuration:**
   ```python
   config = Config()  # Use defaults
   # or
   config = load_config(Path("my-config.yaml"))  # Load from file
   ```

3. **Create and validate a plan:**
   ```python
   planner = OrganizationPlanner(config)
   plan = planner.create_plan(root_dir)

   validator = OperationValidator(plan)
   is_valid, errors, warnings = validator.validate_all()
   ```

4. **Execute the plan:**
   ```python
   executor = OrganizationExecutor(dry_run=False, log_operations=True)
   result = executor.execute_plan(plan)
   ```

5. **Handle results:**
   ```python
   print(f"Files moved: {result.files_moved}")
   print(f"Success rate: {result.success_rate:.1f}%")
   ```

---

## Tips

- **Always test with dry-run first** to see what would happen
- **Use validation** to catch issues before execution
- **Enable logging** for production use
- **Save operation logs** for undo capability
- **Handle exceptions** gracefully in production code

---

## More Examples

For more examples and use cases, see:
- [allsorted documentation](https://github.com/orpheus497/allsorted#readme)
- [API reference](../docs/)
- [Tests](../tests/) - Unit tests show many usage patterns

---

**Made with ❤️ by orpheus497**
