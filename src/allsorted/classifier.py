"""
File classification logic for allsorted.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple

from allsorted.config import Config
from allsorted.models import FileInfo, OrganizationStrategy

logger = logging.getLogger(__name__)


class FileClassifier:
    """Classifies files into categories based on rules and strategy."""

    def __init__(self, config: Config):
        """
        Initialize file classifier.

        Args:
            config: Configuration instance
        """
        self.config = config
        self._classification_cache: dict[str, Tuple[str, str]] = {}

    def classify_file(self, file_info: FileInfo) -> Tuple[str, str]:
        """
        Classify a file into category and subcategory.

        Args:
            file_info: File information

        Returns:
            Tuple of (category, subcategory)
        """
        strategy = self.config.strategy

        if strategy == OrganizationStrategy.BY_EXTENSION:
            return self._classify_by_extension(file_info)
        elif strategy == OrganizationStrategy.BY_DATE:
            return self._classify_by_date(file_info)
        elif strategy == OrganizationStrategy.BY_SIZE:
            return self._classify_by_size(file_info)
        elif strategy == OrganizationStrategy.HYBRID:
            return self._classify_hybrid(file_info)
        else:
            logger.warning(f"Unknown strategy {strategy}, falling back to BY_EXTENSION")
            return self._classify_by_extension(file_info)

    def _classify_by_extension(self, file_info: FileInfo) -> Tuple[str, str]:
        """
        Classify file by extension using classification rules.

        Args:
            file_info: File information

        Returns:
            Tuple of (category, subcategory)
        """
        extension = file_info.extension

        # Check cache first
        if extension in self._classification_cache:
            return self._classification_cache[extension]

        # Look up in classification rules
        category, subcategory = self.config.get_category_for_extension(extension)

        # Cache the result
        self._classification_cache[extension] = (category, subcategory)

        return (category, subcategory)

    def _classify_by_date(self, file_info: FileInfo) -> Tuple[str, str]:
        """
        Classify file by modification date (YYYY/MM/DD structure).

        Args:
            file_info: File information

        Returns:
            Tuple of (year, month-day) for directory structure
        """
        dt = datetime.fromtimestamp(file_info.modified_time)
        year = str(dt.year)
        month_day = f"{dt.month:02d}-{dt.day:02d}"
        return (year, month_day)

    def _classify_by_size(self, file_info: FileInfo) -> Tuple[str, str]:
        """
        Classify file by size category.

        Args:
            file_info: File information

        Returns:
            Tuple of (size_category, subcategory)
        """
        size_mb = file_info.size_mb

        if size_mb < 1:
            return ("Small", "Under1MB")
        elif size_mb < 10:
            return ("Small", "1-10MB")
        elif size_mb < 100:
            return ("Medium", "10-100MB")
        elif size_mb < 1000:
            return ("Medium", "100MB-1GB")
        else:
            return ("Large", "Over1GB")

    def _classify_hybrid(self, file_info: FileInfo) -> Tuple[str, str]:
        """
        Classify file using hybrid approach (extension + date).

        Args:
            file_info: File information

        Returns:
            Tuple of (category-year, subcategory)
        """
        # Get extension-based classification
        ext_category, ext_subcategory = self._classify_by_extension(file_info)

        # Get year from date
        dt = datetime.fromtimestamp(file_info.modified_time)
        year = str(dt.year)

        # Combine: category becomes "Category-YYYY", subcategory stays the same
        hybrid_category = f"{ext_category}-{year}"

        return (hybrid_category, ext_subcategory)

    def get_destination_path(
        self, file_info: FileInfo, root_dir: Path, reason: str = "classify"
    ) -> Path:
        """
        Get the destination path for a file based on classification.
        All created directories will have the all_ prefix.

        Args:
            file_info: File information
            root_dir: Root directory for organization
            reason: Reason for the move ("classify", "duplicate")

        Returns:
            Destination path for the file
        """
        if reason == "duplicate" and self.config.isolate_duplicates:
            # For duplicates, preserve original path structure in all_Duplicates
            relative_path = file_info.path.relative_to(root_dir)
            duplicates_dir = self.config.get_managed_name(self.config.duplicates_folder)
            dest_dir = root_dir / duplicates_dir / relative_path.parent
            return dest_dir / file_info.name

        # For classification, use the classification system with all_ prefix
        category, subcategory = self.classify_file(file_info)
        category_dir = self.config.get_managed_name(category)
        dest_dir = root_dir / category_dir / subcategory
        return dest_dir / file_info.name

    def clear_cache(self) -> None:
        """Clear the classification cache."""
        self._classification_cache.clear()
