"""
Organization plan generation for allsorted.
"""

import logging
from pathlib import Path
from typing import Callable, List, Optional

from allsorted.analyzer import FileAnalyzer
from allsorted.classifier import FileClassifier
from allsorted.config import Config
from allsorted.models import (
    ConflictResolution,
    DirectoryMoveOperation,
    DuplicateSet,
    FileInfo,
    MoveOperation,
    OrganizationPlan,
)
from allsorted.utils import get_unique_path

logger = logging.getLogger(__name__)


class OrganizationPlanner:
    """Generates organization plans for directories."""

    def __init__(self, config: Config):
        """
        Initialize organization planner.

        Args:
            config: Configuration instance
        """
        self.config = config
        self.analyzer = FileAnalyzer(config)
        self.classifier = FileClassifier(config)

    def create_plan(
        self,
        root_dir: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> OrganizationPlan:
        """
        Create a complete organization plan for a directory.

        Args:
            root_dir: Root directory to organize
            progress_callback: Optional callback for progress updates

        Returns:
            OrganizationPlan instance

        Raises:
            ValueError: If root_dir is invalid
        """
        logger.info(f"Creating organization plan for: {root_dir}")

        # Initialize plan
        plan = OrganizationPlan(root_dir=root_dir.resolve())

        try:
            # Step 1: Analyze directory
            self.analyzer.analyze_directory(root_dir, progress_callback)

            # Step 2: Get duplicate sets
            duplicate_sets = self.analyzer.get_duplicate_sets()
            plan.duplicate_sets = duplicate_sets

            # Step 3: Create operations for duplicates
            if self.config.detect_duplicates:
                self._add_duplicate_operations(plan, duplicate_sets)

            # Step 4: Create operations for unique files
            unique_files = self.analyzer.get_unique_files()
            self._add_classification_operations(plan, unique_files)

            # Step 5: Create operations for primary files from duplicate sets
            if duplicate_sets:
                primary_files = [ds.primary for ds in duplicate_sets if ds.primary]
                self._add_classification_operations(plan, primary_files)

            # Step 6: Create operations for directories
            self._add_directory_operations(plan, self.analyzer.directories)

            logger.info(
                f"Plan created with {len(plan.operations)} file operations, "
                f"{len(plan.directory_operations)} directory operations, "
                f"{plan.total_duplicates} duplicates found"
            )

        except Exception as e:
            error_msg = f"Error creating plan: {e}"
            logger.error(error_msg)
            plan.add_error(error_msg)

        return plan

    def _add_duplicate_operations(
        self, plan: OrganizationPlan, duplicate_sets: List[DuplicateSet]
    ) -> None:
        """
        Add operations for duplicate files to the plan.

        Args:
            plan: Organization plan
            duplicate_sets: List of duplicate sets
        """
        if not self.config.isolate_duplicates:
            return

        for dup_set in duplicate_sets:
            # Add operations for extra duplicates (not the primary)
            for file_info in dup_set.extras:
                destination = self.classifier.get_destination_path(
                    file_info, plan.root_dir, reason="duplicate"
                )

                # Check if source and destination are the same
                if file_info.path.resolve() == destination.resolve():
                    logger.debug(
                        f"Skipping duplicate already in correct location: {file_info.path}"
                    )
                    continue

                operation = MoveOperation(
                    source=file_info.path,
                    destination=destination,
                    file_info=file_info,
                    reason="duplicate",
                    conflict_resolution=self.config.conflict_resolution,
                )

                plan.add_operation(operation)

    def _add_classification_operations(self, plan: OrganizationPlan, files: List[FileInfo]) -> None:
        """
        Add classification operations for files to the plan.

        Args:
            plan: Organization plan
            files: List of files to classify
        """
        for file_info in files:
            destination = self.classifier.get_destination_path(
                file_info, plan.root_dir, reason="classify"
            )

            # Check if source and destination are the same
            if file_info.path.resolve() == destination.resolve():
                logger.debug(f"Skipping file already in correct location: {file_info.path}")
                continue

            operation = MoveOperation(
                source=file_info.path,
                destination=destination,
                file_info=file_info,
                reason="classify",
                conflict_resolution=self.config.conflict_resolution,
            )

            plan.add_operation(operation)

    def _add_directory_operations(self, plan: OrganizationPlan, directories: List[Path]) -> None:
        """
        Add operations to move directories to the all_Folders directory.

        Args:
            plan: Organization plan
            directories: List of directories to organize
        """
        if not directories:
            return

        folders_dir_name = self.config.get_managed_name(self.config.folders_folder)
        folders_dir = plan.root_dir / folders_dir_name

        for directory in directories:
            # Skip if it's a managed directory (created by allsorted)
            if self.config.is_managed_directory(directory):
                logger.debug(f"Skipping managed directory: {directory}")
                continue

            # Skip if it's already in the Folders directory
            if directory.parent == folders_dir:
                logger.debug(f"Skipping directory already in Folders: {directory}")
                continue

            # Skip special directories
            if directory.name in [self.config.log_directory]:
                logger.debug(f"Skipping special directory: {directory}")
                continue

            destination = folders_dir / directory.name

            operation = DirectoryMoveOperation(
                source=directory,
                destination=destination,
                reason="organize_folder",
                conflict_resolution=self.config.conflict_resolution,
            )

            plan.add_directory_operation(operation)
            logger.debug(f"Added directory operation: {directory} -> {destination}")

    def optimize_plan(self, plan: OrganizationPlan) -> OrganizationPlan:
        """
        Optimize a plan by removing redundant operations and detecting conflicts.

        Args:
            plan: Organization plan to optimize

        Returns:
            Optimized plan
        """
        logger.info("Optimizing organization plan...")

        # Track destination paths to detect conflicts
        destination_map: dict[Path, List[MoveOperation]] = {}

        optimized_operations = []

        for op in plan.operations:
            dest = op.destination.resolve()

            # Skip operations where source == destination
            if op.source.resolve() == dest:
                logger.debug(f"Removing no-op operation: {op.source}")
                continue

            # Track destinations
            if dest not in destination_map:
                destination_map[dest] = []
            destination_map[dest].append(op)

            optimized_operations.append(op)

        # Resolve conflicts
        for dest_path, operations in destination_map.items():
            if len(operations) > 1:
                logger.warning(
                    f"Conflict detected: {len(operations)} files want to move to {dest_path}"
                )

                # Resolve based on conflict resolution strategy
                for idx, op in enumerate(operations):
                    if idx > 0:  # Keep first, resolve others
                        if op.conflict_resolution == ConflictResolution.RENAME:
                            new_dest = get_unique_path(op.destination)
                            op.destination = new_dest
                            logger.info(f"Renamed conflicting file: {op.source} -> {new_dest}")
                        elif op.conflict_resolution == ConflictResolution.SKIP:
                            optimized_operations.remove(op)
                            plan.skipped_files.append(op.source)
                            logger.info(f"Skipped conflicting file: {op.source}")

        plan.operations = optimized_operations

        logger.info(f"Plan optimized to {len(plan.operations)} operations")
        return plan

    def generate_preview(self, plan: OrganizationPlan, max_items: int = 50) -> str:
        """
        Generate a human-readable preview of the plan.

        Args:
            plan: Organization plan
            max_items: Maximum number of operations to show

        Returns:
            Preview string
        """
        lines = [
            "=" * 80,
            "ORGANIZATION PLAN PREVIEW",
            "=" * 80,
            f"Root Directory: {plan.root_dir}",
            f"Total Files: {plan.total_files}",
            f"Duplicate Files: {plan.total_duplicates}",
            f"Space Recoverable: {plan.space_recoverable / (1024**3):.2f} GB",
            f"Categories: {', '.join(sorted(plan.categories_used))}",
            "",
        ]

        if plan.errors:
            lines.append("ERRORS:")
            for error in plan.errors:
                lines.append(f"  ❌ {error}")
            lines.append("")

        if plan.operations:
            lines.append(f"FILE OPERATIONS (showing first {max_items}):")
            for idx, op in enumerate(plan.operations[:max_items], 1):
                icon = "📋" if op.is_classification else "🔁"
                lines.append(f"{idx:3d}. {icon} {op.source.name}")
                lines.append(f"      -> {op.destination.relative_to(plan.root_dir)}")

            if len(plan.operations) > max_items:
                lines.append(f"      ... and {len(plan.operations) - max_items} more")

        if plan.directory_operations:
            lines.append("")
            lines.append(f"DIRECTORY OPERATIONS (showing first {max_items}):")
            for idx, op in enumerate(plan.directory_operations[:max_items], 1):
                lines.append(f"{idx:3d}. 📁 {op.source.name}")
                lines.append(f"      -> {op.destination.relative_to(plan.root_dir)}")

            if len(plan.directory_operations) > max_items:
                lines.append(f"      ... and {len(plan.directory_operations) - max_items} more")

        if plan.skipped_files:
            lines.append("")
            lines.append("SKIPPED FILES:")
            for skipped in plan.skipped_files[:max_items]:
                lines.append(f"  ⊘ {skipped}")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)
