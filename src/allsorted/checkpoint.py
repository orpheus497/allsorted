"""
Checkpoint and resume functionality for long-running operations.

Allows interrupting and resuming file organization operations without starting over.

Created by orpheus497
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from allsorted.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Checkpoint:
    """Represents a saved checkpoint of an operation."""

    version: str = "1.0"
    timestamp: str = ""
    root_dir: str = ""
    total_operations: int = 0
    completed_operations: int = 0
    failed_operations: int = 0
    completed_hashes: List[str] = None  # type: ignore[assignment]
    current_phase: str = "analysis"  # analysis, planning, execution, cleanup

    def __post_init__(self) -> None:
        """Initialize lists if None."""
        if self.completed_hashes is None:
            self.completed_hashes = []


class CheckpointManager:
    """Manages checkpoint creation and recovery."""

    def __init__(self, root_dir: Path, checkpoint_dir: Optional[Path] = None):
        """
        Initialize checkpoint manager.

        Args:
            root_dir: Root directory being organized
            checkpoint_dir: Directory to store checkpoints (default: root_dir/.devAI)
        """
        self.root_dir = root_dir
        self.checkpoint_dir = checkpoint_dir or (root_dir / ".devAI")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoint_file = self.checkpoint_dir / "checkpoint.json"
        self.checkpoint: Optional[Checkpoint] = None

    def save(
        self,
        phase: str,
        total_ops: int,
        completed_ops: int,
        failed_ops: int = 0,
        completed_hashes: Optional[List[str]] = None,
    ) -> None:
        """
        Save a checkpoint.

        Args:
            phase: Current phase of operation
            total_ops: Total number of operations
            completed_ops: Number of completed operations
            failed_ops: Number of failed operations
            completed_hashes: List of file hashes already processed
        """
        checkpoint = Checkpoint(
            timestamp=datetime.now().isoformat(),
            root_dir=str(self.root_dir),
            total_operations=total_ops,
            completed_operations=completed_ops,
            failed_operations=failed_ops,
            completed_hashes=completed_hashes or [],
            current_phase=phase,
        )

        try:
            with open(self.checkpoint_file, "w") as f:
                json.dump(asdict(checkpoint), f, indent=2)

            logger.info(f"Checkpoint saved: {phase} - {completed_ops}/{total_ops} operations")
            self.checkpoint = checkpoint

        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to save checkpoint: {e}")

    def load(self) -> Optional[Checkpoint]:
        """
        Load the most recent checkpoint.

        Returns:
            Checkpoint object or None if no checkpoint exists
        """
        if not self.checkpoint_file.exists():
            logger.debug("No checkpoint file found")
            return None

        try:
            with open(self.checkpoint_file) as f:
                data = json.load(f)

            checkpoint = Checkpoint(**data)

            logger.info(
                f"Checkpoint loaded: {checkpoint.current_phase} - "
                f"{checkpoint.completed_operations}/{checkpoint.total_operations} operations"
            )

            self.checkpoint = checkpoint
            return checkpoint

        except (OSError, json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None

    def clear(self) -> None:
        """Clear the current checkpoint."""
        if self.checkpoint_file.exists():
            try:
                self.checkpoint_file.unlink()
                logger.info("Checkpoint cleared")
            except OSError as e:
                logger.warning(f"Failed to clear checkpoint: {e}")

        self.checkpoint = None

    def should_skip_file(self, file_hash: str) -> bool:
        """
        Check if a file should be skipped based on checkpoint.

        Args:
            file_hash: Hash of the file

        Returns:
            True if file was already processed
        """
        if not self.checkpoint:
            return False

        return file_hash in self.checkpoint.completed_hashes

    def get_progress(self) -> Dict[str, Any]:
        """
        Get current progress information.

        Returns:
            Dictionary with progress details
        """
        if not self.checkpoint:
            return {
                "exists": False,
                "progress": 0.0,
            }

        total = self.checkpoint.total_operations
        completed = self.checkpoint.completed_operations
        progress = (completed / total * 100) if total > 0 else 0.0

        return {
            "exists": True,
            "phase": self.checkpoint.current_phase,
            "total": total,
            "completed": completed,
            "failed": self.checkpoint.failed_operations,
            "progress": progress,
            "timestamp": self.checkpoint.timestamp,
        }
