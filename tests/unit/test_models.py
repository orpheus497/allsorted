"""
Tests for data models.

Created by orpheus497
"""

from datetime import datetime
from pathlib import Path

import pytest

from allsorted.models import (
    ConflictResolution,
    DirectoryMoveOperation,
    DuplicateSet,
    FileInfo,
    MoveOperation,
    OrganizationPlan,
    OrganizationResult,
    OrganizationStrategy,
)


class TestEnums:
    """Test enumeration types."""

    def test_organization_strategy_values(self) -> None:
        """Test OrganizationStrategy enum values."""
        assert OrganizationStrategy.BY_EXTENSION.value == "by-extension"
        assert OrganizationStrategy.BY_DATE.value == "by-date"
        assert OrganizationStrategy.BY_SIZE.value == "by-size"
        assert OrganizationStrategy.HYBRID.value == "hybrid"

    def test_conflict_resolution_values(self) -> None:
        """Test ConflictResolution enum values."""
        assert ConflictResolution.RENAME.value == "rename"
        assert ConflictResolution.SKIP.value == "skip"
        assert ConflictResolution.OVERWRITE.value == "overwrite"
        assert ConflictResolution.ASK.value == "ask"


class TestFileInfo:
    """Test FileInfo dataclass."""

    def test_file_info_creation(self, temp_dir: Path) -> None:
        """Test creating FileInfo instance."""
        file_path = temp_dir / "test.txt"
        file_info = FileInfo(
            path=file_path,
            size_bytes=1024,
            hash="abc123",
            modified_time=datetime.now().timestamp(),
            is_symlink=False,
        )

        assert file_info.path == file_path
        assert file_info.size_bytes == 1024
        assert file_info.hash == "abc123"
        assert not file_info.is_symlink

    def test_file_info_extension(self, temp_dir: Path) -> None:
        """Test FileInfo extension property."""
        file_info = FileInfo(
            path=Path("/path/to/file.txt"),
            size_bytes=100,
            hash="hash",
            modified_time=0.0,
            is_symlink=False,
        )

        assert file_info.extension == ".txt"

    def test_file_info_extension_no_extension(self, temp_dir: Path) -> None:
        """Test FileInfo extension for file without extension."""
        file_info = FileInfo(
            path=Path("/path/to/README"),
            size_bytes=100,
            hash="hash",
            modified_time=0.0,
            is_symlink=False,
        )

        assert file_info.extension == ""


class TestDuplicateSet:
    """Test DuplicateSet dataclass."""

    def test_duplicate_set_properties(self, temp_dir: Path) -> None:
        """Test DuplicateSet calculated properties."""
        file1 = FileInfo(
            path=temp_dir / "file1.txt",
            size_bytes=1000,
            hash="hash123",
            modified_time=100.0,
            is_symlink=False,
        )
        file2 = FileInfo(
            path=temp_dir / "file2.txt",
            size_bytes=1000,
            hash="hash123",
            modified_time=200.0,
            is_symlink=False,
        )

        dup_set = DuplicateSet(hash="hash123", files=[file1, file2])

        assert dup_set.count == 2
        assert dup_set.space_wasted == 1000
        assert dup_set.primary == file1  # Older file
        assert file2 in dup_set.extras


class TestMoveOperation:
    """Test MoveOperation dataclass."""

    def test_move_operation_creation(self, temp_dir: Path) -> None:
        """Test creating MoveOperation."""
        source = temp_dir / "source.txt"
        dest = temp_dir / "dest.txt"
        file_info = FileInfo(
            path=source,
            size_bytes=100,
            hash="hash",
            modified_time=0.0,
            is_symlink=False,
        )

        operation = MoveOperation(
            source=source,
            destination=dest,
            file_info=file_info,
            reason="test",
            conflict_resolution=ConflictResolution.RENAME,
        )

        assert operation.source == source
        assert operation.destination == dest
        assert operation.reason == "test"
        assert operation.conflict_resolution == ConflictResolution.RENAME

    def test_move_operation_is_classification(self) -> None:
        """Test is_classification property."""
        operation = MoveOperation(
            source=Path("/source"),
            destination=Path("/dest"),
            file_info=None,  # type: ignore
            reason="classify",
            conflict_resolution=ConflictResolution.RENAME,
        )

        assert operation.is_classification

    def test_move_operation_is_duplicate(self) -> None:
        """Test is_duplicate property."""
        operation = MoveOperation(
            source=Path("/source"),
            destination=Path("/dest"),
            file_info=None,  # type: ignore
            reason="duplicate",
            conflict_resolution=ConflictResolution.RENAME,
        )

        assert operation.is_duplicate


class TestOrganizationPlan:
    """Test OrganizationPlan dataclass."""

    def test_organization_plan_creation(self, temp_dir: Path) -> None:
        """Test creating OrganizationPlan."""
        plan = OrganizationPlan(root_dir=temp_dir)

        assert plan.root_dir == temp_dir
        assert plan.operations == []
        assert plan.duplicate_sets == []
        assert plan.errors == []

    def test_organization_plan_add_operation(self, temp_dir: Path) -> None:
        """Test adding operation to plan."""
        plan = OrganizationPlan(root_dir=temp_dir)
        operation = MoveOperation(
            source=temp_dir / "source.txt",
            destination=temp_dir / "dest.txt",
            file_info=None,  # type: ignore
            reason="test",
            conflict_resolution=ConflictResolution.RENAME,
        )

        plan.add_operation(operation)

        assert len(plan.operations) == 1
        assert plan.operations[0] == operation

    def test_organization_plan_total_files(self, temp_dir: Path) -> None:
        """Test total_files property."""
        plan = OrganizationPlan(root_dir=temp_dir)

        # Add some operations
        for i in range(5):
            operation = MoveOperation(
                source=temp_dir / f"source{i}.txt",
                destination=temp_dir / f"dest{i}.txt",
                file_info=None,  # type: ignore
                reason="test",
                conflict_resolution=ConflictResolution.RENAME,
            )
            plan.add_operation(operation)

        assert plan.total_files == 5

    def test_organization_plan_categories_used(self, temp_dir: Path) -> None:
        """Test categories_used property."""
        plan = OrganizationPlan(root_dir=temp_dir)

        # Add operations with different categories
        plan.add_operation(
            MoveOperation(
                source=temp_dir / "file1.txt",
                destination=temp_dir / "all_Docs" / "file1.txt",
                file_info=None,  # type: ignore
                reason="test",
                conflict_resolution=ConflictResolution.RENAME,
            )
        )
        plan.add_operation(
            MoveOperation(
                source=temp_dir / "file2.txt",
                destination=temp_dir / "all_Pics" / "file2.txt",
                file_info=None,  # type: ignore
                reason="test",
                conflict_resolution=ConflictResolution.RENAME,
            )
        )

        categories = plan.categories_used
        assert "all_Docs" in categories
        assert "all_Pics" in categories


class TestOrganizationResult:
    """Test OrganizationResult dataclass."""

    def test_organization_result_creation(self, temp_dir: Path) -> None:
        """Test creating OrganizationResult."""
        plan = OrganizationPlan(root_dir=temp_dir)
        result = OrganizationResult(
            plan=plan,
            started=datetime.now(),
            dry_run=False,
        )

        assert result.plan == plan
        assert not result.dry_run
        assert result.successful_operations == []
        assert result.failed_operations == []

    def test_organization_result_files_moved(self, temp_dir: Path) -> None:
        """Test files_moved property."""
        plan = OrganizationPlan(root_dir=temp_dir)
        result = OrganizationResult(
            plan=plan,
            started=datetime.now(),
            dry_run=False,
        )

        # Add successful operations
        for i in range(3):
            result.successful_operations.append(
                MoveOperation(
                    source=temp_dir / f"source{i}.txt",
                    destination=temp_dir / f"dest{i}.txt",
                    file_info=None,  # type: ignore
                    reason="test",
                    conflict_resolution=ConflictResolution.RENAME,
                )
            )

        assert result.files_moved == 3

    def test_organization_result_success_rate(self, temp_dir: Path) -> None:
        """Test success_rate property."""
        plan = OrganizationPlan(root_dir=temp_dir)
        result = OrganizationResult(
            plan=plan,
            started=datetime.now(),
            dry_run=False,
        )

        # Add 7 successful and 3 failed operations
        for i in range(7):
            result.successful_operations.append(
                MoveOperation(
                    source=temp_dir / f"source{i}.txt",
                    destination=temp_dir / f"dest{i}.txt",
                    file_info=None,  # type: ignore
                    reason="test",
                    conflict_resolution=ConflictResolution.RENAME,
                )
            )

        for i in range(3):
            result.failed_operations.append(
                (
                    MoveOperation(
                        source=temp_dir / f"fail{i}.txt",
                        destination=temp_dir / f"dest{i}.txt",
                        file_info=None,  # type: ignore
                        reason="test",
                        conflict_resolution=ConflictResolution.RENAME,
                    ),
                    "error",
                )
            )

        assert result.success_rate == 70.0

    def test_organization_result_is_complete_success(self, temp_dir: Path) -> None:
        """Test is_complete_success property."""
        plan = OrganizationPlan(root_dir=temp_dir)
        result = OrganizationResult(
            plan=plan,
            started=datetime.now(),
            dry_run=False,
        )

        # Add only successful operations
        result.successful_operations.append(
            MoveOperation(
                source=temp_dir / "source.txt",
                destination=temp_dir / "dest.txt",
                file_info=None,  # type: ignore
                reason="test",
                conflict_resolution=ConflictResolution.RENAME,
            )
        )

        assert result.is_complete_success
