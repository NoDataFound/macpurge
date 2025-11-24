"""
Synthwave-themed console styling for Mac Cleaner.
"""

from rich.console import Console
from rich.theme import Theme

SYNTHWAVE_COLORS = {
    "cyan": "#00D9FF",
    "magenta": "#FF10F0",
    "purple": "#7928CA",
    "pink": "#FF0080",
    "electric_blue": "#00F0FF",
    "neon_yellow": "#F7FF00",
    "hot_pink": "#FF006E",
}

synthwave_theme = Theme(
    {
        "success": f"bold {SYNTHWAVE_COLORS['cyan']}",
        "error": f"bold {SYNTHWAVE_COLORS['hot_pink']}",
        "warning": f"bold {SYNTHWAVE_COLORS['magenta']}",
        "info": f"bold {SYNTHWAVE_COLORS['purple']}",
        "highlight": f"bold {SYNTHWAVE_COLORS['electric_blue']}",
        "accent": f"bold {SYNTHWAVE_COLORS['neon_yellow']}",
        "muted": "dim white",
        "path": f"italic {SYNTHWAVE_COLORS['cyan']}",
        "size": f"bold {SYNTHWAVE_COLORS['magenta']}",
        "category": f"bold {SYNTHWAVE_COLORS['purple']}",
    }
)

console = Console(theme=synthwave_theme)

# Unicode characters as constants (avoids f-string backslash issues in Python 3.9)
CHECKMARK = "\u2713"
CROSS = "\u2717"
WARNING_SIGN = "\u26a0"
INFO_SIGN = "\u2139"
DIAMOND = "\u25c6"
HEXAGON = "\u2b22"
DOUBLE_LINE = "\u2550"


def success(message: str) -> None:
    """Print a success message with cyan checkmark."""
    console.print(f"[success]{CHECKMARK}[/success] {message}")


def error(message: str) -> None:
    """Print an error message with hot pink X."""
    console.print(f"[error]{CROSS}[/error] {message}")


def warning(message: str) -> None:
    """Print a warning message with magenta warning symbol."""
    console.print(f"[warning]{WARNING_SIGN}[/warning] {message}")


def info(message: str) -> None:
    """Print an info message with purple info symbol."""
    console.print(f"[info]{INFO_SIGN}[/info] {message}")


def processing(message: str) -> None:
    """Print a processing message with electric blue diamond."""
    console.print(f"[highlight]{DIAMOND}[/highlight] {message}")


def checkpoint(message: str) -> None:
    """Print a checkpoint message with neon yellow hexagon."""
    console.print(f"[accent]{HEXAGON}[/accent] {message}")


def divider(title: str = "") -> None:
    """Print a synthwave-styled divider."""
    line = DOUBLE_LINE * 50
    if title:
        console.print(f"\n[magenta]{DOUBLE_LINE * 3}[/magenta] [bold cyan]{title}[/bold cyan] [magenta]{line}[/magenta]\n")
    else:
        console.print(f"[magenta]{DOUBLE_LINE * 60}[/magenta]")