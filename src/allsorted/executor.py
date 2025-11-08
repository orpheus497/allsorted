"""
Execution engine for allsorted organization plans.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from allsorted.models import (
    ConflictResolution,
    MoveOperation,
    OrganizationPlan,
    OrganizationResult,
)
from allsorted.utils import ensure_dir, get_unique_path

logger = logging.getLogger(__name__)


class ExecutionError(Exception):
    """Raised when execution fails."""

    pass


class OrganizationExecutor:
    """Executes organization plans with safety and logging."""

    def __init__(self, dry_run: bool = False, log_operations: bool = True, config: Optional["Config"] = None):  # type: ignore[name-defined]
        """
        Initialize executor.

        Args:
            dry_run: If True, simulate operations without moving files
            log_operations: If True, log all operations to a file for undo capability
            config: Optional config instance (will be extracted from plan if not provided)
        """
        self.dry_run = dry_run
        self.log_operations = log_operations
        self.config = config
        self.operation_log_path: Optional[Path] = None

    def execute_plan(
        self,
        plan: OrganizationPlan,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> OrganizationResult:
        """
        Execute an organization plan.

        Args:
            plan: Plan to execute
            progress_callback: Optional callback(current, total) for progress

        Returns:
            OrganizationResult with execution details
        """
        logger.info(
            f"{'[DRY RUN] ' if self.dry_run else ''}Executing plan with "
            f"{len(plan.operations)} file operations and "
            f"{len(plan.directory_operations)} directory operations"
        )

        result = OrganizationResult(
            plan=plan,
            started=datetime.now(),
            dry_run=self.dry_run,
        )

        # Setup operation log
        if self.log_operations and not self.dry_run:
            self._setup_operation_log(plan.root_dir)

        try:
            total_ops = len(plan.operations) + len(plan.directory_operations)
            current_idx = 0

            # Execute file operations first
            for operation in plan.operations:
                current_idx += 1
                if progress_callback:
                    progress_callback(current_idx, total_ops)

                try:
                    self._execute_operation(operation, result)
                except Exception as e:
                    error_msg = f"Failed to execute {operation.source}: {e}"
                    logger.error(error_msg)
                    result.failed_operations.append((operation, str(e)))

            # Execute directory operations after files are moved
            for dir_operation in plan.directory_operations:
                current_idx += 1
                if progress_callback:
                    progress_callback(current_idx, total_ops)

                try:
                    self._execute_directory_operation(dir_operation, result)
                except Exception as e:
                    error_msg = f"Failed to execute {dir_operation.source}: {e}"
                    logger.error(error_msg)

            # Cleanup empty directories
            if not self.dry_run:
                self._cleanup_empty_directories(plan.root_dir, result)

        finally:
            result.completed = datetime.now()

        logger.info(
            f"{'[DRY RUN] ' if self.dry_run else ''}Execution complete. "
            f"Success: {result.files_moved}, Failed: {result.files_failed}, "
            f"Duration: {result.duration_seconds:.2f}s"
        )

        return result

    def _execute_operation(self, operation: MoveOperation, result: OrganizationResult) -> None:
        """
        Execute a single move operation.

        Args:
            operation: Move operation to execute
            result: Result object to update

        Raises:
            ExecutionError: If operation fails
        """
        source = operation.source
        destination = operation.destination

        # Validate source exists
        if not source.exists():
            raise ExecutionError(f"Source file does not exist: {source}")

        # Handle destination directory
        dest_dir = destination.parent
        if not self.dry_run:
            try:
                ensure_dir(dest_dir)
                if dest_dir not in result.directories_created:
                    result.directories_created.append(dest_dir)
            except OSError as e:
                raise ExecutionError(f"Cannot create directory {dest_dir}: {e}") from e

        # Handle file conflicts
        final_destination = self._resolve_conflict(destination, operation.conflict_resolution)

        # Execute the move
        if self.dry_run:
            logger.info(f"[DRY RUN] Would move: {source} -> {final_destination}")
        else:
            # Store source hash for integrity verification if enabled
            source_hash = operation.file_info.hash if operation.file_info else None

            try:
                shutil.move(str(source), str(final_destination))
                logger.info(f"Moved: {source} -> {final_destination}")

                # Verify integrity if enabled
                if source_hash and self._should_verify_integrity():
                    if not self._verify_file_integrity(source_hash, final_destination):
                        # Integrity check failed - this is serious
                        logger.error(f"Integrity verification failed for {final_destination}")
                        raise ExecutionError(f"Integrity verification failed after move: {final_destination}")

                # Log operation for undo capability
                if self.log_operations:
                    self._log_operation(source, final_destination)

            except (OSError, shutil.Error) as e:
                raise ExecutionError(f"Move failed: {e}") from e

        # Update operation with final destination
        operation.destination = final_destination
        result.successful_operations.append(operation)

    def _execute_directory_operation(
        self, operation, result: OrganizationResult
    ) -> None:
        """
        Execute a single directory move operation.

        Args:
            operation: DirectoryMoveOperation to execute
            result: Result object to update

        Raises:
            ExecutionError: If operation fails
        """
        source = operation.source
        destination = operation.destination

        # Validate source exists
        if not source.exists():
            raise ExecutionError(f"Source directory does not exist: {source}")

        # Handle destination directory
        dest_parent = destination.parent
        if not self.dry_run:
            try:
                ensure_dir(dest_parent)
            except OSError as e:
                raise ExecutionError(f"Cannot create parent directory {dest_parent}: {e}") from e

        # Handle conflicts
        final_destination = self._resolve_conflict(destination, operation.conflict_resolution)

        # Execute the move
        if self.dry_run:
            logger.info(f"[DRY RUN] Would move directory: {source} -> {final_destination}")
        else:
            try:
                shutil.move(str(source), str(final_destination))
                logger.info(f"Moved directory: {source} -> {final_destination}")

                # Log operation for undo capability
                if self.log_operations:
                    self._log_operation(source, final_destination)

            except (OSError, shutil.Error) as e:
                raise ExecutionError(f"Directory move failed: {e}") from e

    def _resolve_conflict(self, destination: Path, resolution: ConflictResolution) -> Path:
        """
        Resolve file name conflict at destination.

        Args:
            destination: Desired destination path
            resolution: Conflict resolution strategy

        Returns:
            Final destination path (may be modified)

        Raises:
            ExecutionError: If conflict cannot be resolved
        """
        if not destination.exists():
            return destination

        if resolution == ConflictResolution.RENAME:
            new_dest = get_unique_path(destination)
            logger.info(f"Conflict resolved by renaming: {destination} -> {new_dest}")
            return new_dest

        elif resolution == ConflictResolution.SKIP:
            raise ExecutionError(f"Destination exists and strategy is SKIP: {destination}")

        elif resolution == ConflictResolution.OVERWRITE:
            if not self.dry_run:
                try:
                    destination.unlink()
                    logger.warning(f"Overwriting existing file: {destination}")
                except OSError as e:
                    raise ExecutionError(f"Cannot overwrite {destination}: {e}") from e
            return destination

        elif resolution == ConflictResolution.ASK:
            # In non-interactive context, default to rename
            logger.warning("ASK strategy in non-interactive mode, defaulting to RENAME")
            return self._resolve_conflict(destination, ConflictResolution.RENAME)

        else:
            raise ExecutionError(f"Unknown conflict resolution strategy: {resolution}")

    def _cleanup_empty_directories(self, root_dir: Path, result: OrganizationResult) -> None:
        """
        Remove empty directories after organization.
        Only removes empty directories within managed (all_*) directories.

        Args:
            root_dir: Root directory
            result: Result object to update
        """
        logger.info("Cleaning up empty directories in managed folders...")

        # Use stored config, or get from plan, or fall back to default
        config = self.config
        if config is None:
            # Try to get from plan
            if hasattr(result.plan, 'config'):
                config = result.plan.config
            else:
                # Fall back to default config
                from allsorted.config import Config
                config = Config()

        # Walk from bottom up to delete nested empty dirs first
        for dirpath in sorted(root_dir.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if not dirpath.is_dir():
                continue

            # Don't delete the root
            if dirpath == root_dir:
                continue

            # Skip special directories
            if dirpath.name.startswith("."):
                continue

            # Only clean up directories inside managed directories
            # Check if any parent is a managed directory
            is_in_managed = False
            for parent in dirpath.parents:
                if parent == root_dir:
                    break
                if config.is_managed_directory(parent):
                    is_in_managed = True
                    break
            
            # Also check if the directory itself is a top-level managed directory
            if dirpath.parent == root_dir and config.is_managed_directory(dirpath):
                is_in_managed = True

            if not is_in_managed:
                continue

            try:
                # Check if directory is empty
                if not any(dirpath.iterdir()):
                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would remove empty directory: {dirpath}")
                    else:
                        dirpath.rmdir()
                        logger.info(f"Removed empty directory: {dirpath}")
                        result.directories_removed.append(dirpath)
            except OSError as e:
                logger.debug(f"Could not remove directory {dirpath}: {e}")

    def _setup_operation_log(self, root_dir: Path) -> None:
        """
        Setup operation log file for undo capability.

        Args:
            root_dir: Root directory
        """
        log_dir = root_dir / ".devAI"
        ensure_dir(log_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.operation_log_path = log_dir / f"operations_{timestamp}.json"

        # Initialize log file
        log_data = {
            "version": "1.0",
            "timestamp": timestamp,
            "root_dir": str(root_dir),
            "operations": [],
        }

        with open(self.operation_log_path, "w") as f:
            json.dump(log_data, f, indent=2)

        logger.info(f"Operation log initialized: {self.operation_log_path}")

    def _log_operation(self, source: Path, destination: Path) -> None:
        """
        Log a single operation for undo capability.

        Args:
            source: Source path
            destination: Destination path
        """
        if not self.operation_log_path:
            return

        try:
            # Read existing log
            with open(self.operation_log_path, "r") as f:
                log_data = json.load(f)

            # Add new operation
            log_data["operations"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "source": str(source),
                    "destination": str(destination),
                }
            )

            # Write back
            with open(self.operation_log_path, "w") as f:
                json.dump(log_data, f, indent=2)

        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Could not log operation: {e}")

    def _should_verify_integrity(self) -> bool:
        """
        Check if integrity verification is enabled.

        Returns:
            True if integrity verification should be performed
        """
        config = self.config
        if config is None:
            return False
        return getattr(config, 'verify_integrity', False)

    def _verify_file_integrity(self, expected_hash: str, file_path: Path) -> bool:
        """
        Verify file integrity by recalculating hash.

        Args:
            expected_hash: Expected hash value from source file
            file_path: Path to file to verify

        Returns:
            True if hash matches, False otherwise
        """
        if not file_path.exists():
            logger.error(f"Cannot verify integrity - file does not exist: {file_path}")
            return False

        try:
            # Recalculate hash using same algorithm
            import hashlib
            config = self.config
            algorithm = getattr(config, 'hash_algorithm', 'sha256') if config else 'sha256'

            if algorithm == "xxhash":
                try:
                    import xxhash
                    hasher = xxhash.xxh64()
                except ImportError:
                    hasher = hashlib.sha256()
            else:
                hasher = hashlib.sha256()

            block_size = getattr(config, 'hash_block_size', 65536) if config else 65536

            with open(file_path, "rb") as f:
                while True:
                    block = f.read(block_size)
                    if not block:
                        break
                    hasher.update(block)

            actual_hash = hasher.hexdigest()

            if actual_hash == expected_hash:
                logger.debug(f"Integrity verified for {file_path}")
                return True
            else:
                logger.error(
                    f"Integrity check failed for {file_path}\n"
                    f"Expected: {expected_hash}\n"
                    f"Actual: {actual_hash}"
                )
                return False

        except (OSError, IOError) as e:
            logger.error(f"Error verifying integrity for {file_path}: {e}")
            return False

    def undo_operations(self, log_file: Path) -> tuple[int, int]:
        """
        Undo operations from a log file.

        Args:
            log_file: Path to operations log file

        Returns:
            Tuple of (successful_undos, failed_undos)

        Raises:
            ExecutionError: If log file is invalid
        """
        if self.dry_run:
            logger.warning("Cannot undo operations in dry-run mode")
            return (0, 0)

        logger.info(f"Undoing operations from: {log_file}")

        try:
            with open(log_file, "r") as f:
                log_data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise ExecutionError(f"Cannot read operation log: {e}") from e

        operations = log_data.get("operations", [])
        successful = 0
        failed = 0

        # Undo in reverse order
        for op in reversed(operations):
            source = Path(op["source"])
            destination = Path(op["destination"])

            try:
                if destination.exists():
                    shutil.move(str(destination), str(source))
                    logger.info(f"Undid: {destination} -> {source}")
                    successful += 1
                else:
                    logger.warning(f"Cannot undo, file not found: {destination}")
                    failed += 1
            except (OSError, shutil.Error) as e:
                logger.error(f"Undo failed for {destination}: {e}")
                failed += 1

        logger.info(f"Undo complete. Success: {successful}, Failed: {failed}")
        return (successful, failed)
