"""
Command-line interface for allsorted.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from allsorted import __version__
from allsorted.config import Config, get_default_config_path, load_config, save_config
from allsorted.executor import OrganizationExecutor
from allsorted.models import ConflictResolution, OrganizationStrategy
from allsorted.planner import OrganizationPlanner
from allsorted.reporter import Reporter
from allsorted.validator import OperationValidator

console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Setup logging with rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, show_path=False)],
    )


@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """
    allsorted - Intelligent File Organizer

    Automatically classify, deduplicate, and organize your files.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(verbose)


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Preview operations without executing",
)
@click.option(
    "--no-duplicates",
    is_flag=True,
    help="Disable duplicate detection",
)
@click.option(
    "--strategy",
    type=click.Choice(["by-extension", "by-date", "by-size", "hybrid"]),
    help="Organization strategy",
)
@click.option(
    "--conflict",
    type=click.Choice(["rename", "skip", "overwrite"]),
    help="File conflict resolution strategy",
)
@click.option(
    "--report",
    "-r",
    type=click.Path(),
    help="Save detailed report to file (JSON)",
)
@click.pass_context
def organize(
    ctx: click.Context,
    directory: str,
    config: Optional[str],
    dry_run: bool,
    no_duplicates: bool,
    strategy: Optional[str],
    conflict: Optional[str],
    report: Optional[str],
) -> None:
    """Organize files in DIRECTORY."""

    try:
        # Load configuration
        cfg = load_config(Path(config) if config else None)

        # Apply command-line overrides
        if no_duplicates:
            cfg.detect_duplicates = False
        if strategy:
            cfg.strategy = OrganizationStrategy(strategy)
        if conflict:
            cfg.conflict_resolution = ConflictResolution(conflict)

        root_dir = Path(directory).resolve()

        console.print(f"[bold cyan]Organizing:[/bold cyan] {root_dir}")
        if dry_run:
            console.print("[yellow]DRY RUN MODE - No files will be moved[/yellow]\n")

        # Create planner
        planner = OrganizationPlanner(cfg)

        # Create plan with progress
        console.print("[cyan]Analyzing directory...[/cyan]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Scanning files...", total=100)

            def update_progress(current: int, total: int) -> None:
                progress.update(task, completed=int(current / total * 100), total=100)

            plan = planner.create_plan(root_dir, progress_callback=update_progress)

        # Optimize plan
        console.print("[cyan]Optimizing plan...[/cyan]")
        plan = planner.optimize_plan(plan)

        # Validate plan
        console.print("[cyan]Validating operations...[/cyan]")
        validator = OperationValidator(plan)
        is_valid, errors, warnings = validator.validate_all()

        if warnings:
            console.print("[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  ⚠️  {warning}")

        if errors:
            console.print("[bold red]Validation failed:[/bold red]")
            for error in errors:
                console.print(f"  ❌ {error}")
            sys.exit(1)

        # Show preview
        if dry_run or len(plan.operations) > 100:
            if click.confirm("\nShow detailed preview?", default=False):
                preview = planner.generate_preview(plan, max_items=100)
                console.print(preview)

        # Confirm execution if not dry-run
        if not dry_run and cfg.require_confirmation:
            if not click.confirm(f"\nProceed with {len(plan.operations)} operations?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                sys.exit(0)

        # Execute plan
        executor = OrganizationExecutor(dry_run=dry_run, log_operations=not dry_run)

        console.print(f"\n[cyan]{'Simulating' if dry_run else 'Executing'} operations...[/cyan]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing files...", total=len(plan.operations))

            def exec_progress(current: int, total: int) -> None:
                progress.update(task, completed=current, total=total)

            result = executor.execute_plan(plan, progress_callback=exec_progress)

        # Generate reports
        reporter = Reporter(console)
        console.print("\n")
        reporter.print_summary(result)

        if result.successful_operations:
            console.print("\n")
            reporter.print_statistics(result)

        # Save JSON report if requested
        if report:
            report_path = Path(report)
            reporter.save_json_report(result, report_path)
            console.print(f"\n[green]Report saved:[/green] {report_path}")

        # Save text report to .devAI
        if not dry_run:
            report_dir = root_dir / ".devAI"
            report_dir.mkdir(exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            text_report_path = report_dir / f"report_{timestamp}.txt"
            reporter.save_text_report(result, text_report_path)

        # Exit with appropriate code
        sys.exit(0 if result.is_complete_success else 1)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if ctx.obj.get("verbose"):
            console.print_exception()
        sys.exit(1)


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--max-items",
    "-m",
    type=int,
    default=50,
    help="Maximum items to show in preview",
)
def preview(directory: str, config: Optional[str], max_items: int) -> None:
    """Preview what would be organized without making changes."""

    try:
        cfg = load_config(Path(config) if config else None)
        root_dir = Path(directory).resolve()

        console.print(f"[bold cyan]Preview for:[/bold cyan] {root_dir}\n")

        planner = OrganizationPlanner(cfg)

        console.print("[cyan]Analyzing directory...[/cyan]")
        plan = planner.create_plan(root_dir)
        plan = planner.optimize_plan(plan)

        preview_text = planner.generate_preview(plan, max_items=max_items)
        console.print(preview_text)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@main.command()
@click.argument("log_file", type=click.Path(exists=True))
@click.option("--dry-run", "-n", is_flag=True, help="Preview undo without executing")
def undo(log_file: str, dry_run: bool) -> None:
    """Undo operations from a LOG_FILE."""

    try:
        log_path = Path(log_file)

        if dry_run:
            console.print("[yellow]DRY RUN MODE - Would undo operations[/yellow]")
            console.print(f"Log file: {log_path}")
            sys.exit(0)

        if not click.confirm(f"Undo all operations from {log_path}?"):
            console.print("[yellow]Operation cancelled[/yellow]")
            sys.exit(0)

        executor = OrganizationExecutor(dry_run=False, log_operations=False)
        successful, failed = executor.undo_operations(log_path)

        console.print(f"\n[green]Undo complete[/green]")
        console.print(f"  Successful: {successful}")
        console.print(f"  Failed: {failed}")

        sys.exit(0 if failed == 0 else 1)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
def validate(directory: str, config: Optional[str]) -> None:
    """Validate a directory can be organized safely."""

    try:
        cfg = load_config(Path(config) if config else None)
        root_dir = Path(directory).resolve()

        console.print(f"[bold cyan]Validating:[/bold cyan] {root_dir}\n")

        planner = OrganizationPlanner(cfg)
        console.print("[cyan]Creating plan...[/cyan]")
        plan = planner.create_plan(root_dir)
        plan = planner.optimize_plan(plan)

        console.print("[cyan]Running validation checks...[/cyan]\n")
        validator = OperationValidator(plan)
        is_valid, errors, warnings = validator.validate_all()

        console.print(validator.get_summary())

        if is_valid:
            console.print("\n[bold green]✓ All validation checks passed[/bold green]")
            sys.exit(0)
        else:
            console.print("\n[bold red]✗ Validation failed[/bold red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@main.group()
def config_cmd() -> None:
    """Configuration management commands."""
    pass


@config_cmd.command("show")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
def config_show(config: Optional[str]) -> None:
    """Show current configuration."""

    try:
        cfg = load_config(Path(config) if config else None)

        console.print("[bold cyan]Current Configuration:[/bold cyan]\n")
        console.print(f"Strategy: {cfg.strategy.value}")
        console.print(f"Conflict Resolution: {cfg.conflict_resolution.value}")
        console.print(f"Detect Duplicates: {cfg.detect_duplicates}")
        console.print(f"Isolate Duplicates: {cfg.isolate_duplicates}")
        console.print(f"Follow Symlinks: {cfg.follow_symlinks}")
        console.print(f"Ignore Hidden: {cfg.ignore_hidden}")
        console.print(f"Ignore Patterns: {', '.join(cfg.ignore_patterns)}")

        console.print("\n[bold]Categories:[/bold]")
        for category in sorted(cfg.get_all_categories()):
            console.print(f"  • {category}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@config_cmd.command("init")
@click.option(
    "--path",
    "-p",
    type=click.Path(),
    help="Path for config file (default: ~/.config/allsorted/config.yaml)",
)
def config_init(path: Optional[str]) -> None:
    """Initialize a new configuration file."""

    try:
        config_path = Path(path) if path else get_default_config_path()

        if config_path.exists():
            if not click.confirm(f"Config file exists at {config_path}. Overwrite?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                sys.exit(0)

        cfg = Config()
        save_config(cfg, config_path)

        console.print(f"[green]Configuration file created:[/green] {config_path}")
        console.print("\nEdit this file to customize allsorted behavior.")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
