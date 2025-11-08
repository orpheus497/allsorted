#!/usr/bin/env python3
"""
Basic organization example for allsorted.

This script demonstrates the simplest way to use allsorted programmatically
to organize a directory.

Created by orpheus497
"""

from pathlib import Path

from allsorted.config import Config
from allsorted.executor import OrganizationExecutor
from allsorted.planner import OrganizationPlanner
from allsorted.validator import OperationValidator


def organize_directory(directory_path: str, dry_run: bool = False) -> None:
    """
    Organize a directory using default settings.

    Args:
        directory_path: Path to directory to organize
        dry_run: If True, only show what would be done without making changes
    """
    # Create configuration with defaults
    config = Config()

    # Create planner
    planner = OrganizationPlanner(config)
    root_dir = Path(directory_path).resolve()

    print(f"Analyzing directory: {root_dir}")

    # Create organization plan
    plan = planner.create_plan(root_dir)

    print(f"Found {len(plan.operations)} file operations")
    print(f"Found {len(plan.duplicate_sets)} duplicate sets")

    # Validate plan
    validator = OperationValidator(plan)
    is_valid, errors, warnings = validator.validate_all()

    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
        return

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    # Execute plan
    executor = OrganizationExecutor(dry_run=dry_run, log_operations=not dry_run)
    result = executor.execute_plan(plan)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Organization complete!")
    print(f"Files moved: {result.files_moved}")
    print(f"Files failed: {result.files_failed}")
    print(f"Success rate: {result.success_rate:.1f}%")
    print(f"Duration: {result.duration_seconds:.2f}s")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python basic_organize.py <directory> [--dry-run]")
        sys.exit(1)

    directory = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    try:
        organize_directory(directory, dry_run=dry_run)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
