"""
Data models for Mac Cleaner scan results and cleanup targets.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class CleanupCategory(Enum):
    """Categories of cleanable items."""
    CACHE = "cache"
    LOGS = "logs"
    PYTHON_VENV = "python_venv"
    NODE_MODULES = "node_modules"
    BREW = "brew"
    DOCKER = "docker"
    XCODE = "xcode"
    APPLICATION_SUPPORT = "app_support"
    TRASH = "trash"
    DOWNLOADS = "downloads"
    DERIVED_DATA = "derived_data"


@dataclass
class CleanupTarget:
    """Represents a single cleanup target location."""
    path: Path
    category: CleanupCategory
    size_bytes: int
    description: str
    safe_to_delete: bool = True
    requires_confirmation: bool = False
    
    @property
    def size_mb(self) -> float:
        """Return size in megabytes."""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def size_gb(self) -> float:
        """Return size in gigabytes."""
        return self.size_bytes / (1024 * 1024 * 1024)
    
    @property
    def human_size(self) -> str:
        """Return human-readable size string."""
        if self.size_gb >= 1:
            return f"{self.size_gb:.2f} GB"
        elif self.size_mb >= 1:
            return f"{self.size_mb:.2f} MB"
        else:
            return f"{self.size_bytes / 1024:.2f} KB"


@dataclass
class ScanResult:
    """Results from a cleanup scan operation."""
    targets: list[CleanupTarget] = field(default_factory=list)
    total_size_bytes: int = 0
    scan_errors: list[str] = field(default_factory=list)
    
    def add_target(self, target: CleanupTarget) -> None:
        """Add a cleanup target to results."""
        self.targets.append(target)
        self.total_size_bytes += target.size_bytes
    
    @property
    def total_size_gb(self) -> float:
        """Return total size in gigabytes."""
        return self.total_size_bytes / (1024 * 1024 * 1024)
    
    @property
    def human_total_size(self) -> str:
        """Return human-readable total size."""
        if self.total_size_gb >= 1:
            return f"{self.total_size_gb:.2f} GB"
        else:
            return f"{self.total_size_bytes / (1024 * 1024):.2f} MB"
    
    def by_category(self) -> dict[CleanupCategory, list[CleanupTarget]]:
        """Group targets by category."""
        grouped: dict[CleanupCategory, list[CleanupTarget]] = {}
        for target in self.targets:
            if target.category not in grouped:
                grouped[target.category] = []
            grouped[target.category].append(target)
        return grouped
    
    def category_sizes(self) -> dict[CleanupCategory, int]:
        """Get total size per category."""
        sizes: dict[CleanupCategory, int] = {}
        for target in self.targets:
            if target.category not in sizes:
                sizes[target.category] = 0
            sizes[target.category] += target.size_bytes
        return sizes


@dataclass
class CleanupProgress:
    """Track cleanup operation progress."""
    total_items: int = 0
    processed_items: int = 0
    deleted_bytes: int = 0
    failed_items: list[str] = field(default_factory=list)
    skipped_items: list[str] = field(default_factory=list)
    
    @property
    def deleted_gb(self) -> float:
        """Return deleted size in gigabytes."""
        return self.deleted_bytes / (1024 * 1024 * 1024)
