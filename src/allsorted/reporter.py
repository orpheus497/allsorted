"""
Report generation for allsorted operations.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from allsorted.models import OrganizationResult
from allsorted.utils import format_duration, format_size

logger = logging.getLogger(__name__)


class Reporter:
    """Generates reports and summaries of organization operations."""

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize reporter.

        Args:
            console: Rich console for output (creates new one if None)
        """
        self.console = console or Console()

    def print_summary(self, result: OrganizationResult) -> None:
        """
        Print a summary of the organization result to console.

        Args:
            result: Organization result
        """
        plan = result.plan

        # Create summary table
        table = Table(title="Organization Summary", show_header=False, box=None)
        table.add_column("Item", style="cyan")
        table.add_column("Value", style="bold")

        # Add rows
        status = "DRY RUN ✓" if result.dry_run else "COMPLETED ✓" if result.is_complete_success else "COMPLETED WITH ERRORS"
        table.add_row("Status", status)
        table.add_row("Root Directory", str(plan.root_dir))
        table.add_row("Total Files Processed", str(result.files_moved))
        table.add_row("Operations Failed", str(result.files_failed))
        table.add_row("Success Rate", f"{result.success_rate:.1f}%")
        table.add_row("Duration", format_duration(result.duration_seconds))

        if plan.duplicate_sets:
            table.add_row("Duplicate Sets Found", str(len(plan.duplicate_sets)))
            table.add_row("Duplicate Files", str(plan.total_duplicates))
            table.add_row(
                "Space Recoverable",
                format_size(plan.space_recoverable)
            )

        if result.directories_created:
            table.add_row("Directories Created", str(len(result.directories_created)))

        if result.directories_removed:
            table.add_row("Empty Directories Removed", str(len(result.directories_removed)))

        self.console.print(table)

        # Print errors if any
        if result.failed_operations:
            self.console.print("\n[bold red]Errors:[/bold red]")
            for op, error in result.failed_operations[:10]:  # Show first 10 errors
                self.console.print(f"  ❌ {op.source.name}: {error}")
            if len(result.failed_operations) > 10:
                self.console.print(f"  ... and {len(result.failed_operations) - 10} more errors")

    def print_statistics(self, result: OrganizationResult) -> None:
        """
        Print detailed statistics about the organization.

        Args:
            result: Organization result
        """
        plan = result.plan

        # Calculate statistics
        total_size = sum(op.file_info.size_bytes for op in result.successful_operations)
        
        # Count by category
        category_counts: dict[str, int] = {}
        for op in result.successful_operations:
            if op.destination.parent != plan.root_dir:
                category = op.destination.parent.name
                category_counts[category] = category_counts.get(category, 0) + 1

        # Create statistics table
        table = Table(title="Statistics", show_header=True)
        table.add_column("Category", style="cyan")
        table.add_column("Files", justify="right", style="yellow")
        table.add_column("Percentage", justify="right", style="green")

        total_files = len(result.successful_operations)
        for category in sorted(category_counts.keys()):
            count = category_counts[category]
            percentage = (count / total_files * 100) if total_files > 0 else 0
            table.add_row(category, str(count), f"{percentage:.1f}%")

        self.console.print(table)

        # Print size information
        self.console.print(f"\n[bold]Total Size Organized:[/bold] {format_size(total_size)}")

        if plan.duplicate_sets:
            duplicate_size = sum(ds.space_wasted for ds in plan.duplicate_sets)
            self.console.print(f"[bold]Space Wasted by Duplicates:[/bold] {format_size(duplicate_size)}")

    def save_json_report(self, result: OrganizationResult, output_path: Path) -> None:
        """
        Save detailed report as JSON file.

        Args:
            result: Organization result
            output_path: Path to save JSON report

        Raises:
            OSError: If file cannot be written
        """
        logger.info(f"Saving JSON report to: {output_path}")

        plan = result.plan

        report_data = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "dry_run": result.dry_run,
            "summary": {
                "root_directory": str(plan.root_dir),
                "total_operations": plan.total_files,
                "successful_operations": result.files_moved,
                "failed_operations": result.files_failed,
                "success_rate": result.success_rate,
                "duration_seconds": result.duration_seconds,
            },
            "duplicates": {
                "sets_found": len(plan.duplicate_sets),
                "total_duplicates": plan.total_duplicates,
                "space_recoverable_bytes": plan.space_recoverable,
                "duplicate_sets": [
                    {
                        "hash": ds.hash,
                        "count": ds.count,
                        "size_bytes": ds.files[0].size_bytes if ds.files else 0,
                        "primary": str(ds.primary.path) if ds.primary else None,
                        "extras": [str(f.path) for f in ds.extras],
                    }
                    for ds in plan.duplicate_sets
                ],
            },
            "operations": {
                "successful": [
                    {
                        "source": str(op.source),
                        "destination": str(op.destination),
                        "reason": op.reason,
                        "size_bytes": op.file_info.size_bytes,
                    }
                    for op in result.successful_operations
                ],
                "failed": [
                    {
                        "source": str(op.source),
                        "destination": str(op.destination),
                        "error": error,
                    }
                    for op, error in result.failed_operations
                ],
            },
            "directories": {
                "created": [str(d) for d in result.directories_created],
                "removed": [str(d) for d in result.directories_removed],
            },
            "errors": plan.errors,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"JSON report saved: {output_path}")

    def save_text_report(self, result: OrganizationResult, output_path: Path) -> None:
        """
        Save human-readable text report.

        Args:
            result: Organization result
            output_path: Path to save text report

        Raises:
            OSError: If file cannot be written
        """
        logger.info(f"Saving text report to: {output_path}")

        plan = result.plan

        lines = [
            "=" * 80,
            "ALLSORTED ORGANIZATION REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Root Directory: {plan.root_dir}",
            f"Mode: {'DRY RUN' if result.dry_run else 'EXECUTE'}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Total Operations: {plan.total_files}",
            f"Successful: {result.files_moved}",
            f"Failed: {result.files_failed}",
            f"Success Rate: {result.success_rate:.1f}%",
            f"Duration: {format_duration(result.duration_seconds)}",
            "",
        ]

        if plan.duplicate_sets:
            lines.extend([
                "DUPLICATES",
                "-" * 80,
                f"Duplicate Sets: {len(plan.duplicate_sets)}",
                f"Duplicate Files: {plan.total_duplicates}",
                f"Space Recoverable: {format_size(plan.space_recoverable)}",
                "",
            ])

        if result.directories_created:
            lines.extend([
                "DIRECTORIES CREATED",
                "-" * 80,
            ])
            for directory in result.directories_created[:50]:
                lines.append(f"  + {directory}")
            if len(result.directories_created) > 50:
                lines.append(f"  ... and {len(result.directories_created) - 50} more")
            lines.append("")

        if result.failed_operations:
            lines.extend([
                "ERRORS",
                "-" * 80,
            ])
            for op, error in result.failed_operations:
                lines.append(f"  ❌ {op.source}")
                lines.append(f"     Error: {error}")
            lines.append("")

        lines.extend([
            "=" * 80,
            "END OF REPORT",
            "=" * 80,
        ])

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write("\n".join(lines))

        logger.info(f"Text report saved: {output_path}")
