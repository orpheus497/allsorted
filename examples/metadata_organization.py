#!/usr/bin/env python3
"""
Metadata-based organization example for allsorted.

This script demonstrates how to organize photos by EXIF date
and music by ID3 tags.

Created by orpheus497
"""

from pathlib import Path
from allsorted.config import Config
from allsorted.models import OrganizationStrategy
from allsorted.planner import OrganizationPlanner
from allsorted.executor import OrganizationExecutor


def organize_photos_by_date(directory_path: str, dry_run: bool = True) -> None:
    """
    Organize photos by EXIF date (when photo was taken).

    Args:
        directory_path: Path to photo directory
        dry_run: If True, show what would be done without making changes
    """
    config = Config()

    # Enable metadata extraction
    config.use_metadata = True
    config.metadata_strategy = "exif-date"

    # Use date-based organization
    config.strategy = OrganizationStrategy.BY_DATE

    print(f"Organizing photos by EXIF date")
    print(f"Directory: {directory_path}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    # Create planner
    planner = OrganizationPlanner(config)
    root_dir = Path(directory_path).resolve()

    # Create plan
    plan = planner.create_plan(root_dir)

    print(f"Found {len(plan.operations)} photo files")
    print(f"Found {len(plan.duplicate_sets)} duplicate photos")
    print()

    # Show sample of operations
    print("Sample operations:")
    for i, operation in enumerate(plan.operations[:5]):
        print(f"  {operation.source.name} -> {operation.destination}")

    if len(plan.operations) > 5:
        print(f"  ... and {len(plan.operations) - 5} more")
    print()

    if not dry_run:
        response = input("Proceed with organization? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return

    # Execute
    executor = OrganizationExecutor(dry_run=dry_run, log_operations=not dry_run)
    result = executor.execute_plan(plan)

    print(f"\nOrganization {'simulation' if dry_run else 'execution'} complete!")
    print(f"Files moved: {result.files_moved}")
    print(f"Duration: {result.duration_seconds:.2f}s")


def organize_music_by_artist(directory_path: str, dry_run: bool = True) -> None:
    """
    Organize music by ID3 artist tag.

    Args:
        directory_path: Path to music directory
        dry_run: If True, show what would be done without making changes
    """
    config = Config()

    # Enable metadata extraction
    config.use_metadata = True
    config.metadata_strategy = "id3-artist"

    print(f"Organizing music by ID3 artist tag")
    print(f"Directory: {directory_path}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    # Create planner
    planner = OrganizationPlanner(config)
    root_dir = Path(directory_path).resolve()

    # Create plan
    plan = planner.create_plan(root_dir)

    print(f"Found {len(plan.operations)} music files")
    print()

    # Show sample of operations
    print("Sample operations:")
    for i, operation in enumerate(plan.operations[:5]):
        print(f"  {operation.source.name} -> {operation.destination}")

    if len(plan.operations) > 5:
        print(f"  ... and {len(plan.operations) - 5} more")
    print()

    if not dry_run:
        response = input("Proceed with organization? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return

    # Execute
    executor = OrganizationExecutor(dry_run=dry_run, log_operations=not dry_run)
    result = executor.execute_plan(plan)

    print(f"\nOrganization {'simulation' if dry_run else 'execution'} complete!")
    print(f"Files moved: {result.files_moved}")
    print(f"Duration: {result.duration_seconds:.2f}s")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python metadata_organization.py <mode> <directory> [--live]")
        print("\nModes:")
        print("  photos  - Organize photos by EXIF date")
        print("  music   - Organize music by ID3 artist")
        print("\nOptions:")
        print("  --live  - Actually move files (default is dry-run)")
        print("\nExamples:")
        print("  python metadata_organization.py photos ~/Pictures")
        print("  python metadata_organization.py music ~/Music --live")
        sys.exit(1)

    mode = sys.argv[1]
    directory = sys.argv[2]
    dry_run = "--live" not in sys.argv

    try:
        if mode == "photos":
            organize_photos_by_date(directory, dry_run=dry_run)
        elif mode == "music":
            organize_music_by_artist(directory, dry_run=dry_run)
        else:
            print(f"Unknown mode: {mode}")
            print("Available modes: photos, music")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
