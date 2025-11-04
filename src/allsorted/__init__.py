"""
allsorted - Intelligent File Organizer

A powerful command-line tool that brings order to chaotic directories through
intelligent classification, duplicate detection, and organized file management.

Created by orpheus497
"""

__version__ = "1.0.0"
__author__ = "orpheus497"
__license__ = "MIT"

from allsorted.models import (
    FileInfo,
    DuplicateSet,
    MoveOperation,
    OrganizationPlan,
    OrganizationResult,
    ConflictResolution,
)

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "FileInfo",
    "DuplicateSet",
    "MoveOperation",
    "OrganizationPlan",
    "OrganizationResult",
    "ConflictResolution",
]
