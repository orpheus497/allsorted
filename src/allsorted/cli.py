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
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn

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

        console.print("\n[green]Undo complete[/green]")
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


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.pass_context
def watch(ctx: click.Context, directory: str, config: Optional[str]) -> None:
    """Watch a directory and automatically organize new files.

    This command monitors DIRECTORY for new files and automatically
    organizes them according to the configured classification rules.

    Press Ctrl+C to stop watching.
    """
    try:
        from allsorted.watcher import DirectoryWatcher, WATCHDOG_AVAILABLE

        if not WATCHDOG_AVAILABLE:
            console.print(
                "[bold red]Error:[/bold red] Watch mode requires the 'watchdog' package.\n"
                "Install with: [cyan]pip install watchdog[/cyan]"
            )
            sys.exit(1)

        cfg = load_config(Path(config) if config else None)
        root_dir = Path(directory).resolve()

        console.print(f"[bold cyan]Watching:[/bold cyan] {root_dir}")
        console.print("[yellow]Press Ctrl+C to stop watching[/yellow]\n")

        def on_file_organized(file_path: Path) -> None:
            """Callback when a file is organized."""
            console.print(f"[green]✓[/green] Organized: {file_path.name}")

        watcher = DirectoryWatcher(root_dir, cfg)
        watcher.start(organize_callback=on_file_organized)

        try:
            # Keep running until interrupted
            import time

            while watcher.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping watcher...[/yellow]")
            watcher.stop()
            console.print("[green]Watcher stopped[/green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if ctx.obj.get("verbose"):
            console.print_exception()
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
@click.option(
    "--wizard",
    "-w",
    is_flag=True,
    help="Run interactive configuration wizard",
)
def config_init(path: Optional[str], wizard: bool) -> None:
    """Initialize a new configuration file."""

    try:
        config_path = Path(path) if path else get_default_config_path()

        if config_path.exists():
            if not click.confirm(f"Config file exists at {config_path}. Overwrite?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                sys.exit(0)

        if wizard:
            # Run interactive wizard
            from allsorted.wizard import run_first_time_wizard

            cfg = run_first_time_wizard()
        else:
            # Create default config
            cfg = Config()
            save_config(cfg, config_path)

            console.print(f"[green]Configuration file created:[/green] {config_path}")
            console.print("\nEdit this file to customize allsorted behavior.")
            console.print(
                "Or run: [cyan]allsorted config init --wizard[/cyan] for interactive setup"
            )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@main.command()
@click.argument(
    "shell",
    type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
    required=False,
)
def completion(shell: Optional[str]) -> None:
    """
    Generate shell completion script.

    Examples:
        # Bash
        allsorted completion bash > ~/.local/share/bash-completion/completions/allsorted

        # Zsh
        allsorted completion zsh > ~/.zsh/completion/_allsorted

        # Fish
        allsorted completion fish > ~/.config/fish/completions/allsorted.fish

    Then restart your shell or source the completion file.
    """
    if not shell:
        console.print("[bold cyan]Shell Completion Setup[/bold cyan]\n")
        console.print("Generate completion scripts for your shell:\n")
        console.print("[yellow]Bash:[/yellow]")
        console.print(
            "  allsorted completion bash > ~/.local/share/bash-completion/completions/allsorted"
        )
        console.print("  source ~/.bashrc\n")
        console.print("[yellow]Zsh:[/yellow]")
        console.print("  allsorted completion zsh > ~/.zsh/completion/_allsorted")
        console.print("  # Add ~/.zsh/completion to your fpath in .zshrc")
        console.print("  source ~/.zshrc\n")
        console.print("[yellow]Fish:[/yellow]")
        console.print("  allsorted completion fish > ~/.config/fish/completions/allsorted.fish")
        sys.exit(0)

    # Generate completion script
    if shell == "bash":
        _generate_bash_completion()
    elif shell == "zsh":
        _generate_zsh_completion()
    elif shell == "fish":
        _generate_fish_completion()


def _generate_bash_completion() -> None:
    """Generate bash completion script."""
    script = """
# Bash completion for allsorted
_allsorted_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Main commands
    if [ $COMP_CWORD -eq 1 ]; then
        opts="organize preview validate undo config completion --help --version"
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    # Command-specific options
    case "${prev}" in
        organize|preview)
            opts="--config --dry-run --no-duplicates --strategy --conflict --report --verbose"
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
        --strategy)
            opts="by-extension by-date by-size hybrid"
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
        --conflict)
            opts="rename skip overwrite"
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
        config)
            opts="show init"
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
        completion)
            opts="bash zsh fish"
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
        *)
            # File/directory completion
            COMPREPLY=( $(compgen -f -- ${cur}) )
            ;;
    esac
}

complete -F _allsorted_completion allsorted
"""
    print(script)


def _generate_zsh_completion() -> None:
    """Generate zsh completion script."""
    script = """#compdef allsorted

_allsorted() {
    local -a commands
    commands=(
        'organize:Organize files in directory'
        'preview:Preview organization without changes'
        'validate:Validate directory can be organized'
        'undo:Undo previous organization'
        'config:Manage configuration'
        'completion:Generate shell completion script'
    )

    local -a organize_opts
    organize_opts=(
        '--config[Use custom config file]:file:_files'
        '--dry-run[Preview without changes]'
        '--no-duplicates[Disable duplicate detection]'
        '--strategy[Organization strategy]:strategy:(by-extension by-date by-size hybrid)'
        '--conflict[Conflict resolution]:resolution:(rename skip overwrite)'
        '--report[Save JSON report]:file:_files'
        '--verbose[Verbose output]'
    )

    _arguments -C \
        '1: :->command' \
        '*:: :->args'

    case $state in
        command)
            _describe -t commands 'allsorted command' commands
            ;;
        args)
            case $words[1] in
                organize|preview)
                    _arguments $organize_opts
                    ;;
                config)
                    _values 'config command' 'show' 'init'
                    ;;
                completion)
                    _values 'shell' 'bash' 'zsh' 'fish'
                    ;;
            esac
            ;;
    esac
}

_allsorted
"""
    print(script)


def _generate_fish_completion() -> None:
    """Generate fish completion script."""
    script = """# Fish completion for allsorted

# Main commands
complete -c allsorted -f -n "__fish_use_subcommand" -a organize -d "Organize files in directory"
complete -c allsorted -f -n "__fish_use_subcommand" -a preview -d "Preview organization without changes"
complete -c allsorted -f -n "__fish_use_subcommand" -a validate -d "Validate directory can be organized"
complete -c allsorted -f -n "__fish_use_subcommand" -a undo -d "Undo previous organization"
complete -c allsorted -f -n "__fish_use_subcommand" -a config -d "Manage configuration"
complete -c allsorted -f -n "__fish_use_subcommand" -a completion -d "Generate shell completion"

# Organize options
complete -c allsorted -f -n "__fish_seen_subcommand_from organize preview" -l config -d "Custom config file"
complete -c allsorted -f -n "__fish_seen_subcommand_from organize preview" -l dry-run -d "Preview without changes"
complete -c allsorted -f -n "__fish_seen_subcommand_from organize preview" -l no-duplicates -d "Disable duplicate detection"
complete -c allsorted -f -n "__fish_seen_subcommand_from organize preview" -l strategy -d "Organization strategy" -a "by-extension by-date by-size hybrid"
complete -c allsorted -f -n "__fish_seen_subcommand_from organize preview" -l conflict -d "Conflict resolution" -a "rename skip overwrite"
complete -c allsorted -f -n "__fish_seen_subcommand_from organize preview" -l report -d "Save JSON report"
complete -c allsorted -f -n "__fish_seen_subcommand_from organize preview" -l verbose -d "Verbose output"

# Config subcommands
complete -c allsorted -f -n "__fish_seen_subcommand_from config" -a "show init"

# Completion shells
complete -c allsorted -f -n "__fish_seen_subcommand_from completion" -a "bash zsh fish"

# Global options
complete -c allsorted -f -s v -l verbose -d "Enable verbose output"
complete -c allsorted -f -l help -d "Show help message"
complete -c allsorted -f -l version -d "Show version"
"""
    print(script)


if __name__ == "__main__":
    main()
