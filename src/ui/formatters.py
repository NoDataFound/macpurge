"""
Display formatters for scan results and cleanup summaries.
"""

from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.models.cleanup import CleanupCategory, ScanResult, CleanupProgress
from src.ui.styles import console, SYNTHWAVE_COLORS, success, warning, info


CATEGORY_LABELS = {
    CleanupCategory.CACHE: "Caches",
    CleanupCategory.LOGS: "Logs",
    CleanupCategory.PYTHON_VENV: "Python Environments",
    CleanupCategory.NODE_MODULES: "Node Modules",
    CleanupCategory.BREW: "Homebrew",
    CleanupCategory.DOCKER: "Docker",
    CleanupCategory.XCODE: "Xcode",
    CleanupCategory.APPLICATION_SUPPORT: "Application Support",
    CleanupCategory.TRASH: "Trash",
    CleanupCategory.DOWNLOADS: "Downloads",
    CleanupCategory.DERIVED_DATA: "Derived Data",
}


def human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable size string."""
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    elif size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.2f} KB"
    return f"{size_bytes} B"


def display_scan_summary(result: ScanResult) -> None:
    """Display a summary table of scan results by category."""
    table = Table(
        title="[bold #00D9FF]Scan Summary by Category[/bold #00D9FF]",
        border_style="#FF10F0",
        header_style="bold #7928CA",
        show_lines=True,
    )
    
    table.add_column("Category", style="#00D9FF")
    table.add_column("Items", justify="right", style="#00F0FF")
    table.add_column("Size", justify="right", style="#FF10F0")
    table.add_column("% of Total", justify="right", style="#7928CA")
    
    category_sizes = result.category_sizes()
    category_counts = result.by_category()
    
    sorted_categories = sorted(
        category_sizes.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    for category, size in sorted_categories:
        count = len(category_counts.get(category, []))
        percentage = (size / result.total_size_bytes * 100) if result.total_size_bytes > 0 else 0
        
        table.add_row(
            CATEGORY_LABELS.get(category, category.value),
            str(count),
            human_size(size),
            f"{percentage:.1f}%",
        )
    
    console.print(table)
    console.print()
    
    total_panel = Panel(
        Text.assemble(
            ("Total Reclaimable: ", "bold white"),
            (result.human_total_size, f"bold {SYNTHWAVE_COLORS['cyan']}"),
            (" across ", "white"),
            (str(len(result.targets)), f"bold {SYNTHWAVE_COLORS['magenta']}"),
            (" items", "white"),
        ),
        border_style="#00D9FF",
    )
    console.print(total_panel)


def display_detailed_results(result: ScanResult, limit: int = 20) -> None:
    """Display detailed list of cleanup targets."""
    table = Table(
        title="[bold #00D9FF]Top Cleanup Targets[/bold #00D9FF]",
        border_style="#FF10F0",
        header_style="bold #7928CA",
    )
    
    table.add_column("#", style="dim", width=4)
    table.add_column("Path", style="#00D9FF", max_width=50)
    table.add_column("Category", style="#7928CA")
    table.add_column("Size", justify="right", style="#FF10F0")
    table.add_column("Safe", justify="center")
    
    for i, target in enumerate(result.targets[:limit], 1):
        path_display = str(target.path).replace(str(target.path.home()), "~")
        if len(path_display) > 50:
            path_display = "..." + path_display[-47:]
        
        safe_indicator = (
            f"[#00D9FF]\u2713[/#00D9FF]"
            if target.safe_to_delete and not target.requires_confirmation
            else f"[#F7FF00]\u26a0[/#F7FF00]"
        )
        
        table.add_row(
            str(i),
            path_display,
            CATEGORY_LABELS.get(target.category, target.category.value),
            target.human_size,
            safe_indicator,
        )
    
    console.print(table)
    
    if len(result.targets) > limit:
        info(f"Showing top {limit} of {len(result.targets)} items")


def display_cleanup_summary(progress: CleanupProgress, dry_run: bool = False) -> None:
    """Display cleanup operation summary."""
    console.print()
    
    if dry_run:
        title = "[bold #F7FF00]Dry Run Summary[/bold #F7FF00]"
    else:
        title = "[bold #00D9FF]Cleanup Complete[/bold #00D9FF]"
    
    table = Table(title=title, border_style="#FF10F0")
    
    table.add_column("Metric", style="#7928CA")
    table.add_column("Value", justify="right", style="#00D9FF")
    
    table.add_row("Items Processed", str(progress.processed_items))
    table.add_row("Space Freed", human_size(progress.deleted_bytes))
    table.add_row("Failed Items", str(len(progress.failed_items)))
    table.add_row("Skipped Items", str(len(progress.skipped_items)))
    
    console.print(table)
    
    if progress.failed_items:
        console.print()
        warning(f"Failed to clean {len(progress.failed_items)} items:")
        for path in progress.failed_items[:5]:
            console.print(f"  [dim]{path}[/dim]")
        if len(progress.failed_items) > 5:
            console.print(f"  [dim]... and {len(progress.failed_items) - 5} more[/dim]")


def display_category_selection_menu(result: ScanResult) -> None:
    """Display interactive category selection menu."""
    console.print("\n[bold #00D9FF]Available Categories:[/bold #00D9FF]\n")
    
    category_sizes = result.category_sizes()
    category_counts = result.by_category()
    
    for i, (category, size) in enumerate(
        sorted(category_sizes.items(), key=lambda x: x[1], reverse=True), 1
    ):
        count = len(category_counts.get(category, []))
        label = CATEGORY_LABELS.get(category, category.value)
        
        console.print(
            f"  [#00D9FF]{i:2}[/#00D9FF] "
            f"[#7928CA]{label:25}[/#7928CA] "
            f"[#FF10F0]{human_size(size):>12}[/#FF10F0] "
            f"[dim]({count} items)[/dim]"
        )
    
    console.print()
