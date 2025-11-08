"""
File system watching for automatic organization.

Monitors a directory for new files and automatically organizes them based on rules.

Created by orpheus497

Dependencies:
    - watchdog (Apache-2.0 License) by Yesudeep Mangalapilly
"""

import time
from pathlib import Path
from typing import Callable, Optional

try:
    from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

from allsorted.config import Config
from allsorted.executor import OrganizationExecutor
from allsorted.logging_config import get_logger
from allsorted.planner import OrganizationPlanner

logger = get_logger(__name__)


class FileOrganizeHandler(FileSystemEventHandler):  # type: ignore[misc]
    """Handles file system events and triggers organization."""

    def __init__(
        self,
        root_dir: Path,
        config: Config,
        organize_callback: Optional[Callable[[Path], None]] = None,
    ):
        """
        Initialize event handler.

        Args:
            root_dir: Root directory being watched
            config: Configuration instance
            organize_callback: Optional callback function(file_path) when file is organized
        """
        self.root_dir = root_dir
        self.config = config
        self.organize_callback = organize_callback
        self.planner = OrganizationPlanner(config)
        self.executor = OrganizationExecutor(dry_run=False, log_operations=True)

        # Track recently processed files to avoid duplicates
        self.recently_processed: set[str] = set()
        self.process_delay = 2.0  # Wait 2 seconds after file creation before processing

    def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        self._handle_file(file_path)

    def on_modified(self, event: FileModifiedEvent) -> None:  # type: ignore[override]
        """Handle file modification events."""
        if event.is_directory:
            return

        # Only process if file is newly modified and was stable
        file_path = Path(event.src_path)

        # Skip if recently processed
        if str(file_path) in self.recently_processed:
            return

        self._handle_file(file_path)

    def _handle_file(self, file_path: Path) -> None:
        """
        Handle a new or modified file.

        Args:
            file_path: Path to the file
        """
        # Skip if already in an organized directory
        if any(self.config.is_managed_directory(p) for p in file_path.parents):
            logger.debug(f"Skipping file in managed directory: {file_path}")
            return

        # Wait for file to be fully written
        time.sleep(self.process_delay)

        # Check if file still exists and is stable
        if not file_path.exists():
            logger.debug(f"File disappeared: {file_path}")
            return

        try:
            # Quick check if file size is stable
            initial_size = file_path.stat().st_size
            time.sleep(0.5)
            if not file_path.exists():
                return
            final_size = file_path.stat().st_size

            if initial_size != final_size:
                logger.debug(f"File still being written: {file_path}")
                return

            # Organize the file
            logger.info(f"New file detected: {file_path.name}")
            self._organize_file(file_path)

            # Mark as processed
            self.recently_processed.add(str(file_path))

            # Trigger callback
            if self.organize_callback:
                self.organize_callback(file_path)

        except Exception as e:
            logger.error(f"Error handling file {file_path}: {e}")

    def _organize_file(self, file_path: Path) -> None:
        """
        Organize a single file.

        Args:
            file_path: Path to file to organize
        """
        try:
            # Create a minimal plan for just this file
            from allsorted.analyzer import FileAnalyzer
            from allsorted.models import OrganizationPlan

            analyzer = FileAnalyzer(self.config)
            plan = OrganizationPlan(root_dir=self.root_dir)

            # Analyze just this file
            try:
                file_info = analyzer.analyze_single_file(file_path)
                if file_info:
                    # Create operation for this file
                    self.planner._add_classification_operations(plan, [file_info])

                    # Execute if there are operations
                    if plan.operations:
                        result = self.executor.execute_plan(plan)
                        if result.is_complete_success:
                            logger.info(f"Successfully organized: {file_path.name}")
                        else:
                            logger.warning(f"Failed to organize: {file_path.name}")

            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")

        except Exception as e:
            logger.error(f"Failed to organize {file_path}: {e}")


class DirectoryWatcher:
    """Watches a directory and automatically organizes new files."""

    def __init__(self, root_dir: Path, config: Config):
        """
        Initialize directory watcher.

        Args:
            root_dir: Directory to watch
            config: Configuration instance
        """
        if not WATCHDOG_AVAILABLE:
            raise RuntimeError("watchdog library not available. Install with: pip install watchdog")

        self.root_dir = root_dir
        self.config = config
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[FileOrganizeHandler] = None

    def start(self, organize_callback: Optional[Callable[[Path], None]] = None) -> None:
        """
        Start watching the directory.

        Args:
            organize_callback: Optional callback function(file_path) when file is organized
        """
        if self.observer and self.observer.is_alive():
            logger.warning("Watcher already running")
            return

        self.event_handler = FileOrganizeHandler(self.root_dir, self.config, organize_callback)
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.root_dir),
            recursive=(
                self.config.watch_recursive if hasattr(self.config, "watch_recursive") else True
            ),
        )

        self.observer.start()
        logger.info(f"Started watching directory: {self.root_dir}")

    def stop(self) -> None:
        """Stop watching the directory."""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=5.0)
            logger.info("Stopped watching directory")

        self.observer = None
        self.event_handler = None

    def is_running(self) -> bool:
        """Check if watcher is currently running."""
        return self.observer is not None and self.observer.is_alive()
