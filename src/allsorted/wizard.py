"""
Interactive terminal wizard for first-time configuration.

Provides a user-friendly way to set up allsorted through terminal prompts.

Created by orpheus497
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from allsorted.config import (
    Config,
    ConflictResolution,
    OrganizationStrategy,
    get_default_config_path,
    save_config,
)

console = Console()


def run_first_time_wizard() -> Config:
    """
    Run interactive first-time configuration wizard.

    Guides user through terminal prompts to set up their preferences.

    Returns:
        Configured Config object
    """
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]Welcome to allsorted![/bold cyan]\n\n"
            "Let's set up your preferences through a few quick questions.",
            title="🎯 First-Time Setup",
            border_style="cyan",
        )
    )
    console.print()

    config = Config()

    # Organization Strategy
    _configure_strategy(config)

    # Duplicate Detection
    _configure_duplicates(config)

    # File Handling
    _configure_file_handling(config)

    # Performance Options
    _configure_performance(config)

    # Safety Options
    _configure_safety(config)

    # Save configuration
    _save_configuration(config)

    console.print()
    console.print(
        Panel.fit(
            "[bold green]✓ Configuration complete![/bold green]\n\n"
            "You can change these settings anytime by editing your config file\n"
            "or running: [cyan]allsorted config init[/cyan]",
            title="🎉 All Set!",
            border_style="green",
        )
    )
    console.print()

    return config


def _configure_strategy(config: Config) -> None:
    """Configure organization strategy."""
    console.print("[bold]Organization Strategy[/bold]")
    console.print("How would you like to organize your files?\n")

    strategies_table = Table(show_header=True, header_style="bold cyan", box=None)
    strategies_table.add_column("Option", style="yellow")
    strategies_table.add_column("Description")

    strategies_table.add_row("by-extension", "Group by file type (Photos, Docs, etc.) [default]")
    strategies_table.add_row("by-date", "Group by modification date (2024/01-15, etc.)")
    strategies_table.add_row("by-size", "Group by file size (Small, Medium, Large)")
    strategies_table.add_row("hybrid", "Combine extension and date")

    console.print(strategies_table)
    console.print()

    strategy = Prompt.ask(
        "Choose strategy",
        choices=["by-extension", "by-date", "by-size", "hybrid"],
        default="by-extension",
    )

    config.strategy = OrganizationStrategy(strategy)
    console.print(f"[green]✓[/green] Using [cyan]{strategy}[/cyan] strategy\n")


def _configure_duplicates(config: Config) -> None:
    """Configure duplicate detection settings."""
    console.print("[bold]Duplicate Detection[/bold]")

    config.detect_duplicates = Confirm.ask("Enable duplicate file detection?", default=True)

    if config.detect_duplicates:
        console.print("[green]✓[/green] Duplicate detection enabled")

        config.isolate_duplicates = Confirm.ask(
            "  Move duplicates to separate folder?", default=True
        )

        if config.isolate_duplicates:
            console.print("[green]✓[/green] Duplicates will be isolated in all_Duplicates/")
    else:
        console.print("[yellow]○[/yellow] Duplicate detection disabled")

    console.print()


def _configure_file_handling(config: Config) -> None:
    """Configure file handling options."""
    console.print("[bold]File Handling[/bold]")

    # Conflict resolution
    console.print("How should file name conflicts be handled?\n")

    conflict_table = Table(show_header=True, header_style="bold cyan", box=None)
    conflict_table.add_column("Option", style="yellow")
    conflict_table.add_column("Description")

    conflict_table.add_row("rename", "Rename file with _1, _2, etc. [safest, default]")
    conflict_table.add_row("skip", "Skip files that would conflict")
    conflict_table.add_row("overwrite", "Overwrite existing files [caution]")

    console.print(conflict_table)
    console.print()

    resolution = Prompt.ask(
        "Choose conflict resolution", choices=["rename", "skip", "overwrite"], default="rename"
    )

    config.conflict_resolution = ConflictResolution(resolution)
    console.print(f"[green]✓[/green] Conflicts will be handled by: [cyan]{resolution}[/cyan]")

    # Hidden files
    config.ignore_hidden = Confirm.ask("Ignore hidden files (starting with .)?", default=True)

    console.print()


def _configure_performance(config: Config) -> None:
    """Configure performance options."""
    console.print("[bold]Performance Options[/bold]")
    console.print("These options can speed up processing for large directories.\n")

    # Hash algorithm
    algorithm = Prompt.ask("Hash algorithm", choices=["sha256", "xxhash"], default="sha256")

    config.hash_algorithm = algorithm

    if algorithm == "xxhash":
        console.print("[cyan]ℹ[/cyan] xxHash is 3-5x faster but not cryptographically secure")
    else:
        console.print("[cyan]ℹ[/cyan] SHA256 is slower but cryptographically secure")

    # Parallel processing
    config.parallel_processing = Confirm.ask(
        "Enable parallel processing (multi-core)?", default=False
    )

    if config.parallel_processing:
        max_workers = IntPrompt.ask("  Number of CPU cores to use", default=4)
        config.max_workers = max_workers
        console.print(f"[green]✓[/green] Will use {max_workers} CPU cores")

    # Async I/O
    config.use_async = Confirm.ask("Enable async I/O (better for network paths)?", default=False)

    if config.use_async:
        console.print("[green]✓[/green] Async I/O enabled")

    console.print()


def _configure_safety(config: Config) -> None:
    """Configure safety options."""
    console.print("[bold]Safety Options[/bold]")

    config.require_confirmation = Confirm.ask(
        "Require confirmation before organizing?", default=False
    )

    config.verify_integrity = Confirm.ask(
        "Verify file integrity after moves (slower but safer)?", default=False
    )

    if config.verify_integrity:
        console.print("[cyan]ℹ[/cyan] Files will be verified after moving to ensure no corruption")

    console.print()


def _save_configuration(config: Config) -> None:
    """Save configuration to file."""
    console.print("[bold]Save Configuration[/bold]")

    default_path = get_default_config_path()
    console.print(f"Default location: [cyan]{default_path}[/cyan]")

    use_default = Confirm.ask("Save to default location?", default=True)

    if use_default:
        config_path = default_path
    else:
        custom_path = Prompt.ask("Enter custom path")
        config_path = Path(custom_path)

    try:
        save_config(config, config_path)
        console.print(f"[green]✓[/green] Configuration saved to: [cyan]{config_path}[/cyan]")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to save configuration: {e}")
        console.print("[yellow]Using in-memory configuration only[/yellow]")


def show_quick_start() -> None:
    """Show quick start guide after wizard."""
    console.print()
    console.print(
        Panel(
            "[bold cyan]Quick Start Commands[/bold cyan]\n\n"
            "[yellow]Preview what would be organized:[/yellow]\n"
            "  [cyan]allsorted organize --dry-run[/cyan]\n\n"
            "[yellow]Organize current directory:[/yellow]\n"
            "  [cyan]allsorted organize[/cyan]\n\n"
            "[yellow]Organize specific directory:[/yellow]\n"
            "  [cyan]allsorted organize /path/to/folder[/cyan]\n\n"
            "[yellow]View configuration:[/yellow]\n"
            "  [cyan]allsorted config show[/cyan]",
            title="📚 Next Steps",
            border_style="cyan",
        )
    )


def run_quick_setup() -> Optional[Config]:
    """
    Run a minimal quick setup with just essential questions.

    Returns:
        Config object or None if user cancels
    """
    console.print()
    console.print(
        "[bold cyan]Quick Setup[/bold cyan] (or run [cyan]allsorted config init[/cyan] for full wizard)\n"
    )

    if not Confirm.ask("Set up allsorted now?", default=True):
        return None

    config = Config()

    # Just ask the essentials
    config.detect_duplicates = Confirm.ask("Enable duplicate detection?", default=True)

    console.print("\n[green]✓[/green] Quick setup complete! Using defaults for other options.")

    # Save
    try:
        config_path = get_default_config_path()
        save_config(config, config_path)
        console.print(f"[green]✓[/green] Saved to: [cyan]{config_path}[/cyan]")
    except Exception:
        pass

    console.print()
    return config
