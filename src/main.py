#!/usr/bin/env python3
"""
MacPurge - Synthwave-themed macOS cleanup utility.

Intelligently scan and clean your Mac with checkpoint/resume support.
"""

import sys
from pathlib import Path

import click
from rich.prompt import Confirm, IntPrompt

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.banner import display_banner
from src.ui.styles import console, success, error, warning, info, divider
from src.ui.formatters import (
    display_scan_summary,
    display_detailed_results,
    display_cleanup_summary,
    display_category_selection_menu,
    CATEGORY_LABELS,
)
from src.services.scanner import MacScanner
from src.services.cleaner import MacCleaner
from src.models.cleanup import CleanupCategory
from src.config.settings import settings


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit.")
@click.pass_context
def cli(ctx: click.Context, version: bool) -> None:
    """
    MacPurge - Reclaim your storage with style.
    
    Intelligently scan and clean caches, logs, build artifacts,
    and development dependencies on macOS.
    """
    if version:
        console.print("[bold cyan]MacPurge[/bold cyan] v1.0.0")
        return
    
    if ctx.invoked_subcommand is None:
        display_banner()
        console.print("Run [bold cyan]macpurge --help[/bold cyan] for commands.\n")
        console.print("Quick start:")
        console.print("  [cyan]macpurge scan[/cyan]        Scan for cleanable items")
        console.print("  [cyan]macpurge clean[/cyan]       Interactive cleanup")
        console.print("  [cyan]macpurge quick[/cyan]       Quick safe cleanup")
        console.print()


@cli.command()
@click.option(
    "--all", "include_all", is_flag=True,
    help="Include items requiring confirmation in scan."
)
@click.option(
    "--detailed", is_flag=True,
    help="Show detailed list of all targets."
)
@click.option(
    "--limit", default=20, type=int,
    help="Number of items to show in detailed view."
)
def scan(include_all: bool, detailed: bool, limit: int) -> None:
    """Scan system for cleanable files and directories."""
    display_banner()
    divider("Scanning System")
    
    scanner = MacScanner(settings.HOME_DIR)
    result = scanner.scan(include_dangerous=include_all)
    
    if result.scan_errors:
        for err in result.scan_errors:
            warning(err)
        console.print()
    
    if not result.targets:
        success("Your system is already clean! No significant items found.")
        return
    
    display_scan_summary(result)
    
    if detailed:
        console.print()
        display_detailed_results(result, limit=limit)
    
    console.print()
    info("Run [bold]macpurge clean[/bold] to start cleanup")


@cli.command()
@click.option(
    "--dry-run", is_flag=True,
    help="Preview cleanup without deleting anything."
)
@click.option(
    "--resume/--fresh", default=True,
    help="Resume from checkpoint or start fresh."
)
@click.option(
    "--yes", "-y", is_flag=True,
    help="Skip confirmation prompts for safe items."
)
@click.option(
    "--category", "-c", multiple=True,
    type=click.Choice([c.value for c in CleanupCategory]),
    help="Only clean specific categories."
)
def clean(dry_run: bool, resume: bool, yes: bool, category: tuple) -> None:
    """Interactive cleanup with selective deletion."""
    display_banner()
    
    if dry_run:
        warning("DRY RUN MODE - No files will be deleted")
        console.print()
    
    divider("Scanning System")
    
    scanner = MacScanner(settings.HOME_DIR)
    result = scanner.scan(include_dangerous=True)
    
    if not result.targets:
        success("Your system is already clean!")
        return
    
    if category:
        selected_categories = {CleanupCategory(c) for c in category}
        result.targets = [
            t for t in result.targets
            if t.category in selected_categories
        ]
        if not result.targets:
            warning(f"No items found in selected categories: {', '.join(category)}")
            return
        result.total_size_bytes = sum(t.size_bytes for t in result.targets)
    
    display_scan_summary(result)
    console.print()
    display_detailed_results(result)
    
    console.print()
    
    if not yes and not dry_run:
        proceed = Confirm.ask(
            f"[bold]Proceed with cleanup of [cyan]{result.human_total_size}[/cyan]?[/bold]"
        )
        if not proceed:
            info("Cleanup cancelled.")
            return
    
    divider("Cleaning")
    
    settings.ensure_state_dir()
    cleaner = MacCleaner(dry_run=dry_run, state_dir=str(settings.STATE_DIR))
    
    progress = cleaner.clean_targets(
        result.targets,
        resume=resume,
        interactive=not yes,
    )
    
    display_cleanup_summary(progress, dry_run=dry_run)


@cli.command()
@click.option(
    "--dry-run", is_flag=True,
    help="Preview cleanup without deleting anything."
)
def quick(dry_run: bool) -> None:
    """Quick cleanup of safe items only (caches, logs)."""
    display_banner()
    
    if dry_run:
        warning("DRY RUN MODE - No files will be deleted")
        console.print()
    
    divider("Quick Cleanup")
    
    info("Cleaning system caches and logs...")
    console.print()
    
    cleaner = MacCleaner(dry_run=dry_run, state_dir=str(settings.STATE_DIR))
    progress = cleaner.quick_clean()
    
    display_cleanup_summary(progress, dry_run=dry_run)


@cli.command()
def interactive() -> None:
    """Interactive menu-driven cleanup."""
    display_banner()
    divider("Interactive Mode")
    
    scanner = MacScanner(settings.HOME_DIR)
    result = scanner.scan(include_dangerous=True)
    
    if not result.targets:
        success("Your system is already clean!")
        return
    
    display_scan_summary(result)
    display_category_selection_menu(result)
    
    category_list = list(result.category_sizes().keys())
    
    console.print("[bold]Enter category numbers to clean (comma-separated), or 'all':[/bold]")
    selection = console.input("[cyan]> [/cyan]").strip().lower()
    
    if selection == "all":
        targets_to_clean = result.targets
    elif selection in ("q", "quit", "exit"):
        info("Cleanup cancelled.")
        return
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            selected_categories = {category_list[i] for i in indices if 0 <= i < len(category_list)}
            targets_to_clean = [t for t in result.targets if t.category in selected_categories]
        except (ValueError, IndexError):
            error("Invalid selection")
            return
    
    if not targets_to_clean:
        warning("No items selected")
        return
    
    total_size = sum(t.size_bytes for t in targets_to_clean)
    
    console.print()
    proceed = Confirm.ask(
        f"[bold]Clean {len(targets_to_clean)} items "
        f"([cyan]{total_size / (1024*1024*1024):.2f} GB[/cyan])?[/bold]"
    )
    
    if not proceed:
        info("Cleanup cancelled.")
        return
    
    settings.ensure_state_dir()
    cleaner = MacCleaner(state_dir=str(settings.STATE_DIR))
    
    divider("Cleaning")
    progress = cleaner.clean_targets(targets_to_clean, interactive=True)
    
    display_cleanup_summary(progress)


@cli.command()
def status() -> None:
    """Show checkpoint status and resume info."""
    display_banner()
    
    from src.utils.checkpoint_manager import CheckpointManager
    
    checkpoint_file = settings.STATE_DIR / "cleanup.checkpoint.json"
    
    if checkpoint_file.exists():
        manager = CheckpointManager("cleanup", settings.STATE_DIR)
        checkpoint = manager.load()
        
        if checkpoint:
            console.print("[bold cyan]Active Checkpoint Found[/bold cyan]\n")
            console.print(f"  Timestamp: [cyan]{checkpoint.get('timestamp', 'unknown')}[/cyan]")
            console.print(f"  Processed: [green]{len(checkpoint.get('processed_paths', []))}[/green] items")
            console.print(f"  Failed: [red]{len(checkpoint.get('failed_paths', []))}[/red] items")
            console.print(f"  Skipped: [yellow]{len(checkpoint.get('skipped_paths', []))}[/yellow] items")
            console.print()
            console.print("Run [bold]macpurge clean --resume[/bold] to continue")
            console.print("Run [bold]macpurge clean --fresh[/bold] to start over")
    else:
        info("No active checkpoint found")


@cli.command()
def clear_checkpoint() -> None:
    """Clear any existing checkpoint data."""
    from src.utils.checkpoint_manager import CheckpointManager
    
    manager = CheckpointManager("cleanup", settings.STATE_DIR)
    
    if manager.exists():
        manager.clear()
        success("Checkpoint cleared")
    else:
        info("No checkpoint to clear")


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
