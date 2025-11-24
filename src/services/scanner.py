"""
Scanner service for finding cleanup targets on macOS.
"""

import os
import subprocess
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from src.models.cleanup import CleanupCategory, CleanupTarget, ScanResult
from src.ui.styles import console, info, warning, processing


class MacScanner:
    """Scans macOS system for cleanable files and directories."""
    
    def __init__(self, home_dir: Path | None = None) -> None:
        """
        Initialize scanner with home directory.
        
        Args:
            home_dir: Home directory to scan. Defaults to current user's home.
        """
        self.home = home_dir or Path.home()
        self.library = self.home / "Library"
        
        self.scan_targets: list[dict] = [
            {
                "path": self.library / "Caches",
                "category": CleanupCategory.CACHE,
                "description": "Application caches - safe to delete",
                "scan_subdirs": True,
            },
            {
                "path": self.library / "Logs",
                "category": CleanupCategory.LOGS,
                "description": "System and application logs",
                "scan_subdirs": True,
            },
            {
                "path": self.home / ".cache",
                "category": CleanupCategory.CACHE,
                "description": "User cache directory",
                "scan_subdirs": True,
            },
            {
                "path": self.library / "Developer" / "Xcode" / "DerivedData",
                "category": CleanupCategory.DERIVED_DATA,
                "description": "Xcode build artifacts",
                "scan_subdirs": False,
            },
            {
                "path": self.library / "Developer" / "CoreSimulator" / "Devices",
                "category": CleanupCategory.XCODE,
                "description": "iOS Simulator devices",
                "scan_subdirs": False,
                "requires_confirmation": True,
            },
            {
                "path": self.home / ".Trash",
                "category": CleanupCategory.TRASH,
                "description": "Trash folder",
                "scan_subdirs": False,
            },
            {
                "path": self.home / "Downloads",
                "category": CleanupCategory.DOWNLOADS,
                "description": "Downloads folder",
                "scan_subdirs": True,
                "requires_confirmation": True,
            },
        ]
        
        self.python_patterns = [
            ".venv",
            "venv",
            ".virtualenv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "*.egg-info",
        ]
        
        self.node_patterns = [
            "node_modules",
            ".npm",
            ".yarn",
        ]
    
    def get_directory_size(self, path: Path) -> int:
        """
        Get total size of a directory in bytes.
        
        Args:
            path: Path to directory.
            
        Returns:
            Total size in bytes.
        """
        if not path.exists():
            return 0
        
        try:
            result = subprocess.run(
                ["du", "-sk", str(path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                size_kb = int(result.stdout.split()[0])
                return size_kb * 1024
        except (subprocess.TimeoutExpired, ValueError, IndexError):
            pass
        
        total = 0
        try:
            for entry in path.rglob("*"):
                try:
                    if entry.is_file():
                        total += entry.stat().st_size
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            pass
        
        return total
    
    def find_python_environments(self) -> list[CleanupTarget]:
        """Find Python virtual environments and caches."""
        targets: list[CleanupTarget] = []
        
        search_dirs = [
            self.home,
            self.home / "Projects",
            self.home / "code",
            self.home / "dev",
            self.home / "repos",
            self.home / "Repositories",
            self.home / "Documents",
        ]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            try:
                for pattern in [".venv", "venv", ".virtualenv"]:
                    for venv_path in search_dir.rglob(pattern):
                        if venv_path.is_dir() and (venv_path / "bin" / "python").exists():
                            size = self.get_directory_size(venv_path)
                            if size > 1024 * 1024:
                                targets.append(
                                    CleanupTarget(
                                        path=venv_path,
                                        category=CleanupCategory.PYTHON_VENV,
                                        size_bytes=size,
                                        description=f"Python venv in {venv_path.parent.name}",
                                        requires_confirmation=True,
                                    )
                                )
                
                for pycache in search_dir.rglob("__pycache__"):
                    if pycache.is_dir():
                        size = self.get_directory_size(pycache)
                        if size > 0:
                            targets.append(
                                CleanupTarget(
                                    path=pycache,
                                    category=CleanupCategory.CACHE,
                                    size_bytes=size,
                                    description="Python bytecode cache",
                                )
                            )
            except PermissionError:
                continue
        
        pyenv_path = self.home / ".pyenv"
        if pyenv_path.exists():
            size = self.get_directory_size(pyenv_path)
            targets.append(
                CleanupTarget(
                    path=pyenv_path,
                    category=CleanupCategory.PYTHON_VENV,
                    size_bytes=size,
                    description="pyenv Python versions",
                    requires_confirmation=True,
                    safe_to_delete=False,
                )
            )
        
        return targets
    
    def find_node_modules(self) -> list[CleanupTarget]:
        """Find node_modules directories."""
        targets: list[CleanupTarget] = []
        
        search_dirs = [
            self.home / "Projects",
            self.home / "code",
            self.home / "dev",
            self.home / "repos",
            self.home / "Repositories",
            self.home / "Documents",
        ]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            try:
                for node_modules in search_dir.rglob("node_modules"):
                    if node_modules.is_dir():
                        parent_package = node_modules.parent / "package.json"
                        if parent_package.exists():
                            size = self.get_directory_size(node_modules)
                            if size > 10 * 1024 * 1024:
                                targets.append(
                                    CleanupTarget(
                                        path=node_modules,
                                        category=CleanupCategory.NODE_MODULES,
                                        size_bytes=size,
                                        description=f"node_modules in {node_modules.parent.name}",
                                        requires_confirmation=True,
                                    )
                                )
            except PermissionError:
                continue
        
        return targets
    
    def check_docker(self) -> CleanupTarget | None:
        """Check Docker disk usage."""
        try:
            result = subprocess.run(
                ["docker", "system", "df", "--format", "{{.Size}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if lines:
                    total_str = lines[0]
                    if "GB" in total_str:
                        size_gb = float(total_str.replace("GB", "").strip())
                        size_bytes = int(size_gb * 1024 * 1024 * 1024)
                    elif "MB" in total_str:
                        size_mb = float(total_str.replace("MB", "").strip())
                        size_bytes = int(size_mb * 1024 * 1024)
                    else:
                        return None
                    
                    if size_bytes > 100 * 1024 * 1024:
                        return CleanupTarget(
                            path=Path("/var/lib/docker"),
                            category=CleanupCategory.DOCKER,
                            size_bytes=size_bytes,
                            description="Docker images, containers, and volumes",
                            requires_confirmation=True,
                        )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return None
    
    def check_homebrew(self) -> CleanupTarget | None:
        """Check Homebrew cache size."""
        brew_cache = Path.home() / "Library" / "Caches" / "Homebrew"
        if not brew_cache.exists():
            brew_cache = Path("/usr/local/Homebrew/cache")
        
        if brew_cache.exists():
            size = self.get_directory_size(brew_cache)
            if size > 100 * 1024 * 1024:
                return CleanupTarget(
                    path=brew_cache,
                    category=CleanupCategory.BREW,
                    size_bytes=size,
                    description="Homebrew download cache",
                )
        
        return None
    
    def scan(self, include_dangerous: bool = False) -> ScanResult:
        """
        Perform full system scan for cleanup targets.
        
        Args:
            include_dangerous: Include items that require extra confirmation.
            
        Returns:
            ScanResult containing all found targets.
        """
        result = ScanResult()
        
        scan_items = [
            ("System caches", self._scan_system_targets),
            ("Python environments", self.find_python_environments),
            ("Node modules", self.find_node_modules),
            ("Docker", lambda: [self.check_docker()] if self.check_docker() else []),
            ("Homebrew", lambda: [self.check_homebrew()] if self.check_homebrew() else []),
        ]
        
        with Progress(
            SpinnerColumn(spinner_name="dots", style="bold cyan"),
            TextColumn("[bold purple]{task.description}[/bold purple]"),
            BarColumn(complete_style="cyan", finished_style="magenta"),
            console=console,
        ) as progress:
            task = progress.add_task("Scanning...", total=len(scan_items))
            
            for name, scan_func in scan_items:
                progress.update(task, description=f"Scanning {name}...")
                try:
                    targets = scan_func()
                    if isinstance(targets, list):
                        for target in targets:
                            if target:
                                if include_dangerous or not target.requires_confirmation:
                                    result.add_target(target)
                                elif target.requires_confirmation:
                                    result.add_target(target)
                except Exception as e:
                    result.scan_errors.append(f"Error scanning {name}: {str(e)}")
                
                progress.advance(task)
        
        result.targets.sort(key=lambda t: t.size_bytes, reverse=True)
        
        return result
    
    def _scan_system_targets(self) -> list[CleanupTarget]:
        """Scan predefined system target locations."""
        targets: list[CleanupTarget] = []
        
        for target_config in self.scan_targets:
            path = target_config["path"]
            if not path.exists():
                continue
            
            if target_config.get("scan_subdirs", False):
                try:
                    for subdir in path.iterdir():
                        if subdir.is_dir():
                            size = self.get_directory_size(subdir)
                            if size > 10 * 1024 * 1024:
                                targets.append(
                                    CleanupTarget(
                                        path=subdir,
                                        category=target_config["category"],
                                        size_bytes=size,
                                        description=f"{target_config['description']} ({subdir.name})",
                                        requires_confirmation=target_config.get(
                                            "requires_confirmation", False
                                        ),
                                    )
                                )
                except PermissionError:
                    continue
            else:
                size = self.get_directory_size(path)
                if size > 10 * 1024 * 1024:
                    targets.append(
                        CleanupTarget(
                            path=path,
                            category=target_config["category"],
                            size_bytes=size,
                            description=target_config["description"],
                            requires_confirmation=target_config.get(
                                "requires_confirmation", False
                            ),
                        )
                    )
        
        return targets
