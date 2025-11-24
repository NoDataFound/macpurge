"""
ASCII banner generation for Mac Cleaner.
"""

import pyfiglet
from rich.text import Text

from src.ui.styles import console, SYNTHWAVE_COLORS


def create_gradient_banner(app_name: str = "MacPurge") -> Text:
    """Create a synthwave gradient ASCII banner."""
    ascii_art = pyfiglet.figlet_format(app_name, font="slant")
    lines = ascii_art.split("\n")
    
    gradient_colors = [
        SYNTHWAVE_COLORS["cyan"],
        SYNTHWAVE_COLORS["electric_blue"],
        SYNTHWAVE_COLORS["purple"],
        SYNTHWAVE_COLORS["magenta"],
        SYNTHWAVE_COLORS["pink"],
        SYNTHWAVE_COLORS["hot_pink"],
    ]
    
    styled_text = Text()
    for i, line in enumerate(lines):
        if line.strip():
            color_index = i % len(gradient_colors)
            styled_text.append(line + "\n", style=gradient_colors[color_index])
    
    return styled_text


def display_banner() -> None:
    """Display the full startup banner with version and tagline."""
    console.print()
    console.print(create_gradient_banner())
    console.print(
        "[bold cyan]v1.0.0[/bold cyan] [muted]|[/muted] "
        "[bold magenta]Reclaim Your Storage[/bold magenta]"
    )
    console.print(
        "[muted]Intelligent macOS cleanup with checkpoint/resume support[/muted]"
    )
    console.print()
